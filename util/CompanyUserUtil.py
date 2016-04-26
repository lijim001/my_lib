#coding=utf-8

import urllib,os,time
import simplejson as json

KEY_COMPANY_USERS = 'KEY_COMPANY_USERS_XINWO'
EXPIRE_COMPANY_USERS_TIME = 3600

if __name__ == '__main__':
    import os,sys
    G_PATH = os.path.split(os.path.realpath(__file__))[0]
    sys.path.append(G_PATH + '/../../')
    os.environ['DJANGO_SETTINGS_MODULE'] = 'MobileService.settings'

    from django.conf import settings
    
from MobileService.util.DbUtil import DbUtil

class CompanyUserUtil():
    def __init__(self, database):
        self.redis = database['cache_redis']
        self.user_db = database['user_db']
        self.mobile_db = database['mobile_db']
        self.info_logger = database['mobile_logger']
        self.environment = database['environment']

    def get_company_user_list(self):
        key = KEY_COMPANY_USERS
        redis_data = self.redis.get(key)
        if redis_data:
            return json.loads(redis_data)
        handler = DbUtil(self.mobile_db, self.info_logger)
        ret_list = handler.get_company_user_list()
        if not ret_list:
            return []
        new_ret_list = []
        for phone in ret_list:
            new_ret_list.append(phone[0])
        cache_data = json.dumps(new_ret_list)
        self.redis.save_expire(key, EXPIRE_COMPANY_USERS_TIME, cache_data)
        return new_ret_list