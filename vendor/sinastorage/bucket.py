#-*- coding:UTF-8 -*-
"""Bucket manipulation"""

from __future__ import absolute_import

import time
import hmac
import hashlib
# import httplib
# import urllib2
from sinastorage.compat import six, StringIO, urllib, http_client

import datetime
import warnings
from contextlib import contextmanager
# from urllib import quote_plus
from base64 import b64encode
import json
import sinastorage

from sinastorage.utils import (_amz_canonicalize, metadata_headers, metadata_remove_headers, 
                    rfc822_fmtdate, aws_md5, aws_urlquote, guess_mimetype, 
                    info_dict, expire2datetime, getSize, rfc822_parsedate, FileWithCallback)

sinastorage_domain = "sinacloud.net"

class ACL(object):
    ACL_GROUP_ANONYMOUSE    = 'GRPS000000ANONYMOUSE'        #匿名用户组 
    ACL_GROUP_CANONICAL     = 'GRPS0000000CANONICAL'        #全部认证通过的用户
    
    #full_control | write | write_acp | read | read_acp
    ACL_FULL_CONTROL        = 'full_control'
    ACL_WRITE               = 'write'
    ACL_WRITE_ACP           = 'write_acp'
    ACL_READ                = 'read'
    ACL_READ_ACP            = 'read_acp'

class SCSError(Exception):
    fp = None

    def __init__(self, message, **kwds):
        self.args = message, kwds.copy()
        self.msg, self.extra = self.args
        self.urllib2Response = None
        self.urllib2Request = None
        self.data = ''

    def __str__(self):
        rv = self.msg
        if self.extra:
            rv += " ("
            rv += ", ".join("%s=%r" % i for i in six.iteritems(self.extra))
            rv += ")"
        return rv

    @classmethod
    def from_urllib(cls, e, **extra):
        self = cls("HTTP error", **extra)
        self.urllib2Response = e
        if hasattr(e, 'hdrs'): 
            self.hdrs = e.hdrs 
        else: 
            self.hdrs = []
        if hasattr(e, 'url'): 
            self.url = e.url
        else:
            self.url = ''
        self.urllib2Request = self.extra['req']
        for attr in ("reason", "code", "filename"):
            if attr not in extra and hasattr(e, attr):
                self.extra[attr] = getattr(e, attr)
        self.fp = getattr(e, "fp", None)
        if self.fp:
            # The except clause is to avoid a bug in urllib2 which has it read
            # as in chunked mode, but SCS gives an empty reply.
            try:
                self.data = data = self.fp.read()
            except (http_client.HTTPException, urllib.error.URLError, ) as e:
                self.extra["read_error"] = e
                self.data = u'%s'%self.extra['reason']
            else:
                data = data.decode("utf-8")
                try:
                    msgJsonDict = json.loads(data)
                    self.msg = msgJsonDict['Message']
                except Exception as e:
                    self.data = u'%s'%self.extra['reason']
#                     print e
                    six.print_(e)
        else:
            self.data = u'%s'%self.extra['reason']
        return self

    @property
    def code(self): return self.extra.get("code")

class KeyNotFound(SCSError, KeyError):
    @property
    def key(self): return self.extra.get("key")
    
class ManualCancel(SCSError, KeyError):
    ''' 手动停止 '''
    @property
    def key(self): return self.extra.get("key")
    
class BadRequest(SCSError, KeyError):
    @property
    def key(self): return self.extra.get("key")

class StreamHTTPHandler(urllib.request.HTTPHandler):
    pass

class StreamHTTPSHandler(urllib.request.HTTPSHandler):
    pass

class AnyMethodRequest(urllib.request.Request):
    def __init__(self, *args, **kwds):
        if six.PY3:
            urllib.request.Request.__init__(self, *args, **kwds)
        else:
            if 'method' in kwds:
                self.method = kwds['method']
                del kwds['method']
            urllib.request.Request.__init__(self, *args, **kwds)

    def get_method(self):
        return self.method

def _upload_part(bucket_name, key_name, upload_id, parts_amount, part, source_path, offset, 
                 chunk_bytes, cb, num_cb, amount_of_retries=0, debug=1):
    from sinastorage.vendored.filechunkio import FileChunkIO
    from sinastorage.multipart import FileChunkWithCallback
    """
    Uploads a part with retries.
    """
    if debug == 1:
#         print "_upload_part(%s, %s, %s, %s, %s)" % (source_path, offset, bytes, upload_id, part.part_num)
        six.print_("_upload_part(%s, %s, %s, %s, %s)" % (source_path, offset, bytes, upload_id, part.part_num))
  
    def _upload(retries_left=amount_of_retries):
        try:
            if debug == 1:
#                 print 'Start uploading part #%d ...' % part.part_num
                six.print_('Start uploading part #%d ...' % part.part_num)
              
            bucket = SCSBucket(bucket_name)
              
            with FileChunkWithCallback(source_path, 'rb', offset=offset,
                             bytes=chunk_bytes, cb=cb, upload_id=upload_id, part_num=part.part_num) as fp:
                headers={"Content-Length":str(chunk_bytes)}
                  
                with FileChunkIO(source_path, 'rb', offset=offset,
                                 bytes=chunk_bytes) as fpForMd5:
                    headers["s-sina-sha1"] = aws_md5(fpForMd5)
                  
                scsResponse = bucket.put(key_name, fp, headers=headers, args={'partNumber':'%i'%part.part_num,
                                                         'uploadId':upload_id})
                part.etag = scsResponse.urllib2Response.info()['ETag']
                if num_cb:num_cb(upload_id, parts_amount, part)
                return part
        except Exception as exc:
            raise exc
            if retries_left:
                return _upload(retries_left=retries_left - 1)
            else:
#                 print 'Failed uploading part #%d' % part.part_num
                six.print_('Failed uploading part #%d' % part.part_num)
#                 print exc
                six.print_(exc)
                raise exc
        else:
            if debug == 1:
#                 print '... Uploaded part #%d' % part.part_num
                six.print_('... Uploaded part #%d' % part.part_num)
  
    return _upload()

# def _upload_part(bucket_name, key_name, upload_id, part, source_path, offset, 
#                  chunk_bytes, cb, num_cb, amount_of_retries=0, debug=1):
#      
#     fp = FileChunkWithCallback(source_path, 'rb', offset=offset,
#                              bytes=chunk_bytes, cb=cb, upload_id=upload_id, part_num=part.part_num)
#      
#     try:
#         partResult = _upload_part_by_fileWithCallback(bucket_name, key_name, upload_id, part, fp, num_cb, amount_of_retries)
#     finally:
#         fp.close()
#     
#     print '=====================partResult============',partResult
#     return partResult

def _upload_part_by_fileWithCallback(bucket_name, key_name, upload_id, parts_amount, part, 
                                     fileChunkWithCallback,
                                     num_cb, amount_of_retries=0):
    from sinastorage.vendored.filechunkio import FileChunkIO
    
    """
    Uploads a part with retries.
    """
    def _upload(retries_left=amount_of_retries):
        try:
            bucket = SCSBucket(bucket_name)
            
            headers={"Content-Length":str(fileChunkWithCallback.bytes)}
            with FileChunkIO(fileChunkWithCallback.name, 'rb', offset=fileChunkWithCallback.offset,
                             bytes=fileChunkWithCallback.bytes) as fpForMd5:
                headers["s-sina-sha1"] = aws_md5(fpForMd5)
            
            scsResponse = bucket.put(key_name, fileChunkWithCallback, 
                                     headers=headers, 
                                     args={'partNumber':'%i'%part.part_num,
                                           'uploadId':upload_id})
            part.etag = scsResponse.urllib2Response.info()['ETag']
            part.response = scsResponse
            if num_cb:num_cb(upload_id, parts_amount, part)
            return part
        except Exception as exc:
            raise exc
            if retries_left:
                return _upload(retries_left=retries_left - 1)
            else:
#                 print 'Failed uploading part #%d' % part.part_num
                six.print_('Failed uploading part #%d' % part.part_num)
#                 print exc
                six.print_(exc)
                raise exc
        else:
#             print '... Uploaded part #%d' % part.part_num
            six.print_('... Uploaded part #%d' % part.part_num)

    return _upload()


class SCSRequest(object):
    urllib_request_cls = AnyMethodRequest
    subresource_need_to_sign = ('acl', 'location', 'torrent', 'website', 'logging', 'relax', 'meta', 'uploads', 'part', 'copy', 'multipart')
    subresource_kv_need_to_sign = ('uploadId', 'ip', 'partNumber')

    def __init__(self, bucket=None, key=None, method="GET", headers={},
                 args=None, data=None, subresource=None):
        headers = headers.copy()
#         if data is not None and "s-sina-sha1" not in headers:
#             headers["s-sina-sha1"] = aws_md5(data)
        if "Date" not in headers:
            headers["Date"] = rfc822_fmtdate()
        if hasattr(bucket, "name"):
            bucket = bucket.name
        self.bucket = bucket
        self.key = key
        self.method = method
        self.headers = headers
        if not args:
            args = {}
        self.args = args
        self.args.setdefault('formatter','json')
        self.data = data
        self.subresource = subresource

    def __str__(self):
        return "<SCS %s request bucket %r key %r>" % (self.method, self.bucket, self.key)

    def descriptor(self):
        lines = (self.method,
                 self.headers.get("s-sina-sha1", ""),
                 self.headers.get("Content-Type", ""),
                 self.headers.get("Date", ""))
        preamb = "\n".join(str(line) for line in lines) + "\n"
        headers = _amz_canonicalize(self.headers)       #CanonicalizedAmzHeaders
        res = self.canonical_resource                   #CanonicalizedResource
        return "".join((preamb, headers, res))

    @property
    def canonical_resource(self):
        '''
            详见：http://sinastorage.sinaapp.com/developer/interface/aws/auth.html
        '''
        res = "/"
        if self.bucket:
            res += '%s/'%aws_urlquote(self.bucket)
        if self.key is not None:
            res += "%s" % aws_urlquote(self.key)
        if self.subresource:
            if self.subresource in self.subresource_need_to_sign:
                res += "?%s" % aws_urlquote(self.subresource)
        if self.args:
            rv = {}
            for key, value in six.iteritems(self.args):
#                 key = key.lower()
                if key in self.subresource_kv_need_to_sign:
                    rv[key] = value
            
            if len(rv) > 0 :
                parts = []
                for key in sorted(rv):
                    parts.append("%s=%s" % (key, rv[key]))
                res += "%s%s" % ('&' if self.subresource and self.subresource in self.subresource_need_to_sign else '?', "&".join(parts))
        return res

    def sign(self, cred):
        '''
            对stringToSign进行签名
            http://sinastorage.sinaapp.com/developer/interface/aws/auth.html
        '''
        stringToSign = self.descriptor()
        key = cred.secret_key.encode("utf-8")
        hasher = hmac.new(key, stringToSign.encode("utf-8"), hashlib.sha1)
        sign = (b64encode(hasher.digest())[5:15]).decode("utf-8")     #ssig
        '''
            Authorization=SINA product:/PL3776XmM
            Authorization:"SINA"+" "+"accessKey":"ssig"
        '''
        self.headers["Authorization"] = "SINA %s:%s" % (cred.access_key, sign)
        return sign

    def urllib(self, bucket):
        if hasattr(self.data,'offset') and hasattr(self.data,'bytes'):      #filechunkio
            data = self.data
        elif hasattr(self.data,'fileno'):                                   #file like
            data = self.data
        elif six.PY3 and isinstance(self.data, six.text_type):
            data = bytes(self.data, 'utf-8')
        else:
            data = self.data
            
        #http method 是GET时，不适用https方式请求
        if self.method.lower() == 'get' and bucket.base_url.startswith('https://') :
            bucket.base_url = 'http://'+bucket.base_url[8:]
        return self.urllib_request_cls(method=self.method, url=self.url(bucket.base_url), data=data, headers=self.headers)

    def url(self, base_url, arg_sep="&", bucketAsDomain=False):
        if bucketAsDomain:              #bucket name 作为域名
            url = 'http://'+self.bucket + "/"
        else:
            url = base_url + "/"
            
        #生成url，不适用https方式请求
        if url.startswith('https://') :
            url = 'http://'+url[8:]
            
        if self.key:
            url += aws_urlquote(self.key)
        if self.subresource or self.args:
            ps = []
            if self.subresource:
                ps.append(self.subresource)
            if self.args:
                args = self.args
                if hasattr(args, "iteritems") or hasattr(args, "items"):
                    args = six.iteritems(args)
                args = ((urllib.parse.quote_plus(k), urllib.parse.quote_plus(v)) for (k, v) in args)
                args = arg_sep.join("%s=%s" % i for i in args)
                ps.append(args)
            url += "?" + "&".join(ps)
        return url

class SCSFile(str):
    def __new__(cls, value, **kwds):
        return super(SCSFile, cls).__new__(cls, value)

    def __init__(self, value, **kwds):
        kwds["data"] = value
        self.kwds = kwds

    def put_into(self, bucket, key):
        return bucket.put(key, **self.kwds)

class SCSListing(object):
    """Representation of a single pageful of SCS bucket listing data."""

    truncated = None

    def __init__(self, jsonObj):
        self.resultDict = jsonObj
        self.truncated = self.resultDict['IsTruncated']             #Specifies whether (true) or not (false) all of the results were returned.
        self.marker = self.resultDict['Marker']
        self.prefix = self.resultDict['Prefix']
        self.delimiter = self.resultDict['Delimiter']
        self.contents_quantity = self.resultDict['ContentsQuantity']
        self.common_prefixes_quantity = self.resultDict['CommonPrefixesQuantity']
        self.next_marker = self.resultDict['NextMarker']             #下一页第一条游标

    def __iter__(self):
        
        commonPrefixes = self.resultDict['CommonPrefixes']
        for entry in commonPrefixes:
            item = self._json2item(entry,True)
            yield item
        
        contents = self.resultDict['Contents']
        for entry in contents:
            item = self._json2item(entry)
            yield item

    @classmethod
    def parse(cls, resp):
        return cls(json.loads(resp.read()))

    def _json2item(self, entry, prefix=False):
        
        if prefix :
            ''' 目录 
                {
                    "Prefix": "10000/"
                },
            '''
            isPrefix=True
            return (entry['Prefix'], isPrefix)
        else:
            ''' 文件
                {
                    "SHA1": "61bb70865c151ee0d7ed49ccafd509",
                    "Name": "aa.pdf",
                    "Expiration-Time": null,
                    "Last-Modified": "Tue, 25 Mar 2014 11:16:06 UTC",
                    "Owner": "SINA00000",
                    "MD5": "8ce3e6c0a9818162151",
                    "Content-Type": "application/pdf",
                    "Size": 2430
                },
            '''
            get = lambda tag: entry[tag]
            sha1 = get("SHA1")
            name = get("Name")
            expiration_time = rfc822_parsedate(get("Expiration-Time")) if get("Expiration-Time") else None
            modify = rfc822_parsedate(get("Last-Modified"))
            owner = get("Owner")
            md5 = get("MD5")
            content_type = get("Content-Type")
            size = int(get("Size"))
            isPrefix=False
            return (name, isPrefix, sha1, expiration_time, modify, owner, md5, content_type, size)

class SCSResponse(object):
    ''' response返回结果 '''
    def __init__(self, urllib2Request, urllib2Response):
        self.urllib2Request = urllib2Request
        self.urllib2Response = urllib2Response
        self._responseBody = None
        
        self.responseHeaders = {}
        if self.urllib2Response is not None and hasattr(self.urllib2Response,'info'):
            self.responseHeaders = dict((str(k.lower()), str(v)) for (k,v) in self.urllib2Response.info().items())
        
    def read(self, CHUNK=0):
        try:
            if CHUNK != 0:
                chunk =  self.urllib2Response.read(CHUNK)
            else:
                chunk = self.urllib2Response.read()
                
            if 'content-type' in self.responseHeaders and 'application/json'==self.responseHeaders['content-type'] and self._responseBody is None:
                if not isinstance(chunk, six.text_type):
                    self._responseBody = chunk.decode("utf-8")
                else:
                    self._responseBody = chunk
                return self._responseBody
            
            return chunk
        except Exception as e:
            raise e
    
    def close(self):
        self.read()
        self.urllib2Response.close()
        return self
    
    def info(self):
        return self.urllib2Response.info()
    
    @property
    def responseBody(self):
        if 'content-type' in self.responseHeaders and 'application/json'==self.responseHeaders['content-type'] and self._responseBody is None:
            return self.read()
        else:
            return self._responseBody

class SCSBucket(object):
    default_encoding = "utf-8"
    n_retries = 10

    def __init__(self, name=None, base_url=None, timeout=None, secure=False):
        if sinastorage.getDefaultAppInfo() is not None :
            self.access_key = sinastorage.getDefaultAppInfo().access_key
            self.secret_key = sinastorage.getDefaultAppInfo().secret_key
            secure = sinastorage.getDefaultAppInfo().secure
        else :
            import os
            if 'S3_ACCESS_KEY_ID' in os.environ and 'S3_SECRET_ACCESS_KEY' in os.environ:
                self.access_key = os.environ.get('S3_ACCESS_KEY_ID')
                self.secret_key = os.environ.get('S3_SECRET_ACCESS_KEY')
                secure = True
            else:
                raise ValueError("access_key and secret_key must not be None! \n\
                Please set sinastorage.setDefaultAppInfo('access_key', 'secret_key') \n\
                or set S3_ACCESS_KEY_ID and S3_SECRET_ACCESS_KEY in Environment first!")
        
        scheme = ("http", "https")[int(bool(secure))]
        if not base_url:
            base_url = "%s://%s" % (scheme, sinastorage_domain)
            if name:
                base_url += "/%s" % aws_urlquote(name)
        elif secure is not None:
            if not base_url.startswith(scheme + "://"):
                raise ValueError("secure=%r, url must use %s"
                                 % (secure, scheme))
        self.opener = self.build_opener()
        self.name = name
        
        self.base_url = base_url
        self.timeout = 30
        self.timeout = timeout

    def __str__(self):
        return "<%s %s at %r>" % (self.__class__.__name__, self.name, self.base_url)

    def __repr__(self):
        return self.__class__.__name__ + "(%r, access_key=%r, base_url=%r)" % (
            self.name, self.access_key, self.base_url)

    def __getitem__(self, name): return self.get(name)
    def __delitem__(self, name): return self.delete(name)
    def __setitem__(self, name, value):
        if hasattr(value, "put_into"):
            return value.put_into(self, name)
        else:
            return self.put(name, value)
    def __contains__(self, name):
        try:
            self.info(name)
        except KeyError:
            return False
        else:
            return True

    @contextmanager
    def timeout_disabled(self):
        (prev_timeout, self.timeout) = (self.timeout, None)
        try:
            yield
        finally:
            self.timeout = prev_timeout

    @classmethod
    def build_opener(cls):
        return urllib.request.build_opener(StreamHTTPHandler, StreamHTTPSHandler)

    def request(self, *a, **k):
        k.setdefault("bucket", self.name)
        return SCSRequest(*a, **k)

    def send(self, scsreq):
        scsreq.sign(self)
        for retry_no in range(self.n_retries):
            req = scsreq.urllib(self)
            try:
                if self.timeout:
                    response = self.opener.open(req, timeout=self.timeout)
                else:
                    response = self.opener.open(req)
                
                return SCSResponse(req, response)

            except (urllib.error.HTTPError, urllib.error.URLError, ManualCancel) as e:
                if isinstance(e, ManualCancel):     #手动取消
                    e.urllib2Request = req
                    raise e
                
                # If SCS gives HTTP 500, we should try again.
                ecode = getattr(e, "code", None)
#                 if ecode == 500:
#                     continue
#                 el
                if ecode == 404:
                    exc_cls = KeyNotFound
                elif ecode == 400:
                    exc_cls = BadRequest
                else:
                    exc_cls = SCSError
                raise exc_cls.from_urllib(e, key=scsreq.key, req = req)
        else:
            raise RuntimeError("ran out of retries")  # Shouldn't happen.

    def make_request(self, *a, **k):
        warnings.warn(DeprecationWarning("make_request() is deprecated, "
                                         "use request() and send()"))
        return self.send(self.request(*a, **k))

    def get(self, key):
        scsResponse = self.send(self.request(key=key))
#         response.scs_info = info_dict(dict(response.info()))
        return scsResponse

    def info(self, key):
#         response, request = self.send(self.request(method="HEAD", key=key))
        scsResponse = self.send(self.request(method="HEAD", key=key))
        rv = info_dict(dict(scsResponse.urllib2Response.info()))
        scsResponse.close()
        return rv
    
    def meta(self, key=None):
        scsResponse = self.send(self.request(method="GET", key=key, subresource='meta'))
        metaResult = json.loads(scsResponse.read())
        scsResponse.close()
        return metaResult

    def put(self, key, data=None, acl=None, metadata={}, mimetype=None,
            transformer=None, headers={},args=None,subresource=None):
        if isinstance(data, six.text_type):
            data = data.encode(self.default_encoding)
        headers = headers.copy()
        if mimetype:
            headers["Content-Type"] = str(mimetype)
        elif "Content-Type" not in headers:
            headers["Content-Type"] = guess_mimetype(key)
        headers.update(metadata_headers(metadata))
        if acl: headers["X-AMZ-ACL"] = acl
        if transformer: data = transformer(headers, data)
        if "Content-Length" not in headers:
#             if isinstance(data, file)  isinstance(data, FileChunkIO):
            if hasattr(data,'fileno'):
                headers["Content-Length"] = str(getSize(data.name))
            elif hasattr(data,'__len__'):
                headers["Content-Length"] = str(len(data))
            else:
                raise ValueError("Content-Length must be defined!!")
                
#         if "s-sina-sha1" not in headers:
#             headers["s-sina-sha1"] = aws_md5(data)
        scsreq = self.request(method="PUT", key=key, data=data, headers=headers, 
                              args=args, subresource=subresource)
        scsResponse = self.send(scsreq)
        return scsResponse
    
    def putFileByHeaders(self, key, fileWithCallback):
        '''
            filePath            本地文件路径
            progressCallback    上传文件进度回调方法    _callback(self._total, len(data), *self._args)
        '''
        headers={}
#         f = file(fileWithCallback.name, 'rb')
#         headers["s-sina-sha1"] = aws_md5(f)
#         f.close()
        
        from email.utils import formatdate
        from calendar import timegm
        expireDate = expire2datetime(datetime.timedelta(minutes=60*24))
        expireDate =  formatdate(timegm(expireDate.timetuple()), usegmt=True)
        headers['Date'] = 'Tue, 11 Nov 2015 15:25:57 GMT'#expireDate
        
        return self.put(key=key, data=fileWithCallback, headers=headers)
    
    def putFile(self, key, filePath, progressCallback=None, acl=None, metadata={}, mimetype=None,
            transformer=None, headers={}, args=None, subresource=None):
        '''
            filePath            本地文件路径
            progressCallback    上传文件进度回调方法    _callback(self._total, len(data), *self._args)
        '''
        with open(filePath, 'rb') as fp:
            headers["s-sina-sha1"] = aws_md5(fp)
        
        from email.utils import formatdate
        from calendar import timegm
        expireDate = expire2datetime(datetime.timedelta(minutes=60*24))
        expireDate =  formatdate(timegm(expireDate.timetuple()), usegmt=True)
    
        headers['Date'] = expireDate
        
#         with open(filePath, 'rb') as fp:
#             fileWithCallback = FileWithCallback(fp, progressCallback)
#             return self.put(key, fileWithCallback, acl, metadata, mimetype, transformer, headers, args, subresource)
#         fileWithCallback = FileWithCallback(filePath, 'rb', progressCallback)
        with FileWithCallback(filePath, 'rb', progressCallback) as fileWithCallback:
            return self.put(key, fileWithCallback, acl, metadata, mimetype, transformer, headers, args, subresource)
               
    def put_relax(self,key,sina_sha1, s_sina_length, acl=None, 
                  metadata={}, mimetype=None,headers={}):
        '''
            上传接口Relax
            REST型PUT上传，但不上传具体的文件内容。而是通过SHA-1值对系统内文件进行复制。
        '''
#         if isinstance(sina_sha1, six.text_type):
#             sina_sha1 = sina_sha1.encode(self.default_encoding)
        headers = headers.copy()
        if mimetype:
            headers["Content-Type"] = str(mimetype)
        elif "Content-Type" not in headers:
            headers["Content-Type"] = guess_mimetype(key)
        if sina_sha1 == None:
            raise ValueError("sina_sha1 must not None!!")
        if "s-sina-sha1" not in headers:
            headers["s-sina-sha1"] = sina_sha1
        if s_sina_length == 0:
            raise ValueError("s_sina_length must bigger than 0!!")
        if "s-sina-length" not in headers:
            headers["s-sina-length"] = s_sina_length
        headers.update(metadata_headers(metadata))
        if acl: headers["X-AMZ-ACL"] = acl
        if "Content-Length" not in headers:
            headers["Content-Length"] = 0
        scsreq = self.request(method="PUT", key=key, headers=headers,subresource='relax')
        return self.send(scsreq).close()
        
    def update_meta(self, key, metadata={}, acl=None, mimetype=None, headers={}):
        '''
            更新文件meta信息
            删除meta功能暂时不可用
        '''
        headers = headers.copy()
        if mimetype:
            headers["Content-Type"] = str(mimetype)
        elif "Content-Type" not in headers:
            headers["Content-Type"] = guess_mimetype(key)
        headers.update(metadata_headers(metadata))
#         headers.update(metadata_remove_headers(remove_metadata))
        if acl: headers["X-AMZ-ACL"] = acl
        if "Content-Length" not in headers:
            headers["Content-Length"] = 0
        scsreq = self.request(method="PUT", key=key, headers=headers, subresource='meta')
        return self.send(scsreq).close()   

    def acl_info(self, key, mimetype=None, headers={}):
        '''
            获取文件的acl信息
        '''
        headers = headers.copy()
        if mimetype:
            headers["Content-Type"] = str(mimetype)
        elif "Content-Type" not in headers:
            headers["Content-Type"] = guess_mimetype(key)
        if "Content-Length" not in headers:
            headers["Content-Length"] = 0
        scsreq = self.request(key=key, args={'formatter':'json'}, headers=headers, subresource='acl')
        scsResponse = self.send(scsreq)
        aclResult = json.loads(scsResponse.read())
        scsResponse.close()
        return aclResult
    
    def update_acl(self, key, acl={}):
        '''
            设置文件、bucket的acl
            组：
            GRPS0000000CANONICAL : 全部认证通过的用户
            GRPS000000ANONYMOUSE : 匿名用户
            
            ID：
            SINA0000001001HBK3UT、......
            
            权限(小写):
            FULL_CONTROL | WRITE | WRITE_ACP | READ | READ_ACP
            
            格式:
            {  
                'SINA0000000000000001' :  [ "read", "read_acp" , "write", "write_acp" ],
                'GRPS000000ANONYMOUSE' :  [ "read", "read_acp" , "write", "write_acp" ],
                'GRPS0000000CANONICAL' :  [ "read", "read_acp" , "write", "write_acp" ],
            }
        '''
        headers = {}
        headers["Content-Type"] = 'text/json'
        aclJson = json.dumps(acl)
        if "Content-Length" not in headers:
            headers["Content-Length"] = str(len(aclJson))
        scsreq = self.request(method="PUT", key=key, data=aclJson, headers=headers, subresource='acl')
        scsResponse = self.send(scsreq)
        return scsResponse.close()
        

    def delete(self, key):
        try:
            scsResponse = self.send(self.request(method="DELETE", key=key))
            return True
        except KeyNotFound as e:
            e.fp.close()
            return False
        else:
            return 200 <= scsResponse.urllib2Response.code < 300

    def copy(self, source, key, acl=None, metadata=None,
             mimetype=None, headers={}):
        """
            注意：
            source    必须从bucket开始，如：'/cloud0/aaa.txt'
        """
        headers = headers.copy()
        headers.update({"Content-Type": mimetype or guess_mimetype(key)})
        if "Content-Length" not in headers:
            headers["Content-Length"] = 0
        headers["X-AMZ-Copy-Source"] = source
        if acl: headers["X-AMZ-ACL"] = acl
        if metadata is not None:
            headers["X-AMZ-Metadata-Directive"] = "REPLACE"
            headers.update(metadata_headers(metadata))
        else:
            headers["X-AMZ-Metadata-Directive"] = "COPY"
        return self.send(self.request(method="PUT", key=key, headers=headers)).close()

    def _get_listing(self, args):
        return SCSListing.parse(self.send(self.request(key='', args=args)))

    def listdir(self, prefix=None, marker=None, limit=None, delimiter=None):
        """
        List bucket contents.

        return a generator SCSListing
        Yields tuples of (name, isPrefix, sha1, expiration_time, modify, owner, md5, content_type, size).

        *prefix*, if given, predicates `key.startswith(prefix)`.
        *marker*, if given, predicates `key > marker`, lexicographically.
        *limit*, if given, predicates `len(keys) <= limit`.

        *key* will include the *prefix* if any is given.

        .. note:: This method can make several requests to SCS if the listing is
                  very long.
        """
        m = (("prefix", prefix),
             ("marker", marker),
             ("max-keys", limit),
             ("delimiter", delimiter),
             ("formatter","json"))
        args = dict((str(k), str(v)) for (k, v) in m if v is not None)
        
        listing = self._get_listing(args)
        return listing
#         while listing:
#             for item in listing:
#                 yield item
#  
#             if limit is None and listing.truncated:
#                 args["marker"] = listing.next_marker
#                 listing = self._get_listing(args)
#             else:
#                 break
    
    def list_buckets(self):
        """
            List buckets.
            Yields tuples of (Name, CreationDate).
        """
        scsResponse = self.send(self.request(key=''))
        bucketJsonObj = json.loads(scsResponse.read())
        scsResponse.close()
        
        for item in bucketJsonObj['Buckets']:
            entry = (item['Name'],rfc822_parsedate(item['CreationDate']))
            yield entry

    def make_url(self, key, args=None, arg_sep="&", bucketAsDomain=False):
        scsreq = self.request(key=key, args=args)
        return scsreq.url(self.base_url, arg_sep=arg_sep, bucketAsDomain=bucketAsDomain)

    def make_url_authed(self, key, expire=datetime.timedelta(minutes=5), 
                        ip=None, bucketAsDomain=False):
        """Produce an authenticated URL for scs object *key*.

        *expire* is a delta or a datetime on which the authenticated URL
        expires. It defaults to five minutes, and accepts a timedelta, an
        integer delta in seconds, or a datetime.

        To generate an unauthenticated URL for a key, see `B.make_url`.
        """
        expire = expire2datetime(expire)
        expire = time.mktime(expire.timetuple()[:9])
        expire = str(int(expire))
        args = None
        if ip:
            args = {'ip':ip}
        scsreq = self.request(key=key, headers={"Date": expire}, args=args)
        sign = scsreq.sign(self)
        args_list = {"KID": 'sina,%s'%self.access_key,
                      "Expires": expire,
                      "ssig": sign}
        if ip:
            args_list['ip'] = ip
        scsreq.args = args_list.items()
        return scsreq.url(self.base_url, arg_sep="&", bucketAsDomain=bucketAsDomain)

    def url_for(self, key, authenticated=False,
                expire=datetime.timedelta(minutes=5)):
        msg = "use %s instead of url_for(authenticated=%r)"
        dep_cls = DeprecationWarning
        if authenticated:
            warnings.warn(dep_cls(msg % ("make_url_authed", True)))
            return self.make_url_authed(key, expire=expire)
        else:
            warnings.warn(dep_cls(msg % ("make_url", False)))
            return self.make_url(key)

    def put_bucket(self,  acl=None):
        headers = {"Content-Length": "0"}
        if acl:
            headers["X-AMZ-ACL"] = acl
        scsResponse = self.send(self.request(method="PUT", key=None, headers=headers))
        return scsResponse.close()

    def delete_bucket(self):
        return self.delete(None)
    
    '''
    判断bucket是否存在
    '''
    def exist(self):
        if self.name is None:
            raise RuntimeError("bucket name must be set!!")
        try:
            self.listdir(limit=1)
            return True
        except KeyNotFound:
            return False
        
    '''
    multiple upload
    '''
    def initiate_multipart_upload(self, key_name, acl=None, metadata={}, mimetype=None,
            headers={}):
        ''' 初始化分片上传 
        
            return type : dict
                {
                    u'UploadId': u'535dd723761d4f14a7210945cd7dea11', 
                    u'Key': u'test-python.zip', 
                    u'Bucket': u'create-a-bucket'
                }
        '''
        headers = headers.copy() if headers else {}
        if mimetype:
            headers["Content-Type"] = str(mimetype)
        elif "Content-Type" not in headers:
            headers["Content-Type"] = guess_mimetype(key_name)
        headers.update(metadata_headers(metadata))
        if acl: headers["X-AMZ-ACL"] = acl
        headers["Content-Length"] = "0"
        scsreq = self.request(method="POST", key=key_name, headers=headers, subresource='multipart')
        scsResponse = self.send(scsreq)
        initMultipartUploadResult = json.loads(scsResponse.read())
        scsResponse.close()
        from sinastorage.multipart import MultipartUpload
        multipart = MultipartUpload(self)
        multipart.upload_id = initMultipartUploadResult["UploadId"]
        multipart.bucket_name = initMultipartUploadResult["Bucket"]
        multipart.key_name = initMultipartUploadResult["Key"]
        multipart.init_multipart_response = scsResponse
        return multipart
    
    def complete_multipart_upload(self, multipart):
        
        jsonArray = []
        for part in multipart.parts:
            jsonDict = {}
            jsonDict['PartNumber']=part.part_num
            jsonDict['ETag']=part.etag
            jsonArray.append(jsonDict)
        
        data = json.dumps(jsonArray)
        
        headers = {}
        headers["Content-Type"] = guess_mimetype(multipart.key_name)
        headers["Content-Length"] = str(len(data))
        if "s-sina-sha1" not in headers:
            headers["s-sina-sha1"] = aws_md5(data)
        
        scsreq = self.request(method="POST", data=data, headers=headers, key=multipart.key_name, args={'uploadId':multipart.upload_id})
        scsResponse = self.send(scsreq)
        return scsResponse.close()
        
    
    def list_parts(self,upload_id,key_name):
        ''' 列出已经上传的所有分块 '''
        headers = {}
        headers["Content-Type"] = 'text/xml'
        headers["Content-Length"] = 0
        
        scsreq = self.request(method="GET", headers=headers, key=key_name, args={'uploadId':upload_id})
        scsResponse = self.send(scsreq)
        parts = json.loads(scsResponse.read())
        scsResponse.close()
        return parts
    
    def multipart_upload(self, key_name, source_path, acl=None, metadata={}, mimetype=None,
            headers={}, cb=None, num_cb=None):
        try:
            # multipart portions copyright Fabian Topfstedt
            # https://pypi.python.org/pypi/filechunkio/1.5
        
            import math
            import mimetypes
            from multiprocessing import Pool
            from sinastorage.vendored.filechunkio import FileChunkIO
            multipart_capable = True
            parallel_processes = 4
            min_bytes_per_chunk = 5 * 1024 * 1024                     #每片分片最大文件大小
            usage_flag_multipart_capable = """ [--multipart]"""
            usage_string_multipart_capable = """
                multipart - Upload files as multiple parts. This needs filechunkio.
                            Requires ListBucket, ListMultipartUploadParts,
                            ListBucketMultipartUploads and PutObject permissions."""
        except ImportError as err:
            multipart_capable = False
            usage_flag_multipart_capable = ""
            usage_string_multipart_capable = '\n\n     "' + \
                err.message[len('No module named '):] + \
                '" is missing for multipart support '
            
            raise err
            
        """
        Parallel multipart upload.
        """
        multipart = self.initiate_multipart_upload(key_name, acl, metadata, mimetype, headers)
        source_size = getSize(source_path)
        bytes_per_chunk = max(int(math.sqrt(min_bytes_per_chunk) * math.sqrt(source_size)),
                              min_bytes_per_chunk)
        chunk_amount = int(math.ceil(source_size / float(bytes_per_chunk)))
        multipart.bytes_per_part = bytes_per_chunk
        multipart.parts_amount = chunk_amount
        
        pool = Pool(processes=parallel_processes)
        i = 0
        for part in multipart.get_next_part():
            offset = i * bytes_per_chunk
            remaining_bytes = source_size - offset
            chunk_bytes = min([bytes_per_chunk, remaining_bytes])
            pool.apply_async(func = _upload_part, 
                             args = (self.name, key_name, multipart.upload_id, 
                                     multipart.parts_amount, part, source_path, 
                                     offset, chunk_bytes,cb, num_cb,), 
                             callback = lambda part : multipart.parts.append(part))
#             partResult = _upload_part(bucketName, key_name, multipart.upload_id, multipart.parts_amount, part, source_path, offset, chunk_bytes,
#                                             cb, num_cb)
            
#             multipart.parts.append(partResult)
            
            i = i + 1
            
        pool.close()
        pool.join()
    
        if len(multipart.parts) == chunk_amount:
            self.complete_multipart_upload(multipart)
#             multipart.complete_upload()
#             key = bucket.get_key(keyname)
#             key.set_acl(acl)
        else:
#             mp.cancel_upload()
#             print  len(multipart.parts) , chunk_amount
            six.print_(len(multipart.parts) , chunk_amount)

            raise RuntimeError("multipart upload is failed!!")
        


class ReadOnlySCSBucket(SCSBucket):
    """Read-only SCS bucket.

    Mostly useful for situations where urllib2 isn't available (e.g. Google App
    Engine), but you still want the utility functions (like generating
    authenticated URLs, and making upload HTML forms.)
    """

    def build_opener(self):
        return None
