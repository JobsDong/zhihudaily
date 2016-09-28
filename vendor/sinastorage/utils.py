#-*- coding:UTF-8 -*-

"""Misc. SCS-related utilities."""

import time
import hashlib
import datetime
import mimetypes
from base64 import b64encode
# from urllib import quote
from sinastorage.compat import urllib
from calendar import timegm
import os,time
# from bucket import ManualCancel
# import bucket
from sinastorage.compat import six

def _amz_canonicalize(headers):
    r"""Canonicalize AMZ headers in that certain AWS way.

    >>> _amz_canonicalize({"x-amz-test": "test"})
    'x-amz-test:test\n'
    >>> _amz_canonicalize({"x-amz-first": "test",
    ...                    "x-amz-second": "hello"})
    'x-amz-first:test\nx-amz-second:hello\n'
    >>> _amz_canonicalize({})
    ''
    """
    
    ''' 
        CanonicalizedAmzHeaders描述
        CanonicalizedAmzHeaders = "\n".join( allheaders witch startswith "x-amz-" or "x-sina-" ) + '\n'
        这里的所有header名需要转换成小写，并按header名进行排序，过滤掉空格，并加以’\n’进行连接
    '''
    rv = {}
    for header, value in six.iteritems(headers):
        header = header.lower()
#         if header.startswith("x-amz-"):  #edit by hanchao
        if header.startswith("x-amz-") or header.startswith("x-sina-"):
            rv.setdefault(header, []).append(value)
    parts = []
    for key in sorted(rv):
        parts.append("%s:%s\n" % (key, ",".join(rv[key])))
    return "".join(parts)

def metadata_headers(metadata):
    return dict(("X-AMZ-Meta-" + h, v) for h, v in six.iteritems(metadata))

def metadata_remove_headers(metadata_key):
    return dict(("x-amz-remove-meta-"+k,'') for k in metadata_key)

def headers_metadata(headers):
    return dict((h[11:], v) for h, v in six.iteritems(headers)
                            if h.lower().startswith("x-amz-meta-"))

iso8601_fmt = '%Y-%m-%dT%H:%M:%S.000Z'

def _iso8601_dt(v): return datetime.datetime.strptime(v, iso8601_fmt)
def rfc822_fmtdate(t=None):
    from email.utils import formatdate
    if t is None:
        t = datetime.datetime.utcnow()
    return formatdate(timegm(t.timetuple()), usegmt=True)
def rfc822_parsedate(v):
    from email.utils import parsedate
    return datetime.datetime.fromtimestamp(time.mktime(parsedate(v)))

def expire2datetime(expire, base=None):
    """Force *expire* into a datetime relative to *base*.

    If expire is a relatively small integer, it is assumed to be a delta in
    seconds. This is possible for deltas up to 10 years.

    If expire is a delta, it is added to *base* to yield the expire date.

    If base isn't given, the current time is assumed.

    >>> base = datetime.datetime(1990, 1, 31, 1, 2, 3)
    >>> expire2datetime(base) == base
    True
    >>> expire2datetime(3600 * 24, base=base) - base
    datetime.timedelta(1)
    >>> import time
    >>> expire2datetime(time.mktime(base.timetuple())) == base
    True
    """
    if hasattr(expire, "timetuple"):
        return expire
    if base is None:
        base = datetime.datetime.now()
    # *expire* is not a datetime object; try interpreting it
    # as a timedelta, a UNIX timestamp or offsets in seconds.
    try:
        return base + expire
    except TypeError:
        # Since the operands could not be added, reinterpret
        # *expire* as a UNIX timestamp or a delta in seconds.
        # This is rather arbitrary: 10 years are allowed.
        unix_eighties = 315529200
        if expire < unix_eighties:
            return base + datetime.timedelta(seconds=expire)
        else:
            return datetime.datetime.fromtimestamp(expire)

def aws_md5(data):
    """Make an AWS-style MD5 hash (digest in base64)."""
#     hasher = hashlib.new("md5")
#     if hasattr(data, "read"):
#         data.seek(0)
#         while True:
#             chunk = data.read(8192)
#             if not chunk:
#                 break
#             hasher.update(chunk)
#         data.seek(0)
#     else:
#         hasher.update(data)
#     return b64encode(hasher.digest()).decode("ascii")
    hasher = hashlib.new("sha1")
    if hasattr(data, "read"):
        data.seek(0)
        while True:
            chunk = data.read(8192)
            if not chunk:
                break
            hasher.update(chunk)
        data.seek(0)
    else:
        if six.PY3 and isinstance(data, six.text_type):
            data = bytes(data, 'utf-8')
        hasher.update(data)
    
    return hasher.hexdigest()#.decode("ascii")#hex(hasher.digest()).decode("ascii")

def aws_urlquote(value):
    r"""AWS-style quote a URL part.

    >>> aws_urlquote("/bucket/a key")
    '/bucket/a%20key'
    """
    if isinstance(value, six.text_type):
        value = value.encode("utf-8")
    return urllib.parse.quote(value, "/")

def guess_mimetype(fn, default="application/octet-stream"):
    """Guess a mimetype from filename *fn*.

    >>> guess_mimetype("foo.txt")
    'text/plain'
    >>> guess_mimetype("foo")
    'application/octet-stream'
    """
    if "." not in fn:
        return default
    bfn, ext = fn.lower().rsplit(".", 1)
    if ext == "jpg": ext = "jpeg"
    try:
        content_type = mimetypes.guess_type(bfn + "." + ext)[0]
        return content_type if content_type is not None else default
    except Exception as e:
        return default

def info_dict(headers):
    headers = dict((str(k.lower()), str(v)) for (k,v) in headers.items() if headers and hasattr(headers, 'items'))
    rv = {"headers": headers, "metadata": headers_metadata(headers)}
    if "content-length" in headers:
        rv["size"] = int(headers["content-length"])
    if "content-type" in headers:
        rv["mimetype"] = headers["content-type"]
    if "date" in headers:
        rv["date"] = rfc822_parsedate(headers["date"])
    if "last-modified" in headers:
        rv["modify"] = rfc822_parsedate(headers["last-modified"])
    return rv

def name(o):
    """Find the name of *o*.

    Functions:
    >>> name(name)
    'sinastorage.utils.name'
    >>> def my_fun(): pass
    >>> name(my_fun)
    'sinastorage.utils.my_fun'

    Classes:
    >>> class MyKlass(object): pass
    >>> name(MyKlass)
    'sinastorage.utils.MyKlass'

    Instances:
    >>> name(MyKlass())
    'sinastorage.utils.MyKlass'

    Types:
    >>> name(str), name(object), name(int)
    ('str', 'object', 'int')

    Type instances:
    >>> name("Hello"), name(True), name(None), name(Ellipsis)
    ('str', 'bool', 'NoneType', 'ellipsis')
    """
    if hasattr(o, "__name__"):
        rv = o.__name__
        modname = getattr(o, "__module__", None)
        # This work-around because Python does it itself,
        # see typeobject.c, type_repr.
        # Note that Python only checks for __builtin__.
        if modname not in (None, "", "__builtin__", "builtins"):
            rv = o.__module__ + "." + rv
    else:
        for o in getattr(o, "__mro__", o.__class__.__mro__):
            rv = name(o)
            # If there is no name for the this baseclass, this ensures we check
            # the next rather than say the object has no name (i.e., return
            # None)
            if rv is not None:
                break
    return rv

def getSize(filename):
    st = os.stat(filename)#.st_size
    return st.st_size

from io import FileIO

class FileWithCallback(FileIO):
    def __init__(self, name, mode='r', callback=None, cb_args=(), cb_kwargs={}):
        self._callback = callback
        self._cb_args = cb_args
        self._cb_kwargs = cb_kwargs
        self._progress = 0
        super(FileWithCallback, self).__init__(name, mode, closefd=True)
        self.seek(0, os.SEEK_END)
        self._len = self.tell()
        self.seek(0)
        
    def __enter__(self):
        return self
    
    def __exit__(self, type, value, trace):
        self.close()
        
#     def name(self):
#         return self.buf.name
        
    def __len__(self):
        return self._len

    def read(self, n=-1):
        chunk = super(FileWithCallback, self).read(n)
        self._progress += int(len(chunk))
        self._cb_kwargs.update({'size':self._len, 'progress':self._progress})
        if self._callback:
            try:
                self._callback(*self._cb_args, **self._cb_kwargs)
            except:
                from sinastorage.bucket import ManualCancel
                raise ManualCancel('operation abort')
        
        return chunk
        


# class FileWithCallback(file):
#     def __init__(self, path, mode, callback, *args):
#         file.__init__(self, path, mode)
#         self.seek(0, os.SEEK_END)
#         self._total = self.tell()
#         self.seek(0)
#         self._callback = callback
#         self._args = args
#         self.lastTimestamp = time.time()
#         self.received = 0
#         
#         self.cancelRead = False
# 
#     def __len__(self):
#         return self._total
# 
#     def read(self, size):
#         if self.cancelRead :
#             raise bucket.ManualCancel('operation abort')
#         data = file.read(self, size)
#         self.received += len(data)
#         if self._callback and (time.time() - self.lastTimestamp >= 1.0):
#             self._callback(self._total, self.received, *self._args)
#             self.lastTimestamp = time.time()
#             self.received = 0
#             
#         return data
