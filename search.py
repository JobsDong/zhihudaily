#!/usr/bin/python
# -*- coding=utf-8 -*-

"""全文搜索操作
"""

__author__ = ['"wuyadong" <wuyadong311521@gmail.com>']

from whoosh.index import open_dir
from whoosh.fields import Schema, TEXT, ID, DATETIME
from whoosh.qparser import QueryParser


class FTS(object):

	def __init__(self, index_path):
		schema = Schema(path=ID(stored=True), title=TEXT,
						content=TEXT, date=DATETIME)
		self._ix = open_dir(index_path, schema)
		self._writer = self._ix.writer()
		self._searcher = self._ix.searcher()
		self._parser = QueryParser("content", self._ix.schema)

	def search(self, query_string, limit=10):
		"""搜索文件
		"""
		query = parser.parse(query_string)
		results = searcher.search(query)
		return results

	def add_doc(self, path, title=None, content=None, date=None):
		"""增加文件
		"""
		self._writer.add_document(path=path, title=title,
								  content=content, date=date)
		self._writer.commit()

	def close(self):
		if self._searcher:
			self._searcher.close()