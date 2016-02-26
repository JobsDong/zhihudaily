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
from search.fts_search import FTSSearcher, LazyCollection
from utils.extract_util import str2unicode


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


class KvdbFTSSearcher(FTSSearcher):

    name = None

    def __init__(self):
        self._fragmenter_maxchars = 70
        self._fragmenter_surround = 70
        self._formatter = MarkFormatter()
        sae_analyzer = SaeAnalyzer()
        sae_storage = SaeStorage(self.name)
        schema = Schema(news_id=ID(unique=True, stored=True),
                        title=TEXT(field_boost=2.0, analyzer=sae_analyzer),
                        content=TEXT(analyzer=sae_analyzer))

        if sae_storage.index_exists():
            self._ix = sae_storage.open_index(schema=schema)
        else:
            self._ix = sae_storage.create_index(schema=schema)
        self._parser = MultifieldParser(["title", "content"], self._ix.schema)

    def search(self, query_string, start=0, limit=10):
        # refresh searcher
        searcher = self._ix.searcher()
        query_string = str2unicode(query_string)
        query = self._parser.parse(query_string)
        search_results = searcher.search(query, limit=start+limit)
        total_count = len(search_results)
        # 设置highlight属性
        search_results.formatter = self._formatter
        search_results.fragmenter.maxchars = self._fragmenter_maxchars
        search_results.fragmenter.surround = self._fragmenter_surround

        search_results = search_results[start:start+limit]

        results = []
        for hit in search_results:
            text = hit["content"]
            summary = hit.highlights("content", text=text, top=2)
            results.append({
                "news_id": hit["news_id"],
                "title": hit["title"],
                "content": summary,
            })

        return LazyCollection(results, total_count)

    def add_many_docs(self, news_list=None):
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

    def close(self):
        pass