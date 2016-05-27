#!/usr/bin/env python
# -*- coding: utf-8 -*-


__author__ = ['"wuyadong" <wuyadong311521@gmail.com>']

import logging
from base.handler import BaseHandler
from base.daily_store import DailyStorer
from utils.date_util import today_str, yesterday_date_str, tomorrow_date_str
from utils.cache_util import cached


class DailyHandler(BaseHandler):
    """用于获取某一天的新闻
    """
    def __init__(self, application, request, **kwargs):
        super(DailyHandler, self).__init__(application, request, **kwargs)

    def get(self, *args, **kwargs):
        # 获取日期
        date_str = self.get_argument("date", today_str())

        # 获取日报
        try:
            news_list = get_daily_news(date_str)

            before_date_str = yesterday_date_str(date_str)
            after_date_str = tomorrow_date_str(date_str) \
                if today_str() != date_str else None
        except Exception as e:
            import traceback
            stack = traceback.format_exc()
            logging.error("get daily news failed date_str:%s error:%s cause:%s"
                          % (date_str, e, stack))
            self.write_error(404, reason="Invalidate date {%s}" % date_str)
        else:
            self.render("daily.html", news_list=news_list,
                        before_date=before_date_str,
                        after_date=after_date_str)


@cached(expiration=60*10)
def get_daily_news(date_str):
    """获取日报信息
    """
    daily_storer = DailyStorer()
    news_list = []
    try:
        newses = daily_storer.filter_news_list(date_str)
        if newses:
            for news in newses:
                news_list.append(dict(share_url=news.share_url,
                                      image_public_url=news.image_public_url,
                                      image_source=news.image_source,
                                      title=news.title))
        return news_list
    finally:
        daily_storer.close()