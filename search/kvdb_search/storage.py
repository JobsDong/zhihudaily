#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""使用sae的kvdb作为whoosh的storage
"""

__author__ = ['"wuyadong" <wuyadong311521@gmail.com>']

import os
import json
import time
from threading import Lock
from whoosh.filedb.filestore import Storage
from whoosh.filedb.structfile import StructFile
from whoosh.util import random_name
from StringIO import StringIO
from utils.extract_util import unicode2str

import sae.kvdb

MAX_VALUE_LENGTH = 1048576
DELIMITER = "_block_"


class KVDBCollection(object):

    def __init__(self, fpath):
        self.fpath = unicode2str(fpath)
        self.kvdb = sae.kvdb.KVClient()

    def _fpath(self, name):
        name = unicode2str(name)
        return os.path.join(self.fpath, name)

    def exists(self, name):
        return self.kvdb.get(self._fpath(name)) is not None

    def list(self):
        keys = self.kvdb.getkeys_by_prefix(self.fpath)
        keys = list(keys)
        if len(keys) == 0:
            return []
        else:
            fnames = []
            for key in keys:
                if DELIMITER not in key:
                    fnames.append(key.replace("%s/" % self.fpath, ""))
            return fnames

    def delete(self, name):
        keys = self.kvdb.getkeys_by_prefix(os.path.join(self._fpath(name)))
        for key in keys:
            self.kvdb.delete(key)

    def last_modified(self, name):
        stat_json = json.loads(self.kvdb.get(self._fpath(name)))
        return stat_json["timestamp"]

    def length(self, name):
        stat_json = json.loads(self.kvdb.get(self._fpath(name)))
        return stat_json["bytes"]

    def _block_generator(self, content):
        while True:
            data = content.read(MAX_VALUE_LENGTH)
            if not data:
                break
            yield data

    def set_value(self, name, value):
        timestamp = time.time()
        length = len(value)

        # content
        content = StringIO(value)
        block_paths = []
        for index, block in enumerate(self._block_generator(content)):
            block_path = "%s%s%s" % (self._fpath(name), DELIMITER, index)
            self.kvdb.set(block_path, block)
            block_paths.append(block_path)

        # stat
        self.kvdb.set(self._fpath(name), json.dumps({"timestamp": timestamp,
                                                     "bytes": length,
                                                     "blocks": block_paths}))

    def get_value(self, name):
        stat_json = json.loads(self.kvdb.get(self._fpath(name)))
        blocks = stat_json['blocks']
        data = StringIO()
        for block_path in blocks:
            block_path = unicode2str(block_path)
            data.write(self.kvdb.get(block_path))
        value = data.getvalue()
        return value

    def close(self):
        self.kvdb.disconnect_all()


class SaeStorage(Storage):
    """实现存储在SAE上的Storage
    """

    def __init__(self, name):
        self.name = name
        self.kvdb_coll = KVDBCollection(name)
        self.locks = {}

    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self.name)

    def create(self):
        return self

    def destroy(self, *args, **kwargs):
        # remove all files
        self.clean()
        # remove locks
        del self.locks

    def create_file(self, fname, *args, **kwargs):
        def onclose_fn(sfile):
            value = sfile.file.getvalue()
            self.kvdb_coll.set_value(fname, value)
        f = StructFile(StringIO(), name=fname, onclose=onclose_fn)
        return f

    def open_file(self, fname, *args, **kwargs):
        if not self.kvdb_coll.exists(fname):
            raise NameError(fname)

        content = self.kvdb_coll.get_value(fname)

        def onclose_fn(sfile):
            value = sfile.file.getvalue()
            self.kvdb_coll.set_value(fname, value)

        return StructFile(StringIO(content), name=fname, onclose=onclose_fn)

    def clean(self):
        fnames = self.list()
        for fname in fnames:
            self.kvdb_coll.delete(fname)

    def list(self):
        fnames = self.kvdb_coll.list()
        return fnames

    def file_exists(self, name):
        return self.kvdb_coll.exists(name)

    def file_modified(self, name):
        return self.kvdb_coll.last_modified(name)

    def file_length(self, name):
        return self.kvdb_coll.length(name)

    def delete_file(self, name):
        self.kvdb_coll.delete(name)

    def rename_file(self, name, new_name, safe=False):
        content = self.kvdb_coll.get_value(name)
        self.kvdb_coll.delete(name)
        self.kvdb_coll.set_value(new_name, content)

    def lock(self, name):
        if name not in self.locks:
            self.locks[name] = Lock()
        return self.locks[name]

    def close(self):
        self.kvdb_coll.close()

    def temp_storage(self, name=None):
        name = name or "%s.tmp" % random_name()
        temp_store = SaeStorage(name)
        return temp_store.create()