import configparser
import pymysql
import logging
import random
from functools import reduce
import sys
from functools import cmp_to_key
from utils import hash_str
from utils import encode_id
config = configparser.ConfigParser()
config.read('./merge/merge.ini')


# Connect to database merge
merge_database_setting = config['merge Database']
connection_merge = pymysql.connect(
    host=merge_database_setting['MYSQL_HOST'],
    user=merge_database_setting['MYSQL_USER'],
    password=merge_database_setting['MYSQL_PASSWORD'],
    db=merge_database_setting['MYSQL_DBNAME'],
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor,
    port=int(merge_database_setting['MYSQL_PORT']))

# Connect to database_ieee
ieee_database_setting = config['IEEE Database']
connection_ieee = pymysql.connect(
    host=ieee_database_setting['MYSQL_HOST'],
    user=ieee_database_setting['MYSQL_USER'],
    password=ieee_database_setting['MYSQL_PASSWORD'],
    db=ieee_database_setting['MYSQL_DBNAME'],
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor,
    port=int(ieee_database_setting['MYSQL_PORT']))

# Connect to database_acm
acm_database_setting = config['ACM Database']
connection_acm = pymysql.connect(
    host=acm_database_setting['MYSQL_HOST'],
    user=acm_database_setting['MYSQL_USER'],
    password=acm_database_setting['MYSQL_PASSWORD'],
    db=acm_database_setting['MYSQL_DBNAME'],
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor,
    port=int(acm_database_setting['MYSQL_PORT']))


def my_select(connection, sql):
    try:
        cursor = connection.cursor()
        cursor.execute(sql)
        res = cursor.fetchall()
        return res
    except Exception as e:
        logging.warning('error in select, sql {}'.format(sql))
        connection.rollback()
        raise e
    finally:
        cursor.close()

def my_insert_many(connection, sql, values):
    try:
        cursor = connection.cursor()
        cursor.executemany(sql, values)
        connection.commit()
    except pymysql.err.IntegrityError as e:
        logging.warning(e.args[1])
    except Exception as e:
        logging.warning('error in insert, sql {}'.format(sql))
        connection.rollback()
        raise e
    finally:
        cursor.close()


def get_same_from_it(src, target, is_equal = lambda src_item, target_item: src_item == target_item):
    """
    从可迭代对象中找出某个元素（自定义相等），没有则返回None
    """
    for i in src:
        if is_equal(i, target):
            return i
    return None

def change_merge_map(from_list, to_list, mapping_list, change = lambda x: x, update = lambda x, y: x, is_equal = lambda x, y: x == y, src = 'unknown', equal_callback = lambda x, y: None):
    """
    将一个list所有的元素做变化（change），加入另一之中（merge），重复的不加入（通过函数定义），每次记录对应（mapping）
    必须有id
    src 为来源标识（比如，acm， ieee）
    """
    for item in from_list:
        new_main_record = item.copy()
        new_main_record = change(new_main_record)
        main_record = get_same_from_it(to_list, new_main_record, is_equal)
        if main_record != None:
            # 已有记录
            main_record = update(main_record, item)
            mapping_list.append((
                main_record['id'],
                item['id'],
                src,
                True
            ))
            # 所有其他的对应的也认为是 true
            for i in mapping_list:
                if i[0] == main_record['id'] and i[3] == False:
                    new_map_record = (i[0], i[1], i[2], True)
                    mapping_list.remove(i)
                    mapping_list.append(new_map_record)
                    break
            equal_callback(main_record, item)
            logging.info('found equal{},{}'.format(main_record, item))
        else:
            to_list.append(new_main_record)
            mapping_list.append((
                new_main_record['id'],
                item['id'],
                src,
                False
            ))

def change_ieee_id(item):
    item['id'] = hash_str('ieee' + item['id'])
    return item

def change_acm_id(item):
    item['id'] = hash_str('acm' + item['id'])
    return item


def merge_publication():
    # merge publication by name and publication time
    publications_ieee = my_select(connection_ieee, 'select * from publication')
    publications_acm = my_select(connection_acm, 'select * from publication')
    publications = []
    publication_mapping = []

    change_merge_map(publications_ieee, publications, publication_mapping, change=change_ieee_id, is_equal=lambda x, y: x['name'] == y['name'] and x['publication_date'] == y['publication_date'], src='IEEE')

    change_merge_map(publications_acm, publications, publication_mapping, change=change_acm_id, is_equal=lambda x, y: x['name'] == y['name'] and x['publication_date'] == y['publication_date'], src='ACM')

    # 按照下面 sql 对应顺序把字典改为元组
    publications = map(
        lambda x: (x['id'], x['name'], x['publication_date'], str(random.uniform(0, 1))),
        publications
    )
    my_insert_many(connection_merge, 'insert ignore into publication_mapping values(%s, %s, %s, %s)', publication_mapping)
    my_insert_many(connection_merge, 'insert ignore into publication(`id`, `name`, `publication_date`, `impact`) VALUES(%s, %s, %s, %s)', publications)
    return publication_mapping


def merge_paper():
    # paper
    # TODO: 也许全加载到内存不是一个好主意。以后再重构。
    paper_mapping = []
    papers = []
    paper_ieee = my_select(connection_ieee, 'select * from paper')
    paper_acm = my_select(connection_acm, 'select * from paper')

    def paper_is_equal(p1, p2):
        """
        return true if two paper is the same paper
        """
        if p1.get('doi') == p2.get('doi') and p1.get('doi') != None:
            return True
        if p1['title'] == p2['title']:
            return True
        return False
    def update_paper(main_record, new_record):
        if main_record['link'] == None:
            main_record['link'] = new_record['link']
        if main_record['doi'] == None:
            main_record['doi'] = new_record['doi']
        return main_record
    change_merge_map(paper_ieee, papers, paper_mapping, change=change_ieee_id, is_equal=paper_is_equal, src='IEEE', update=update_paper)
    change_merge_map(paper_acm, papers, paper_mapping, change=change_acm_id, is_equal=paper_is_equal, src='ACM', update=update_paper)

    for paper in papers:
        # map the publication id
        publication_map_record = get_same_from_it(publication_mapping, paper, lambda x, y: x[1] == y['publication_id'])
        if publication_map_record != None:
            paper['publication_id'] = publication_map_record[0]
        else:
            logging.warning('paper with no publication id in publication table paper id {}'.format(paper['id']))

    papers = map(
        lambda x: (
            x['id'],
            x['title'],
            x['abs'],
            x['publication_id'],
            x['publication_date'],
            x['link'],
            x['doi'],
            x['citation'],
        ),
        papers
    )

    my_insert_many(connection_merge, 'insert ignore into paper(id, title, abs, publication_id, publication_date, link, doi, citation) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)', papers)
    my_insert_many(connection_merge, 'insert ignore into paper_mapping(id_main, id, src, merged) values(%s, %s, %s, %s)', paper_mapping)
    return paper_mapping



def map_paper_id(id):
    """
    把分库 paper id 对应到合并库 id
    """
    for paper_map in paper_mapping:
        if(paper_map[1] == id):
            return paper_map[0]
    return 0

def merge_domain():
    ieee_domain = my_select(connection_ieee, 'select * from domain')
    acm_domain = my_select(connection_acm, 'select * from domain')
    ieee_paper_domain = my_select(connection_ieee, 'select * from paper_domain')
    acm_paper_domain = my_select(connection_acm, 'select * from paper_domain')
    domain = ieee_domain + acm_domain
    domain = map(lambda x: (
        x['id'], x['name'], x['url']
    ), domain)
    def paper_domain_map_paper_id(paper_domain):
        paper_domain['pid'] = map_paper_id(paper_domain['pid'])
        return paper_domain
    paper_domain = map(paper_domain_map_paper_id, ieee_paper_domain + acm_paper_domain)
    paper_domain = map(lambda x: (x['pid'], x['did']), paper_domain)
    my_insert_many(connection_merge, 'insert ignore into domain(id, name, url) values(%s, %s, %s)', domain)
    my_insert_many(connection_merge, 'insert ignore into paper_domain(pid, did) values(%s, %s)', paper_domain)

def merge_affiliation():
    ieee_affiliation = my_select(connection_ieee, 'select * from affiliation')
    acm_affiliation = my_select(connection_acm, 'select * from affiliation')
    affiliation = map(lambda x:(
        x['id'], x['name'], x['description']
    ), ieee_affiliation + acm_affiliation)
    my_insert_many(connection_merge, 'insert ignore into affiliation(id, name, description) values(%s, %s, %s)', affiliation)

def merge_researcher(paper_mapping):
    ieee_researchers = my_select(connection_ieee, 'select * from researcher')
    acm_researchers = my_select(connection_acm, 'select * from researcher')
    ieee_researcher_paper = my_select(connection_ieee, 'select * from paper_researcher')
    acm_researcher_paper = my_select(connection_acm, 'select * from paper_researcher')
    # 新 id 到原 id 和 src 的映射
    researchers_id_mapping = {}
    researchers = []
    researchers_mapping = []
    
    # 通过字典记录从现id 到原 id 和 src 的映射
    for i in ieee_researchers:
        new_id = hash_str('ieee' + i['id'])
        researchers_id_mapping[new_id] = {'src_id':i['id'], 'src': 'ieee'}
        i['id'] = new_id
    for i in acm_researchers:
        new_id = hash_str('acm' + i['id'])
        researchers_id_mapping[new_id] = {'src_id':i['id'], 'src': 'acm'}
        i['id'] = new_id

    def map_paper_id_in_research_paper_ieee(record):
        """ 把一个 paper_researcher 中的 pid rid 进行修改
        """
        record['pid'] = map_paper_id(record['pid'])
        record['rid'] = hash_str('ieee' + record['rid'])
        return record
    
    def map_paper_id_in_research_paper_acm(record):
        record['pid'] = map_paper_id(record['pid'])
        record['rid'] = hash_str('acm' + record['rid'])
        return record

    # researcher_paper 合并，将其中的 pid rid 更改
    researcher_paper = list(map(map_paper_id_in_research_paper_ieee, ieee_researcher_paper))
    researcher_paper += list(map(map_paper_id_in_research_paper_acm, acm_researcher_paper))
    # 找不到 pid 的舍去
    researcher_paper = list(filter(lambda x: isinstance(x['pid'], str), researcher_paper))

    # 合并researcher
    paper_merged = list(filter(lambda x: x[3] and x[2] == 'ACM', paper_mapping))
    merged_paper_ids = list(map(lambda x: x[0], paper_merged))
    researcher_merge_info = []
    researcher_merge_sets_dict = {}
    for paper_id in merged_paper_ids:
        r_p = list(filter(lambda x, id = paper_id: x['pid'] == id, researcher_paper))
        result = {}
        for i in r_p:
            if i['order'] in result:
                result[i['order']].append(i['rid'])
            else:
                result[i['order']] = [i['rid'],]
        # 合并其中的researcher
        for i in result:
            if len(result[i]) > 1:
                if result[i][0] > result[i][1]:
                    researcher_merge_info.append([result[i][0], result[i][1]])
                else:
                    researcher_merge_info.append([result[i][1], result[i][0]])
    def cmp_researcher_set(x, y):
        if x[0] > y[0]:
            return 1
        if x[0] < y[0]:
            return -1
        if x[0][1] > y[0][1]:
            return 1
        if x[0][1] < y[0][1]:
            return -1
        return 0
    researcher_merge_info = sorted(researcher_merge_info, key=cmp_to_key(cmp_researcher_set))
    for i in researcher_merge_info:
        if i[0] in researcher_merge_sets_dict:
            researcher_merge_sets_dict[i[0]].add(i[1])
        else:
            researcher_merge_sets_dict[i[0]] = {i[0], i[1]}
    researcher_merge_sets_list = list(map(lambda x, r_dict=researcher_merge_sets_dict: r_dict[x], researcher_merge_sets_dict))
    researcher_2_set = {}
    for i in researcher_merge_sets_list:
        for j in i:
            researcher_2_set[j] = i
    def researcher_is_equal(r1, r2, r2s):
        if r1['id'] not in r2s or r2['id'] not in r2s:
            return False
        return r2s[r1['id']] == r2s[r2['id']]


    change_merge_map(
        ieee_researchers, 
        researchers, 
        researchers_mapping,
        is_equal=lambda x, y, r2s=researcher_2_set: researcher_is_equal(x, y, r2s),
        src='IEEE',
    )
    change_merge_map(
        acm_researchers, 
        researchers, 
        researchers_mapping,
        is_equal=lambda x, y, r2s=researcher_2_set: researcher_is_equal(x, y, r2s),
        src='ACM',
    )
    researchers_mapping = list(map(lambda x: list(x), researchers_mapping))
    dict_rid_2_researcher_mapping = {}
    for i in researchers_mapping:
        dict_rid_2_researcher_mapping[i[1]] = i

    for i in researchers_mapping:
        i[1] = researchers_id_mapping[i[1]]['src_id']


    # 将 researcher_paper 中被合并的 rid 扔掉
    def rm_merged_researchers(rp):
        return not dict_rid_2_researcher_mapping[rp['rid']][3]
    researcher_paper = list(filter(rm_merged_researchers, researcher_paper))
    researchers = list(map(lambda x: (
        x['id'],
        x['name']
    ), researchers))
    researcher_paper = list(map(lambda x: (
        x['pid'],
        x['rid'],
        x['order']
    ), researcher_paper))
    my_insert_many(connection_merge, 'insert ignore into researcher_mapping(id_main, id, src, merged) values(%s, %s, %s, %s)', researchers_mapping)
    my_insert_many(connection_merge, 'insert ignore into researcher(id, name) values(%s, %s)', researchers)
    my_insert_many(connection_merge, 'insert ignore into paper_researcher(`pid`, `rid`, `order`) values(%s, %s, %s)', researcher_paper)

    return researchers_mapping
            
    
publication_mapping = merge_publication()
paper_mapping = merge_paper()

merge_domain()
merge_affiliation()
researcher_mapping = merge_researcher(paper_mapping)

print('haha')