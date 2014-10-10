#!/usr/bin/python
# -*- coding=utf-8 -*-

"""知乎日报API
"""

__author__ = ['"wuyadong" <wuyadong311521@gmail.com>']

import os
import thread
import time

import tornado.web

import config
import model
import crawl
import handler


def loop_crawl(interval=60 * 60):
	while True:
		crawl.fetch_latest()
		time.sleep(interval)


class Application(tornado.web.Application):

	def __init__(self):
		handlers = [
			(r'/', handler.DayHandler),
		    (r'/.*', handler.ErrorHandler),
		]

		settings = {
			"static_path": os.path.join(os.path.dirname(__file__), "static"),
		    "template_path": os.path.join(os.path.dirname(__file__), "templates"),
		    "log_file_prefix": "tornado.log",
		}

		tornado.web.Application.__init__(self, handlers, **settings)

		# 数据库链接
		self.db = model.Dao()

		# 定时程序
		thread.start_new_thread(loop_crawl, (config.INTERVAL,))


application = Application()
