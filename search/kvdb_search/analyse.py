#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""sae的分词
"""

__author__ = ['"wuyadong" <wuyadong311521@gmail.com>']

from whoosh.analysis import LowercaseFilter, StopFilter, StemFilter
from whoosh.analysis import Tokenizer, Token
from whoosh.lang.porter import stem

import urllib
import urllib2
import json
import re

STOP_WORDS = frozenset((u'一些', u'一切', u'万一', u'不仅', u'不但', u'不管',
                        u'为了', u'于是', u'从此', u'从而', u'以为', u'但是',
                        u'你', u'我', u'他', u'例如', u'关于', u'即使', u'反而',
                        u'另外', u'只有', u'只是', u'可以', u'呀', u'吧', u'吗',
                        u'否则', u'和', u'哪些', u'因为', u'尽管', u'的', u'了',
                        u'和'))

accepted_chars = re.compile(ur"[\u4E00-\u9FA5]+")


class SaeTokenizer(Tokenizer):

    def cut(self, text):
        text = text.encode('utf-8') if isinstance(text, unicode) else str(text)
        content = self._request(text)
        words = json.loads(content, encoding='UTF-8')
        start_pos = 0
        for word in words:
            try:
                yield word['word'], start_pos, start_pos + len(word['word'])
                start_pos += len(word['word'])
            except Exception:
                # sae analyzer unknown exception
                pass

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
        payload = urllib.urlencode([('context', text), ])
        args = urllib.urlencode([('word_tag', 0), ('encoding', 'UTF-8'), ])
        url = "http://segment.sae.sina.com.cn/urlclient.php" + "?" + args
        result = urllib2.urlopen(url, payload).read()
        return result


def SaeAnalyzer(stoplist=STOP_WORDS, minsize=1, stemfn=stem, cachesize=50000):
    return (SaeTokenizer() | LowercaseFilter() |
            StopFilter(stoplist=stoplist, minsize=minsize) |
            StemFilter(stemfn=stemfn, ignore=None, cachesize=cachesize))