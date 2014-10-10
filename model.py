#!/usr/bin/python
# -*- coding=utf-8 -*-

"""数据库操作
"""

import MySQLdb
import config

__author__ = ['"wuyadong" <wuyadong311521@gmail.com>']


def decode(value):
	if isinstance(value, unicode):
		value = value.encode('utf8')

	return value


class Dao(object):

	def __init__(self):
		self._cx = MySQLdb.connect(host=config.DB_HOST, port=config.DB_PORT,
		                           user=config.DB_USER,
		                           passwd=config.DB_PASS, db=config.DB_NAME)
		self._cu = self._cx.cursor()

	def exist(self, news_id):
		self._cu.execute("SELECT id FROM news WHERE id=%s", [str(news_id)])
		return self._cu.fetchone() is not None

	def insert(self, date_str, news):
		body = news.get('body', '')
		image = news.get('image', '') or news.get('theme_image', '')
		image_source = news.get('image_source', '') or news.get('theme_name', '')

		self._cu.execute("INSERT INTO news VALUES (%s, %s, %s, %s, %s, %s, %s)",
		                 [decode(news['id']), decode(news['title']),
		                  decode(news['share_url']), decode(date_str),
		                  decode(body), decode(image),
		                  decode(image_source)])
		self._cx.commit()

	def select_news_list(self, date_str):
		self._cu.execute("SELECT * FROM news WHERE date=%s", [date_str])
		news = self._cu.fetchall()
		return news

	def close(self):
		if self._cu:
			self._cu.close()
		if self._cx:
			self._cx.close()