#coding=utf-8

import urllib,os,time
import simplejson as json

EXPIRE_BAN_USERS_TIME = 1800

KEY_BAN_USER_SET_PREFIX = 'KEY_BAN_USER_SET_PREFIX_'

if __name__ == '__main__':
    import os,sys
    G_PATH = os.path.split(os.path.realpath(__file__))[0]
    sys.path.append(G_PATH + '/../../')
    os.environ['DJANGO_SETTINGS_MODULE'] = 'MobileService.settings'

    from django.conf import settings
    
from MobileService.util.DbUtil import DbUtil

class BanUserUtil():
    def __init__(self, database):
        self.redis = database['cache_redis']
        self.user_db = database['user_db']
        self.mobile_db = database['mobile_db']
        self.info_logger = database['mobile_logger']
        self.environment = database['environment']

    def check_banner_user(self, app, phone):
        key = KEY_BAN_USER_SET_PREFIX + app
        if not self.redis.exists(key):
            handler = DbUtil(self.mobile_db, self.info_logger)
            user_phone_list = handler.get_user_ban_list(app)
            self.redis.sadd(key, 'null')
            for user_phone in user_phone_list:
                self.redis.sadd(key, user_phone)
            self.redis.expire(key, EXPIRE_BAN_USERS_TIME)
            
        if self.redis.sismember(key, phone):
            return False
        else:
            return True
            
    def clear_cache(self,app):
        key = KEY_BAN_USER_SET_PREFIX + app
        self.redis.delete(key)
        
