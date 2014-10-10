#!/usr/bin/python
# -*- coding=utf-8 -*-


__author__ = ['"wuyadong" <wuyadong311521@gmail.com>']

import datetime
import tornado.web


class BaseHandler(tornado.web.RequestHandler):

	def get_error_html(self, status_code, **kwargs):
		exception = kwargs.get('exception', None)
		return self.render_string("error.html", code=status_code,
		                          exception=exception,
		                          reason=self._reason)


class DayHandler(BaseHandler):

	def get(self, *args, **kwargs):
		default_date_str = datetime.datetime.now().strftime("%Y%m%d")
		date_str = self.get_query_argument("date", default_date_str)
		news_list = self.application.db.select_news_list(date_str)
		self.render("day.html", before_date=before_date_str(date_str),
		            news_list=news_list)


class ErrorHandler(BaseHandler):

	def prepare(self):
		self.render("404.html")


def before_date_str(date_str):
	now_date = datetime.datetime.strptime(date_str, "%Y%m%d")
	before_date = now_date - datetime.timedelta(days=1)
	return before_date.strftime("%Y%m%d")
