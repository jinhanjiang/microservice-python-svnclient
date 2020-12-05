#!/usr/bin/python
#coding=utf-8

import sys
reload(sys)
sys.setdefaultencoding('utf-8')
sys.path.append(r'../libs')

import re
import json
import time
import hashlib
import requests
from htpasswd import HtpasswdFile

def requestApi(dataJson={}):
    API_KEY = "10000"
    API_TOKEN = "513b60e222800340e4d7a12f2454794e"

    # 提交的数据
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36',
        'content-type':'application/json', 
        'x-requested-with': 'XMLHttpRequest',
    }
    # 认证提交的值参数转为字符串，否则导致验证失败
    authInfo = {
        "key": API_KEY,
        "timestamp": '%s'%int(time.time()),
        "version": '1.0'
    }
    data = ('%s|%s|%s') %(
        json.dumps(dataJson, sort_keys=True, separators=(',', ':')), 
        json.dumps(authInfo, sort_keys=True, separators=(',', ':')), 
        API_TOKEN
    )
    authInfo['auth-fields'] = ','.join(authInfo.keys())
    authInfo['sign'] = hashlib.sha256(data.encode('utf-8')).hexdigest();
    authInfo['debug'] = "1"
    for idx in authInfo:
        headers["x-api-%s"%(idx.lower())] = authInfo[idx]

    resp = requests.post("http://127.0.0.1:9005/getAccountList", data=json.dumps(dataJson), headers=headers)
    print(resp.text)


def passwdUser():
    filename = '../pwd.conf'
    username = 'xiaoguo'
    password = '123456'

    passwdfile = HtpasswdFile(filename)
    passwdfile.load()
 
    # 删除用户
    #passwdfile.delete(username)

    # 更新用户及密码
    passwdfile.update(username, password)

    # 执行完保存
    passwdfile.save()

if __name__ == '__main__':
    # passwdUser()
    requestApi()