# -*- coding: utf-8 -*-
"""

    ppstore.dbconnection
    ~~~~~~~~~~~~~~~~~

    (Deprecated) A module containing a class to connect to database, query it, request
    updates and commit to database.

    :author: Muzammil Abdul Rehman
    :copyright: Northeastern University © 2018.
    :license: Custom BSD, see LICENSE for more details.
    :email: passport@ccs.neu.edu

"""

import configs.system
import MySQLdb
import traceback
from ConfigParser import SafeConfigParser

# Notes: Please add SSL to this connection.

##############################################################################
# A basic class to handle database connections, queries, inserts, updates,
# commits, rollbacks, etc
##############################################################################


class DatabaseConnection(object):

    def __init__(self):
        config_parser = SafeConfigParser()
        config_parser.read(configs.system.CONFIG_FILE_PATH)
        if configs.system.HOSTED_LOCALLY:
            section = "Local"
        else:
            section = "Remote"
        username = config_parser.get(section, 'username')
        password = config_parser.get(section, 'password')
        hostname = config_parser.get(section, 'hostname')
        database = config_parser.get(section, 'database')

        self.__db_con = MySQLdb.connect(host=hostname,
                                        user=username,
                                        passwd=password,
                                        db=database)
        self.cursor = None
        # self.cursor = self.__db_con.cursor()

    def query(self, query, params):
        self.new_cursor()
        self.cursor.query(query, params)

    def execute(self, query, params, commit_to_db):
        try:
            self.new_cursor()
            self.cursor.execute(query, params)
            if commit_to_db:
                self.__db_con.commit()
                self.close_cursor()
            return True
        except:
            traceback.print_exc()
            self.rollback()
            return False

    def commit(self):
        self.__db_con.commit()

    def rollback(self):
        try:
            self.__db_con.rollback()
        except:
            traceback.print_exc()

    def new_cursor(self):
        self.close_cursor()
        self.cursor = self.__db_con.cursor()

    def close_cursor(self):
        if self.cursor is not None:
            self.cursor.close()
            self.cursor = None

    def close_connection(self):
        self.close_cursor()
        self.__db_con.close()
