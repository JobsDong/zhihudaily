#!/usr/bin/python
# -*- coding=utf-8 -*-


__author__ = ['"wuyadong" <wuyadong311521@gmail.com>']

from lxml import html


def extract_text(content):
    try:
        tree = html.fromstring(content, parser=html.HTMLParser(encoding='utf-8'))
        rc = []
        for node in tree.itertext():
            rc.append(node.strip())
        return u''.join(rc)
    except Exception:
        return content


def str2unicode(text):
    return text.decode('utf-8') if isinstance(text, str) else unicode(text)


def unicode2str(text):
    return text.encode('utf-8') if isinstance(text, unicode) else str(text)

#----------------本地化的Connection---------------
from config import static_path


class Connection(object):
    """本地化的Storage服务
    """

    def put_object(self, bucket_name, object_name, image_data, image_type):
        image_dir = os.path.join(static_path, bucket_name)

        if not os.path.exists(image_dir):
            os.mkdir(image_dir)
        with open(os.path.join(image_dir, object_name), "wb") as object_file:
            object_file.write(image_data)

    def generate_url(self, bucket_name, object_name):
        return "/static/%s/%s" % (bucket_name, object_name)

#------------SAE支持的whoosh-----------

import os
from threading import Lock
from sae.storage import Bucket
from whoosh.filedb.filestore import Storage
from whoosh.filedb.structfile import StructFile
from whoosh.compat import BytesIO
from whoosh.util import random_name


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
            self._bucket.put_object(self._fpath(name), sfile.file.getvalue())

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
        if name not in self.list():
            raise NameError(name)
        if safe and newname in self.list():
            raise NameError("File %r exists" % newname)

        content = self._bucket.get_object_contents(self._fpath(name))
        self._bucket.delete_object(self._fpath(name))
        self._bucket.put_object(self._fpath(newname), content)

    def lock(self, name):
        if name not in self.locks:
            self.locks[name] = Lock()
        return self.locks[name]

    def temp_storage(self, name=None):
        name = name or "%s.tmp" % random_name()
        path = os.path.join(self.folder, name)
        tempstore = SaeStorage(self.bucket_name, path)
        return tempstore.create()

import pylibmc
import config

if config.debug:
    mc_client = pylibmc.Client([config.MEMCACHE_HOST])
else:
    mc_client = pylibmc.Client([])


# ----------------------memorized------------------------------------------
def cached(expiration=60*30, key=None):

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


class SaeMemcacheStorage(Storage):
    """实现存储在SAE上的MemCache
    """

    def __init__(self, index_directory="index_fs"):
        self._index_dir = index_directory
        if self._index_dir not in mc_client:
            mc_client.set(self._index_dir, {})
        self.locks = {}

    def create(self):
        mc_client.set(self._index_dir, {})
        return self

    def _fpath(self, fname):
        return "%s/%s" % (self._index_dir, fname)

    def destroy(self):
        self.clean()
        del self.locks

    def clean(self):
        f2s = mc_client.get(self._index_dir) or {}
        if f2s:
            mc_client.delete_multi([self._fpath(fname) for fname in f2s.keys()])
        mc_client.set(self._index_dir, {})

    def list(self):
        f2s = mc_client.get(self._index_dir) or {}
        return f2s.keys()

    def total_size(self):
        f2s = mc_client.get(self._index_dir) or {}
        return sum(f2s.values())

    def file_exists(self, name):
        return name in self.list()

    def file_length(self, name):
        f2s = mc_client.get(self._index_dir) or {}
        if name not in f2s:
            raise NameError(name)
        return f2s[name]

    def file_modified(self, name):
        return -1

    def delete_file(self, name):
        f2s = mc_client.get(self._index_dir) or {}
        if name not in f2s:
            raise NameError(name)
        mc_client.delete(self._fpath(name))
        del f2s[name]
        mc_client.set(self._index_dir, f2s)

    def rename_file(self, name, newname, safe=False):
        f2s = mc_client.get(self._index_dir) or {}
        if name not in f2s:
            raise NameError(name)
        if safe and newname in f2s:
            raise NameError("File %r exists" % newname)

        content = mc_client.get(self._fpath(name)) or ""
        del f2s[name]
        mc_client.delete(self._fpath(name))
        mc_client.set(self._fpath(newname), content)
        f2s[newname] = len(content)
        mc_client.set(self._index_dir, f2s)

    def create_file(self, name, **kwargs):
        def onclose_fn(sfile):
            f2s = mc_client.get(self._index_dir) or {}
            v = sfile.file.getvalue()
            mc_client.set(self._fpath(name), v)
            f2s[name] = len(v)
            mc_client.set(self._index_dir, f2s)

        f = StructFile(BytesIO(), name=name, onclose=onclose_fn)
        return f

    def open_file(self, name, *args, **kwargs):
        f2s = mc_client.get(self._index_dir) or {}
        if name not in f2s:
            raise NameError
        content = mc_client.get(self._fpath(name)) or ""

        def onclose_fn(sfile):
            mc_client.set(self._fpath(name), sfile.file.getvalue())
        return StructFile(BytesIO(content), name=name, onclose=onclose_fn)

    def lock(self, name):
        if name not in self.locks:
            self.locks[name] = Lock()
        return self.locks[name]

    def temp_storage(self, dir_path=None):
        dir_path = dir_path or "%s.tmp" % random_name()
        temp_store = SaeMemcacheStorage(dir_path)
        return temp_store.create()