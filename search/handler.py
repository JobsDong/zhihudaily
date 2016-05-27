#!/usr/bin/env python
# -*- coding: utf-8 -*-


__author__ = ['"wuyadong" <wuyadong311521@gmail.com>']

import logging
import traceback
from base.handler import BaseHandler
from base.daily_store import DailyStorer
from utils.pagination_util import Paginator, InvalidPageError

from search.fts_search import FTSSearcher, FTSSearchError


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
            total_count, hit_list = search(keywords, (page-1) * SEARCH_PER_PAGE,
                                           SEARCH_PER_PAGE)
            hits = Paginator(hit_list, page, total_count, SEARCH_PER_PAGE)

        except (FTSSearchError, InvalidPageError)as e:
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


def search(keywords, start, limit):
    """搜索接口

    Arguments:
      keywords: 关键词语
      start: 开始位置
      limit: 返回个数

    Returns:
      tuple: (total_count, results)
    """
    fts_searcher = FTSSearcher()
    daily_storer = DailyStorer()

    try:
        hits = []
        results = fts_searcher.search(keywords, start=start, limit=limit)

        for hit in results:
            news = daily_storer.get_news(hit['news_id'])
            title = hit['title']
            summary = hit['content']
            hits.append(dict(
                image_public_url=news.image_public_url,
                share_url=news.share_url,
                date=news.date,
                title=title,
                summary=summary,
            ))

        return results.total_count, hits
    finally:
        daily_storer.close()
        fts_searcher.close()