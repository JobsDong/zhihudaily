#!/usr/bin/env python
# -*- coding=utf-8 -*-


__author__ = ['"wuyadong" <wuyadong311521@gmail.com>']

import config
from base.handler import BaseHandler

from daily.dao import DailyDao
from whoosh_search import SAEFTSSearcher


class SearchHandler(BaseHandler):
    """处理搜索
    """
    def __init__(self, application, request, **kwargs):
        super(SearchHandler, self).__init__(application, request, **kwargs)

    def get(self, *args, **kwargs):
        keywords = self.get_argument("keywords", "")
        if not keywords.strip():
            self.redirect("/")
            return

        hits = search(keywords)
        self.render("search.html", hits=hits, keywords=keywords)


def search(keywords):
    hits = []
    fts_searcher = SAEFTSSearcher(config.FS_BUCKET, config.INDEX_DIR)
    results = fts_searcher.search(keywords, limit=10)

    db = DailyDao(config.DB_HOST, config.DB_PORT, config.DB_USER,
                  config.DB_PASS, config.DB_NAME)
    try:
        for hit in results:
            news = db.get_news(hit['news_id'])
            summary = hit['summary']
            hits.append(dict(
                image_public_url=news[8],
                share_url=news[3],
                date=news[4],
                title=news[2],
                summary=summary,
            ))
    finally:
        db.close()
        fts_searcher.close()

    return hits