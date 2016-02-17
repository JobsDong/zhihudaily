#!/usr/bin/env python
# -*- coding: utf-8 -*-


__author__ = ['"wuyadong" <wuyadong311521@gmail.com>']

import config
import logging
import traceback
from base.handler import BaseHandler
from utils.pagination_util import Paginator, InvalidPageError
from utils.cache_util import cached

from daily.dao import DailyDao
from search.ali_search import AliFTSSearcher, AliSearchError


SEARCH_PER_PAGE = 10


class SearchHandler(BaseHandler):
    """处理搜索
    """
    def __init__(self, application, request, **kwargs):
        super(SearchHandler, self).__init__(application, request, **kwargs)

    def get(self, *args, **kwargs):
        keywords = self.get_argument("keywords", "")
        page = self.get_argument("page", 1)
        if not keywords.strip():
            self.redirect("/")
            return

        if not is_validate_number(page):
            self.write_error(400, reason="not validate page number")
            return

        page = int(page)
        try:
            total_count, hit_list = search(keywords, page * SEARCH_PER_PAGE,
                                           SEARCH_PER_PAGE)
            hits = Paginator(hit_list, page, total_count, SEARCH_PER_PAGE)

        except (AliSearchError, InvalidPageError)as e:
            stack = traceback.format_exc()
            logging.error("Search keywords{%s} page:{%s} error:%s\n stack:%s"
                          % (keywords, page, e, stack))
            self.write_error(500)
        else:
            self.render("search.html", hits=hits, keywords=keywords)


def is_validate_number(number):
    try:
        number = int(number)
    except (TypeError, ValueError):
        return False
    if number < 1:
        return False
    return True


@cached(expiration=60*60)
def search(keywords, start, limit):
    """搜索接口

    Argumenst:
      keywords: 关键词语
      start: 开始位置
      limit: 返回个数

    Returns:
      tuple: (total_count, results)
    """
    fts_searcher = AliFTSSearcher(config.ALI_SEARCH_HOST, config.ALI_SEARCH_APP,
                                  config.ACCESS_KEY, config.ACCESS_SECRET)

    db = DailyDao(config.DB_HOST, config.DB_PORT, config.DB_USER,
                  config.DB_PASS, config.DB_NAME)
    try:
        hits = []
        results = fts_searcher.search(keywords, start=start, limit=limit)

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

        return results.total_count, hits
    finally:
        db.close()
        fts_searcher.close()