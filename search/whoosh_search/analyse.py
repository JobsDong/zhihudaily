#!/usr/bin/env python
# -*- coding=utf-8 -*-

"""专门用于分词
"""

__author__ = ['"wuyadong" <wuyadong311521@gmail.com>']


import urllib
import urllib2
import json
import re
import logging

from whoosh.analysis import LowercaseFilter, StopFilter, StemFilter
from whoosh.analysis import Tokenizer, Token
from whoosh.lang.porter import stem

from utils.extract_util import unicode2str

STOP_WORDS = frozenset(('a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'can',
                        'for', 'from', 'have', 'if', 'in', 'is', 'it', 'may',
                        'not', 'of', 'on', 'or', 'tbd', 'that', 'the', 'this',
                        'to', 'us', 'we', 'when', 'will', 'with', 'yet',
                        'you', 'your', u'的', u'了', u'和'))

accepted_chars = re.compile(ur"[\u4E00-\u9FA5]+")


class AnalyzeException(Exception):
    """
    Analyzer Exception
    """


class SaeTokenizer(Tokenizer):

    def cut(self, text):
        text = unicode2str(text)
        content = self._request(text)
        words = json.loads(content, encoding='UTF-8')
        start_pos = 0
        for word in words:
            try:
                yield word['word'], start_pos, start_pos + len(word['word'])
                start_pos += len(word['word'])
            except Exception, e:
                # sae analyzer unknown exception
                import traceback
                stack = traceback.format_exc()
                logging.error("sae tokenizer error:%s\n%s" % (e, stack))

    def __call__(self, text, **kargs):
        words = self.cut(text)
        token = Token()
        for (w, start_pos, stop_pos) in words:
            if not accepted_chars.match(w) and len(w) <= 1:
                continue
            token.original = token.text = w
            token.pos = start_pos
            token.startchar = start_pos
            token.endchar = stop_pos
            yield token

    def _request(self, text):
        payload = urllib.urlencode([('context', text),])
        args = urllib.urlencode([('word_tag', 0), ('encoding', 'UTF-8'),])
        url = "http://segment.sae.sina.com.cn/urlclient.php" + "?" + args
        result = urllib2.urlopen(url, payload).read()
        return result


def SaeAnalyzer(stoplist=STOP_WORDS, minsize=1, stemfn=stem, cachesize=50000):
    return (SaeTokenizer() | LowercaseFilter() |
            StopFilter(stoplist=stoplist, minsize=minsize) |
            StemFilter(stemfn=stemfn, ignore=None, cachesize=cachesize))
