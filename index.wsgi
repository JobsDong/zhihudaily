#!/usr/bin/python
# -*- coding=utf-8 -*-

"""知乎日报
"""

__author__ = ['"wuyadong" <wuyadong311521@gmail.com>']

from config import debug, static_path, template_path

if not debug:
	import sae

import os
import tornado.wsgi
import handler


class Application(tornado.wsgi.WSGIApplication):

	def __init__(self):
		handlers = [
			(r'/', handler.DayHandler),
			(r'/crawl', handler.CrawlHandler),
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
	server = wsgiref.simple_server.make_server("", 8080, app)
	server.serve_forever()