#!/usr/bin/python
# -*- coding=utf-8 -*-


__author__ = ['"wuyadong" <wuyadong311521@gmail.com>']

import datetime
import hashlib
import tornado.web
import database
import crawl
import config


class BaseHandler(tornado.web.RequestHandler):
	"""定义公共函数
	"""

	def get_error_html(self, status_code, **kwargs):
		reason = "Server Error" if not hasattr(self, "_reason") else self._reason
		exception = kwargs.get('exception', "")

		return self.render_string("error.html", code=str(status_code),
		                          reason=str(reason), exception=str(exception))


class CrawlHandler(BaseHandler):
	"""用于执行采集任务
	"""

	def get(self, *args, **kwargs):
		secret = self.get_argument("secret", "")
		m = hashlib.md5()
		m.update(secret)
		if m.hexdigest() != config.secret:
			self.set_status(403, "password wrong")
		else:
			date_str = self.get_argument("date", None)
			if date_str:
				crawl.fetch_before(date_str)
			else:
				crawl.fetch_latest()
			self.set_status(200, "success")


class DayHandler(BaseHandler):
	"""用于获取某一天的新闻
	"""
	def __init__(self, application, request, **kwargs):
		super(DayHandler, self).__init__(application, request, **kwargs)
		self._db = database.Dao()

	def get(self, *args, **kwargs):
		default_date_str = datetime.datetime.now().strftime("%Y%m%d")
		date_str = self.get_argument("date", default_date_str)
		news_list = self._db.select_news_list(date_str)
		self.render("day.html", now_date=now_date_str(date_str),
		            before_date=before_date_str(date_str),
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


def now_date_str(date_str):
	if datetime.datetime.now().strftime("%Y%m%d") == date_str:
		return "今日热闻"
	else:
		return date_str
