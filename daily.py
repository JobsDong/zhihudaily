#!/usr/bin/python
# -*- coding=utf-8 -*-

"""知乎日报API
"""

__author__ = ['"wuyadong" <wuyadong311521@gmail.com>']

import httplib
import socket
import json


class ZhiHuServiceException(Exception):

    def __init__(self, status, msg, err):
        self.args = (status, msg, err)
        self.status = status
        self.msg = msg
        self.err = err


class ZhiHuClientException(Exception):

    def __init__(self, msg):
        super(ZhiHuClientException, self).__init__(msg)


class ZhiHu(object):
    """知乎日报的SDK类
    """
    def __init__(self):
        self._host = "news-at.zhihu.com"
        self._port = 80
        self._timeout = 10

    def get_latest_news(self):
        content = self._do_http_request("/api/3/news/latest")
        return json.loads(content)

    def get_news(self, news_id):
        content = self._do_http_request("/api/3/news/%s" % news_id)
        return json.loads(content)

    def get_before_news(self, date_str):
        content = self._do_http_request("/api/3/news/before/%s" % date_str)
        return json.loads(content)

    def _decode_msg(self, msg):
        if isinstance(msg, str):
            msg = unicode(msg, 'utf-8')

        return msg

    def _do_http_request(self, url):
        http, content, msg, error, status = None, None, None, None, None
        try:
            http = httplib.HTTPConnection(self._host, self._port, self._timeout)
            http.request("GET", url)
            response = http.getresponse()

            status = response.status
            if status / 100 == 2:
                content = self._decode_msg(response.read())
            else:
                msg = response.reason
                error = self._decode_msg(response.read())
        except (httplib.HTTPException, socket.error, socket.timeout) as e:
            raise ZhiHuClientException(str(e))
        except Exception as e:
            raise ZhiHuClientException(str(e))
        finally:
            if http:
                http.close()
        if msg:
            raise ZhiHuServiceException(status, msg, error)

        return content

if __name__ == "__main__":
    zh = ZhiHu()
    print zh.get_latest_news()
