#!/usr/bin/python
# -*- coding: utf-8 -*-

import sqlite3
import Logger
import os


class SqliteDB(object):

    def __init__(self):
        self.logger = Logger.Logger().get_logger()

    def connect(self, db):
        if not os.path.exists(db):
            self.logger.warning('数据库文件不存在，创建数据库文件：'+db)
        try:
            self.conn = sqlite3.connect(db)
        except Exception as e:
            self.logger.exception(e)
            self.logger.error('连接数据库 '+db+' 失败！')
        else:
            self.logger.info('成功连接数据：'+db)
            return self.conn

    def execute(self, sql):
        self.conn.execute(sql)

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()

