#!/usr/bin/python
# -*- coding=utf-8 -*-


__author__ = ['"wuyadong" <wuyadong311521@gmail.com>']

from lxml import html


def extract_text(content):
    tree = html.fromstring(content, parser=html.HTMLParser(encoding='utf-8'))
    rc = []
    for node in tree.itertext():
        rc.append(node.strip())
    return u''.join(rc)


def str2unicode(text):
    return text.decode('utf-8') if isinstance(text, str) else text


def unicode2str(text):
    return text.encode('utf-8') if isinstance(text, unicode) else text

#----------------模拟Connection---------------
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

#------------模拟whoosh-----------

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

#-------------------对jieba分词进行SAE的适应性改造--------------
import jieba
import jieba.analyse
from math import log
import marshal
import os.path


def list_bucket_file_names(bucket, dir_path):
    file_generate = bucket.list(path=os.path.join(dir_path, ""))
    file_names = []
    for f in file_generate:
        file_names.append(f['name'][len(dir_path)+1:])
    return file_names


def exists_bucket_file_name(bucket, dir_path, fname):
    return fname in list_bucket_file_names(bucket, dir_path)


def modify_time(bucket, fpath):
    return bucket.stat_object(fpath).get('last_modified', '')


def rename_file(bucket, path, new_path):
    content = bucket.get_object_contents(path)
    bucket.delete_object(path)
    bucket.put_object(new_path, content)


def gen_pfdict(bucket, fpath):
    lfreq = {}
    pfdict = set()
    ltotal = 0.0
    print fpath
    content = bucket.get_object_contents(fpath)
    lineno = 0
    for line in content.rstrip().decode('utf-8').split('\n'):
        lineno += 1
        try:
            word, freq = line.split(' ')[:2]
            freq = float(freq)
            lfreq[word] = freq
            ltotal += freq
            for ch in xrange(len(word)):
                pfdict.add(word[:ch+1])
        except ValueError, e:
            print "%s at line %s %s" % (fpath, lineno, line)
            raise
    return pfdict, lfreq, ltotal


def initialize_jieba(bucket_name, jieba_dir, dict_name="dict.txt", cache_name="jieba.cache", idf_name="idf.txt"):
    """使用Sae Storage中的词典初始化jieba库
    :return:
    """
    bucket = Bucket(bucket_name)

    # set dict.txt jieba.cache
    with jieba.DICT_LOCK:
        if jieba.initialized:
            return
        if jieba.pfdict:
            del jieba.pfdict
            jieba.pfdict = None

        print "Building prefix dict"
        cache_path = os.path.join(jieba_dir, cache_name)
        dict_path = os.path.join(jieba_dir, dict_name)

        load_from_cache_fail = True
        if cache_name in list_bucket_file_names(bucket, jieba_dir) and modify_time(bucket, cache_path) > modify_time(bucket, dict_path):
            print "Loading model from cache %s" % cache_path
            try:
                content = bucket.get_object_contents(cache_path)
                jieba.pfdict, jieba.FREQ, jieba.total, jieba.min_freq = marshal.load(content)
                load_from_cache_fail = not isinstance(jieba.pfdict, set)
            except:
                load_from_cache_fail = True

        if load_from_cache_fail:
            jieba.pfdict, jieba.FREQ, jieba.total = gen_pfdict(bucket, dict_path)
            jieba.FREQ = dict((k, log(float(v) / jieba.total)) for k, v in jieba.FREQ.iteritems()) #normalize
            jieba.min_freq = min(jieba.FREQ.itervalues())
            print "Dumping model to file cache %s" % cache_path
            try:
                temp_name = "%s.tmp" % random_name()
                temp_path = os.path.join(jieba_dir, temp_name)
                bs = marshal.dumps((jieba.pfdict, jieba.FREQ, jieba.total, jieba.min_freq))
                bucket.put_object(temp_path, bs)

                # rename
                content = bucket.get_object_contents(temp_path)
                bucket.delete_object(temp_path)
                bucket.put_object(cache_path, content)
            except:
                print "Dump cache file failed."

    # jieba idf
    class IDFLoader:
        def __init__(self):
            self.path = ""
            self.idf_freq = {}
            self.median_idf = 0.0

        def set_new_path(self, new_idf_path):
            print "Loading model from idf %s" % new_idf_path
            if self.path != new_idf_path:
                content = bucket.get_object_contents(new_idf_path).decode('utf-8')
                idf_freq = {}
                lines = content.rstrip('\n').split('\n')
                for line in lines:
                    word, freq = line.split(' ')
                    idf_freq[word] = float(freq)
                median_idf = sorted(idf_freq.values())[len(idf_freq)//2]
                self.idf_freq = idf_freq
                self.median_idf = median_idf
                self.path = new_idf_path

        def get_idf(self):
            return self.idf_freq, self.median_idf

    jieba.idf_loader = IDFLoader()
    jieba.idf_loader.set_new_path(os.path.join(jieba_dir, "idf.txt"))

ChineseAnalyzer = jieba.analyse.ChineseAnalyzer