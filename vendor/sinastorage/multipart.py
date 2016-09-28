#-*- coding:UTF-8 -*-
'''
Created on 2014年4月29日

'''
from sinastorage.vendored.filechunkio import FileChunkIO
import time

from . import bucket

class Part(object):
    ''' 分片对象 '''
    def __init__(self, part_num, etag=None):
        self.part_num = part_num
        self.etag = etag
        self.scsResponse = None        #每片响应结果

class MultipartUpload(object):
    '''
    分片上传
    '''
    def __init__(self, bucket=None):
        self.scsBucket = bucket
        self.bucket_name = None
        self.key_name = None
        self.upload_id = None
        self.parts = []
        
        self.parts_amount = 0
        self.bytes_per_part = None
        
        self.init_multipart_response = None     #初始化分片上传请求结果
        self.complete_multipart_response = None     #合并分片上传请求结果
        
        self.current_part_num_offset = 0
        
    def get_next_part(self):
        ''' 获取下一片分片 '''
        part = None
        while self.current_part_num_offset < self.parts_amount:
            part = Part(self.current_part_num_offset)
#             self.parts.append(part)
            yield part
            self.current_part_num_offset += 1
                

class FileChunkWithCallback(FileChunkIO):
    def __init__(self, name, mode='r', closefd=True, offset=0, bytes=None, cb=None,
                 upload_id=0, part_num=0, *args, **kwargs):
        FileChunkIO.__init__(self, name, mode, closefd, offset, bytes,  *args, **kwargs)
        
        self._callback = cb
        self.upload_id = upload_id
        self.part_num = part_num
        self.received = 0
        self.lastTimestamp = time.time()
        
        self.allReceived = 0
        
        self.cancelRead = False
        
    def read(self, n=-1):
        if self.cancelRead :
            raise bucket.ManualCancel('operation abort')
        
        data = super(FileChunkWithCallback, self).read(n)
        amount = len(data)
        self.received += amount
        self.allReceived += amount
        if self._callback and ((time.time() - self.lastTimestamp >= 1.0) or self.allReceived==self.bytes) and self.received!=0:
            self._callback(self.upload_id, self.part_num, self.bytes, self.received)
            self.lastTimestamp = time.time()
            self.received = 0
            
        return data
        
        
        
        
        
        
        