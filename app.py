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

from common import Const, Message, login_required, get_file_md5, isjson, json_decode
from bottle import Bottle, request, response, route, hook, run, default_app
from htpasswd import HtpasswdFile

Const.PWD_FILE = './pwd.conf'
Const.AUTH_FILE = './auth.conf'

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

'''
获取SVN账号，及分组，组员或人员项目权限
account: [
    "xiaoming": {
        "allPriv": false,
        "allPrivRW": "",
        "projectRW": [
            {
                "p": "project1:/",
                "r": "rw"
            },
            ...
        ],
        "group": [
            "dev"
        ]
    },
    ...
],
groups: {
    "dev": [
        "xiaoming",
        ...
    ]
},
projects: {
    "project1:/": {
        "groups": [
            {"g": "dev", "r": "rw"},
            ...
        ],
        "accounts": [
            {"a": "xiaoming", "r": "rw"},
            ...
        ]
    }
}
'''
@route('/getAccountList', method='POST')
@login_required()
def getAccountList():
    accounts = {}; groups = {}; projects = {}
    with open(Const.PWD_FILE, 'r') as fp, open(Const.AUTH_FILE, 'r') as fa:
        accountLines = fp.readlines()
        for line in accountLines:
            # print(line.strip())
            accounts[line.strip().split(":")[0]] = {
                'allPriv': False,
                'allPrivRW': "",
                'group': [],
                'projectRW': []
            }

        isUnderGroups = False; allPriv = False; lastProject = None
        
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
                        if '/' == lastProject:
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

            # 非[groups]下，即项目下的权限
            elif lastProject:
                # 设置项目
                if not projects.has_key(lastProject):
                    projects[lastProject] = {
                        "groups": [],
                        "accounts": [],
                    }

                # 是否所有权限
                if allPriv:
                    pr = re.match(r'^@', line)
                    if pr:
                        groupName = line.replace('@', '').split("=")[0]
                        rightRW = line.split("=")[1]
                        for user in groups[groupName]:
                            if accounts.has_key(user):
                                accounts[user]['allPriv'] = True
                                accounts[user]['allPrivRW'] = rightRW
                                accounts[user]['projectRW'].append({
                                    "p": lastProject,
                                    "r": rightRW
                                })
                        projects[lastProject]["groups"].append({
                            "g": groupName,
                            "r": rightRW
                            })
                    else:
                        user = line.split("=")[0]
                        if accounts.has_key(user):
                            rightRW = line.split("=")[1]
                            if accounts.has_key(user):
                                accounts[user]['allPriv'] = True
                                accounts[user]['allPrivRW'] = rightRW
                                accounts[user]['projectRW'].append({
                                    "p": lastProject,
                                    "r": rightRW
                                })
                            projects[lastProject]["accounts"].append({
                                "a": user,
                                "r": rightRW
                                })
                
                else:
                    # [xxx:/]项目下的权限
                    pr = re.match(r'^@', line)
                    if pr:
                        groupName = line.replace('@', '').split("=")[0]
                        rightRW = line.split("=")[1]
                        for user in groups[groupName]:
                            if accounts.has_key(user):
                                accounts[user]['projectRW'].append({
                                    "p": lastProject,
                                    "r": rightRW
                                    })
                        projects[lastProject]["groups"].append({
                            "g": groupName,
                            "r": rightRW
                            })
                    else:
                        user = line.split("=")[0]
                        rightRW = line.split("=")[1]
                        if accounts.has_key(user):
                            accounts[user]['projectRW'].append({
                                "p": lastProject,
                                "r": rightRW
                                })
                            projects[lastProject]["accounts"].append({
                                "a": user,
                                "r": rightRW
                                })
    return {
        "success": True, 
        "accounts": accounts, 
        "authfilemd5": get_file_md5(Const.AUTH_FILE), 
        "groups": groups, 
        "projects": projects,
        "pwdfilemd5": get_file_md5(Const.PWD_FILE)
    }

'''
更新分组及项目权限

{
    "authfilemd5": "",
    "pwdfilemd5": "",
    "groups": {
        "dev": [
            "xiaoming"
        ]
    },
    "projects": {
        "project1:/": {
            "groups": [
                {"g": "dev", "r": "rw"}
            ],
            "accounts": [
                {"a": "xiaoming", "r": "rw"}
            ]
        }
    }
}
'''
@route('/updateAuth', method='POST')
@login_required()
def updateAuth():
    dataJson = request.json
    if not dataJson.has_key('groups') or not dataJson.has_key('projects'):
        raise Message("分组权限参数必传", 1001)

    if not dataJson.has_key('authfilemd5') or not dataJson.has_key('pwdfilemd5'):
        raise Message("验证参数必传", 1002)

    authfilemd5 = get_file_md5(Const.AUTH_FILE)
    if authfilemd5 != dataJson['authfilemd5']:
        raise Message("文件可能被修改", 1003)

    pwdfilemd5 = get_file_md5(Const.PWD_FILE)
    if pwdfilemd5 != dataJson['pwdfilemd5']:
        raise Message("文件可能被修改", 1004)

    txts = ["[groups]"]
    if not isinstance(dataJson['groups'], dict):
        raise Message("分组参数无效", 1005)
   
    accounts = []; groups = []
    with open(Const.PWD_FILE, 'r') as fp:
        accountLines = fp.readlines()
        for line in accountLines:
            accounts.append(line.strip().split(":")[0])

    for groupName in sorted(dataJson['groups']):
        if not isinstance(dataJson['groups'][groupName], list): 
            raise Message("组[%s]数据无效"%groupName, 1006)

        users = []; groupUsers = dataJson['groups'][groupName]
        for user in groupUsers:
            if user in accounts:
                users.append(user)
        if len(users) > 0:
            txts.append("%s=%s"%(groupName, ",".join(users)))
            groups.append(groupName)

    txts.append("\n")
        
    if not isinstance(dataJson["projects"], dict):
        raise Message("项目参数无效", 1007)

    for project in sorted(dataJson["projects"]):
        if not isinstance(dataJson["projects"][project], dict):
            raise Message("项目[%s]数据无效"%project, 1008)

        projectInfo = dataJson["projects"][project]
        if not isinstance(projectInfo["groups"], list) or not isinstance(projectInfo["accounts"], list):
            raise Message("项目[%s]数据无效"%project, 1009)             

        if len(projectInfo["groups"]) > 0 or len(projectInfo["accounts"]) > 0:
            txts.append("[%s]"%project)
            for obj in projectInfo["groups"]:
                if obj["g"] in groups:
                    txts.append('@%s=%s'%(obj["g"], obj["r"]))
            for obj in projectInfo["accounts"]:
                if obj["a"] in accounts:
                    txts.append('%s=%s'%(obj["a"], obj["r"]))
        txts.append("\n")

    # 转化为txt保存到文件中
    txt = "\n".join(txts)

    with open(Const.AUTH_FILE, 'w') as fa:
        fa.write(txt)
    return {
        "success": True,
        "authfilemd5": get_file_md5(Const.AUTH_FILE)
    }

'''
创建 或 更新用户账号密码
'''
@route('/updateUser', method='POST')
@login_required()
def updateUser():
    dataJson = request.json
    if not dataJson.has_key('username') or not dataJson.has_key('password'):
        raise Message("用户名或密码参数必传", 1001)

    if not dataJson.has_key('pwdfilemd5'):
        raise Message("验证参数必传", 1002)

    pwdfilemd5 = get_file_md5(Const.PWD_FILE)
    if pwdfilemd5 != dataJson['pwdfilemd5']:
        raise Message("文件可能被修改", 1003)

    passwdfile = HtpasswdFile(Const.PWD_FILE)
    passwdfile.load()
 
    # 更新用户及密码
    passwdfile.update(dataJson['username'], dataJson['password'])

    # 执行完保存
    passwdfile.save()
    return {
        "success": True,
        "pwdfilemd5": get_file_md5(Const.PWD_FILE)
    }

'''
删除用户
'''
@route('/delUser', method='POST')
@login_required()
def delUser():
    dataJson = request.json
    if not dataJson.has_key('username'):
        raise Message("用户名参数必传", 1001)

    if not dataJson.has_key('pwdfilemd5'):
        raise Message("验证参数必传", 1002)

    pwdfilemd5 = get_file_md5(Const.PWD_FILE)
    if pwdfilemd5 != dataJson['pwdfilemd5']:
        raise Message("文件可能被修改", 1003)

    passwdfile = HtpasswdFile(Const.PWD_FILE)
    passwdfile.load()

    # 删除用户
    passwdfile.delete(dataJson['username'])

    # 执行完保存
    passwdfile.save()
    return {
        "success": True,
        "pwdfilemd5": get_file_md5(Const.PWD_FILE)
    }

if __name__ == '__main__':
    run(host='0.0.0.0', port=9005, reloader=True)
else:
    application = default_app()