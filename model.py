#!/usr/bin/python
# -*- coding=utf-8 -*-

"""数据库操作
"""

import sqlite3

__author__ = ['"wuyadong" <wuyadong311521@gmail.com>']


class Dao(object):

	def __init__(self):
		self._cx = sqlite3.connect("daily.db")
		self._cu = self._cx.cursor()

	def exist(self, news_id):
		self._cu.execute("SELECT id FROM news WHERE id=?", [news_id])
		return self._cu.fetchone() is not None

	def insert(self, date_str, news):
		body = news.get('body', '')
		image = news.get('image', '') or news.get('theme_image', '')
		image_source = news.get('image_source', '') or news.get('theme_name', '')

		self._cu.execute("INSERT INTO news VALUES (?, ?, ?, ?, ?, ?, ?)",
		                 [news['id'], news['title'], news['share_url'],
		                 date_str, body, image,
		                 image_source])
		self._cx.commit()

	def select_news_list(self, date_str):
		self._cu.execute("SELECT * FROM news WHERE date_str=?", [date_str])
		news = self._cu.fetchall()
		return news

	def close(self):
		if self._cu:
			self._cu.close()
		if self._cx:
			self._cx.close()