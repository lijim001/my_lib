#coding=utf-8

import urllib,os,time,random,uuid,hashlib

if __name__ == '__main__':
    import os,sys
    G_PATH = os.path.split(os.path.realpath(__file__))[0]
    sys.path.append(G_PATH + '/../../')
    os.environ['DJANGO_SETTINGS_MODULE'] = 'MobileService.settings'

from django.conf import settings    
from MobileService.util.DbUtil import *

MIN_CODE = 100001
MAX_CODE = 999998

class DbCouponUtil(DbUtil):
    def __init__(self, database, logger=None):
        DbUtil.__init__(self, database, logger)
        
    def get_max_activity_id(self):
        self.get_db_connect()
        sql = 'select max(left(code,3)) from gift_money'
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                result = self.cursor.fetchone()
                self.release_db_connect()
                return result[0]
            else:
                self.release_db_connect()
                return None
        except Exception, e:
            if self.logger:
                self.logger.error('get_max_activity_id except %s'%(e))
            self.release_db_connect()
            return None
    
    def get_max_suffix(self, prefix):
        self.get_db_connect()
        sql = 'select max(right(code, 6)) from gift_money where left(code,3)="%s"'%(str(prefix))
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                result = self.cursor.fetchone()
                self.release_db_connect()
                return result[0]
            else:
                self.release_db_connect()
                return None
        except Exception, e:
            if self.logger:
                self.logger.error('get_max_suffix except %s'%(e))
            self.release_db_connect()
            return None
            
    def create_gift_money(self, money, code, end_time=0):
        self.get_db_connect()
        sql = 'insert into gift_money (money, end_time, code) values (%s,%s,%s)'
        try:
            count = self.cursor.execute(sql, [money, end_time, code])
            new_id = self.cursor.lastrowid
            self.conn.commit()
            self.release_db_connect()
            return new_id
        except Exception,e:
            if self.logger:
                self.logger.error('create_gift_money except %s'%(e))
            self.release_db_connect()    
            return 0    
    
    def get_gift_money_info_by_code(self, code):
        self.get_db_connect()
        sql = 'select id, name, money, end_time from gift_money where code=%s'
        try:
            count = self.cursor.execute(sql, [code])
            if count > 0:
                result = self.cursor.fetchone()
                self.release_db_connect()
                return result
            else:
                self.release_db_connect()
                return None
        except Exception, e:
            if self.logger:
                self.logger.error('get_gift_money_info_by_code except %s'%(e))
            self.release_db_connect()
            return None

    def draw_gift_money(self, id, user_id, user_phone, money, operator = '', comment = ''):
        self.get_db_connect()
        try:
            sql = 'select name from gift_money where id=%s'
            count = self.cursor.execute(sql, [id])
            if count > 0:
                result = self.cursor.fetchone()
                if result[0]:
                    return False
            sql = 'update gift_money set name=%s,draw_time=%s,given=%s,operator=%s where id=%s'
            count1 = self.cursor.execute(sql, [str(user_phone), int(time.time()), 0 if not user_id else 1, operator, id])
            if comment:
                sql = 'update gift_money set comment=%s where id=%s'
                count2 = self.cursor.execute(sql, [comment, id])
            
            if user_id:
                sql = 'insert into user_score_info (user_id, money, type, state, comments) values (%s,%s,%s,%s,%s)'
                count = self.cursor.execute(sql, [user_id, money, 1, 1, comment])
                
                sql = 'insert into user_score (user_id, money) values (%s,%s) ON DUPLICATE KEY UPDATE money=money+%s'
                count = self.cursor.execute(sql, [user_id, money, money])
            self.conn.commit()
            if count1 == 0:
                self.conn.rollback()
                return False
            self.release_db_connect()
            return True
        except Exception,e:
            self.conn.rollback()
            if self.logger:
                self.logger.error('draw_gift_money except %s'%(e))
            self.release_db_connect()    
            return False 

    def give_user_draw_gift_money(self, user_id, user_phone):
        self.get_db_connect()
        try:
            sql = 'select money from gift_money where name=%s and given=0'
            count = self.cursor.execute(sql, [user_phone])
            handle_money = 0
            if count == 0:
                return False
                
            self.cursor.scroll(0, mode='absolute')
            results = self.cursor.fetchall()

            sql = 'update gift_money set given=1 where name=%s'
            count = self.cursor.execute(sql, [user_phone])
            for result in results:
                money = result[0]
                sql = 'insert into user_score_info (user_id, money, type, state) values (%s,%s,%s,%s)'
                count = self.cursor.execute(sql, [user_id, money, 1, 1])
                
                sql = 'insert into user_score (user_id, money) values (%s,%s) ON DUPLICATE KEY UPDATE money=money+%s'
                count = self.cursor.execute(sql, [user_id, money, money])
            self.conn.commit()
            self.release_db_connect()
            return True
        except Exception,e:
            self.conn.rollback()
            if self.logger:
                self.logger.error('give_user_draw_gift_money except %s'%(e))
            self.release_db_connect()    
            return False
            
class CouponUtil():
    def __init__(self,database):
        self.mobile_db = database['mobile_db']
        self.shop_db = database['shop_db']
        self.user_db = database['user_db']
        self.info_logger = database['mobile_logger']
            
    def check_coupon_enough_money(self, user_id, coupon):
        handler = DbUtil(self.mobile_db, self.info_logger)
        money = handler.get_user_available_score_money(user_id)
        if coupon <= money:
            return True
        else:
            return False
            
    def get_max_activity_id(self):
        handler = DbCouponUtil(self.mobile_db, self.info_logger)
        str_max_id = ''
        max_activity_id = handler.get_max_activity_id()
        if not max_activity_id:
            max_activity_id = 0
        else:
            max_activity_id = int(max_activity_id)
        max_activity_id += 1
        
        if max_activity_id < 10:
            str_max_id = '00' + str(max_activity_id)
        elif max_activity_id < 100:
            str_max_id = '0' + str(max_activity_id)
        else:
            str_max_id = str(max_activity_id)
        return str_max_id
            
    def create_activity_gift_money(self, money, count, end_time=0):
        handler = DbCouponUtil(self.mobile_db, self.info_logger)
        current_id = self.get_max_activity_id()
        suffix_values_list = random.sample(range(MIN_CODE, MAX_CODE), count)
        for suffix in suffix_values_list:
            code = str(current_id) + str(suffix)
            if handler.create_gift_money(money, code, end_time):
                self.info_logger.info('create_activity_gift_money ok %s'%(str(code)))
            else:
                self.info_logger.info('create_activity_gift_money failed %s'%(str(code)))
        return True
    
    def can_draw_gift_money(self, code):
        handler = DbCouponUtil(self.mobile_db, self.info_logger)
        money_info = handler.get_gift_money_info_by_code(code)
        if not money_info:
            return None
        name = money_info[1]
        end_time = money_info[3]
        if name:
            return None
        if end_time and int(time.time()) > end_time:
            return None
            
        return money_info
    
    def get_user_id(self, user_phone):
        handler = DbCouponUtil(self.user_db, self.info_logger)
        user_info = handler.get_userinfo_by_user_name(user_phone)
        if user_info:
            return user_info[0]
        else:
            return None
        
    def draw_gift_money(self, user_phone, code, operator = '', comment = ''):
        handler = DbCouponUtil(self.mobile_db, self.info_logger)
        money_info = self.can_draw_gift_money(code)
        if not money_info:
            print '111111'
            return 0
        print code
        user_id = self.get_user_id(user_phone)
        id = money_info[0]
        name = money_info[1]
        money = money_info[2]
        print id,name,money
        if handler.draw_gift_money(id, user_id, user_phone, money, operator, comment):
            self.info_logger.info('draw_gift_money %s %s user_id: %s ok'%(str(user_phone), str(code), str(user_id)))
            return money
        else:
            return 0
        
    def give_user_draw_gift_money(self, user_id, user_phone):
        handler = DbCouponUtil(self.mobile_db, self.info_logger)
        return handler.give_user_draw_gift_money(user_id, user_phone)
    
    def fill_suffix(self, suffix):
        suffix_len = len(suffix)
        need_add_zero = 6 - suffix_len
        if need_add_zero <= 0:
            return suffix
        add_prefix = ''
        for i in range(0, need_add_zero):
            add_prefix += '0'
            
        return add_prefix + str(suffix)
        
    def give_user_gift_money_directly(self, user_phone, money, creator, comment = ''):
        handler = DbCouponUtil(self.mobile_db, self.info_logger)
        prefix = '000'
        suffix = handler.get_max_suffix(prefix)
        if not suffix:
            suffix = 0
        suffix = str(int(suffix) + 1)
        suffix = self.fill_suffix(suffix)
        code = prefix + str(suffix)
        id = handler.create_gift_money(money, code, 0)
        if not id:
            self.info_logger.error('give_user_gift_money_directly failed %s %s'%(str(user_phone), str(money)))
        else:
            if self.draw_gift_money(user_phone, code, creator, comment):
                self.info_logger.info('give_user_gift_money_directly ok %s %s'%(str(user_phone), str(money)))
            else:
                self.info_logger.error('give_user_gift_money_directly draw failed %s %s'%(str(user_phone), str(money)))
                
        return True
    
if __name__ == '__main__':
    handler = CouponUtil(settings.COMMON_DATA)
    #handler.create_activity_gift_money(200, 10)
    handler.give_user_gift_money_directly('12411678953', 200, u'吴振宇', u'测试')
    
