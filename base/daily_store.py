#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""保存日报
"""

__author__ = ['"wuyadong" <wuyadong311521@gmail.com>']

from utils.sys_util import import_object


class News(object):

    def __init__(self, news_id, share_url, title, date_str,
                 body, image, image_source, image_public_url):
        self.news_id = news_id
        self.share_url = share_url
        self.title = title
        self.date = date_str
        self.body = body
        self.image = image
        self.image_source = image_source
        self.image_public_url = image_public_url


class DailyStorer(object):
    """日报存储/查询
    """

    _impl_class = None
    _impl_kwargs = None

    @classmethod
    def configure(cls, impl, **kwargs):
        """配置存储的子类以及参数
        """
        if isinstance(impl, basestring):
            impl = import_object(impl)

        if impl is not None and not issubclass(impl, cls):
            raise ValueError("Invalid subclass of %s" % cls)

        cls._impl_class = impl
        cls._impl_kwargs = kwargs

    def __new__(cls, *args, **kwargs):
        impl = cls._impl_class
        init_kwargs = cls._impl_kwargs
        instance = super(DailyStorer, cls).__new__(impl)
        for n, v in init_kwargs.items():
            setattr(instance, n, v)
        return instance

    def filter_news_list(self, date_str):
        """根据时间筛选news列表
        """
        raise NotImplemented

    def get_news(self, news_id):
        """获取某一个news
        """
        raise NotImplemented

    def add_news(self, news):
        """增加一个news
        """
        raise NotImplemented

    def close(self):
        """关闭
        """
        raise NotImplemented