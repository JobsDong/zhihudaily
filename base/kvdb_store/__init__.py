#!/usr/bin/env python
# -*- coding: utf-8 -*-


__author__ = ['"wuyadong" <wuyadong311521@gmail.com>']

import json
import os.path
import sae.kvdb
from base.daily_store import DailyStorer, News

DATE_DELIMITER = "_date_"
NEWS_DELIMITER = "_news_"


class KvdbStorer(DailyStorer):

    def __init__(self):
        self.kvdb = sae.kvdb.KVClient()

    def _date_key(self, date_str):
        return "%s%s" % (DATE_DELIMITER, str(date_str))

    def _news_id_key(self, news_id):
        return "%s%s" % (NEWS_DELIMITER, str(news_id))

    def _save_date_ids(self, date_str, news_ids):
        self.kvdb.set(self._date_key(date_str), json.dumps({
            "news_id": news_ids
        }))

    def _ids_for_date(self, date_str):
        date_value = self.kvdb.get(self._date_key(date_str))
        if date_value is None:
            return []
        return json.loads(date_value)['news_id']

    def filter_news_list(self, date_str):
        # date stat
        news_ids = self._ids_for_date(date_str)
        news_list = []
        # missed_news_ids
        missed_news_ids = []
        for news_id in news_ids:
            news = self.get_news(news_id)
            if news is None:
                missed_news_ids.append(news_id)
            else:
                news_list.append(news)
        # fix missed news ids
        if len(missed_news_ids) > 0:
            self._save_date_ids(date_str, [news_id for news_id in news_ids
                                           if news_id not in missed_news_ids])

        return news_list

    def get_news(self, news_id):
        news_value = self.kvdb.get(self._news_id_key(news_id))
        if news_value is None:
            return None

        news_json = json.loads(news_value)
        return News(news_json['news_id'], news_json['share_url'],
                    news_json['title'], news_json['date_str'],
                    news_json['body'], news_json['image'],
                    news_json['image_source'], news_json['image_public_url'])

    def add_news(self, news):
        # 插入
        news_ids = self._ids_for_date(news.date)
        # add news id
        news_ids.append(news.news_id)
        self._save_date_ids(news.date, news_ids)

        news_json = {"news_id": news.news_id, "share_url": news.share_url,
                     "title": news.title, "date_str": news.date,
                     "body": news.body, "image": news.image,
                     "image_source": news.image_source,
                     "image_public_url": news.image_public_url}
        self.kvdb.set(self._news_id_key(news.news_id), json.dumps(news_json))

    def close(self):
        self.kvdb.disconnect_all()