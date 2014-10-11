#!/usr/bin/python
# -*- coding=utf-8 -*-


__author__ = ['"wuyadong" <wuyadong311521@gmail.com>']

import datetime
import tornado.web
import model
import crawl


class BaseHandler(tornado.web.RequestHandler):
	"""定义公共函数
	"""

	def get_error_html(self, status_code, **kwargs):
		exception = kwargs.get('exception', None)
		return self.render_string("error.html", code=status_code,
		                          exception=exception,
		                          reason=str(kwargs))


class CrawlHandler(BaseHandler):
	"""用于执行采集任务
	"""

	def get(self, *args, **kwargs):
		date_str = self.get_argument("date", None)
		if date_str:
			crawl.fetch_before(date_str)
		else:
			crawl.fetch_latest()
		self.finish()


class DayHandler(BaseHandler):
	"""用于获取某一天的新闻
	"""
	def __init__(self, application, request, **kwargs):
		super(DayHandler, self).__init__(application, request, **kwargs)
		self._db = model.Dao()

	def get(self, *args, **kwargs):
		default_date_str = datetime.datetime.now().strftime("%Y%m%d")
		date_str = self.get_argument("date", default_date_str)
		news_list = self._db.select_news_list(date_str)
		self.render("day.html", before_date=before_date_str(date_str),
		            news_list=news_list)


class ErrorHandler(BaseHandler):
	"""处理错误信息
	"""

	def prepare(self):
		self.render("404.html")


def before_date_str(date_str):
	"""计算前一天的date_str

	:param date_str:
	:return:
	"""
	now_date = datetime.datetime.strptime(date_str, "%Y%m%d")
	before_date = now_date - datetime.timedelta(days=1)
	return before_date.strftime("%Y%m%d")