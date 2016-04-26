#coding=utf-8

import urllib,os,time,random,uuid,hashlib
from datetime import datetime,date,timedelta
if __name__ == '__main__':
    import os,sys
    G_PATH = os.path.split(os.path.realpath(__file__))[0]
    sys.path.append(G_PATH + '/../../')
    os.environ['DJANGO_SETTINGS_MODULE'] = 'MobileService.settings'

from django.conf import settings    
from MobileService.util.DbUtil import *

KEY_BRAND_HOT_PREFIX = 'BRAND_HOT_'

class DbBrandHotUtil(DbUtil):
    def __init__(self, database, logger=None):
        DbUtil.__init__(self, database, logger)
        
    def get_brand_hot(self, brand_name, start_time, end_time):
        self.get_db_connect()
        sql = 'select sum(hot) from brand_hot_list where brand_name=%s and hot_date >= %s and hot_date < %s'
        try:
            count = self.cursor.execute(sql, [brand_name, start_time, end_time])
            if count > 0:
                result = self.cursor.fetchone()
                self.release_db_connect()
                if not result[0]:
                    return 0
                return result[0]
            else:
                self.release_db_connect()
                return 0
        except Exception, e:
            if self.logger:
                self.logger.error('get_brand_hot except %s'%(e))
            self.release_db_connect()
            return 0
            
    def update_brand_hot(self, brand_name, hot):
        self.get_db_connect()
        if hot is None:
            return False
        sql = 'update brand set hot_current=%s where title=%s'
        try:
            count = self.cursor.execute(sql, [hot,brand_name])
            self.conn.commit()
            self.release_db_connect()
            return True
        except Exception, e:
            if self.logger:
                self.logger.error('update_brand_hot except %s'%(e))
            self.release_db_connect()
            return False
            
    def sync_brand_hot(self, brand_name, record_time, hot):
        self.get_db_connect()
        sql = 'insert into brand_hot_list (brand_name, hot_date, hot) values (%s,%s,%s) on duplicate key update hot=hot+%s'
        try:
            count = self.cursor.execute(sql, [brand_name, record_time, hot, hot])
            self.conn.commit()
            self.release_db_connect()
            return True
        except Exception,e:
            if self.logger:
                self.logger.error('sync_brand_hot except %s'%(e))
            self.release_db_connect()    
            return False
    
    def get_cooperation_brands_name(self):
        self.get_db_connect()

        sql = 'select bd.title from brand bd inner join shopaddr_brand sb on sb.brand_id=bd.id inner join shop_address_info sai on sai.id=sb.shopaddr_id inner join channels cs on cs.id=sai.channel_id where bd.status=1 and sai.status=1 and cs.type!=3 group by bd.id order by CONVERT(bd.title USING gbk)'
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                self.cursor.scroll(0, mode='absolute')
                results = self.cursor.fetchall()
                ret_list = []
                create_time = 0
                for result in results:
                    ret_list.append(result[0])
                self.release_db_connect()
                return ret_list
            else:
                self.release_db_connect()
                return []
        except Exception,e:
            if self.logger:
                self.logger.error('get_cooperation_brands_name except %s'%(e))        
            self.release_db_connect()
            return []
            
class BrandHotUtil():
    def __init__(self,database):
        self.mobile_db = database['mobile_db']
        self.shop_db = database['shop_db']
        self.user_db = database['user_db']
        self.info_logger = database['mobile_logger']
        self.redis = database['cache_redis']
        
    def get_time_key(self):
        #return str(date.today() - timedelta(days=1))
        return str(date.today())
        
    def increase_brand_hot(self, brand_name, hot):
        if not brand_name:
            self.info_logger.info('no brand_name')
            return False
        for brand in brand_name.split(','):
            key_time = self.get_time_key()
            key = KEY_BRAND_HOT_PREFIX + brand
            self.redis.inc_item(key, key_time, hot)
            #self.info_logger.info('increase_brand_hot %s %s'%(brand.encode('utf8','ignore'), str(hot)))
        
    def is_today(self, record_time):
        try:
            print 'is today start'
            print str(date.today())
            print record_time
            if str(date.today()) == record_time:
                return True
            else:
                return False
        except Exception,e:
            print e
            return False
        
    def sync_brand_hot_db(self, brand_name):
        handler = DbBrandHotUtil(self.shop_db, self.info_logger)
        key = KEY_BRAND_HOT_PREFIX + brand_name
        ret_data = self.redis.get_item(key)
        if not ret_data:
            return False
        for record_time, hot in ret_data.items():
            print ret_data
            if self.is_today(record_time):
                continue
            handler.sync_brand_hot(brand_name, record_time, hot)
            self.redis.del_items(key, record_time)
    
    def get_compute_scope(self):
        return (str(date.today() - timedelta(days=7)), str(date.today()))

    def compute_brand_hot(self, brand_name):
        start_time, end_time = self.get_compute_scope()
        handler = DbBrandHotUtil(self.shop_db, self.info_logger)
        hot = handler.get_brand_hot(brand_name, start_time, end_time)
        print handler.update_brand_hot(brand_name,hot)
        
    def do(self):
        handler = DbBrandHotUtil(self.shop_db, self.info_logger)
        brand_list = handler.get_cooperation_brands_name()
        for brand_name in brand_list:
            self.sync_brand_hot_db(brand_name)
            self.compute_brand_hot(brand_name)
    
    
if __name__ == '__main__':
    handler = BrandHotUtil(settings.COMMON_DATA)
    #handler.increase_brand_hot(u'东鹏', 200)
    #handler.sync_brand_hot_db(u'东鹏')
    if len(sys.argv) == 2 and sys.argv[1] == 'routine':
        handler.do()