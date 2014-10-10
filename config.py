#!/usr/bin/python
# -*- coding=utf-8 -*-


__author__ = ['"wuyadong" <wuyadong311521@gmail.com>']

import sae.const

# 数据库配置
DB_HOST = sae.const.MYSQL_HOST
DB_NAME = sae.const.MYSQL_DB
DB_USER = sae.const.MYSQL_USER
DB_PASS = sae.const.MYSQL_PASS
DB_PORT = int(sae.const.MYSQL_PORT)


# 采集间隔
INTERVAL = 60 * 60
