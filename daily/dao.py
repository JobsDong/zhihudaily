#!/usr/bin/env python
# -*- coding: utf-8 -*-


__author__ = ['"wuyadong" <wuyadong311521@gmail.com>']

from base.database import BaseDao


def _decode(value):
    if isinstance(value, unicode):
        value = value.encode('utf8')
    return value


class DailyDao(BaseDao):

    def get_news_list(self, date_str):
        """找出某一天的所有新闻
        """
        cursor = self._cursor()
        try:
            cursor.execute("SELECT * FROM newses WHERE date=%s "
                           "ORDER BY id DESC", [date_str])
            news = cursor.fetchall()
            return news
        finally:
            cursor.close()

    def get_news(self, news_id):
        """根据news_id获取news的信息
        """
        cursor = self._cursor()
        try:
            cursor.execute("SELECT * FROM newses WHERE news_id=%s", [news_id])
            news = cursor.fetchone()
            return news
        finally:
            cursor.close()

    def insert(self, public_image_url, date_str, news):
        """插入一条新闻
        """
        cursor = self._cursor()
        try:
            body = news.get('body', '')
            image = news.get('image', '') or news.get('theme_image', '')
            image_source = news.get('image_source', '') \
                           or news.get('theme_name', '')

            cursor.execute("INSERT INTO newses (news_id, title, share_url, "
                           "date, body, image, image_source, image_public_url) "
                           "VALUES "
                           "(%s, %s, %s, %s, %s, %s, %s, %s)",
                           [_decode(news['id']), _decode(news['title']),
                           _decode(news['share_url']), _decode(date_str),
                           _decode(body), _decode(image),
                           _decode(image_source), _decode(public_image_url)])
        finally:
            cursor.close()
