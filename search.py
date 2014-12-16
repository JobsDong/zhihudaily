#!/usr/bin/python
# -*- coding=utf-8 -*-

"""全文搜索操作
"""

__author__ = ['"wuyadong" <wuyadong311521@gmail.com>']

from whoosh.index import open_dir, create_in, exists_in
from whoosh.fields import Schema, TEXT, ID
from whoosh.qparser import MultifieldParser
from jieba.analyse import ChineseAnalyzer


class FTS(object):

    def __init__(self, index_path):
        analyzer = ChineseAnalyzer()
        schema = Schema(path=ID(unique=True, stored=True),
                        title=TEXT(analyzer=analyzer),
                        content=TEXT(analyzer=analyzer))
        if exists_in(index_path):
            self._ix = open_dir(index_path, schema=schema)
        else:
            self._ix = create_in(index_path, schema=schema)
        self._parser = MultifieldParser(["title", "content"], self._ix.schema)

    def search(self, query_string, limit=10):
        """搜索文件
        """
        # convert to unicode
        query_string = str2unicode(query_string)

        with self._ix.searcher() as s:
            query = self._parser.parse(query_string)
            search_results = s.search(query, limit=limit)

        return search_results

    def add_doc(self, path, title=None, content=None):
        """增加文件
        """
        writer = self._ix.writer()
        path = str2unicode(path)
        title = str2unicode(title)
        content = str2unicode(content)
        writer.add_document(path=path, title=title,
                            content=content)
        writer.commit(optimize=True, merge=True)

    def add_many_doc(self, docs=None):
        writer = self._ix.writer()
        docs = docs or []
        for doc in docs:
            if 'path' in doc and 'title' in doc and 'content' in doc:
                writer.add_document(path=str2unicode(doc['path']),
                                    title=str2unicode(doc['title']),
                                    content=str2unicode(doc['content']))
        writer.commit(optimize=True, merge=True)


def str2unicode(text):
    return text.decode('utf-8') if isinstance(text, str) else text
