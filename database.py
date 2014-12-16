#!/usr/bin/python
# -*- coding=utf-8 -*-

"""数据库操作
"""

import time
import collections
import MySQLdb
import logging

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
        self._max_idle_time = 30
        try:
            self.reconnect()
        except Exception:
            logging.error("Cannot connect to MySQL", exc_info=True)

    def exist(self, news_id):
        """判断news是否存在

        :param news_id:
        :return: bool
        """
        cursor = self._cursor()
        cursor.execute("SELECT news_id FROM news WHERE id=%s", [str(news_id)])
        return cursor.fetchone() is not None

    def insert(self, public_image_url, date_str, news):
        """插入一条新闻

        :param public_image_url:
        :param date_str:
        :param news:
        :return:
        """
        cursor = self._cursor()
        try:
            body = news.get('body', '')
            image = news.get('image', '') or news.get('theme_image', '')
            image_source = news.get('image_source', '') \
                           or news.get('theme_name', '')

            cursor.execute("INSERT INTO news (news_id, title, share_url, "
                           "date, body, image, image_source, image_public_url) "
                           "VALUES "
                           "(%s, %s, %s, %s, %s, %s, %s, %s)",
                           [decode(news['id']), decode(news['title']),
                           decode(news['share_url']), decode(date_str),
                           decode(body), decode(image),
                           decode(image_source), decode(public_image_url)])
        finally:
            cursor.close()

    def select_news_list(self, date_str):
        """找出某一天的所有新闻

        :param date_str:
        :return: list
        """
        cursor = self._cursor()
        try:
            cursor.execute("SELECT * FROM news WHERE date=%s "
                           "ORDER BY id DESC", [date_str])
            news = cursor.fetchall()
            return news
        finally:
            cursor.close()

    def clean_news_list(self, date_str):
        """删除date_str之前的所有数据

        :param date_str:
        :return:
        """
        cursor = self._cursor()
        try:
            cursor.execute("DELETE FROM news WHERE date<=%s", [date_str])
        finally:
            cursor.close()

    def get_news(self, news_id):
        """根据news_id获取news的信息

        :param news_id:
        :return:
        """
        cursor = self._cursor()
        try:
            cursor.execute("SELECT * FROM news WHERE news_id=%s", [news_id])
            news = cursor.fetchOne()
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
