# %%
import configparser
import pymysql
import logging
import sys
import os
sys.path.insert(0, os.getcwd())  
from merge.db_helper import db_helper
from merge.utils import solve_affiliation_name
from merge.utils import hash_str

# %%
config = configparser.ConfigParser()
config.read('/home/leo/Desktop/ASE/data-processing/merge/merge2.ini')
db = db_helper(config['merge Database'])

# %%
def change_affiliation(db: db_helper):
    affiliations = db.my_select('select * from affiliation')
    affiliations_mapping = []
    num_aff = len(affiliations)
    num_now = 0
    for aff in affiliations:
        num_now += 1
        if(num_now % 100 == 0):
            logging.warning('cleaning affiliations, {}/{}'.format(num_now, num_aff))
        new_name = solve_affiliation_name(aff['name'])
        new_id = hash_str(new_name)
        affiliations_mapping.append({
            'id': new_id,
            'name': new_name,
            'src_id': aff['id'],
            'src_name': aff['name'],
        })
        if new_name == aff['name']:
            continue
        main_record = db.my_select('select count(*) from affiliation where `id` = "{}"'.format(new_id))
        main_record_num = main_record[0]['count(*)']
        if main_record_num == 0:
            db.my_delete_update(
                """
                UPDATE affiliation SET id = "{}", name = "{}" WHERE `id` = "{}"
                """.format(new_id, new_name, aff['id'])
            )
            db.my_delete_update(
                """
                UPDATE researcher_affiliation SET aid = "{}" WHERE `aid` = "{}"
                """.format(new_id, aff['id'])
            )
        elif main_record_num == 1:
            # 并且不是自身 (由于new_name != aff['name'])
            db.my_delete_update(
                """
                delete from affiliation where `id` = "{}"
                """.format(aff['id'])
            )
            db.my_delete_update(
                """
                delete from researcher_affiliation WHERE `aid` = "{}"
                """.format(aff['id'])
            )
        else:
            logging.warning('duplite id in affiliation, id: "{}"'.format(new_id))

        

    affiliations_mapping_tuple = list(map(
        lambda x: (
            x['id'],
            x['name'],
            x['src_id'],
            x['src_name']
        ),
        affiliations_mapping
    ))

    db.my_insert_many(
        'INSERT IGNORE INTO affiliation_mapping(`id`, `name`, `src_id`, `src_name`) VALUES (%s, %s, %s, %s)',
        affiliations_mapping_tuple)
        
    print('haha')
        
change_affiliation(db)
# %%
db.my_delete_update("update paper set `publication_id` = '303c6505b0003fbe411e1ba2a57a07e6' where `publication_id` = '4237b0ea88597836adfb9bfa7884279d';")
# %%
