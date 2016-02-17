#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""基于whoosh, sae的分词, sae的kvdb的搜索
"""

__author__ = ['"wuyadong" <wuyadong311521@gmail.com>']

import logging
import traceback

from whoosh import writing
from whoosh.fields import Schema, TEXT, ID
from whoosh.qparser import MultifieldParser
from whoosh import highlight

from search.kvdb_search.analyse import SaeAnalyzer
from search.kvdb_search.storage import SaeStorage
from utils.extract_util import unicode2str, str2unicode


class KvdbSearchError(Exception):
    pass


class KvdbFTSIndexer(object):

    def __init__(self):
        analyzer = SaeAnalyzer()
        storage = SaeStorage()
        schema = Schema(news_id=ID(unique=True, stored=True),
                        title=TEXT(field_boost=2.0, analyzer=analyzer),
                        content=TEXT(analyzer=analyzer))
        if storage.index_exists():
            self._ix = storage.open_index(schema=schema)
        else:
            self._ix = storage.create_index(schema=schema)

    def add_many_docs(self, news_list=None):
        """增加文档如索引

        Args:
          news_list: 需要增加的文档，格式如:[{"news_id": 23, "title": "人民",
                                        "content": "民主"}, {}]

        Raises:
          KvdbSearchError: 如果发生错误
        """
        if news_list:
            writer = self._ix.writer()
            for news in news_list:
                try:
                    news_id = str2unicode(news['news_id'])
                    title = str2unicode(news['title'])
                    content = str2unicode(news['content'])
                    writer.update_document(news_id=news_id, title=title,
                                           content=content)
                except Exception as e:
                    stack = traceback.format_exc()
                    logging.error("Index document{%s} failed, "
                                  "error:%s\n stack:%s" % (news["news_id"],
                                                           e, stack))
            writer.commit()

    def clear(self):
        writer = self._ix.writer()
        writer.commit(mergetype=writing.CLEAR)


class MarkFormatter(highlight.Formatter):
    """search formatter
    """

    def format_token(self, text, token, replace=False):
        token_text = highlight.get_text(text, token, False)
        return "<mark>%s</mark>" % token_text

    def format(self, fragments, replace=False):
        formatted = [self.format_fragment(f, replace=replace)
                     for f in fragments]
        return "<br>".join(formatted)


class KvdbFTSSearcher(object):

    def __init__(self):
        self._fragmenter_maxchars = 70
        self._fragmenter_surround = 70
        self._formatter = MarkFormatter()
        analyzer = SaeAnalyzer()
        storage = SaeStorage()
        schema = Schema(news_id=ID(unique=True, stored=True),
                        title=TEXT(field_boost=2.0, analyzer=analyzer),
                        content=TEXT(analyzer=analyzer))

        if storage.index_exists():
            self._ix = storage.open_index(schema=schema)
        else:
            self._ix = storage.create_index(schema=schema)
        self._parser = MultifieldParser(["title", "content"], self._ix.schema)
        self._searcher = self._ix.searcher()

    def search(self, query_string, start=0, limit=10):
        """搜索文件
        """
        # refresh searcher
        self._searcher = self._searcher.refresh()
        query_string = str2unicode(query_string)
        query = self._parser.parse(query_string)
        search_results = self._searcher.search(query, limit=limit)

        # 设置highlight属性
        search_results.formatter = self._formatter
        search_results.fragmenter.maxchars = self._fragmenter_maxchars
        search_results.fragmenter.surround = self._fragmenter_surround
        return search_results

    def close(self):
        self._searcher.close()