#!/usr/bin/env python
# -*- coding: utf-8 -*-


__author__ = ['"wuyadong" <wuyadong311521@gmail.com>']

import config
import logging
from base.handler import BaseHandler
from daily.dao import DailyDao
from utils.date_util import today_str, yesterday_date_str, tomorrow_date_str


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


def get_daily_news(date_str):
    """获取日报信息
    """
    news_list = []
    dao = DailyDao(config.DB_HOST, config.DB_PORT, config.DB_USER,
                   config.DB_PASS, config.DB_NAME)
    try:
        newses = dao.get_news_list(date_str)
        if newses:
            for news in newses:
                news_list.append(dict(share_url=news[3],
                                      image_public_url=news[8],
                                      image_source=news[7],
                                      title=news[2]))
        return news_list
    finally:
        dao.close()