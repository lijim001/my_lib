#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
队列处理封装
'''

import os
import time
import json
import socket
import logging
import hashlib
import amqp
from amqp.exceptions import AMQPError


class RedisQueue(object):
    '''
    redis队列处理器
    '''
    def __init__(self, redis, queue_key, queue_num):
        '''
        @redis: redis实例
        @queue_key: 队列的key
        @queue_num: 队列的个数
        '''
        self.redis = redis
        self.queue_key = queue_key
        self.queue_num = queue_num

    def handle(self, msg):
        '''
        队列业务处理器
        @msg: 队列中的数据
        '''
        raise Exception('not implemented: %s, msg=%s' % (self.queue_key, msg))

    def wait_queue(self, queue_id, timeout=2):
        '''
        @queue_id:队列的ID
        @timeout:超时时间
        '''
        while True:
            key = self.queue_key % queue_id
            msg = self.redis.lpop(key)
            if msg:
                try:
                    self.handle(msg)
                except Exception, e:
                    logging.error('error when process redis_key:%s, error:%s, msg:%s', key,
                                  str(e), msg, exc_info=True)
            else:
                time.sleep(timeout)

    def push_queue(self, partition_value, msg_data):
        '''
        消息入队
        @partition_value: 队列hash的值
        @msg_data: 消息
        return: 是否成功入队 True or False
        '''
        queue_id = int(hashlib.md5(partition_value).hexdigest()[0:2], 16) % self.queue_num
        if self.redis.rpush(self.queue_key % queue_id, json.dumps(msg_data)):
            return True
        return False

class RabbitQueue(object):
    '''
    rabbit队列处理器
    '''
    def __init__(self, rabbit_cnf):
        '''
        @rabbit_cnf: rabbit配置
        {
            'queue_key':'队列名',
            'exchange':'交换机名',
            'route_key':'路由key',
            'type':'交换机类型',
            'host':'rabbitmq主机',
            'port':'rabbitmq端口'
        }
        '''
        self.host = rabbit_cnf['host']
        self.queue_key = rabbit_cnf['queue_key']
        self.exchange = rabbit_cnf['exchange']
        self.type = rabbit_cnf['type']
        self.route_key = rabbit_cnf['route_key']
        conn = amqp.Connection(host=self.host)
        self.chan = conn.channel()
        self.chan.queue_declare(queue=self.queue_key, durable=True, exclusive=False, auto_delete=False)
        self.chan.exchange_declare(exchange=self.exchange, type=self.type, durable=True, auto_delete=False)
        self.chan.queue_bind(self.queue_key, exchange=self.exchange, routing_key=self.route_key)

    def handle(self, msg):
        '''
        队列业务处理器
        @msg: 队列中的数据
        '''
        raise Exception('not implemented: %s %s msg=%s' % (self.exchange, self.queue_key, msg))

    def wait_queue(self):
        '''
        @queue_key: 队列的名字
        '''
        try:
            self.chan.basic_consume(callback=self.handle, queue=self.queue_key, no_ack=True)
            while True:
                self.chan.wait()
        except socket.error as e:
            logging.error('读队列异常: %s', str(e), exc_info=True)

    def push_queue(self, msg_data):
        '''
        消息入队
        @msg_data: 消息
        return: 是否成功入队 True or False
        '''
        msg = amqp.Message(json.dumps(msg_data))
        msg.properties["delivery_mode"] = 2
        self.chan.basic_publish(msg, exchange=self.exchange, routing_key=self.route_key)


class RabbitQueue2(object):
    '''
    rabbit队列处理器, 逐渐过渡到该class
    '''
    def __init__(self, rabbit_cnf):
        '''
        @rabbit_cnf: rabbit配置
        {
            'host':'rabbitmq主机',
            'port':'rabbitmq端口'
            'userid':[可选, guest], '用户名',
            'password':[可选, guest], '密码',
            'virtual_host:'[可选, /], '虚拟主机',
            'insist':[可选, False], '...',
            'exchange': {
                '交换机名':{
                    'type':'交换机类型',
                    'durable':[可选, True], '持久化',
                    'auto_delete':[可选, False], '是否在没有客户端连上的时候, 自动删除',
                    'queue':{
                        '队列名': {
                            'exclusive':[可选, False], '是否私有',
                            'durable':[可选, True], '持久化',
                            'auto_delete':[可选, False], '是否在没有客户端连上的时候, 自动删除',
                            'routing_key_list':'路由key的列表'
                        }, ....
                    },
                }, ...
            }
        }
        '''
        # Rabbitmq配置
        self.cnf = rabbit_cnf
        self.conn = None
        self.chan = None
        self.reconnect()

    def reconnect(self):
        '''
        重连
        Notice: 如果连接长时间不活动, LVS会将连接关掉, 本地的socket变为:
                "can't identify protocol", 而调用chan.close 和 conn.close()
                也关不掉在 "泄露" 的 fileno
        '''
        # 关掉连接、channel
        self.close()

        # 创建连接、channel
        self.conn = amqp.Connection(host=self.cnf['host'],
                                    port=self.cnf['port'],
                                    userid=self.cnf.get('userid', 'guest'),
                                    password=self.cnf.get('password', 'guest'),
                                    virtual_host=self.cnf.get('virtual_host', '/'),
                                    insist=self.cnf.get('insist', False))
        self.chan = self.conn.channel()

        # 声明交换机
        for ex_name in self.cnf['exchange']:
            ex_cnf = self.cnf['exchange'][ex_name]
            self.chan.exchange_declare(exchange=ex_name,
                                       type=ex_cnf['type'],
                                       durable=ex_cnf.get('durable', True),
                                       auto_delete=ex_cnf.get('auto_delete', False))

            # 声明队列
            for queue_name in ex_cnf.get('queue', []):
                queue_cnf = ex_cnf['queue'][queue_name]
                self.chan.queue_declare(queue=queue_name,
                                        durable=queue_cnf.get('durable', True),
                                        exclusive=queue_cnf.get('exclusive', False),
                                        auto_delete=queue_cnf.get('auto_delete', False))

                # 绑定交换机、队列
                for routing_key in queue_cnf['routing_key_list']:
                    self.chan.queue_bind(queue_name,
                                         exchange=ex_name,
                                         routing_key=routing_key)

    def close(self):
        '''
        关闭connection、channel
        '''
        # 先取出当前连接的文件句柄
        if self.conn:
            fileno = self.conn.sock.fileno()
        else:
            fileno = -1

        # 关掉channel
        try:
            if self.chan:
                self.chan.close()
                self.chan = None
        except socket.error as e:
            logging.error('error when closing chan:%s', str(e), exc_info=True)

        # 关掉connection
        try:
            if self.conn:
                self.conn.close()
                self.conn = None
                fileno = -1
        except socket.error as e:
            logging.error('error when closing conn:%s', str(e), exc_info=True)

        # 关掉连接句柄
        try:
            if fileno >= 0:
                os.close(fileno)
        except OSError as e:
            logging.error('error when closing fileno:%s %s', fileno, str(e),
                          exc_info=True)

    def basic_consume(self, callback, queue_name, no_ack=True):
        '''
        消费...
        '''
        self.chan.basic_consume(callback=callback, queue=queue_name, no_ack=no_ack)

    def wait(self):
        '''
        等待处理消息
        '''
        try:
            while True:
                self.chan.wait()
        except (socket.error, AMQPError) as e:
            logging.error('读队列异常: %s', str(e), exc_info=True)
            self.close()

    def basic_publish(self, msg_data, exchange_name, routing_key):
        '''
        消息入队
        @msg_data: 消息
        return: 是否成功入队 True or False
        '''
        msg = amqp.Message(json.dumps(msg_data))
        msg.properties['delivery_mode'] = 2
        try:
            self.chan.basic_publish(msg, exchange=exchange_name, routing_key=routing_key)
        except (socket.error, AMQPError) as e:
            logging.error('fail to basic_publish:%s', str(e), exc_info=True)
            # 重连后, 再重试发送!
            self.reconnect()
            self.chan.basic_publish(msg, exchange=exchange_name, routing_key=routing_key)

