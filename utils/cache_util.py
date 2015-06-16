#!/usr/bin/env python
# -*- coding=utf-8 -*-

"""缓存
"""

__author__ = ['"wuyadong" <wuyadong311521@gmail.com>']

import pylibmc

mc_client = pylibmc.Client([])


def cached(expiration=60*30, key=None):
    """装饰
    """
    def wrap(fn):
        def _wrap(*args, **kwargs):

            if key:
                mc_key = key
            else:
                mc_key = "%s:%s-%s-%s" % ("cached", fn.func_name,
                                          str(args), str(kwargs))

            result = mc_client.get(mc_key)
            if not result:
                result = fn(*args, **kwargs)

                try:
                    mc_client.set(mc_key, result, time=expiration)
                except ValueError:
                    pass

            return result
        return _wrap
    return wrap
