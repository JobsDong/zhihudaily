#!/usr/bin/python
# -*- coding: utf-8 -*-


__author__ = ['"wuyadong" <wuyadong311521@gmail.com>']


debug = True

#-----------------------------静态文件和模板文件----------------------------------
import os

# static path
static_path = os.path.join(os.path.dirname(__file__), "static")

# template path
template_path = os.path.join(os.path.dirname(__file__), "templates")

#---------------------------------图片bucket------------------------------------
# 图片存储的bucket name
IMAGE_BUCKET = "dailyimage"

#---------------------------------数据库----------------------------------------
import sae.const

# 数据库配置
DB_HOST = sae.const.MYSQL_HOST
DB_NAME = sae.const.MYSQL_DB
DB_USER = sae.const.MYSQL_USER
DB_PASS = sae.const.MYSQL_PASS
DB_PORT = int(sae.const.MYSQL_PORT)

#----------------------------------管理员---------------------------------------
# admin 帐号密码
username = "admin"
password = "admin"

#---------------------------------全文搜索---------------------------------------
from search.fts_search import FTSSearcher

# ali fts searcher
FTSSearcher.configure("search.ali_search.AliFTSSearcher",
                      uri="http://opensearch-cn-hangzhou.aliyuncs.com",
                      app="zhihudaily", access_key="fake_key",
                      access_secret="fake_secret")

# sae kvdb fts searcher
# FTSSearcher.configure("search.kvdb_search.KvdbFTSSearcher",
#                       name="zhihudaily")