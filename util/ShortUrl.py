#coding=utf-8

import urllib,os,time,sys
import urllib2,cookielib,httplib
import simplejson as json

if __name__ == '__main__':
    G_PATH = os.path.split(os.path.realpath(__file__))[0]
    sys.path.append(G_PATH + '/../../')
    os.environ['DJANGO_SETTINGS_MODULE'] = 'MobileService.settings'
    from django.conf import settings
    
class DbShortUrlUtil(DbUtil):
    def __init__(self, database, logger=None):
        DbUtil.__init__(self, database, logger)
        

class ShortUrlUtil():
    def __init__(self, database):
        self.info_logger = database['mobile_logger']
        self.gearman_config = database['gearman_config']
        self.redis = database['cache_redis']
        self.mobile_db = database['mobile_db']
        self.database = database
        
    def get_token(self):
        pass
        
    
if __name__ == '__main__':
    print get_short_url('http://static.mobile.xinwo.com/image/purchase_sort/purchase_men.png')
        