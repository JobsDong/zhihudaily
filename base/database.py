#!/usr/bin/env python
# -*- coding=utf-8 -*-


"""数据库操作
"""

__author__ = ['"wuyadong" <wuyadong311521@gmail.com>']


import time
import MySQLdb
import logging


class BaseDao(object):
    """
    """

    def __init__(self, host, port, user, passwd, db):
        self._db = None
        self._db_args = dict(host=host, port=port,
                             user=user, passwd=passwd,
                             db=db)
        self._last_use_time = time.time()
        self._max_idle_time = 30
        try:
            self.reconnect()
        except Exception, e:
            import traceback
            stack = traceback.format_exc()
            logging.error("Cannot connect to MySQL:%s\n%s" % (e, stack))

    def close(self):
        if getattr(self, "_db", None) is not None:
            self._db.close()
            self._db = None

    def reconnect(self):
        self.close()
        self._db = MySQLdb.connect(**self._db_args)
        self._db.autocommit(True)

    def _ensure_connected(self):
        if (self._db is None) or \
                (time.time() - self._last_use_time > self._max_idle_time):
            self.reconnect()
        self._last_use_time = time.time()

    def _cursor(self):
        self._ensure_connected()
        return self._db.cursor()
