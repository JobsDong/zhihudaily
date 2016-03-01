#!/usr/bin/env python
# -*- coding: utf-8 -*-


__author__ = ['"wuyadong" <wuyadong311521@gmail.com>']


def import_object(name):
    """import an object by name
    """
    if isinstance(name, unicode):
        name = name.encode("utf-8")

    if name.count(".") == 0:
        return __import__(name, None, None)

    parts = name.split(".")
    obj = __import__(".".join(parts[:-1]), None, None, [parts[-1]], 0)
    try:
        return getattr(obj, parts[-1])
    except AttributeError:
        raise ImportError("No module named %s" % parts[-1])