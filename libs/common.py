#!/usr/bin/python
#coding:utf-8

'''
This file is part of doba.

Licensed under The MIT License
For full copyright and license information, please see the MIT-LICENSE.txt
Redistributions of files must retain the above copyright notice.

@author    jinhanjiang<jinhanjiang@foxmail.com>
@copyright jinhanjiang<jinhanjiang@foxmail.com>
@license   http://www.opensource.org/licenses/mit-license.php MIT License
'''

import time
import json
import hashlib
from bottle import request, redirect


# 以下定义的类
class Message(Exception):
    def __init__(self, message, code=0):
        self.message = message
        self.code = code
    def __str__(self):
        return '[%d]%s'%(self.code, self.message)

class Const:
    def __setattr__(self, name, value):
        if name in self.__dict__.keys():
            raise Message("Can't rebind const (%s)"%name, 1021)
        if not key.isupper():
            raise Message("Const variable must be combined with upper letters:'%s"%name, 1022)
        self.__dict__[name] = value


# 以下定义的函数
def json_encode(jsonobj):
    return json.dumps(jsonobj, sort_keys=True, separators=(',', ':'))

def json_decode(jsonstr):
    return json.loads(jsonstr)

def isjson(jsonstr):
    try:
        jsonobj = json.loads(jsonstr)
    except ValueError, e:
        return False    
    return True

def str2int(s):
    try:
        return int(s)
    except:
        if('-'==s[0]):
            return 0 - str2int(s[1:])
        elif s[0] in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']:
            num = 0
            for i in range(len(s) ):
                if s[i] in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']:
                    num = num * 10 + int(s[i])
                else:
                    return num
        else:
            return 0

def get_file_md5(fname):
    m = hashlib.md5()
    with open(fname,'rb') as fobj:
        while True:
            data = fobj.read(4096)
            if not data:
                break
            m.update(data)
    return m.hexdigest()

AUTH_REQUEST_EXPIRE_TIME = 180
def login_required():
    '''
    定义一个装饰器用于装饰需要验证的页面
    装饰器必须放在route装饰器下面
    '''
    apiKeyTokenInfos = {
        '10000': '513b60e222800340e4d7a12f2454794e'
    }
    # https://www.opscaff.com/2016/12/27/wl003python3-api%E5%8A%A0%E5%AF%86/
    def api_auth_valid():
        if not request.is_ajax:
            raise Message("无效的Ajax请求", 1001)

        # print(json.dumps(request.keys(), indent=4))
        authFields = request.get('HTTP_X_API_AUTH_FIELDS')
        if not authFields:
            raise Message("缺少必要参数1", 1002)

        authInfo = {}
        for idx in authFields.split(','):
            authInfo[idx] = request.get(('HTTP_X_API_%s'%idx).replace('-', '_').upper())

        if not authInfo.has_key('key') or not \
            authInfo.has_key('timestamp') or not \
            authInfo.has_key('version'):
            raise Message("缺少必要参数2", 1003)

        apiKey = authInfo['key']
        sign = request.get('HTTP_X_API_SIGN')
        timestamp = str2int(authInfo['timestamp'])

        # 验证版本，后期可根据版本调整传参方式
        if '1.0' != authInfo['version']:
            raise Message("API版本无效", 1004)

        # 验证提交的时间戳，用于将提交的sign每次不一致
        nowtime = str2int(time.time())
        if (nowtime - timestamp) > AUTH_REQUEST_EXPIRE_TIME: 
            raise Message("请求超时", 1005)
        
        # 去除不必要的加密参数
        if authInfo.has_key('sign'):
            del authInfo['sign']
        if authInfo.has_key('auth-fields'):
            del authInfo['auth-fields']
        if authInfo.has_key('auth_fields'):
            del authInfo['auth_fields']
        if authInfo.has_key('debug'):
            del authInfo['debug']

        # 通过传参ID获取加密密钥
        apiToken = ''
        if apiKey and apiKeyTokenInfos[apiKey]:
            apiToken = apiKeyTokenInfos[apiKey]
        if not apiToken:
            raise Message("API_KEY无效", 1006)

        # 通过传参，生成sign
        data = ('%s|%s|%s') %(
            json_encode(request.json), 
            json_encode(authInfo), 
            apiToken
        )
        newSign = hashlib.sha256(data.encode('utf-8')).hexdigest();

        # 传参中的sign 和 当前重新生成的sign验证参数是否一样
        # print(data)
        # print('req: %s'%sign)
        # print('new: %s'%newSign)
        if sign != newSign:
            debug = request.get('HTTP_X_API_DEBUG')
            if debug:
                raise Message(json_encode({"requestSign":sign, "clientSign":newSign, "clientString":'%s%s'%(data[0:-26], "".ljust(20, '*'))}), 1010)
            raise Message("密钥验证未通过", 1010)
        return True
    
    def login_permission(func):
        # 定义包装函数
        def wrapper(*args, **kargs):
            # 验证用户数据
            try:
                api_auth_valid()
                return func(**kargs)
            except Message as msg:
                if isjson(msg.message):
                    return {"success": False, "code": msg.code, "message": "api call failed", "response": json_decode(msg.message)}
                return {"success": False, "code": msg.code, "message": msg.message}
        return wrapper
 
    return login_permission