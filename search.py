#!/usr/bin/python
# -*- coding=utf-8 -*-

"""全文搜索操作
"""

__author__ = ['"wuyadong" <wuyadong311521@gmail.com>']

import logging
import traceback
import util
from config import debug, FS_BUCKET, index_dir

if debug:
    import os
    from whoosh.filedb import filestore
    if not os.path.exists(index_dir):
        os.mkdir(index_dir)
    default_storage = filestore.FileStorage(path=index_dir)
    import jieba.analyse
    analyzer = jieba.analyse.ChineseAnalyzer()

else:
    default_storage = util.SaeStorage(FS_BUCKET, path=index_dir)
    import analyse
    analyzer = analyse.SaeAnalyzer()

from whoosh import writing
from whoosh.fields import Schema, TEXT, ID
from whoosh.qparser import MultifieldParser
from whoosh import highlight


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


class FTSIndexer(object):
    """专门用于建立索引
    """

    def __init__(self, storage=default_storage):
        schema = Schema(news_id=ID(unique=True, stored=True),
                        title=TEXT(field_boost=2.0, analyzer=analyzer),
                        content=TEXT(analyzer=analyzer))
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

                    news_id = util.str2unicode(news_id)
                    title = util.str2unicode(title)
                    content = util.str2unicode(content)
                    writer.update_document(news_id=news_id, title=title,
                                           content=content)
                except Exception, e:
                    stack = traceback.format_exc()
                    logging.error("add doc error:%s\n%s" % (e, stack))

            writer.commit()


class FTSSearcher(object):
    """用于检索
    """

    def __init__(self, storage=default_storage):
        self._fragmenter_maxchars = 70
        self._fragmenter_surround = 70
        self._formatter = MarkFormatter()
        schema = Schema(news_id=ID(unique=True, stored=True),
                        title=TEXT(field_boost=2.0, analyzer=analyzer),
                        content=TEXT(analyzer=analyzer))
        self._ix = storage.open_index(schema=schema)
        self._parser = MultifieldParser(["title", "content"], self._ix.schema)
        self._searcher = self._ix.searcher()

    def search(self, query_string, limit=10):
        """搜索文件
        """
        # refresh searcher
        query_string = util.str2unicode(query_string)

        query = self._parser.parse(query_string)
        search_results = self._searcher.search(query, limit=limit)

        # 设置highlight属性
        search_results.formatter = self._formatter
        search_results.fragmenter.maxchars = self._fragmenter_maxchars
        search_results.fragmenter.surround = self._fragmenter_surround

        return search_results

    def close(self):
        self._searcher.close()