#!/usr/bin/python
# -*- coding: utf-8 -*-


__author__ = ['"wuyadong" <wuyadong311521@gmail.com>']


debug = True
import os

# static path
static_path = os.path.join(os.path.dirname(__file__), "static")

# template path
template_path = os.path.join(os.path.dirname(__file__), "templates")

# ali fts search
ALI_SEARCH_HOST = "http://opensearch-cn-hangzhou.aliyuncs.com"
ALI_SEARCH_APP = "zhihudaily"
ACCESS_KEY = "fake_key"
ACCESS_SECRET = "fake_secret"

# 图片存储的bucket name
IMAGE_BUCKET = "dailyimage"

# 密码(311521)的md5
secret = "76a4cebbe7af10ffd169cd9494adcf2f"

import sae.const

# 数据库配置
DB_HOST = sae.const.MYSQL_HOST
DB_NAME = sae.const.MYSQL_DB
DB_USER = sae.const.MYSQL_USER
DB_PASS = sae.const.MYSQL_PASS
DB_PORT = int(sae.const.MYSQL_PORT)
