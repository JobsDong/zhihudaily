#!/usr/bin/env python
# -*- coding: utf-8 -*-


__author__ = ['"wuyadong" <wuyadong311521@gmail.com>']

import tornado.web


class BaseHandler(tornado.web.RequestHandler):
    """定义公共函数
    """

    def get_error_html(self, status_code, **kwargs):
        reason = kwargs.get('reason', "Server Error")
        exception = kwargs.get('exception', "")

        return self.render_string("error.html", code=str(status_code),
                                  reason=str(reason), exception=str(exception))


class ErrorHandler(BaseHandler):
    """处理错误信息
    """

    def prepare(self):
        self.render("404.html")