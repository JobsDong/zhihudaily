#!/usr/bin/python
# -*- coding=utf-8 -*-


__author__ = ['"wuyadong" <wuyadong311521@gmail.com>']

from lxml import html


def extract_text(content):
    tree = html.fromstring(content, parser=html.HTMLParser(encoding='utf-8'))
    rc = []
    for node in tree.itertext():
        rc.append(node.strip())
    return u''.join(rc)


def str2unicode(text):
    return text.decode('utf-8') if isinstance(text, str) else text


def unicode2str(text):
    return text.encode('utf-8') if isinstance(text, unicode) else text
