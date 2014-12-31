#!/usr/bin/python
# -*- coding=utf-8 -*-

"""专门用于分词
"""

__author__ = ['"wuyadong" <wuyadong311521@gmail.com>']

from whoosh.analysis import LowercaseFilter, StopFilter, StemFilter
from whoosh.analysis import Tokenizer, Token
from whoosh.lang.porter import stem

import httplib
import socket
import json
import re

from util import unicode2str

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

    def __init__(self):
        super(SaeTokenizer, self).__init__()
        self._host = "segment.sae.sina.com.cn"
        self._timeout = 10

    def cut(self, text):
        text = unicode2str(text)
        value = {"context": text}
        content = self._do_http_request("POST",
                                        "/urlclient.php?encoding=UTF-8&word_tag=0",
                                        value=str(value))
        words = json.loads(content)
        start_pos = 0
        for word in words:
            yield word['word'], start_pos, start_pos + len(word)
            start_pos += len(word)

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

    def _decode_msg(self, msg):
        if isinstance(msg, str):
            msg = unicode(msg, 'utf-8')

        return msg

    def _do_http_request(self, method, uri, headers=None, value=None):
        if headers is None:
            headers = {}
        if value is not None:
            length = len(value)
            headers['Content-Length'] = length

        http, content, msg, error, status = None, None, None, None, None
        try:
            http = httplib.HTTPConnection(self._host, timeout=self._timeout)
            http.request(method, uri, value, headers)
            response = http.getresponse()

            status = response.status
            if status / 100 == 2:
                content = self._decode_msg(response.read())
            else:
                msg = response.reason
                error = self._decode_msg(response.read())
        except (httplib.HTTPException, socket.error, socket.timeout) as e:
            raise AnalyzeException(str(e))
        except Exception as e:
            raise AnalyzeException(str(e))
        finally:
            if http:
                http.close()
        if msg:
            raise AnalyzeException(status, msg, error)

        return content


def SaeAnalyzer(stoplist=STOP_WORDS, minsize=1, stemfn=stem, cachesize=50000):
    return (SaeTokenizer() | LowercaseFilter() |
            StopFilter(stoplist=stoplist, minsize=minsize) |
            StemFilter(stemfn=stemfn, ignore=None, cachesize=cachesize))
