# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter, is_item
import json

from data_crawler.items import IEEEPaperItem, PaperItem, ACMPaperItem
from scrapy.exceptions import DropItem
from data_crawler.utils import hash_str as encode
from data_crawler.utils import remove_html

import pymysql
import datetime
from twisted.enterprise import adbapi
import logging



class DataCrawlerPipeline:
    def process_item(self, item, spider):
        return item

# 空的item去除
class RemoveEmptyItemPipeline:
    def process_item(self, item, spider):
        if item == None:
            raise DropItem("found none item")
        if isinstance(item, IEEEPaperItem) and (item.get('title') == None or item['authors'] == None):
            # TODO: 暂时对于空的paper的判断是通过是否有title来进行，可能要进行修改
            raise DropItem("Drop ieee paper item")
        return item


# 将所有的item保存为json。TODO: 其他正式的保存方式
class JsonWriterPipeline:
    def open_spider(self, spider):
        self.file = open('test_files/crawled_items.json', 'w')

    def close_spider(self, spider):
        self.file.close()

    def process_item(self, item, spider):
        line = json.dumps(ItemAdapter(item).asdict()) + "\n"
        self.file.write(line)
        return item

class ACMPaper2UnifyPipeline:
    """
    transfer ACM paper item to unify paper item
    """
    def process_item(self, item, spider):
        def get_acm_keywords(tree):
            """
            从ACM index tree中获得所有关键词
            """
            if tree == None:
                return []
            result = []
            if tree['url'] != None:
                # 根结点是没有url的，其title是文章标题
                result.append(tree['title'])
            for child in tree['child']:
                result.extend(get_acm_keywords(child))
            return result
        # 只处理ACMPaperItem
        if not isinstance(item, ACMPaperItem):
            return item
        paper = PaperItem()
        paper['title'] = item['title']

        order = 0
        paper['authors'] = []
        if 'authors' in item and item['authors'] != None:
            for author in item['authors']:
                order += 1
                if 'author_profile' not in author:
                    # 没有 id 的作者，暂时不考虑
                    continue
                author_profile_sp = author['author_profile'].split('/profile/')
                author_id = author_profile_sp[len(author_profile_sp) - 1] # d.g. "/profile/99659280949"
                paper_author = {
                    'id': author_id, 
                    'name': author['author_name'],
                    'order': order,
                    'affiliation': author.get('affiliation', [])
                }
                paper['authors'].append(paper_author)    
        paper['abstract'] = item['abstract']
        paper['publication_id'] = item['publication_id']
        paper['publicationTitle'] = item['publication_title']
        paper['doi'] = item['doi']
        paper['id'] = item['doi']
        paper['citation'] = item['citation']
        paper['publicationYear'] = item['year']
        paper['url'] = item['url']
        
        paper['references'] = []
        if 'references' in item and item['references'] != None:
            for reference in item['references']:
                ref = {
                    'order': reference.get('order', None),
                    'title': None,
                    'doi': None,
                    'ieee_document_id': None,
                    'citation': reference.get('reference_citation', None)
                }
                if 'reference_links' in reference:
                    for link in reference['reference_links']:
                        if link['link_type'] == 'Digital Library':
                            # logging.warning(link['link_type'])
                            # 形式可能是 "/doi/10.1109/TSE.2015.2419611" 或 "https://dl.acm.org/doi/10.1145/3092703.3092718"
                            link_element = link['link_url'].split('/')
                            ref['doi'] = link_element[len(link_element) - 2] + '/' + link_element[len(link_element) - 1]
                paper['references'].append(ref)
        
        paper['keywords'] = get_acm_keywords(item['index_term_tree'])

        return paper


class IEEEPaper2UnifyPipeline:
    """
    transfer IEEE paper item to unify paper item
    """
    def process_item(self, item, spider):
        # 只处理IEEEPaperItem
        if not isinstance(item, IEEEPaperItem):
            return item
        paper = PaperItem()
        paper['title'] = item['title']

        order = 0
        paper['authors'] = []
        if 'authors' in item and item['authors'] != None:
            for author in item['authors']:
                order += 1
                if 'id' not in author:
                    # 对于没有 id 的 author，暂时不考虑。
                    continue
                paper_author = {
                    'id': author['id'],
                    'name': author['name'],
                    'order': order,
                    'affiliation': author.get('affiliation', [])
                }
                paper['authors'].append(paper_author)
        paper['abstract'] = item['abstract']
        paper['publication_id'] = str(item['publication_number']) + '_' + str(item['issue_number'])
        paper['publicationTitle'] = item['publicationTitle']
        paper['doi'] = item['doi']
        paper['id'] = item['articleNumber']
        paper['citation'] = item['metrics']['citationCountPaper']
        paper['publicationYear'] = item['publicationYear']
        paper['url'] = item['url']

        # 对IEEE需要处理两种：crossRefLink acmLink. 第三种是document类型的，需要爬一个新的页面。
        paper['references'] = []
        if 'references' in item and item['references'] != None:
            for reference in item['references']:
                ref = {
                    'order': reference.get('order', None),
                    'title': reference.get('title', None),
                    'doi': None,
                    'ieee_document_id': None,
                    'citation': reference.get('text', None)
                }
                if 'links' in reference and reference['links'] != None:
                    if 'acmLink' in reference['links'] and 'https://doi.org/' in reference['links']['acmLink']:
                            ref['doi'] = reference['links']['acmLink'][16:]
                    if 'crossRefLink' in reference['links'] and 'https://doi.org/' in reference['links']['crossRefLink']:
                            # 不确定是否crossref都是doi开头，故只取doi的
                            ref['doi'] = reference['links']['crossRefLink'][16:] # remove https://doi.org/, 16 charactors
                    if 'documentLink' in reference['links']:
                        ref['ieee_document_id'] = reference['links']['documentLink'].split('/')[2]
                paper['references'].append(ref)


        # 将IEEE controlled index作为domain存储
        paper['keywords'] = []
        if 'keywords' in item and item['keywords'] != None:
            for keyword_group in item['keywords']:
                if keyword_group.get('type') == 'INSPEC: Controlled Indexing':
                    for controlled_index in keyword_group['kwd']:
                        paper['keywords'].append(controlled_index)
        return paper

class UnifyRmHTMLPipeline:
    """
    remove html in paper item
    """
    def process_item(self, item, spider):
        # 只处理PaperItem
        if not isinstance(item, PaperItem):
            return item
        item['title'] = remove_html(item['title'])
        item['abstract'] = remove_html(item['abstract'])
        return item

class UnifyPaperMysqlPipeline(object):
    def __init__(self, dbpool):
        self.dbpool = dbpool

    @classmethod
    def from_settings(cls, settings):  # 函数名固定，会被scrapy调用，直接可用settings的值
        """
        数据库建立连接
        :param settings: 配置参数
        :return: 实例化参数
        """
        adbparams = dict(
            host=settings['MYSQL_HOST'],
            db=settings['MYSQL_DBNAME'],
            user=settings['MYSQL_USER'],
            password=settings['MYSQL_PASSWORD'],
            cursorclass=pymysql.cursors.DictCursor,  # 指定cursor类型
            port=settings['MYSQL_PORT']
        )
        # 连接数据池ConnectionPool，使用pymysql连接
        dbpool = adbapi.ConnectionPool('pymysql', **adbparams)
        # 返回实例化参数
        return cls(dbpool)

    def process_item(self, item, spider):
        # 只处理PaperItem
        if not isinstance(item, PaperItem):
            return item
        """
        使用twisted将MySQL插入变成异步执行。通过连接池执行具体的sql操作，返回一个对象
        """
        
        query = self.dbpool.runInteraction(self.do_insert_paper, item)  # 指定操作方法和操作数据
        # 添加异常处理
        query.addCallback(self.handle_error)  # 处理异常

    def do_insert_paper(self, cursor, paper):
        """
        对数据库插入一篇文章，并不需要commit，twisted会自动commit
        """
        logging.debug('inserting paper doi "{}" to mysql'.format(paper['doi']))
        # insert database table: paper
        insert_sql = """
            insert into paper(id, title, abs, publication_id, publication_date, link, doi, citation) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)
                    """
        self.execute_sql(
            insert_sql, 
            (
                paper['id'],
                paper['title'],
                paper['abstract'],
                paper['publication_id'],
                paper['publicationYear'],
                paper['url'],
                paper['doi'],
                paper['citation']
            ),
            cursor
        )

        # insert database table: researcher paper_researcher affiliation researcher_affiliation
        # 学者的id为 数据库名_数据库内部ID 如IEEE_37086831215
        for author in paper['authors']:

            # insert database table: researcher
            insert_author_sql = """
                            insert into researcher(`id`, `name`) VALUES(%s, %s)
                            """
            self.execute_sql(
                insert_author_sql,
                (author['id'], author['name']),
                cursor
            )

            # insert database table: paper_researcher
            insert_paper_researcher_sql = """
                            insert into paper_researcher(`pid`, `rid`, `order`) VALUES(%s, %s, %s)
                            """
            self.execute_sql(
                insert_paper_researcher_sql,
                (paper['id'], author['id'], author['order']),
                cursor,
            )

            # insert database table: affiliation researcher_affiliation
            insert_affiliation_sql = """
            insert into affiliation(`id`, `name`)  VALUES(%s, %s)
            """
            insert_researcher_affiliation_sql = """
            insert into researcher_affiliation(`rid`, `aid`, `year`) VALUES(%s, %s, %s)
            """
            if author.get('affiliation') != None:
                for aff in author['affiliation']:
                    # insert database table: affiliation
                    self.execute_sql(
                        insert_affiliation_sql,
                        (encode(aff), aff),
                        cursor,
                    )

                    # insert database table: researcher_affiliation
                    self.execute_sql(
                        insert_researcher_affiliation_sql,
                        (author['id'], encode(aff), paper['publicationYear']),
                        cursor,
                    )
            

        # insert database table: domain paper_domain
        # TODO: 暂时把所有的关键词作为domain存储
        insert_domain_sql = """
        insert into domain(`id`, `name`) VALUES(%s, %s)
        """
        insert_paper_domain_sql = """
        insert into paper_domain(`pid`, `did`) VALUES(%s, %s)
        """
        for keyword in paper['keywords']:
            logging.debug('inserting keyword "{}" in paper doi:"{}" title:"{}"'.format(keyword, paper['doi'], paper['title']))
            self.execute_sql(
                insert_domain_sql, 
                (encode(keyword), keyword),
                cursor
            )
            # insert database table: paper_domain
            self.execute_sql(
                insert_paper_domain_sql, 
                (paper['id'], encode(keyword)),
                cursor
            )
            
        # insert database table: paper_reference
        # 将所有 reference 尽可能多的信息进行保存。1 对 n 关系。
        insert_paper_reference_sql = """
        insert into paper_reference(`pid`, `order`, `r_doi`, `r_title`, `r_document_id`, `r_citation`) VALUES(%s, %s, %s, %s, %s, %s)
        """
        for reference in paper['references']:
            self.execute_sql(
                insert_paper_reference_sql,
                (paper['id'], reference['order'], reference['doi'], reference['title'], reference['ieee_document_id'], reference['citation']),
                cursor
            )
        
        # insert database table: publication
        insert_publication_sql = """
        insert into publication(`id`, `name`, `publication_date`) VALUES(%s, %s, %s)
        """
        self.execute_sql(
            insert_publication_sql,
            (paper['publication_id'], paper['publicationTitle'], paper['publicationYear']),
            cursor
        )


    @staticmethod
    def execute_sql(sql, values, cursor):
        """
        callback_dupl_key是插入数据库时发现key重复时的回调函数(当且仅当传了这个参数)
        callback_dulp_key_args是一个iterable, unpack之后作为callback_dulp_key's arguments 
        """
        try:
            cursor.execute(sql, values)
        except pymysql.err.IntegrityError as e:
            if(e.args[0] == 1062):
                # 1062是pymysql duplicate key的错误码
                logging.debug(e)
            else:
                # TODO: other exceptions
                logging.warning(e)


    def handle_error(self, failure):
        if failure:
            # 打印错误信息
            print(failure)
            logging.error('$ messages from MysqlPipeline: ' + str(failure))

