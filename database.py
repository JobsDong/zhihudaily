#!/usr/bin/python
# -*- coding=utf-8 -*-

"""数据库操作
"""

import time
import MySQLdb
import logging
import datetime

import config

__author__ = ['"wuyadong" <wuyadong311521@gmail.com>']


def decode(value):
	if isinstance(value, unicode):
		value = value.encode('utf8')

	return value


class Dao(object):

	def __init__(self):
		self._db = None
		self._db_args = dict(host=config.DB_HOST, port=config.DB_PORT,
                             user=config.DB_USER, passwd=config.DB_PASS,
                             db=config.DB_NAME)
		self._last_use_time = time.time()
		self._max_idle_time = 7 * 3600
		try:
			self.reconnect()
		except Exception:
			logging.error("Cannot connect to MySQL", exc_info=True)

	def exist(self, news_id):
		cursor = self._cursor()
		cursor.execute("SELECT id FROM news WHERE id=%s", [str(news_id)])
		return cursor.fetchone() is not None

	def insert(self, public_image_url, date_str, news):
		cursor = self._cursor()
		try:
			body = news.get('body', '')
			image = news.get('image', '') or news.get('theme_image', '')
			image_source = news.get('image_source', '') \
			               or news.get('theme_name', '')

			cursor.execute("INSERT INTO news VALUES "
			               "(%s, %s, %s, %s, %s, %s, %s, %s, %s)",
		                   [decode(news['id']), decode(news['title']),
		                   decode(news['share_url']), decode(date_str),
		                   decode(body), decode(image),
		                   decode(image_source), decode(public_image_url),
		                   datetime.datetime.now()])
		finally:
			cursor.close()

	def select_news_list(self, date_str):
		cursor = self._cursor()
		try:
			cursor.execute("SELECT * FROM news WHERE date=%s "
			               "ORDER BY insert_time DESC", [date_str])
			news = cursor.fetchall()
			return news
		finally:
			cursor.close()

	def close(self):
		if getattr(self, "_db", None) is not None:
			self._db.close()
			self._db = None

	def reconnect(self):
		self.close()
		self._db = MySQLdb.connect(**self._db_args)
		self._db.autocommit(True)

	def _ensure_connected(self):
		if (self._db is None) or \
				(time.time() - self._last_use_time > self._max_idle_time):
			self.reconnect()
		self._last_use_time = time.time()

	def _cursor(self):
		self._ensure_connected()
		return self._db.cursor()