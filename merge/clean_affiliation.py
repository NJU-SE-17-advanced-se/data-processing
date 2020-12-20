# %%
import configparser
import pymysql
import logging
import sys
import os
sys.path.insert(0, os.path.join(os.getcwd(), "..")) 
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
    for aff in affiliations:
        new_name = solve_affiliation_name(aff['name'])
        new_id = hash_str(new_name)
        affiliations_mapping.append({
            'id': new_id,
            'name': new_name,
            'src_id': aff['id'],
            'src_name': aff['name'],
        })
        main_record = db.my_select('select count(*) from affiliation where `id` = "{}"'.format(new_id))
        if main_record[0]['count(*)'] == 0:
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
        else:
            # 已有那个 aff
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
