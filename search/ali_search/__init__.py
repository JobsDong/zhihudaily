#!/usr/bin/env python
# -*- coding: utf-8 -*-


__author__ = ['"wuyadong" <wuyadong311521@gmail.com>']

import base64
import json
import datetime
import re
import hmac
import hashlib
import urllib
import urllib2
import uuid
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
        "Timestamp": (datetime.datetime.now() + datetime.timedelta(hours=-8))
            .strftime("%Y-%m-%dT%H:%M:%SZ"),
        "SignatureMethod": "HMAC-SHA1",
        "SignatureVersion": "1.0",
        "SignatureNonce": "%s" % str(uuid.uuid1()),
    })

    return params


def _signature(method, params, access_secret):
    # 1.
    sorted_keys = sorted(params.keys())
    signatures = []
    for key in sorted_keys:
        signatures.append("%s=%s" % (key, _encode(params[key])))
    signature_str = "&".join(signatures)
    # 2.
    string_2_sign = method.upper() + "&" + "%2F" + "&" + _encode(signature_str)
    # 3.
    signature = base64.b64encode(hmac.new(access_secret + "&",
                                          msg=string_2_sign.encode('utf-8'),
                                          digestmod=hashlib.sha1).digest())
    return signature


def _encode(string):
    if not isinstance(string, basestring):
        string = str(string)

    if isinstance(string, unicode):
        string = str(string)

    return urllib.quote_plus(string).replace('+', '%20').replace('*', '%%2A')\
        .replace('%7E', '~')


def request(method, uri, access_key, access_secret, params=None):
    # 公共参数
    params = _build_common_params(params, access_key)
    signature = _signature(method, params, access_secret)
    params['Signature'] = signature
    try:
        para_data = urllib.urlencode(params)

        if method.lower() == "get":
            uri = "%s?%s" % (uri, para_data)
            para_data = None

        f = urllib2.urlopen(uri, para_data)
        resp = f.read()
        f.close()
    except Exception as e:
        raise AliSearchError("request search server failed", e)
    else:
        result = json.loads(resp)
        if result['status'] == 'OK':
            return result
        else:
            raise AliSearchError('result status is not ok result:%s' % resp)


class AliFTSIndexer(object):

    def __init__(self, uri, app, access_key, access_secret):
        self._uri = uri
        self._app = app
        self._access_key = access_key
        self._access_secret = access_secret

    def add_many_docs(self, news_list=None):
        """增加文档如索引

        Args:
          news_list: 需要增加的文档，格式如:[{"news_id": 23, "title": "人民",
                                        "content": "民主"}, {}]

        Raises:
          AliSearchError: 如果发生错误

        """
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
        request("POST", url, self._access_key,
                self._access_secret, params={"action": "push",
                                             "table_name": "news",
                                             "items": json.dumps(news_data)})

    def clear(self):
        pass


class AliFTSSearcher(object):

    def __init__(self, uri, app, access_key, access_secret):
        self._uri = uri
        self._app = app
        self._access_key = access_key
        self._access_secret = access_secret

    def search(self, query_string, limit=10):
        """关键词搜索

        Args:
          query_string: str or unicode 搜索关键词
          limit: int 最大个数

        Returns:
          results: [] 形式如下:[{"news_id": 23, "title": "<mark>中国</mark>公惨淡",
                            "content": "<mark>中国</mark>人民名住..."}, {...}]

        Raises:
          AliSearchError: 如果搜索发生错误
        """
        # 构造uri
        url = "%s/search" % self._uri
        query_string = unicode2str(query_string)
        words = re.compile("\s+").split(query_string)
        # 构造参数
        params = {
            "query": "config=hit:%s&&query=%s" % (limit, " OR ".join(words)),
            "index_name": self._app,
            "summary": "summary_field:content,summary_element:mark,"
                       "summary_len:300;summary_field:title,summary_element:mark",
        }

        # 请求
        r = request("GET", url, self._access_key, self._access_secret, params)
        results = []
        for item in r['result']['items']:
            results.append({
                "news_id": unicode2str(item['news_id']),
                "title": unicode2str(item['title']),
                "content": unicode2str(item['content']),
            })
        return results

    def close(self):
        pass