#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
kafaka Syslog 客户端
'''

import time
import socket
import logging

class KSyslogClient(object):
    '''
    syslog client的封装
    '''
    def __init__(self, conf):
        '''
        初始化
        @conf: client的配置文件
        {
            'host':'127.0.0.1',
            'port':10068
            'fail_threshold': 3,
            'retry_timeout': 60,
        }
        return: None
        '''
        # 主机、端口
        self.host = conf['host']
        self.port = conf['port']

        # 失败阈值, 三次
        self.fail_threshold = conf['fail_threshold']

        # 重试时间, 一分钟
        self.retry_timeout = conf['retry_timeout']

        # 失败次数、时间
        self.fail_count = 0
        self.fail_time = 0

        # fd
        self.sock = None
        self.auto_connect()

    def auto_connect(self):
        '''
        自动重连
        '''
        try:
            if self.sock:
                self.sock.close()
                self.sock = None
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(1)
            self.sock.connect((self.host, self.port))
        except socket.error as e:
            logging.error('fail to connect %s:%s %s', self.host, self.port, str(e), exc_info=True)
            self.set_status(False)
        else:
            self.set_status(True)

    def publish(self, topic, msg):
        '''
        发布消息
        @topic: kafka topic
        @msg: 消息
        return: 是否成功 True or False
        '''
        # 检查是否可用
        if not self.check_status():
            return False

        is_succ = True
        try:
            self.sock.send('%s,%s\n' % (topic, msg))
        except socket.error as e:
            self.set_status(False)
            logging.error('fail to send kafka %s', str(e), exc_info=True)
            self.auto_connect()
            is_succ = False
        else:
            self.set_status(True)
        return is_succ

    def check_status(self):
        '''
        检查当前可用状态
        @return: 是否可用
        '''
        now = int(time.time())

        # 小于失败阈值 或 过了重试时间
        if self.fail_count <= self.fail_threshold or now > self.fail_time + self.retry_timeout:
            return True
        else:
            return False

    def set_status(self, is_succ=True):
        '''
       设置当前可用状态
        @is_succ: 是否成功
        @return: None
        '''
        now = int(time.time())

        # 本次成功, 则清空失败状态
        if is_succ:
            self.fail_count, self.fail_time = 0, 0
        else:
            self.fail_count += 1
            self.fail_time = now

