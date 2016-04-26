#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
签名逻辑
'''
import hashlib


class Signer(object):
    '''
    签名基类
    '''
    @staticmethod
    def factory(sign_type, secret_cnf):
        '''
        根据类型创建不同的处理类
        '''
        if sign_type == 'MD5':
            return MD5Signer(secret_cnf['MD5'])
        elif sign_type == 'RSA':
            return RSASigner(secret_cnf['RSA'])
        else:
            raise Exception('oh no!')


class MD5Signer(object):
    '''
    签名基类
    '''
    def __init__(self, secret):
        '''
        初始化
        '''
        self.secret = secret

    def verify(self, data):
        '''
        验证签名
        @data: 待验签的数据, 字典形式
        return: True or False
        '''
        str_data = '&'.join(['%s=%s' % (k, v) for k, v in sorted(data.items()) if k != 'sign' and v != ''])
        return hashlib.md5(str_data + '&secret=%s' % self.secret).hexdigest() == data['sign']


class RSASigner(object):
    '''
    签名基类
    '''
    def __init__(self, secret):
        '''
        初始化
        '''
        self.secret = secret

    def verify(self, data):
        '''
        验证签名
        @data: 待验签的数据, 字典形式
        return: True or False
        '''
        pass

