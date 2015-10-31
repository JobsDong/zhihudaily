#!/usr/bin/env python
# -*- coding: utf-8 -*-


__author__ = ['"wuyadong" <wuyadong311521@gmail.com>']

import config
import logging
from base.handler import BaseHandler

from daily.dao import DailyDao
from search.ali_search import AliFTSSearcher


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
        try:
            hits = search(keywords)
        except Exception as e:
            import traceback
            stack = traceback.format_exc()
            logging.error("Search error, keywords:{%s}, error:%s\nstack:%s" %
                          (keywords, e, stack))
            self.write_error(500)
        else:
            self.render("search.html", hits=hits, keywords=keywords)


def search(keywords):
    hits = []
    fts_searcher = AliFTSSearcher(config.ALI_SEARCH_HOST, config.ALI_SEARCH_APP,
                                  config.ACCESS_KEY, config.ACCESS_SECRET)
    results = fts_searcher.search(keywords, limit=10)

    db = DailyDao(config.DB_HOST, config.DB_PORT, config.DB_USER,
                  config.DB_PASS, config.DB_NAME)
    try:
        for hit in results:
            news = db.get_news(hit['news_id'])
            title = hit['title']
            summary = hit['content']
            hits.append(dict(
                image_public_url=news[8],
                share_url=news[3],
                date=news[4],
                title=title,
                summary=summary,
            ))
    finally:
        db.close()
        fts_searcher.close()

    return hits