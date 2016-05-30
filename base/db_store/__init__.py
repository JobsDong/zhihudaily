#!/usr/bin/env python
# -*- coding: utf-8 -*-


__author__ = ['"wuyadong" <wuyadong311521@gmail.com>']

from base.daily_store import DailyStorer, News
from base.db_store.database import BaseDao


def _decode(value):
    if isinstance(value, unicode):
        value = value.encode('utf8')
    return value


class DatabaseStorer(DailyStorer):

    host = None
    port = None
    user = None
    passwd = None
    db = None

    def __init__(self):
        self._dao = BaseDao(self.host, self.port, self.user,
                            self.passwd, self.db)

    def _convert_news(self, news_line):
        return News(news_line[1], news_line[3], news_line[2], news_line[4],
                    news_line[5], news_line[6], news_line[7], news_line[8])

    def filter_news_list(self, date_str):
        cursor = self._dao.cursor()
        try:
            cursor.execute("SELECT * FROM newses WHERE date=%s "
                           "ORDER BY id DESC", [date_str])
            news_list = cursor.fetchall()
            # 转换
            return [self._convert_news(news) for news in news_list]
        finally:
            cursor.close()

    def get_news(self, news_id):
        cursor = self._dao.cursor()
        try:
            cursor.execute("SELECT * FROM newses WHERE news_id=%s", [news_id])
            news = cursor.fetchone()
            return self._convert_news(news)
        finally:
            cursor.close()

    def add_news(self, news):
        cursor = self._dao.cursor()
        try:
            news_item = [_decode(item) for item in
                         [news.news_id, news.title, news.share_url, news.date,
                          news.body, news.image, news.image_source,
                          news.image_public_url]]
            cursor.execute("INSERT INTO newses (news_id, title, share_url, "
                           "date, body, image, image_source, image_public_url) "
                           "VALUES "
                           "(%s, %s, %s, %s, %s, %s, %s, %s)", news_item)
        finally:
            cursor.close()

    def close(self):
        self._dao.close()