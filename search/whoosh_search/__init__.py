#!/usr/bin/env python
# -*- coding=utf-8 -*-


__author__ = ['"wuyadong" <wuyadong311521@gmail.com>']

import traceback
import logging
from storage import SaeStorage
from analyse import SaeAnalyzer
from utils.extract_util import str2unicode

from whoosh import writing
from whoosh.fields import Schema, TEXT, ID
from whoosh.qparser import MultifieldParser
from whoosh import highlight


class SAEFTSIndexer(object):
    """专门用于建立索引
    """

    def __init__(self, fs_bucket, index_dir):
        # 持久化
        storage = SaeStorage(fs_bucket, path=index_dir)
        # 分词
        analyzer = SaeAnalyzer()

        schema = Schema(news_id=ID(unique=True, stored=True),
                        title=TEXT(field_boost=2.0, analyzer=analyzer),
                        content=TEXT(analyzer=analyzer, stored=True))
        if storage.index_exists():
            self._ix = storage.open_index(schema=schema)
        else:
            self._ix = storage.create_index(schema=schema)

    def clear(self):
        writer = self._ix.writer()
        writer.commit(mergetype=writing.CLEAR)

    def add_many_docs(self, news_list=None):
        """增加许多文件
        """
        if news_list:
            writer = self._ix.writer()
            for news in news_list:
                try:
                    news_id = news['news_id']
                    title = news['title']
                    content = news['content']

                    news_id = str2unicode(news_id)
                    title = str2unicode(title)
                    content = str2unicode(content)
                    writer.update_document(news_id=news_id, title=title,
                                           content=content)
                except Exception, e:
                    stack = traceback.format_exc()
                    logging.error("add doc error:%s\n%s" % (e, stack))

            writer.commit()


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


class SAEFTSSearcher(object):
    """用于检索
    """

    def __init__(self, fs_bucket, index_dir):
        # 持久化
        storage = SaeStorage(fs_bucket, path=index_dir)
        # 分词
        analyzer = SaeAnalyzer()

        self._fragmenter_maxchars = 70
        self._fragmenter_surround = 70
        self._formatter = MarkFormatter()
        schema = Schema(news_id=ID(unique=True, stored=True),
                        title=TEXT(field_boost=2.0, analyzer=analyzer),
                        content=TEXT(analyzer=analyzer, stored=True))
        self._ix = storage.open_index(schema=schema)
        self._parser = MultifieldParser(["title", "content"], self._ix.schema)
        self._searcher = self._ix.searcher()

    def search(self, query_string, limit=10):
        """搜索文件
        """
        # refresh searcher
        query_string = str2unicode(query_string)

        query = self._parser.parse(query_string)
        search_results = self._searcher.search(query, limit=limit)

        # 设置highlight属性
        search_results.formatter = self._formatter
        search_results.fragmenter.maxchars = self._fragmenter_maxchars
        search_results.fragmenter.surround = self._fragmenter_surround
        hits = []
        for hit in search_results:
            hits.append({
                "news_id": hit['news_id'],
                "summary": hit.highlights('content',
                                          text=hit['content'],
                                          top=2),
            })

        return hits

    def close(self):
        self._searcher.close()