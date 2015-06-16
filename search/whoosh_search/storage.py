#!/usr/bin/env python
# -*- coding=utf-8 -*-

"""Storage
"""

__author__ = ['"wuyadong" <wuyadong311521@gmail.com>']


import os
from threading import Lock
from sae.storage import Bucket
from whoosh.filedb.filestore import Storage, RamStorage
from whoosh.filedb.structfile import StructFile
from whoosh.compat import BytesIO


class SaeStorage(Storage):
    """实现存储在SAE上的Storage
    """

    def __init__(self, bucket_name, path):
        self.bucket_name = bucket_name
        self.folder = path
        self._bucket = Bucket(bucket_name)
        self.locks = {}

    def __repr__(self):
        return "%s(%r)(%r)" % (self.__class__.__name__, self.bucket_name,
                               self.folder)

    def create(self):
        return self

    def destroy(self):
        # Remove all files
        self.clean()
        # REMOVE locks
        del self.locks

    def create_file(self, name, **kwargs):
        def onclose_fn(sfile):
            self._bucket.put_object(self._fpath(name), sfile.file.getvalue())

        f = StructFile(BytesIO(), name=name, onclose=onclose_fn)
        return f

    def open_file(self, name, **kwargs):
        if self._bucket.stat_object(self._fpath(name)) is None:
            raise NameError(name)
        content = self._bucket.get_object_contents(self._fpath(name))

        def onclose_fn(sfile):
            new_content = sfile.file.getvalue()
            if new_content != content:
                self._bucket.put_object(self._fpath(name), new_content)

        return StructFile(BytesIO(content), name=name, onclose=onclose_fn)

    def _fpath(self, fname):
        return os.path.join(self.folder, fname)

    def clean(self):
        files = self.list()
        for fname in files:
            self._bucket.delete_object(self._fpath(fname))

    def list(self):
        file_generate = self._bucket.list(path=self._fpath(""))
        file_names = []
        for f in file_generate:
            file_names.append(f['name'][len(self.folder)+1:])
        return file_names

    def file_exists(self, name):
        return name in self.list()

    def file_modified(self, name):
        return self._bucket.stat_object(self._fpath(name))\
            .get('last_modified', '')

    def file_length(self, name):
        return int(self._bucket.stat_object(self._fpath(name))['bytes'])

    def delete_file(self, name):
        self._bucket.delete_object(self._fpath(name))

    def rename_file(self, name, newname, safe=False):
        name_list = self.list()
        if name not in name_list:
            raise NameError(name)
        if safe and newname in name_list:
            raise NameError("File %r exists" % newname)

        content = self._bucket.get_object_contents(self._fpath(name))
        self._bucket.delete_object(self._fpath(name))
        self._bucket.put_object(self._fpath(newname), content)

    def lock(self, name):
        if name not in self.locks:
            self.locks[name] = Lock()
        return self.locks[name]

    def temp_storage(self, name=None):
        temp_store = RamStorage()
        return temp_store.create()