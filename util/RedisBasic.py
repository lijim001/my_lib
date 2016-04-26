#coding=utf-8

import logging
import redis, os, sys
import ConfigParser

ITEM_REDIS_HOST = 'rd_host'
ITEM_REDIS_HOSTS = 'rd_hosts'
ITEM_REDIS_PORT = 'rd_port'
ITEM_REDIS_DB = 'rd_database'

class MyBaseRedis():
    def __init__(self, config_file_name, config_section_name, logger = None):
        self.logger = logger
        self.create_redis_by_config(config_file_name,config_section_name)
    
    def create_redis_by_config(self, file_name, section_name):
        try:
            cf = ConfigParser.ConfigParser()
            cf.read(file_name)
            self.host = cf.get(section_name, ITEM_REDIS_HOST)
            self.port = cf.getint(section_name, ITEM_REDIS_PORT)
            self.db = cf.getint(section_name, ITEM_REDIS_DB)
            self.r = redis.Redis(host=self.host, port=self.port, db=self.db)
            if self.logger != None:
                self.logger.debug('MyBaseRedis create reids OK : %s %d %d'%(self.host, self.port, self.db))
        except Exception,e:
            print e
            if self.logger != None:
                self.logger.error('MyBaseRedis create basic redis except: %s'%(e))
            sys.exit(1)
            
    def re_connect(self):
        try:
            self.r = redis.Redis(host=self.host, port=self.port, db=self.db)
            self.logger.warning('MyBaseRedis re_connect OK')
        except Exception,e:
            if self.logger != None:
                self.logger.error('MyBaseRedis re_connect except: %s'%(e))

class MyBaseMultiRedis():
    def __init__(self, config_file_name, config_section_name, logger = None):
        self.logger = logger
        self.rs = []
        self.create_redis_by_config(config_file_name,config_section_name)
    
    def create_redis_by_config(self, file_name, section_name):
        try:
            cf = ConfigParser.ConfigParser()
            cf.read(file_name)
            self.hosts_list = cf.get(section_name, ITEM_REDIS_HOSTS).split('|')
            self.port = cf.getint(section_name, ITEM_REDIS_PORT)
            self.db = cf.getint(section_name, ITEM_REDIS_DB)
            for host in self.hosts_list:
                self.rs.append(redis.Redis(host=host, port=self.port, db=self.db))
                print 'create write redis %s'%(host)
            if self.logger != None:
                self.logger.debug('MyBaseRedis create reids OK : %s %d %d'%(str(self.hosts_list), self.port, self.db))
        except Exception,e:
            print e
            if self.logger != None:
                self.logger.error('MyBaseRedis create basic redis except: %s'%(e))
            sys.exit(1)
                        