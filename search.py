#!/usr/bin/python
# -*- coding=utf-8 -*-

"""全文搜索操作
"""

__author__ = ['"wuyadong" <wuyadong311521@gmail.com>']

from whoosh.index import open_dir, create_in, exists_in
from whoosh.fields import Schema, TEXT, ID
from whoosh.qparser import MultifieldParser
from whoosh import highlight
from jieba.analyse import ChineseAnalyzer

import config
import util


class MarkFormatter(highlight.Formatter):
    """search formatter
    """
    def format_token(self, text, token, replace=False):
        token_text = highlight.get_text(text, token, False)

        return "<mark>%s</mark>" % token_text


class FTS(object):

    def __init__(self):
        index_path = config.index_path
        analyzer = ChineseAnalyzer()
        self._fragmenter_maxchars = 100
        self._fragmenter_surround = 100
        self._formatter = MarkFormatter()
        schema = Schema(news_id=ID(unique=True, stored=True),
                        title=TEXT(analyzer=analyzer),
                        content=TEXT(analyzer=analyzer))
        if exists_in(index_path):
            self._ix = open_dir(index_path, schema=schema)
        else:
            self._ix = create_in(index_path, schema=schema)
        self._parser = MultifieldParser(["content"], self._ix.schema)
        self._searcher = self._ix.searcher()

    def search(self, query_string, limit=10):
        """搜索文件
        """
        # refresh searcher
        self._searcher = self._searcher.refresh()
        query_string = util.str2unicode(query_string)

        query = self._parser.parse(query_string)
        search_results = self._searcher.search(query, limit=limit)

        # 设置highlight属性
        search_results.formatter = self._formatter
        search_results.fragmenter.maxchars = self._fragmenter_maxchars
        search_results.fragmenter.surround = self._fragmenter_surround

        return search_results

    def add_doc(self, news_id, title=None, content=None):
        """增加文件
        """
        writer = self._ix.writer()
        news_id = util.str2unicode(news_id)
        title = util.str2unicode(title)
        content = util.str2unicode(content)
        writer.add_document(news_id=news_id, title=title,
                            content=content)
        writer.commit(optimize=True, merge=True)

    def close(self):
        self._searcher.close()
