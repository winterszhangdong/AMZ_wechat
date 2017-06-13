#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging.config


class Logger(object):
    def __init__(self):
        # log配置文件
        logging.config.fileConfig('logging.conf')
        # 创建logger
        self.logger = logging.getLogger('wechatLogger')

    def get_logger(self):
        return self.logger
