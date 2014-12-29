#!/usr/bin/python
# -*- coding=utf-8 -*-


__author__ = ['"wuyadong" <wuyadong311521@gmail.com>']

import os

debug = not os.environ.get("APP_NAME", "")

# static path
static_path = os.path.join(os.path.dirname(__file__), "static")

# template path
template_path = os.path.join(os.path.dirname(__file__), "templates")

# index path
index_dir = 'dailyindex'

# jieba path
jieba_dir = 'dailyjieba'


# 图片存储的bucket name
IMAGE_BUCKET = "dailyimage"

# 索引,词典，idf文件保存的bucket name
FS_BUCKET = "dailyfiles"

# 密码(311521)的md5
secret = "76a4cebbe7af10ffd169cd9494adcf2f"

if debug:
    DB_HOST = "127.0.0.1"
    DB_NAME = "daily"
    DB_USER = "root"
    DB_PASS = "root"
    DB_PORT = 3306
else:
    import sae.const

    # 数据库配置
    DB_HOST = sae.const.MYSQL_HOST
    DB_NAME = sae.const.MYSQL_DB
    DB_USER = sae.const.MYSQL_USER
    DB_PASS = sae.const.MYSQL_PASS
    DB_PORT = int(sae.const.MYSQL_PORT)
