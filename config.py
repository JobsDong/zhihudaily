#!/usr/bin/python
# -*- coding=utf-8 -*-


__author__ = ['"wuyadong" <wuyadong311521@gmail.com>']

from os import environ

debug = not environ.get("APP_NAME", "")

if debug:
	DB_HOST = "127.0.0.1"
	DB_NAME = "daily"
	DB_USER = "root"
	DB_PASS = "root"
	DB_PORT = 3306

	INTERVAL = 10
	BUCKET = "dailyimage"
else:
	import sae.const

	# 数据库配置
	DB_HOST = sae.const.MYSQL_HOST
	DB_NAME = sae.const.MYSQL_DB
	DB_USER = sae.const.MYSQL_USER
	DB_PASS = sae.const.MYSQL_PASS
	DB_PORT = int(sae.const.MYSQL_PORT)

	# 采集间隔
	INTERVAL = 60 * 60
	BUCKET = "dailyimage"