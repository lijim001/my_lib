#coding=utf-8

import logging,time
import redis, os, sys
import ConfigParser

from MobileService.util.RedisBasic import *

delim = '|'

RECONNECT_TRY_TIMES = 3

'''
DOWNLOAD_KEY_NAME is a list saving weibo_id
'''

class StringRedis(MyBaseRedis):
    def __init__(self, config_file_name, config_section_name, logger= None):
        MyBaseRedis.__init__(self, config_file_name, config_section_name, logger)
    def save(self, key, value):
        return self.r.set(key, value)
    def get(self, key):
        return self.r.get(key)
    def cache(self, key, value, timeout):
        return self.r.set(key, value, timeout)
    def expire(self, key, value):
        return self.r.expire(key, value)
    def delete(self, key):
        return self.r.delete(key)
     
class RedisList(MyBaseRedis):
    def __init__(self, config_file_name, config_section_name, logger = None):
        MyBaseRedis.__init__(self, config_file_name, config_section_name, logger)
    
    def save_info(self, key, *items):
        for i in range(RECONNECT_TRY_TIMES):
            try:
                self.r.lpush(key, items)
                self.r.expire(key, 180)
            except Exception,e:
                print e
                self.re_connect()
            else:
                return
    
    def get_info(self, key, start, end):
        for i in range(RECONNECT_TRY_TIMES):
            try:
                s = self.r.lrange(key, start, end)
                print 'get cache'
                print s
                return s
            except Exception,e:
                print e
                self.re_connect()
        return None

class MyHashRedis(MyBaseRedis):
    def __init__(self, config_file_name, config_section_name, logger = None):
        self.logger = logger
        MyBaseRedis.__init__(self, config_file_name, config_section_name, logger)
        
    def get_item(self, key, field = None):
        for i in range(0, RECONNECT_TRY_TIMES):
            try:
                if field:
                    return self.r.hget(key, field)
                else:
                    return self.r.hgetall(key)
            except Exception,e:
                if self.logger:
                    self.logger.error('get item except %s'%(e))
                self.re_connect()
        return {}

    def get_item_fields(self, key, field_list):
        for i in range(0, RECONNECT_TRY_TIMES):
            try:
                return self.r.hmget(key, field_list)
            except Exception,e:
                if self.logger:
                    self.logger.error('get item field except %s'%(e))
                self.re_connect()
        return []
        
    def get_items(self, keys, field = None):
        for i in range(0, RECONNECT_TRY_TIMES):
            try:
                pipe = self.r.pipeline()
                for key in keys:
                    if field:
                        pipe.hget(key, field)
                    else:
                        pipe.hgetall(key)
                start = time.time()
                ret_data = pipe.execute()
                end = time.time()
                print end-start
                return ret_data
            except Exception,e:
                if self.logger:
                    self.logger.error('get items except %s'%(e))
                self.re_connect()
        return {}
        
    def set_item(self, key, field, value):
        for i in range(0, RECONNECT_TRY_TIMES):
            try:
                self.r.hset(key, field, value)
                return True
            except Exception,e:
                if self.logger:
                    self.logger.error('set item except %s'%(e))
                self.re_connect()        
        return False

    def set_items(self, key, item_dict):
        for i in range(0, RECONNECT_TRY_TIMES):
            try:
                self.r.hmset(key, item_dict)
                return True
            except Exception,e:
                if self.logger:
                    self.logger.error('set item except %s'%(e))
                self.re_connect()        
        return False
        
    def inc_item(self, key, field, value):
        for i in range(0, RECONNECT_TRY_TIMES):
            try:
                return self.r.hincrby(key, field, value)
            except Exception,e:
                if self.logger:
                    self.logger.error('inc item except %s'%(e))
                self.re_connect()        
        return 0        

class MyRedis(MyBaseRedis):
    def __init__(self, config_file_name, config_section_name, logger= None):
        MyBaseRedis.__init__(self, config_file_name, config_section_name, logger)
        
    def save(self, key, value):
        return self.r.set(key, value)
    def save_expire(self, key, value, timeout):
        return self.r.setex(key,timeout, value)
    def get(self, key):
        return self.r.get(key)
    def cache(self, key, value, timeout):
        return self.r.set(key, value, timeout)
    def expire(self, key, value):
        return self.r.expire(key, value)
    def delete(self, key):
        return self.r.delete(key)
    def exists(self, key):
        return self.r.exists(key)
    def incr(self, key, amount=1):
        return self.r.incr(key, amount)
    def keys(self, prefix):
        return self.r.keys(prefix)
    
    def sadd(self, key, value):
        return self.r.sadd(key, value)
        
    def sismember(self, set_name, key):
        return self.r.sismember(set_name, key)
  
    def delete_prefix(self, prefix):
        pipeline = self.r.pipeline()
        search_key = prefix + '*'
        match_keys = self.r.keys(search_key)
        for key in match_keys:
            self.delete(key)
        return pipeline.execute()

    def delete_prefixs(self, prefixs):
        pipeline = self.r.pipeline()
        for prefix in prefixs:
            search_key = prefix + '*'
            match_keys = self.r.keys(search_key)
            for key in match_keys:
                self.delete(key)
        return pipeline.execute()
        
    def save_list_info(self, key, expire, items):
        try:
            self.r.lpush(key, *items)
            self.r.expire(key, expire)
        except Exception,e:
            if self.logger != None:
                self.logger.error('save_list_info except %s'%(e))
            self.re_connect()
        else:
            return
    
    def get_list_info(self, key, start, end):
        for i in range(RECONNECT_TRY_TIMES):
            try:
                s = self.r.lrange(key, start, end)
                return s
            except Exception,e:
                if self.logger != None:
                    self.logger.error('get_list_info except %s'%(e))
                self.re_connect()
        return None
        
    def get_list_len(self, key):
        if not self.r.exists(key):
            return 0
        for i in range(0, RECONNECT_TRY_TIMES):
            try:
                return self.r.llen(key)
            except Exception,e:
                if self.logger:
                    self.logger.error('get_list_len except %s'%(e))
                self.re_connect()
        return 0

    def del_items(self, key, fields):
        for i in range(0, RECONNECT_TRY_TIMES):
            try:
                return self.r.hdel(key, fields)
            except Exception,e:
                if self.logger:
                    print e
                    self.logger.error('del item except %s'%(e))
                self.re_connect()
        return {}
        
    def get_item(self, key, field = None):
        for i in range(0, RECONNECT_TRY_TIMES):
            try:
                if field:
                    return self.r.hget(key, field)
                else:
                    return self.r.hgetall(key)
            except Exception,e:
                if self.logger:
                    self.logger.error('get item except %s'%(e))
                self.re_connect()
        return {}

    def get_item_fields(self, key, field_list):
        for i in range(0, RECONNECT_TRY_TIMES):
            try:
                return self.r.hmget(key, field_list)
            except Exception,e:
                if self.logger:
                    self.logger.error('get item field except %s'%(e))
                self.re_connect()
        return []
        
    def get_items(self, keys, field = None):
        for i in range(0, RECONNECT_TRY_TIMES):
            try:
                pipe = self.r.pipeline()
                for key in keys:
                    if field:
                        pipe.hget(key, field)
                    else:
                        pipe.hgetall(key)
                start = time.time()
                ret_data = pipe.execute()
                end = time.time()
                print end-start
                return ret_data
            except Exception,e:
                if self.logger:
                    self.logger.error('get items except %s'%(e))
                self.re_connect()
        return {}
        
    def set_item(self, key, field, value):
        for i in range(0, RECONNECT_TRY_TIMES):
            try:
                self.r.hset(key, field, value)
                return True
            except Exception,e:
                if self.logger:
                    self.logger.error('set item except %s'%(e))
                self.re_connect()        
        return False

    def set_items(self, key, item_dict):
        for i in range(0, RECONNECT_TRY_TIMES):
            try:
                self.r.hmset(key, item_dict)
                return True
            except Exception,e:
                if self.logger:
                    self.logger.error('set item except %s'%(e))
                self.re_connect()        
        return False
        
    def inc_item(self, key, field, value):
        for i in range(0, RECONNECT_TRY_TIMES):
            try:
                return self.r.hincrby(key, field, value)
            except Exception,e:
                if self.logger:
                    self.logger.error('inc item except %s'%(e))
                self.re_connect()        
        return 0
        
class MyMutliRedis(MyBaseMultiRedis):
    def __init__(self, config_file_name, config_section_name, logger= None):
        MyBaseMultiRedis.__init__(self, config_file_name, config_section_name, logger)

    def set_item(self, key, field, value):
        for r in self.rs:
            try:
                r.hset(key, field, value)
                if self.logger:
                    self.logger.info('MyMutliRedis set item ok')
            except Exception,e:
                if self.logger:
                    self.logger.error('MyMutliRedis set item except %s'%(e))
        return True
        
    def set_items(self, key, item_dict):
        for r in self.rs:
            print 'MyMutliRedis set_items'
            try:
                r.hmset(key, item_dict)
            except Exception,e:
                if self.logger:
                    self.logger.error('MyMutliRedis set items except %s'%(e))
        return True

    def save(self, key, value):
        for r in self.rs:
            r.set(key, value)
        return True

    def get(self, key):
        return self.rs[0].get(key)
        
    def delete(self, key):
        for r in self.rs:
            r.delete(key)
        return True
        
if __name__ == '__main__':
    redis = WeiboFriendRedisSet('SINA_WEIBO_F_S')
    redis.save_friend_info(00000000)
    # redis = WeiboUpdateRedis()
    # redis.save_weibo_info(1223)
