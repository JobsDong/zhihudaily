#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""文本提取
"""

__author__ = ['"wuyadong" <wuyadong311521@gmail.com>']

from lxml import html


def extract_text(content):
    try:
        tree = html.fromstring(content, parser=html.HTMLParser(encoding='utf-8'))
        rc = []
        for node in tree.itertext():
            rc.append(node.strip())
        return u''.join(rc)
    except Exception:
        return content


def str2unicode(text):
    return text.decode('utf-8') if isinstance(text, str) else unicode(text)


def unicode2str(text):
    return text.encode('utf-8') if isinstance(text, unicode) else str(text)