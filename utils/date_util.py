#!/usr/bin/env python
# -*- coding=utf-8 -*-


__author__ = ['"wuyadong" <wuyadong311521@gmail.com>']

import datetime


def yesterday_date_str(date_str):
    """计算前一天的date_str
    """
    now_date = datetime.datetime.strptime(date_str, "%Y%m%d")
    before_date = now_date - datetime.timedelta(days=1)
    return before_date.strftime("%Y%m%d")


def tomorrow_date_str(date_str):
    """计算后一天的date_str
    """
    now_date = datetime.datetime.strptime(date_str, "%Y%m%d")
    before_date = now_date + datetime.timedelta(days=1)
    return before_date.strftime("%Y%m%d")


def is_today_str(date_str):
    """判断是否是今天
    """
    if datetime.datetime.now().strftime("%Y%m%d") == date_str:
        return True
    else:
        return False


def today_str():
    """获取今天的日期
    """
    return datetime.datetime.now().strftime("%Y%m%d")
