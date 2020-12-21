import sys
import os
sys.path.insert(0, os.getcwd()) 
from merge.db_helper import db_helper
import configparser

import unittest


class test_db(unittest.TestCase):
    __count_str = 'count(*)'

    @classmethod
    def setUpClass(cls):
        config = configparser.ConfigParser()
        config.read('./merge/merge.ini')
        database_setting = config['merge Database']
        cls.__db = db_helper(database_setting)

    def test_paper_domain(self):
        p_not_in_paper = self.__db.my_select('select count(*) from paper_domain where pid not in (select id from paper)')
        self.assertEqual(p_not_in_paper[0][self.__count_str], 0)

        d_not_in_domain = self.__db.my_select('select count(*) from paper_domain where did not in (select id from domain)')
        self.assertEqual(d_not_in_domain[0][self.__count_str], 0)
    
    def test_paper_mapping(self):
        id_main_not_in_paper = self.__db.my_select('select count(*) from paper_mapping where id_main not in (select id from paper)')
        self.assertEqual(id_main_not_in_paper[0][self.__count_str], 0)
    
    def test_paper_reference(self):
        rid_not_in_paper = self.__db.my_select('select count(*) from paper_reference where rid not in (select id from paper)')
        self.assertEqual(rid_not_in_paper[0][self.__count_str], 0)

        pid_not_in_paper = self.__db.my_select('select count(*) from paper_reference where pid not in (select id from paper)')
        self.assertEqual(pid_not_in_paper[0][self.__count_str], 0)

    def test_paper_researcher(self):
        rid_not_in_researcher = self.__db.my_select('select count(*) from paper_researcher where rid not in (select id from researcher)')
        self.assertEqual(rid_not_in_researcher[0][self.__count_str], 0)

        pid_not_in_paper = self.__db.my_select('select count(*) from paper_researcher where pid not in (select id from paper)')
        self.assertEqual(pid_not_in_paper[0][self.__count_str], 0)
    
    def test_researcher_affiliation(self):
        rid_not_in_researcher = self.__db.my_select('select count(*) from researcher_affiliation where rid not in (select id from researcher)')
        self.assertEqual(rid_not_in_researcher[0][self.__count_str], 0)

        aid_not_in_affiliation = self.__db.my_select('select count(*) from researcher_affiliation where aid not in (select id from affiliation)')
        self.assertEqual(aid_not_in_affiliation[0][self.__count_str], 0)
    
    def test_paper(self):
        pid_not_in_publication = self.__db.my_select('select count(*) from paper p where p.publication_id not in (select id from publication)')
        self.assertEqual(pid_not_in_publication[0][self.__count_str], 0)

    def test_researcher(self):
        # 没有文章的作者
        rid_not_in_paper_researcher = self.__db.my_select('select count(*) from researcher where id not in (select rid from paper_researcher);')
        self.assertEqual(rid_not_in_paper_researcher[0][self.__count_str], 0)
        


if __name__ == '__main__':
    unittest.main()