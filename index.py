#!/usr/bin/python
# -*- coding=utf-8 -*-

"""知乎日报API
"""

__author__ = ['"wuyadong" <wuyadong311521@gmail.com>']

import os
import datetime

import tornado.web
import tornado.wsgi
from tornado.web import url

import model


class MainHandler(tornado.web.RequestHandler):

	def get(self, *args, **kwargs):
		default_date_str = datetime.datetime.now().strftime("%Y%m%d")
		date_str = self.get_query_argument("date", default_date_str)
		news_list = self.application.db.select_news_list(date_str)
		self.render("homepage.html", news_list=news_list)


class Application(tornado.web.Application):

	def __init__(self):
		handlers = [
			url(r'', MainHandler),
		]

		settings = {
			"static_path": os.path.join(os.path.dirname(__file__), "static"),
		    "template_path": os.path.join(os.path.dirname(__file__), "templates"),
		    "log_file_prefix": "tornado.log",

		}

		tornado.web.Application.__init__(self, handlers, **settings)
		self.db = model.Dao()