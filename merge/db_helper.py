import logging
import pymysql
class db_helper():
    """ 连接数据库和访问数据库的模块

    按道理来说应该是每一个数据库对应一个 db_helper 类

    Attributes:
        __connection: pymysql connection 类，用于连接数据库
    """
    __connection = None
    def __init__(self, config):
        """
        Attributes:
            config: list of config setting for pymysql
        """
        self.__connection = pymysql.connect(
            host=config['MYSQL_HOST'],
            user=config['MYSQL_USER'],
            password=config['MYSQL_PASSWORD'],
            db=config['MYSQL_DBNAME'],
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor,
            port=int(config['MYSQL_PORT']))
                
    def my_select(self, sql):
        """ 从数据库中 select

        Args:
            sql: 选择语句
            
        Returns:
            list of select items
        """
        try:
            cursor = self.__connection.cursor()
            cursor.execute(sql)
            res = cursor.fetchall()
            return res
        except Exception as e:
            logging.warning('error in select, sql {}'.format(sql))
            logging.warning(e)
            self.__connection.rollback()
            raise e
        finally:
            cursor.close()

    def my_insert_many(self, sql, values):
        try:
            cursor = self.__connection.cursor()
            cursor.executemany(sql, values)
            self.__connection.commit()
        except pymysql.err.IntegrityError as e:
            logging.warning(e.args[1])
        except Exception as e:
            logging.warning('error in insert, sql {}'.format(sql))
            self.__connection.rollback()
            raise e
        finally:
            cursor.close()
    
    def my_delete_update(self, sql):
        try:
            cursor = self.__connection.cursor()
            cursor.execute(sql)
            self.__connection.commit()
        except pymysql.err.IntegrityError as e:
            logging.warning(e.args[1])
        except Exception as e:
            logging.warning('error in delete/update, sql: "{}"'.format(sql))
            self.__connection.rollback()
            raise e
        finally:
            cursor.close()