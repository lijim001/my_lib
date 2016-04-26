#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
pyssdb
~~~~~~~

A SSDB Client Library for Python.

:copyright: (c) 2013 by Yue Du.
:license: BSD 2-clause License, see LICENSE for more details.
'''

__version__ = '0.1.0'
__author__ = 'Yue Du <ifduyue@gmail.com>'
__url__ = 'https://github.com/ifduyue/pyssdb'
__license__ = 'BSD 2-Clause License'

import os
import socket
import string
import logging
import functools
import itertools


class Error(Exception):
    '''
    ssdb处理错误
    '''
    def __init__(self, reason, *args):
        '''
        初始化错误信息
        '''
        super(Error, self).__init__(reason, *args)
        self.reason = reason
        self.message = ' '.join(args)


class Connection(object):
    '''
    到ssdb的连接
    '''
    def __init__(self, host='127.0.0.1', port=8888, socket_timeout=None):
        '''
        @host: 主机名
        @port: 端口
        @socket_timeout: 超时时间
        '''
        self.pid = os.getpid()
        self.host = host
        self.port = port
        self.socket_timeout = socket_timeout
        self._sock = None
        self._fp = None
        self.last_cmd = None

    def connect(self):
        '''
        连接
        '''
        if self._sock:
            return
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.socket_timeout)
            sock.connect((self.host, self.port))
            self._sock = sock
            self._fp = sock.makefile('r')
        except socket.error:
            raise

    def disconnect(self):
        '''
        断开连接
        '''
        if self._sock is None:
            return
        try:
            self._sock.close()
        except socket.error:
            pass
        self._sock = self._fp = None

    def reconnect(self):
        '''
        重连
        '''
        self.disconnect()
        self.connect()

    def send(self, cmd, *args):
        '''
        @cmd: ssdb命令
        @args: 扩展参数
        '''
        if cmd == 'delete':
            cmd = 'del'
        self.last_cmd = cmd
        if self._sock is None:
            self.connect()
        args = (cmd, ) + args
        if isinstance(args[-1], int):
            args = args[:-1] + (str(args[-1]), )
        buf = ''.join(['%d\n%s\n' % (len(str(e)), e) for e in args]) + '\n'
        try:
            self._sock.sendall(buf)
        except socket.error:
            logging.error('fail to send %s, try to reconnect', buf)
            self.reconnect()
            # retry one time
            self._sock.sendall(buf)

    def recv(self):
        '''
        接收响应并解析结果
        '''
        cmd = self.last_cmd
        ret = []
        while True:
            line = self._fp.readline().rstrip('\n')
            if not line:
                break
            data = self._fp.read(int(line))
            self._fp.read(1) # discard '\n'
            ret.append(data)

        status, body = ret[0], ret[1:]

        if status == 'not_found':
            return None
        elif status == 'ok':
            if cmd.endswith('keys') or cmd.endswith('list') or \
                    cmd.endswith('scan') or cmd.endswith('range') or \
                    (cmd.startswith('multi_') and cmd.endswith('get')):
                return body
            elif len(body) == 1:
                if cmd.endswith('set') or cmd.endswith('del') or \
                        cmd.endswith('incr') or cmd.endswith('decr') or \
                        cmd.endswith('size') or cmd.endswith('rank') or \
                        cmd == 'setx':
                    return int(body[0])
                else:
                    return body[0]
            elif not body:
                return True

        raise Error(*ret)


class ConnectionPool(object):
    '''
    连接池
    '''
    def __init__(self, connection_class=Connection, max_connections=1048576, **connection_kwargs):
        '''
        @connection_class: 连接的实现类
        @max_connections: 允许的最大连接数
        @connection_kwargs: 连接的扩展参数
        '''
        self.pid = os.getpid()
        self.connection_class = connection_class
        self.connection_kwargs = connection_kwargs
        self.max_connections = max_connections
        self.idle_connections = []
        self.active_connections = set()

    def checkpid(self):
        '''
        检查是否是当前进程, 如果不是, 则断开重连
        '''
        if self.pid != os.getpid():
            self.disconnect()
            self.__init__(self.connection_class, self.max_connections, **self.connection_kwargs)

    def get_connection(self):
        '''
        从池中取得一个连接, 加入到active连接池中
        '''
        self.checkpid()
        try:
            connection = self.idle_connections.pop()
        except IndexError:
            connection = self.new_connection()
        self.active_connections.add(connection)
        return connection

    def new_connection(self):
        '''
        创建一个新连接
        '''
        if len(self.active_connections) + len(self.idle_connections) > self.max_connections:
            raise Error("Too many connections")
        return self.connection_class(**self.connection_kwargs)

    def release(self, connection):
        '''
        归还一个连接
        '''
        self.checkpid()
        if connection.pid == self.pid:
            self.active_connections.remove(connection)
            self.idle_connections.append(connection)

    def disconnect(self):
        '''
        断开连接池中的所有连接
        '''
        active_connections, self.active_connections = self.active_connections, set()
        idle_connections, self.idle_connections = self.idle_connections, []
        for connection in itertools.chain(active_connections, idle_connections):
            connection.disconnect()


class SSDBClient(object):
    '''
    ssdb 客户端
    '''
    def __init__(self, host='127.0.0.1', port=8888, connection_pool=None, socket_timeout=None,
                 max_connections=1048576):
        '''
        初始化连接池
        '''
        if not connection_pool:
            connection_pool = ConnectionPool(host=host, port=port, socket_timeout=socket_timeout,
                                             max_connections=max_connections)
        self.connection_pool = connection_pool
        connection = self.connection_pool.new_connection()
        connection.connect()
        self.connection_pool.idle_connections.append(connection)

    def execute_command(self, cmd, *args):
        '''
        执行命令
        '''
        connection = self.connection_pool.get_connection()
        try:
            connection.send(cmd, *args)
            return connection.recv()
        finally:
            self.connection_pool.release(connection)

    def disconnect(self):
        '''
        断开到ssdb的连接
        '''
        self.connection_pool.disconnect()

    def __getattr__(self, cmd):
        '''
        属性代理
        '''
        if cmd in self.__dict__:
            return self.__dict__[cmd]
        elif cmd in self.__class__.__dict__:
            return self.__class__.__dict__[cmd]
        ret = self.__dict__[cmd] = functools.partial(self.execute_command, cmd)
        return ret


if __name__ == '__main__':
    SSDB = SSDBClient('127.0.0.1', 8999)
    print SSDB.set('key', 'value')
    print SSDB.get('key')
    for i in string.ascii_letters:
        SSDB.incr(i)
    print SSDB.keys('a', 'z', 1)
    print SSDB.keys('a', 'z', 10)
    print SSDB.get('z')
    print SSDB.get('a')
    SSDB.disconnect()

