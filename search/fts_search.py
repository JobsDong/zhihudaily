#!/usr/bin/env python
# -*- coding: utf-8 -*-


__author__ = ['"wuyadong" <wuyadong311521@gmail.com>']


from utils.sys_util import import_object


class FTSSearchError(Exception):
    """搜索错误
    """


class FTSSearcher(object):
    """全文搜索
    """

    _impl_class = None
    _impl_kwargs = None

    @classmethod
    def configure(cls, impl, **kwargs):
        """配置全文搜索的子类以及参数
        """
        if isinstance(impl, basestring):
            impl = import_object(impl)
        if impl is not None and not issubclass(impl, cls):
            raise ValueError("Invalid subclass of %s" % cls)

        cls._impl_class = impl
        cls._impl_kwargs = kwargs

    def __new__(cls, **kwargs):
        init_kwargs = {}
        init_kwargs.update(kwargs)
        impl = cls._impl_class

        instance = super(FTSSearcher, cls).__new__(impl, init_kwargs)
        return instance

    def search(self, query_string, start=0, limit=10):
        """增加文档如索引

        Args:
          news_list: 需要增加的文档，格式如:[{"news_id": 23, "title": "人民",
                                        "content": "民主"}, {}]

        Returns:
          LazyCollection: 搜索结果

        Raises:
          FTSSearchError: 如果发生错误

        """
        raise NotImplemented

    def add_many_docs(self, news_list=None):
        """增加文档索引

        Args:
          news_list: 需要增加的文档，格式如:[{"news_id": 23, "title": "人民",
                                        "content": "民主"}, {}]

        Raises:
          FTSIndexError: 如果发生错误

        """
        raise NotImplemented

    def clear(self):
        """清除索引
        """
        raise NotImplemented

    def close(self):
        """关闭
        """
        raise NotImplemented


class LazyCollection(object):
    """增加total_count的Collection
    """

    def __init__(self, object_list, total_count):
        self.object_list = object_list
        self.total_count = total_count

    def __len__(self):
        return len(self.object_list)

    def __getitem__(self, index):
        if not isinstance(index, (slice,) + (int, long)):
            raise TypeError
        if not isinstance(self.object_list, list):
            self.object_list = list(self.object_list)
        return self.object_list[index]