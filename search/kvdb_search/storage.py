#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""使用sae的kvdb作为whoosh的storage
"""

__author__ = ['"wuyadong" <wuyadong311521@gmail.com>']


import os
from threading import Lock
import sae.kvdb
from whoosh.filedb.filestore import Storage
from whoosh.filedb.structfile import StructFile
from whoosh.compat import BytesIO
from whoosh.util import random_name


class SaeStorage(Storage):
    """实现存储在SAE上的Storage
    """

    def __init__(self, path):
        self.folder = path
        self._client = sae.kvdb.Client()
        self.locks = {}

    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self.folder)

    def create(self):
        return self

    def destroy(self):
        # Remove all files
        self.clean()
        # REMOVE locks
        del self.locks

    def create_file(self, name, **kwargs):
        def onclose_fn(sfile):
            self._client.set(self._fpath(name), sfile.file.getvalue())

        f = StructFile(BytesIO(), name=name, onclose=onclose_fn)
        return f

    def open_file(self, name, **kwargs):
        content = self._client.get(self._fpath(name))
        if content is None:
            raise NameError(name)

        def onclose_fn(sfile):
            self._client.replace(self._fpath(name), sfile.file.getvalue())

        return StructFile(BytesIO(content), name=name, onclose=onclose_fn)

    def _fpath(self, fname):
        return os.path.join(self.folder, fname)

    def clean(self):
        files = self.list()
        for fname in files:
            self._client.delete(self._fpath(fname))

    def list(self):
        file_generate = self._client.getkeys_by_prefix(prefix=self._fpath(""))
        file_names = []
        for f in file_generate:
            file_names.append(f['name'][len(self.folder)+1:])
        return file_names

    def file_exists(self, name):
        return name in self.list()

    def file_modified(self, name):
        return ''

    def file_length(self, name):
        pass

    def delete_file(self, name):
        self._client.delete(self._fpath(name))

    def rename_file(self, name, newname, safe=False):
        if name not in self.list():
            raise NameError(name)
        if safe and newname in self.list():
            raise NameError("File %r exists" % newname)

        content = self._client.get(self._fpath(name))
        self._client.delete(self._fpath(name))
        self._client.set(self._fpath(newname), content)

    def lock(self, name):
        if name not in self.locks:
            self.locks[name] = Lock()
        return self.locks[name]

    def temp_storage(self, name=None):
        name = name or "%s.tmp" % random_name()
        path = os.path.join(self.folder, name)
        tempstore = SaeStorage(path)
        return tempstore.create()
