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

MAX_MONEY = 3000

class DbOrderCutoffUtil(DbUtil):
    def __init__(self, database, logger=None):
        DbUtil.__init__(self, database, logger)
            
    def make_percent(self, first_time = True):
        if first_time:
            percent = '100-1000|' + str(float('%0.2f'%(random.randint(500, 1000) *1.00/100))) + '||'
            percent += '1000-3000|' + str(float('%0.2f'%(random.randint(500, 800) *1.00/100)))
        else:
            percent = '100-1000|' + str(float('%0.2f'%(random.randint(200, 500) *1.00/100))) + '||'
            percent += '1000-3000|' + str(float('%0.2f'%(random.randint(200, 400) *1.00/100)))
            
        return percent
    
    def make_zero_percent(self):
        return '100-1000|0||1000-3000|0'
            
    def get_user_shop_cutoff(self, user_phone, shop_id):
        self.get_db_connect()
        sql = 'select percent from user_shop_cutoff where user_phone=%s and shop_id=%s'
        try:
            count = self.cursor.execute(sql, [user_phone, shop_id])
            if count > 0:
                result = self.cursor.fetchone()
                self.release_db_connect()
                return result[0]
                
            sql = 'select percent from user_shop_cutoff where user_phone=%s'
            count = self.cursor.execute(sql, [str(user_phone)])
            first_time = (count == 0)
            if count > 0:
                sql = 'select name from backend_user where name=%s and enable=1'
                count = self.cursor.execute(sql, [str(user_phone)])
                if count > 0:
                    first_time = 1
            percent = self.make_percent(first_time)
            
            sql = 'insert into user_shop_cutoff (user_phone,shop_id,percent) values (%s,%s,%s)'
            count = self.cursor.execute(sql, [user_phone, shop_id, percent])
            self.conn.commit()
            self.release_db_connect()
            return percent
        except Exception,e:
            if self.logger:
                self.logger.error('get_user_shop_cutoff except %s'%(e))
            self.release_db_connect()    
            return ''
    
    def update_user_shop_cutoff_zero(self, user_phone, shop_id):
        self.get_db_connect()
        try:
            percent = self.make_zero_percent()
            sql = 'update user_shop_cutoff set percent=%s where user_phone=%s and shop_id=%s'
            count = self.cursor.execute(sql, [percent, str(user_phone), str(shop_id)])
            self.conn.commit()
            self.release_db_connect()
            return True
        except Exception,e:
            if self.logger:
                self.logger.error('update_user_shop_cutoff except %s'%(e))
            self.release_db_connect()    
            return False
    
class OrderCutoffUtil():
    def __init__(self,database):
        self.mobile_db = database['mobile_db']
        self.shop_db = database['shop_db']
        self.user_db = database['user_db']
        self.info_logger = database['mobile_logger']
        self.redis = database['cache_redis']
        
    def get_user_shop_cutoff(self, user_phone, shop_id):
        handler = DbOrderCutoffUtil(self.mobile_db, self.info_logger)
        return handler.get_user_shop_cutoff(user_phone, shop_id)
    
    def get_user_shop_cutoff_money(self, user_phone, shop_id, money):
        handler = DbOrderCutoffUtil(self.mobile_db, self.info_logger)
        percent_info = handler.get_user_shop_cutoff(user_phone, shop_id)
        try:
            money = float(money)
        except:
            return -1
        if not percent_info:
            return money
        if money < 100:
            return money
        total_infos = percent_info.split('||')
        percent = 0
        for info in total_infos:
            scope_info = info.split('|')
            percent = scope_info[1]
            scopes = scope_info[0].split('-')
            if money >= float(scopes[0]) and money <= float(scopes[1]):
                self.info_logger.info('get_user_shop_cutoff_money %s'%(str(float('%0.2f'%(money * (1 - float(percent) / 100))))))
                return float('%0.2f'%(money * (1 - float(percent) / 100)))
        
        self.info_logger.info('get_user_shop_cutoff_money %s %s'%(str(float('%0.2f'%(MAX_MONEY * (1 - float(percent) / 100)))), float(money)))
        return float('%0.2f'%((float(money) - MAX_MONEY) + float('%0.2f'%(MAX_MONEY * (1 - float(percent) / 100)))))
        
    def update_user_shop_cutoff_zero(self, user_phone, shop_id):
        handler = DbOrderCutoffUtil(self.mobile_db, self.info_logger)
        return handler.update_user_shop_cutoff_zero(user_phone, shop_id)
    
if __name__ == '__main__':
    handler = OrderCutoffUtil(settings.COMMON_DATA)
    phone = 13100011100
    for i in range(1,201):
        money = random.randrange(100, 1000)
        phone = phone + 1
        #ran = handler.get_user_shop_cutoff_money(str(phone), i, money)
        ran = handler.get_user_shop_cutoff_money('13811678953', i, money)
        print money, money - ran
        time.sleep(1)
    #print handler.get_user_coupon_list('13811678953')
    #handler.sync_brand_hot_db(u'东鹏')
