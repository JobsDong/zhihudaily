#!/usr/bin/env python
# -*- coding=utf-8 -*-

"""知乎日报
"""

__author__ = ['"wuyadong" <wuyadong311521@gmail.com>']


import config
import sae

import tornado.wsgi
from base.handler import ErrorHandler
from daily.handler import DailyHandler
from search.handler import SearchHandler
from operation.handler import OperationHandler


class Application(tornado.wsgi.WSGIApplication):

    def __init__(self):
        handlers = [
            (r'/', DailyHandler),
            (r'/search', SearchHandler),
            (r'/operation/(.*)', OperationHandler),
            (r'/.*', ErrorHandler),
        ]

        settings = {
            "static_path": config.static_path,
            "template_path": config.template_path,
            "debug": config.debug,
        }

        tornado.wsgi.WSGIApplication.__init__(self, handlers, **settings)


app = Application()

application = sae.create_wsgi_app(app)
