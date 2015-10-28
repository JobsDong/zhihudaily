#!/usr/bin/env python
# -*- coding: utf-8 -*-


__author__ = ['"wuyadong" <wuyadong311521@gmail.com>']

import config
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
        news_list = get_daily_news(date_str)

        # 如果日报为空，并且参数是今天，就用昨天的数据
        after_date_str = tomorrow_date_str(date_str) \
            if today_str() != date_str else None

        self.render("daily.html", news_list=news_list,
                    before_date=yesterday_date_str(date_str),
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