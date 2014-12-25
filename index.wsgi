#!/usr/bin/python
# -*- coding=utf-8 -*-

"""知乎日报
"""

import os
import sys

root = os.path.dirname(__file__)

# 两者取其一
sys.path.insert(0, os.path.join(root, 'site-packages'))

__author__ = ['"wuyadong" <wuyadong311521@gmail.com>']

from config import debug, static_path, template_path

if not debug:
    import sae
else:
    from tornado.options import define, options
    define("port", default=8080, help="run on the given port", type=int)

import tornado.wsgi
import handler


class Application(tornado.wsgi.WSGIApplication):

    def __init__(self):
        handlers = [
            (r'/', handler.DayHandler),
            (r'/search', handler.SearchHandler),
            (r'/operation/(.*)', handler.OperationHandler),
            (r'/.*', handler.ErrorHandler),
        ]

        settings = {
            "static_path": static_path,
            "template_path": template_path,
            "debug": debug,
        }

        tornado.wsgi.WSGIApplication.__init__(self, handlers, **settings)


app = Application()

if not debug:
    application = sae.create_wsgi_app(app)
else:
    import wsgiref.simple_server
    try:
        tornado.options.parse_command_line()
        server = wsgiref.simple_server.make_server("", options.port, app)
        server.serve_forever()
    except KeyboardInterrupt:
        print "close"
