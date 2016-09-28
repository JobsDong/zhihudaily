from __future__ import absolute_import

__version__ = "1.1.6"

from .bucket import SCSFile, SCSBucket, SCSError, KeyNotFound
SCSFile, SCSBucket, SCSError, KeyNotFound
__all__ = "SCSFile", "SCSBucket", "SCSError"


class appinfo(object):
    def __init__(self,access_key,secret_key,secure):
        self.access_key=access_key
        self.secret_key=secret_key
        self.secure = secure

def getDefaultAppInfo():
    pass

def setDefaultAppInfo(access_key,secret_key,secure=False):
    default = appinfo(access_key,secret_key,secure)
    global getDefaultAppInfo 
    getDefaultAppInfo = lambda: default