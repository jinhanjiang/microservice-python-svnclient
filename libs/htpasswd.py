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

import os
import sys
from string import ascii_letters, digits
from random import choice
import subprocess

try:
    import crypt
except ImportError:
    try:
        import fcrypt as crypt
    except ImportError:
        sys.stderr.write("Cannot find a crypt module.  "
                         "Possibly http://carey.geek.nz/code/python-fcrypt/\n")
        sys.exit(1)

'''
passwdfile = HtpasswdFile(filename)
passwdfile.load()
 
# 删除用户
passwdfile.delete(username)

# 更新用户及密码
passwdfile.update(username, password)

# 执行完保存
passwdfile.save()
'''
 
 
class UnknownEncryptionMode(Exception):
    def __init__(self, mode):
        self.mode = mode
    def __str__(self):
        return "Encryption Mode %s is unknown/unsupported" % self.mode

class HtpasswdFile:
    """A class for manipulating htpasswd files."""
    def __init__(self, filename, create=False, encryption_mode='md5'):
        self.entries = []
        self.filename = filename
        self.encryption_mode = encryption_mode
        if not create:
            if os.path.exists(self.filename):
                self.load()
            else:
                raise Exception("%s does not exist" % self.filename)
 
    def load(self):
        """Read the htpasswd file into memory."""
        lines = open(self.filename, 'r').readlines()
        self.entries = []
        for line in lines:
            username, pwhash = line.split(':')
            entry = [username, pwhash.rstrip()]
            self.entries.append(entry)
 
    def save(self):
        """Write the htpasswd file to disk"""
        open(self.filename, 'w').writelines(["%s:%s\n" % (entry[0], entry[1])
                                             for entry in self.entries])
 
    def update(self, username, password):
        """Replace the entry for the given user, or add it if new."""
        pwhash = self._encrypt_password(password)
        matching_entries = [entry for entry in self.entries
                            if entry[0] == username]
        if matching_entries:
            matching_entries[0][1] = pwhash
        else:
            self.entries.append([username, pwhash])
 
    def delete(self, username):
        """Remove the entry for the given user."""
        self.entries = [entry for entry in self.entries
                        if entry[0] != username]

    def _encrypt_password(self, password):
        """encrypt the password for given mode """
        if self.encryption_mode.lower() == 'crypt':
            return self._crypt_password(password)
        elif self.encryption_mode.lower() == 'md5':
            return self._md5_password(password)
        else:
            raise UnknownEncryptionMode(self.encryption_mode)

    def _crypt_password(self, password):
        """ Crypts password """
        def salt():
            """ Generates some salt """
            symbols = ascii_letters + digits
            return choice(symbols) + choice(symbols)
        
        return crypt.crypt(password, salt())

    def _md5_password(self, password):
        """ Crypts password using openssl binary and MD5 encryption """
        return subprocess.check_output(['openssl', 'passwd', '-apr1', password]).decode('utf-8').strip()
