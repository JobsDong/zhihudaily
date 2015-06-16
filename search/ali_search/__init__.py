#!/usr/bin/env python
# -*- coding=utf-8 -*-


__author__ = ['"wuyadong" <wuyadong311521@gmail.com>']

import datetime
import re
import time
import hmac
import hashlib
import urlparse
import urllib
import json
import random
import requests
from utils.extract_util import str2unicode, unicode2str


class AliSearchError(Exception):
    """
    """


def _build_common_params(params, access_key):
    if params is None:
        params = dict()
    params.update({
        "Version": "v2",
        "AccessKeyId": access_key,
        "Timestamp": datetime.datetime.utcnow().isoformat(),
        "SignatureVersion": "1.0",
        "SignatureNonce": "%s%s" % (time.ctime(), random.randint(0, 10000)),
        "SignatureMethod": "HMAC-SHA1",
    })

    return params


def _signature(method, params, access_secret):
    # 1.
    sorted_keys = sorted(params.keys())
    signatures = []
    for key in sorted_keys:
        signatures.append("%s=%s" % (urllib.urlencode(key), urllib.urlencode(params[key])))
    signature_str = "&".join(signatures)
    # 2.
    string_2_sign = method.upper() + "&" + "%2F" + "&" + signature_str
    # 3.
    signature = hmac.new(access_secret + "&", msg=string_2_sign, digestmod=hashlib.sha1).digest()
    return signature


def request(method, uri, access_key, access_secret, params=None, data=None, headers=None):
    # 公共参数
    params = _build_common_params(params, access_key)
    signature = _signature(method, params, access_secret)
    params['Signature'] = signature

    try:
        if method.lower() == "get":
            resp = requests.get(uri, params=params, headers=headers)
        else:
            headers['Content-Type'] = 'application/x-www-form-urlencoded'
            resp = requests.post(uri, params=params, data=data, headers=headers)
    except Exception as e:
        raise AliSearchError(e)
    else:
        if resp.status_code / 100 == 2:
            result = resp.json()
            if result['status'] == 'OK':
                return result
            else:
                raise AliSearchError('failed')
        else:
            return AliSearchError(code=resp.status_code, reason=resp.reason)




class AliFTSIndexer(object):

    def __init__(self, uri, app, access_key, access_secret):
        self._uri = uri
        self._app = app
        self._access_key = access_key
        self._access_secret = access_secret

    def add_many_docs(self, news_list=None):
        # 构造url
        url = "%s/index/doc/%s" % (self._uri, self._app)
        # 构造内容
        news_data = []
        for news in news_list:
            news_data.append({
                "cmd": "add",
                "fields": {
                    "news_id": str2unicode(news['news_id']),
                    "title": str2unicode(news['title']),
                    "content": str2unicode(news['content']),
                }
            })

        # 发出请求
        request("POSt", url, self._access_key,
                self._access_secret, data=json.dumps(news_data))

    def clear(self):
        pass


class AliFTSSearcher(object):

    def __init__(self, uri, app, access_key, access_secret):
        self._uri = uri
        self._app = app
        self._access_key = access_key
        self._access_secret = access_secret

    def search(self, query_string, limit=10):
        # 构造uri
        url = "%s/search" % self._uri
        query_string = unicode2str(query_string)
        words = re.compile("\s+").split(query_string)
        strs = []
        for word in words:
            strs.append("content:'%s'" % word)
        # 构造参数
        params = {
            "query": "config=hit:%s&&query=%s" % (limit, " OR ".join(strs)),
            "index_name": self._app,
            "summary": {
                "summary_field": "content",
                "summary_element": "mark",
                "summary_len": 70
            }
        }

        # 请求
        r = request("GET", url, self._access_key, self._access_secret, params)
        results = []
        for item in r['result']['items']:
            results.append({
                "news_id": item['news_id'],
                "title": item['title'],
                "content": item['content'],
            })
        return results