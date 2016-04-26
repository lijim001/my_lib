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

BASE_SQL_SYSTEM_COUPON = 'select id,title,percent,shop_id,days,sort,brand_name,min_money,max_cut_money from percent_coupon'

BASE_SQL_SYSTEM_GROUP_COUPON = 'select id,title,percent,shop_id,days,sort,brand_name,min_money,sum(max_cut_money) from percent_coupon'


BASE_SQL_USER_COUPON = 'select id,user_phone,percent,shop_id,end_time,create_time,sort,brand_name,min_money,max_cut_money,state,source from user_percent_coupon'

BASE_SQL_USER_GROUP_COUPON = 'select id,user_phone,percent,shop_id,end_time,create_time,sort,brand_name,min_money,sum(max_cut_money),state,source from user_percent_coupon'

class DbPercentCouponUtil(DbUtil):
    def __init__(self, database, logger=None):
        DbUtil.__init__(self, database, logger)
    
    def format_coupon(self, result):
        ret_dict = {}
        ret_dict['id'] = result[0]
        ret_dict['title'] = result[1]
        ret_dict['percent'] = float(result[2])
        ret_dict['shop_id'] = result[3]
        ret_dict['days'] = result[4]
        ret_dict['sort'] = result[5]
        ret_dict['brand_name'] = result[6]
        ret_dict['min_money'] = result[7]
        ret_dict['max_cut_money'] = result[8]
        if ret_dict['sort']:
            ret_dict['desc'] = u'仅适用于' + ret_dict['sort'] + u'类商品支付使用'
        return ret_dict
        
    def format_user_coupon(self, result):
        ret_dict = {}
        ret_dict['id'] = result[0]
        ret_dict['user_phone'] = result[1]
        ret_dict['percent'] = float(result[2])
        ret_dict['shop_id'] = result[3]
        ret_dict['end_time'] = int(time.mktime(result[4].timetuple()))
        ret_dict['create_time'] = int(time.mktime(result[5].timetuple()))
        ret_dict['sort'] = result[6]
        ret_dict['brand_name'] = result[7]
        ret_dict['min_money'] = result[8]
        ret_dict['max_cut_money'] = result[9]
        ret_dict['state'] = result[10]
        ret_dict['source'] = result[11]
        now = int(time.time())
        if ret_dict['sort']:
            ret_dict['desc'] = u'仅适用于' + ret_dict['sort'] + u'类商品支付使用'        
        ###timeout
        if now > ret_dict['end_time']:
            ret_dict['state'] = 2
        return ret_dict
        
    def get_system_coupon_sort_list(self, filter_sort=[]):
        self.get_db_connect()
        sql = 'select id,title,percent,shop_id,days,sort,brand_name,min_money,sum(max_cut_money) from percent_coupon where enable=1'
        ret_list = []
        if filter_sort:
            sql += ' and sort not in ("%s")'%('","'.join(filter_sort))
        sql += ' group by sort'
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                self.cursor.scroll(0, mode='absolute')
                results = self.cursor.fetchall()
                self.release_db_connect()
                for result in results:
                    ret_list.append(self.format_coupon(result))
            return ret_list
        except Exception, e:
            if self.logger:
                self.logger.error('get_system_coupon_sort_list except %s'%(e))
            self.release_db_connect()
            return []
            
    def get_system_coupon_in_sort_list(self, sort_list=[]):
        self.get_db_connect()
        sql = 'select id,title,percent,shop_id,days,sort,brand_name,min_money,sum(max_cut_money) from percent_coupon where enable=1'
        ret_list = []
        if not sort_list:
            return []
        else:
            sql += ' and sort in ("%s")'%('","'.join(sort_list))
            sql += ' group by sort'
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                self.cursor.scroll(0, mode='absolute')
                results = self.cursor.fetchall()
                self.release_db_connect()
                for result in results:
                    ret_list.append(self.format_coupon(result))
            return ret_list
        except Exception, e:
            if self.logger:
                self.logger.error('get_system_coupon_in_sort_list except %s'%(e))
            self.release_db_connect()
            return []
            
    def get_system_coupon_detail(self, id):
        self.get_db_connect()

        sql = BASE_SQL_SYSTEM_COUPON + ' where enable=1 and id=%s'
        try:
            count = self.cursor.execute(sql, [id])
            if count > 0:
                result = self.cursor.fetchone()
                return self.format_coupon(result)
            else:
                self.release_db_connect()
                return {}
        except Exception,e:
            if self.logger:
                self.logger.error('get_system_coupon_detail except %s'%(e))        
            self.release_db_connect()
            return {}
            
    def send_user_coupon(self, user_phone, coupon_info, source):
        if coupon_info['days']:
            end_time = str(date.today() + timedelta(days=coupon_info['days']))
        else:
            end_time = '0000-00-00 00:00:00'
        input_list = []
        input_list.append(str(user_phone))
        input_list.append(coupon_info['percent'])
        input_list.append(coupon_info['shop_id'])
        input_list.append(end_time)
        input_list.append(coupon_info['sort'])
        input_list.append(coupon_info['brand_name'])
        input_list.append(coupon_info['min_money'])
        input_list.append(coupon_info['max_cut_money'])
        input_list.append(source)
        
        self.get_db_connect()
        sql = 'insert into user_percent_coupon (user_phone,percent,shop_id,end_time,sort,brand_name,min_money,max_cut_money,source) values (%s,%s,%s,%s,%s,%s,%s,%s,%s)'
        try:
            count = self.cursor.execute(sql, input_list)
            self.conn.commit()
            self.release_db_connect()
            return True
        except Exception,e:
            if self.logger:
                self.logger.error('send_user_coupon except %s'%(e))
            self.release_db_connect()    
            return False
    
    def get_user_coupon_list(self, user_phone):
        self.get_db_connect()
        sql = 'select upc.id,upc.user_phone,upc.percent,upc.shop_id,upc.end_time,upc.create_time,upc.sort,upc.brand_name,upc.min_money,upc.max_cut_money,upc.state,upc.source,s.id from user_percent_coupon upc left join newshop.sort s on s.title=upc.sort and s.parentid=0 where upc.user_phone=%s and upc.enable=1 order by upc.id desc'
        ret_list = []

        try:
            count = self.cursor.execute(sql, [user_phone])
            if count > 0:
                self.cursor.scroll(0, mode='absolute')
                results = self.cursor.fetchall()
                self.release_db_connect()
                for result in results:
                    ret_dict = self.format_user_coupon(result)
                    ret_dict['sort_id'] = result[12] if result[12] else 0
                    ret_list.append(ret_dict)
            return ret_list
        except Exception, e:
            if self.logger:
                self.logger.error('get_user_coupon_list except %s'%(e))
            self.release_db_connect()
            return []

    def get_user_coupon_detail(self, id):
        self.get_db_connect()
        sql = BASE_SQL_USER_COUPON + ' where id=%s and enable=1'
        ret_list = []

        try:
            count = self.cursor.execute(sql, [id])
            if count > 0:
                result = self.cursor.fetchone()
                return self.format_user_coupon(result)
            return {}
        except Exception, e:
            if self.logger:
                self.logger.error('get_user_coupon_detail except %s'%(e))
            self.release_db_connect()
            return {}
            
    def get_user_can_use_coupon_list(self, user_phone, money):
        self.get_db_connect()
        now = str(datetime.now())
        sql = BASE_SQL_USER_COUPON + ' where user_phone=%s and enable=1 and min_money <= %s and end_time > %s order by max_cut_money desc'
        ret_list = []

        try:
            count = self.cursor.execute(sql, [user_phone, str(money), now])
            if count > 0:
                self.cursor.scroll(0, mode='absolute')
                results = self.cursor.fetchall()
                self.release_db_connect()
                for result in results:
                    ret_list.append(self.format_user_coupon(result))
            return ret_list
        except Exception, e:
            if self.logger:
                self.logger.error('get_user_can_use_coupon_list except %s'%(e))
            self.release_db_connect()
            return []
            
    def get_shop_coupon_info(self, shop_id):
        self.get_db_connect()
        sort_list = []
        brand_list = []
        sql = 'select sss.title,bd.title from newshop.shop_address_info sai inner join newshop.shopaddr_brand sb on sb.shopaddr_id=sai.id inner join newshop.brand bd on bd.id=sb.brand_id inner join newshop.brand_sort bs on bs.brand_id=bd.id inner join newshop.sort s on s.id=bs.sort_id inner join newshop.sort ss on ss.id=s.parentid inner join newshop.sort sss on sss.id=ss.parentid where sai.id=%s group by sss.title,bd.title'
        try:
            count = self.cursor.execute(sql, [shop_id])
            if count > 0:
                self.cursor.scroll(0, mode='absolute')
                results = self.cursor.fetchall()
                for result in results:
                    sort_list.append(result[0])
                    brand_list.append(result[1])
                    
                sort_list = list(set(sort_list))
                brand_list = list(set(brand_list))
                return sort_list, brand_list
            else:
                self.release_db_connect()
                return [],[]
        except Exception,e:
            if self.logger:
                self.logger.error('get_shop_coupon_info except %s'%(e))        
            self.release_db_connect()
            return [],[]
    
    def get_coupon_infos_by_source(self, source, group_sort = 0):
        self.get_db_connect()
        ret_list = []
        if group_sort:
            sql = BASE_SQL_USER_GROUP_COUPON + ' where source=%s group by sort order by id desc'
        else:
            sql = BASE_SQL_USER_COUPON + ' where source=%s order by id desc'
        
        try:
            count = self.cursor.execute(sql, [source])
            if count > 0:
                self.cursor.scroll(0, mode='absolute')
                results = self.cursor.fetchall()
                self.release_db_connect()
                for result in results:
                    ret_list.append(self.format_user_coupon(result))
            return ret_list
        except Exception, e:
            if self.logger:
                self.logger.error('get_coupon_infos_by_source except %s'%(e))
            self.release_db_connect()
            return []
            
    def get_coupon_infos_by_sort_list(self, sort_list, group_sort = 0):
        self.get_db_connect()
        if not sort_list:
            return []
        if group_sort:
            sql = BASE_SQL_SYSTEM_GROUP_COUPON + ' where enable=1 and sort in ("%s") group by sort order by id desc'%('","'.join(sort_list))
        else:
            sql = BASE_SQL_SYSTEM_COUPON + ' where enable=1 and sort in ("%s") order by id desc'%('","'.join(sort_list))
        ret_list = []
        
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                self.cursor.scroll(0, mode='absolute')
                results = self.cursor.fetchall()
                self.release_db_connect()
                for result in results:
                    ret_list.append(self.format_coupon(result))
            print ret_list
            return ret_list
        except Exception, e:
            if self.logger:
                self.logger.error('get_coupon_infos_by_sort_list except %s'%(e))
            self.release_db_connect()
            return []    
    
class PercentCouponUtil():
    def __init__(self,database):
        self.mobile_db = database['mobile_db']
        self.shop_db = database['shop_db']
        self.user_db = database['user_db']
        self.info_logger = database['mobile_logger']
        self.redis = database['cache_redis']
        
    def get_system_coupon_sort_list(self, filter_sort=[]):
        handler = DbPercentCouponUtil(self.mobile_db, self.info_logger)
        return handler.get_system_coupon_sort_list(filter_sort)
        
    def get_system_coupon_shop_list(self, shop_id, category):
        handler = DbPercentCouponUtil(self.mobile_db, self.info_logger)
        sort_list = []
        if shop_id:
            sort_list, brand_list = handler.get_shop_coupon_info(shop_id)
        if category:
            sort_list.append(category)
        return self.get_system_coupon_sort_list(sort_list)
        
    def get_system_coupon_detail(self, id):
        handler = DbPercentCouponUtil(self.mobile_db, self.info_logger)
        return handler.get_system_coupon_detail(id)
    
    def get_user_coupon_detail(self, id):
        handler = DbPercentCouponUtil(self.mobile_db, self.info_logger)
        return handler.get_user_coupon_detail(id)
    
    ###source : 1|service_phone, 2|self, 3|order_number, 4|sales_phone
    def send_user_coupon(self, user_phone, ids, source='2|self'):
        if not ids:
            return False
        ret = False
        for id in ids.split(','):
            coupon_info = self.get_system_coupon_detail(id)
            if not coupon_info:
                continue
            handler = DbPercentCouponUtil(self.mobile_db, self.info_logger)
            if handler.send_user_coupon(user_phone, coupon_info, source):
                ret = True
        return ret
    
    def get_user_coupon_list(self, user_phone):
        handler = DbPercentCouponUtil(self.mobile_db, self.info_logger)
        return handler.get_user_coupon_list(user_phone)
        
    def get_user_can_use_coupon_list(self, user_phone, shop_id, money):
        handler = DbPercentCouponUtil(self.mobile_db, self.info_logger)
        sort_list, brand_list = handler.get_shop_coupon_info(shop_id)
        coupon_list = handler.get_user_can_use_coupon_list(user_phone, money)
        finally_coupon_list = []
        print coupon_list
        for coupon_info in coupon_list:
            sort = coupon_info['sort']
            coupon_shop_id = coupon_info['shop_id']
            brand_name = coupon_info['brand_name']
            if sort and sort not in sort_list:
                print 'no use'
                continue
            if brand_name and brand_name not in brand_list:
                continue
            if coupon_shop_id and str(coupon_shop_id) != str(shop_id):
                continue
            finally_coupon_list.append(coupon_info)
        return finally_coupon_list
        
    def check_user_can_use_coupon(self, user_phone, coupon_id, shop_id, money):
        handler = DbPercentCouponUtil(self.mobile_db, self.info_logger)
        coupon_info = handler.get_user_coupon_detail(coupon_id)
        if not coupon_info:
            return False
            
        sort = coupon_info['sort']
        coupon_shop_id = coupon_info['shop_id']
        brand_name = coupon_info['brand_name']
        min_money = coupon_info['min_money']
        if money < min_money:
            return False
        if coupon_shop_id and str(coupon_shop_id) != str(shop_id):
            return False
        sort_list, brand_list = handler.get_shop_coupon_info(shop_id)
        if sort and sort not in sort_list:
            return False
        if brand_name and brand_name not in brand_list:
            return False

        return True
        
    def get_coupon_infos_by_order(self, order_number, group_sort = 0):
        handler = DbPercentCouponUtil(self.mobile_db, self.info_logger)
        return handler.get_coupon_infos_by_source('3|' + order_number, group_sort)
    
    def get_coupon_infos_by_sort_list(self, sort_list):
        handler = DbPercentCouponUtil(self.mobile_db, self.info_logger)    
        return handler.get_coupon_infos_by_sort_list(sort_list)
        
    def get_system_coupon_in_sort_list(self, sort_list=[]):
        handler = DbPercentCouponUtil(self.mobile_db, self.info_logger)    
        return handler.get_system_coupon_in_sort_list(sort_list)
        
if __name__ == '__main__':
    handler = PercentCouponUtil(settings.COMMON_DATA)
    #print handler.get_system_coupon_sort_list()
    #print handler.get_system_coupon_detail(1)
    print handler.send_user_coupon('15011133157', 2)
    print handler.send_user_coupon('15011133157', 3)
    #print handler.get_user_coupon_list('13811678953')
    print handler.get_user_can_use_coupon_list('13811678953', 314, 200)
    #handler.sync_brand_hot_db(u'东鹏')
