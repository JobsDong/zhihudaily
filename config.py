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

#---------------------------------日报数据存储------------------------------------
from base.daily_store import DailyStorer

# sae数据库存储(sae数据库需要租金，不建议使用)
import sae.const
DailyStorer.configure("base.db_store.DatabaseStorer",
                      host=sae.const.MYSQL_HOST,
                      port=int(sae.const.MYSQL_PORT),
                      user=sae.const.MYSQL_USER,
                      passwd=sae.const.MYSQL_PASS,
                      db=sae.const.MYSQL_DB)

#----------------------------------运维管理员-------------------------------------
# admin 帐号密码
username = "admin"
password = "admin"

#---------------------------------全文搜索---------------------------------------
from search.fts_search import FTSSearcher

# ali fts searcher
# FTSSearcher.configure("search.ali_search.AliFTSSearcher",
#                       uri="http://opensearch-cn-hangzhou.aliyuncs.com",
#                       app="zhihudaily", access_key="fake_key",
#                       access_secret="fake_secret")

# sae kvdb fts searcher (由于sae的kvdb有分钟配额限制，数据量稍大就会被禁止,不建议使用)
FTSSearcher.configure("search.kvdb_search.KvdbFTSSearcher",
                      name="zhihudaily")