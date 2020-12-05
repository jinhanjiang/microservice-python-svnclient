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

# svn账号管理，组权限管理
import re
import sys
import hashlib
reload(sys)
sys.setdefaultencoding('utf-8')
sys.path.append(r'./libs')

from common import login_required, get_file_md5, isjson, json_decode, Message
from bottle import Bottle, request, response, route, hook, run, default_app


app = Bottle()

@hook('after_request')
def enable_cors():
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET,POST,PUT,OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Referer, Accept, Origin, User-Agent, \
        Content-Type, X-Requested-With, X-Api-Auth-Fields, X-Api-Sign, X-Api-Debug, X-Api-Key, X-Api-Timestamp, X-Api-Version'

@route('/')
def index():
    return 'svn client:0.1.0'

@route('/getAccountList', method='POST')
@login_required()
def getAccountList():
    accounts = {}
    groups = {}   
    pwdfile = './pwd.conf'
    authfile = './auth.conf'

    with open(pwdfile, 'r') as fp, open(authfile, 'r') as fa:
        accountLines = fp.readlines()
        for line in accountLines:
            accounts[line.strip().split(":")[0]] = {
                'allPriv': False,
                'allPrivRW': "",
                'group': [],
                'projectRW': []
            }

        isUnderGroups = False
        allPriv = False
        lastProject = None
        
        groupLists = fa.readlines()
        for line in groupLists:
            line = line.strip()
            if not line:
                continue

            m1 = re.match(r'\[', line)
            if m1:
                # 判断是否在[groups]下面的内容
                # 人员所在组
                m2 = re.match(r'^\[groups\]$', line)
                isUnderGroups = True if m2 else False

                if not isUnderGroups:
                    # 项目权限
                    m3 = re.match(r'^\[(.*?)\]$', line)
                    if m3:
                        lastProject = m3.group(1)
                        # 以下用户有所有权限
                        if '/' == m3.group(1):
                            allPriv = True
                        else:
                            allPriv = False

                continue

            # 如果在[groups]下，解析人员对应的组
            if isUnderGroups:
                groupName = line.split("=")[0]
                users = line.split("=")[1].split(",")
                # print(line.strip().split("=")[1])
                groups[groupName] = []
                for user in users:
                    if accounts.has_key(user):
                       accounts[user]['group'].append(groupName)
                    groups[groupName].append(user)
            # 非[groups]下， 即项目下的权限
            else:
                # 是否所有权限
                if allPriv:
                    pr = re.match(r'^@', line)
                    if pr:
                        groupName = line.replace('@', '').split("=")[0]
                        for user in groups[groupName]:
                            if accounts.has_key(user):
                                accounts[user]['allPriv'] = True
                                accounts[user]['allPrivRW'] = line.split("=")[1]
                    else:
                        user = line.split("=")[0]
                        if accounts.has_key(user):
                            accounts[user]['allPriv'] = True
                            accounts[user]['allPrivRW'] = line.split("=")[1]
                
                else:
                    # [xxx:/]项目下的权限
                    if lastProject:
                        pr = re.match(r'^@', line)
                        if pr:
                            groupName = line.replace('@', '').split("=")[0]
                            for user in groups[groupName]:
                                if accounts.has_key(user):
                                    accounts[user]['projectRW'].append({
                                        "p": lastProject,
                                        "r": line.split("=")[1]
                                    })
                        else:
                            user = line.split("=")[0]
                            if accounts.has_key(user):
                                accounts[user]['projectRW'].append({
                                    "p": lastProject,
                                    "r": line.split("=")[1]
                                })
    return {
        "success": True, 
        "accounts": accounts, 
        # 更新数据时，验证md5值是否变化，防止同时修改文件
        "authfilemd5": get_file_md5(authfile), 
        "groups": groups, 
        "pwdfilemd5": get_file_md5(pwdfile)
    }


@route('/updateUser', method='POST')
@login_required()
def updateUser():
    dataJson = request.json
    print(dataJson)

if __name__ == '__main__':
    run(host='0.0.0.0', port=9005, reloader=True)
else:
    application = default_app()