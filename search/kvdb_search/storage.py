#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""使用sae的kvdb作为whoosh的storage
"""

__author__ = ['"wuyadong" <wuyadong311521@gmail.com>']

from threading import Lock
from whoosh.filedb.filestore import Storage, RamStorage
from whoosh.filedb.structfile import StructFile
from whoosh.compat import BytesIO

import sae.kvdb


class LockError(Exception):
    pass


class SaeStorage(Storage):
    """实现存储在SAE上的Storage
    """

    def __init__(self, name):
        self.name = name
        self._client = sae.kvdb.Client()
        self.locks = {}

    def create(self):
        return self

    def destroy(self, *args, **kwargs):
        f_names = self.list()
        for f_name in f_names:
            self._client.delete("%s%s" % (self.name, f_name))

    def create_file(self, name):
        def onclose_fn(sfile):
            self._client.set("%s%s" % (self.name, name), sfile.file.getvalue())

        f = StructFile(BytesIO(), name=name, onclose=onclose_fn)
        return f

    def open_file(self, name, *args, **kwargs):
        return StructFile(self._client.get("%s%s" % (self.name, name)))

    def list(self):
        key_generator = self._client.getkeys_by_prefix(self.name)
        keys = []
        for f in key_generator:
            keys.append(f.replace(self.name, ""))

        return keys

    def file_exists(self, name):
        return self._client.get("%s%s" % (self.name, name)) is not None

    def file_modified(self, name):
        return -1

    def file_length(self, name):
        return len(self._client.get("%s%s" % (self.name, name)))

    def delete_file(self, name):
        return self._client.delete("%s%s" % (self.name, name))

    def rename_file(self, name, new_name, safe=False):
        v = self._client.get("%s%s" % (self.name, name))
        self._client.set("%s%s" % (self.name, new_name), v)
        self._client.delete("%s%s" % (self.name, name))

    def lock(self, name):
        if name not in self.locks:
            self.locks[name] = Lock()
        return self.locks[name]

    def close(self):
        self._client.disconnect_all()

    def temp_storage(self, name=None):
        temp_store = RamStorage()
        return temp_store.create()