#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
pylibmc封装
'''
import time
import logging
import pylibmc


class MClient(object):
    '''
    memcache client的封装
    '''
    min_cycle, max_cycle, total_time, counter, succ, fail, ext = 0xffffL, 0L, 0L, 0L, 0L, 0L, ''

    def __init__(self, servers, binary=True):
        '''
        初始化
        @servers: MC服务列表
        @binary: 是否二进制协议
        return: None
        '''
        self.servers = servers
        self.binary = binary
        self.behaviors = {
            'tcp_nodelay':True,
            'ketama':True,
            'remove_failed':2,
            'retry_timeout':30
        }
        self.__mc = None
        self.reconnect()

    def reconnect(self):
        '''
        重连
        '''
        if self.__mc:
            try:
                self.__mc.disconnect_all()
            except pylibmc.Error:
                pass
            self.__mc = None
        self.__mc = pylibmc.Client(self.servers, binary=self.binary, behaviors=self.behaviors)
        logging.warn('==>reconnect: %s', self.servers)

    def __getattr__(self, attr):
        '''
        代理其他属性
        @attr: 属性名
        '''
        return getattr(self.__mc, attr)

    def __del__(self):
        '''
        对象删除时, 关闭连接
        '''
        self.__mc.disconnect_all()

    def __repr__(self):
        '''
        重载显示
        '''
        return '<MCStore(server=%s)>' % repr(self.servers)

    def __str__(self):
        '''
        字符串表示
        '''
        return self.servers

    def set(self, key, data, expire=0):
        '''
        set操作
        @key: 键值
        @data: 存储的数据
        @expire: 失效时间, 秒
        return: 是否成功
        '''
        start = time.time()
        r = bool(self.__mc.set(key, data, expire))
        self.update_stat((time.time()-start)*1000, key, cmd='set')
        return r

    def _failover(self, key_list):
        '''
        有一个memcached服务挂了, 促进pylibmc摘掉相关Node
        pylibmc只对更新操作进行失败检测并摘掉Node, 但是: 不能自动重连!fk!
        这样也有问题: 如果只是连接断了, 会造成数据的不一致!
        @key_list: 当前的Key列表
        return: None
        '''
        try:
            for i in key_list:
                self.__mc.delete(i)
        except pylibmc.Error as e:
            logging.error('failover:%s', str(e), exc_info=True)

    def get(self, key):
        '''
        get操作
        @key: 键值
        return: 存储的数据
        '''
        start = time.time()
        try:
            r = self.__mc.get(key)
        except pylibmc.Error as e:
            logging.error('fail to get:%s, %s', key, str(e), exc_info=True)
            self.reconnect()
            r = self.__mc.get(key)
        self.update_stat((time.time()-start)*1000, key, cmd='get')
        return r

    def get_multi(self, keys, prefix=''):
        '''
        批量获取
        @keys: 键值列表
        @prefix: 键值的前缀, 这样可以方便的处理得到的数据
        return: 数据字典 key=>value
        '''
        start = time.time()
        try:
            r = self.__mc.get_multi(keys, prefix)
        except pylibmc.Error as e:
            logging.error('fail to get_multi:%s, %s', keys, str(e), exc_info=True)
            self.reconnect()
            r = self.__mc.get_multi(keys, prefix)
        self.update_stat((time.time()-start)*1000, keys, prefix=prefix, cmd='get_multi')
        return r

    def delete(self, key):
        '''
        删除操作
        @key: 键值
        return: 是否成功
        '''
        start = time.time()
        r = bool(self.__mc.delete(key))
        self.update_stat((time.time()-start)*1000, key, cmd='delete')
        return r

    def mutex(self, key, expire=5, value=''):
        '''
        加锁
        @key: 加锁的Key
        @expire: 失效时间
        return: 是否成功
        '''
        return self.__mc.add(key, value, expire)

    def unmutex(self, key):
        '''
        解锁
        @key: 加锁的Key
        return: 是否删除成功
        '''
        return self.__mc.delete(key)

    @classmethod
    def reset_stat(cls):
        '''
        重置统计数据
        return: None
        '''
        cls.min_cycle, cls.max_cycle, cls.total_time = 0xffffL, 0L, 0L
        cls.counter, cls.succ, cls.fail, cls.ext = 0L, 0L, 0L, ''

    @classmethod
    def stat(cls):
        '''
        查看统计数据
        return: MC操作的统计信息
        '''
        return {
            'min_cycle':cls.min_cycle,
            'max_cycle':cls.max_cycle,
            'total_time':cls.total_time,
            'counter':cls.counter,
            'succ':cls.succ,
            'fail':cls.fail,
            'ext':cls.ext
        }

    def update_stat(self, spent_time, keys, prefix='', server='', cmd='get'):
        '''
        更新统计数据
        @spent_time: 花费时间
        @keys: 操作的键值
        @prefix: 键值的前缀
        @server: 服务器
        @cmd: 执行的命令
        return: None
        '''
        self.__class__.min_cycle = min(self.min_cycle, spent_time)
        if spent_time > self.__class__.max_cycle:
            self.__class__.max_cycle = spent_time
            self.__class__.ext = '%s:(%s)%s+%s' % (cmd, str(server), prefix, str(keys))
        self.__class__.total_time += spent_time
        self.__class__.counter += 1
        self.__class__.succ += 1

