#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Session实现
'''

import uuid
import time
import hashlib
import logging
import datetime
import cPickle as pickle

class SessionManager(object):
    '''
    会话管理器
    '''
    def __init__(self, secret, backend):
        '''
        初始化会话管理器
        @secret: 会话Secret
        @backend: 后端存储
        return: None
        '''
        self.secret = secret
        self.backend = backend

    def save_session(self, session, expires=0):
        '''
        保存会话
        @session: 会话数据
        @expires: 失效时间
        return: None
        '''
        data = pickle.dumps(dict(session.items()))
        if len(data) >= 16000:
            logging.warning('hi, man, session(%s) data is too big:%d', session.sid, len(data))
        self.backend.set(session.sid, data, expires)

    def load_session(self, session_id=None):
        '''
        通过session_id加载会话, session_id为空, 生成新的Session
        @session_id: 会话iD
        return: 会话
        '''
        # 会话ID为空, 生成新的Session
        if not session_id:
            session_id = self.gen_session_id()
            return Session(session_id, self)

        # 从后端存储读取Session
        try:
            data = self.backend.get(session_id)
            data = pickle.loads(data) if data else {}
            assert isinstance(data, dict)
        except AssertionError, e:
            logging.error('session data wrong: %s, %s', data, str(e), exc_info=True)
            data = {}
        return Session(session_id, self, data)

    def gen_session_id(self):
        '''
        生成会话ID
        '''
        return hashlib.sha1('%s%s%s' % (uuid.uuid4(), time.time(), self.secret)).hexdigest()

class Session(dict):
    '''
    会话对象
    '''
    def __init__(self, session_id, mgr, data=None):
        '''
        初始化会话对象
        @session_id: 会话ID
        @mgr: 会话管理器
        @data: 会话数据
        return: None
        '''
        super(Session, self).__init__()
        self.sid = session_id
        self._mgr = mgr
        self.update(data or {})
        self._change = False

    def save(self, expires=0):
        '''
        保存会话数据
        @expires: 失效时间, 单位为秒
        return: None
        '''
        self._mgr.save_session(self, expires)

    def __missing__(self, key):
        '''
        Key不存在, 忽略...
        @key: 会话中的键值
        return: None
        '''
        return None

    def __delitem__(self, key):
        '''
        删除数据
        @key: 会话中的键值
        return: None
        '''
        if key in self:
            super(Session, self).__delitem__(key)

    def __setitem__(self, key, value):
        '''
        添加数据
        @key: 会话中的键值
        @value: 数据
        return: None
        '''
        super(Session, self).__setitem__(key, value)

    def set(self, key, value, expires=0):
        '''
        每次添加数据时, 都序列化到后端存储
        @key: 会话中的键值
        @value: 数据
        @expires: 失效时间
        return: None
        '''
        self[key] = value
        self.save(expires)

class TornadoSessionManager(SessionManager):
    '''
    针对tornado的会话管理器
    '''
    def __init__(self, secret, backend, cookie_name, domain=None):
        '''
        初始化会话管理器
        @secret: 会话Secret
        @backend: 后端存储
        @cookie_name: Cookie名称
        @domain: 域
        return: None
        '''
        super(TornadoSessionManager, self).__init__(secret, backend)
        self.cookie_name = cookie_name
        self.domain = domain
        self.request_handler = None

    def set_request_handler(self, request_handler):
        '''
        设置tornado的Request Handler
        @request_handler: tornado的请求处理Handler
        return: None
        '''
        self.request_handler = request_handler

    def load_session(self, session_id=None):
        '''
        加载会话
        @session_id: 会话iD
        return: 会话对象
        '''
        if self.request_handler:
            session_id = self.request_handler.get_cookie(self.cookie_name)
        return super(TornadoSessionManager, self).load_session(session_id)

    def save_session(self, session, expires=0):
        '''
        保存会话
        @session: 会话对象
        @expires: 失效时间, 秒
        return: None
        '''
        if self.request_handler:
            utc_now = datetime.datetime.utcnow()
            _expires = utc_now + datetime.timedelta(seconds=expires) if expires else None
            self.request_handler.set_cookie(self.cookie_name, session.sid, domain=self.domain,
                                            expires=_expires)
        super(TornadoSessionManager, self).save_session(session, expires)

