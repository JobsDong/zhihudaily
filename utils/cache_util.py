#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""缓存
"""

__author__ = ['"wuyadong" <wuyadong311521@gmail.com>']

import pylibmc
import pickle
from utils.extract_util import unicode2str

mc_client = pylibmc.Client([])


def cached(expiration=60*30, key=None):
    """装饰
    """
    def wrap(fn):
        def _wrap(*args, **kwargs):

            if key:
                mc_key = key
            else:
                mc_key = "%s:%s-%s-%s" % (
                    "cached", fn.func_name,
                    "|".join([unicode2str(arg) for arg in args]),
                    "|".join(["%s:%s" % (unicode2str(n), unicode2str(v))
                             for n, v in kwargs.items()]))

            result = mc_client.get(mc_key)
            if result is not None:
                result = pickle.loads(result)
            else:
                result = fn(*args, **kwargs)

                try:
                    mc_client.set(mc_key, pickle.dumps(result), time=expiration)
                except ValueError:
                    pass

            return result
        return _wrap
    return wrap
