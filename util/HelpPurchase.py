#coding=utf-8

import urllib,os,time,sys,copy
import pymongo,MySQLdb
from datetime import datetime

if __name__ == '__main__':
    G_PATH = os.path.split(os.path.realpath(__file__))[0]
    sys.path.append(G_PATH + '/../../')
    os.environ['DJANGO_SETTINGS_MODULE'] = 'MobileService.settings'
    from django.conf import settings
    
from MobileService.util.mongodb_util import *
from MobileService.util.DbUtil import DbUtil
from MobileService.util.GearmanUtil import *

SALES_PURCHASE_COLECTION = 'sales_purchase' 

class DbHelpPurchaseUtil(DbUtil):
    def __init__(self, database, logger=None):
        DbUtil.__init__(self, database, logger)
        
    def customer_create_purchase(self, user_phone, category, brand_name, content, pic, type, create_time,unit,budget_amount):
        self.get_db_connect()
        sql = 'insert into help_purchase (user_phone, category, brand_name,content,pic,type,create_time,unit,budget_amount,last_reply_time) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'
        try:
            input_list = []
            input_list.append(str(user_phone))
            input_list.append(category)
            input_list.append(brand_name)
            input_list.append(content)
            input_list.append(pic)
            input_list.append(type)
            input_list.append(create_time)
            input_list.append(unit)
            input_list.append(budget_amount)
            input_list.append(create_time)
            count = self.cursor.execute(sql, input_list)
            
            self.conn.commit()
            self.release_db_connect()
            return True
        except Exception,e:
            if self.logger:
                self.logger.error('customer_create_purchase except %s'%(e))
            self.release_db_connect()    
            return False
    
    def get_customer_purchase_list(self, user_phone):
        self.get_db_connect()
        sql = 'select hp.id,hp.user_phone,hp.category,hp.brand_name,hp.content,hp.pic,hp.type,hp.last_reply_time,count(hpr.id),bd.logo from help_purchase hp left join help_purchase_reply hpr on hp.id=hpr.hp_id and hpr.is_send_c=1 left join newshop.brand bd on bd.title=hp.brand_name where user_phone=%s group by hp.id order by last_reply_time desc'
        try:
            ret_list = []
            count = self.cursor.execute(sql, [str(user_phone)])
            if count == 0:
                return []
            self.cursor.scroll(0, mode='absolute')
            results = self.cursor.fetchall()
            for result in results:
                ret_dict = {}
                ret_dict['id'] = result[0]
                ret_dict['user_phone'] = result[1]
                ret_dict['category'] = result[2]
                ret_dict['brand_name'] = result[3]
                ret_dict['content'] = result[4]
                pics = result[5]
                if not pics:
                    ret_dict['images'] = []
                else:
                    ret_dict['images'] = pics.split(',')
                ret_dict['type'] = result[6]
                ret_dict['last_reply_time'] = 0 if not result[7] else int(time.mktime(result[7].timetuple()))
                ret_dict['reply_num'] = result[8]
                ret_dict['logo'] = result[9] if result[9] else ''
                ret_list.append(ret_dict)
            self.release_db_connect()
            return ret_list
        except Exception,e:
            if self.logger:
                self.logger.error('get_customer_purchase_list except %s'%(e))
            self.release_db_connect()    
            return []

    def get_purchase_base_info(self, purchase_id):
        if not purchase_id:
            return {}
        self.get_db_connect()
        sql = 'select hp.id,hp.user_phone,hp.category,hp.brand_name,hp.content,hp.pic,hp.type,hp.last_reply_time,count(hpr.id),hp.unit,hp.budget_amount,hp.status,bd.logo,hp.create_time from help_purchase hp left join help_purchase_reply hpr on hp.id=hpr.hp_id and hpr.is_send_c=1 left join newshop.brand bd on bd.title=hp.brand_name where hp.id=%s group by hp.id order by last_reply_time desc'
        try:
            ret_list = []
            count = self.cursor.execute(sql, [str(purchase_id)])
            result = self.cursor.fetchone()
            ret_dict = {}
            ret_dict['id'] = result[0]
            ret_dict['user_phone'] = result[1]
            ret_dict['category'] = result[2]
            ret_dict['brand_name'] = result[3]
            ret_dict['content'] = result[4]
            pics = result[5]
            if not pics:
                ret_dict['images'] = []
            else:
                ret_dict['images'] = pics.split(',')
            ret_dict['type'] = result[6]
            ret_dict['last_reply_time'] = 0 if not result[7] else int(time.mktime(result[7].timetuple()))
            ret_dict['reply_num'] = result[8]
            ret_dict['unit'] = result[9] if result[9] else ''
            ret_dict['money'] = result[10] if result[10] else 0
            ret_dict['status'] = result[11]
            ret_dict['logo'] = result[12] if result[12] else ''
            ret_dict['create_time'] = 0 if not result[13] else int(time.mktime(result[13].timetuple()))
            self.release_db_connect()
            return ret_dict
        except Exception,e:
            if self.logger:
                self.logger.error('get_purchase_base_info except %s'%(e))
            self.release_db_connect()    
            return {}
            
    def sales_reply_purchase(self, purchase_id, sales_phone, goods_name, category, brand_name, content, pic, money, deadline,unit,create_time,goods_id=0,shop_id=0):
        self.get_db_connect()
        sql = 'insert into help_purchase_reply (sales_phone, hp_id, category, brand_name,content,pic,goods_name,quote,quote_end_time,create_time,unit,goods_id,shop_id) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'
        try:
            input_list = []
            input_list.append(sales_phone)
            input_list.append(purchase_id)
            input_list.append(category)
            input_list.append(brand_name)
            input_list.append(content)
            input_list.append(pic)
            input_list.append(goods_name)
            input_list.append(money)
            input_list.append(deadline)
            input_list.append(create_time)
            input_list.append(unit)
            input_list.append(goods_id)
            input_list.append(shop_id)
            count = self.cursor.execute(sql, input_list)
            
            self.conn.commit()
            self.release_db_connect()
            return True
        except Exception,e:
            if self.logger:
                self.logger.error('sales_reply_purchase except %s'%(e))
            self.release_db_connect()    
            return False
    
    def get_sales_by_category_brand(self, category, brand_name):
        self.get_db_connect()
        try:
            if category:
                sql = 'select distinct(sub.telephone) from newshop.shopusers_beg sub inner join newshop.channel_beg_address cba ON sub.shopaddrbeg_id=cba.id inner join newshop.shop_address_info sai on sai.id=cba.shop_id inner join newshop.shopaddr_brand sb on sb.shopaddr_id=sai.id inner join newshop.brand bd on bd.id=sb.brand_id inner join newshop.brand_sort bs on bs.brand_id=bd.id inner join newshop.sort s on s.id=bs.sort_id inner join newshop.sort ss on s.parentid=ss.id inner join newshop.sort sss on ss.parentid=sss.id where sss.title=%s and sss.parentid=0'
                count = self.cursor.execute(sql, [category])
            elif brand_name:
                sql = 'select sub.telephone from newshop.shopusers_beg sub inner join newshop.channel_beg_address cba ON sub.shopaddrbeg_id=cba.id inner join newshop.shop_address_info sai on sai.id=cba.shop_id inner join newshop.shopaddr_brand sb on sb.shopaddr_id=sai.id inner join newshop.brand bd on bd.id=sb.brand_id where bd.title=%s'
                count = self.cursor.execute(sql, [brand_name])
            else:
                return []
            ret_list = []
            
            self.cursor.scroll(0, mode='absolute')
            results = self.cursor.fetchall()
            for result in results:
                ret_list.append(result[0])
            self.release_db_connect()
            return ret_list
        except Exception,e:
            if self.logger:
                self.logger.error('get_sales_by_category_brand except %s'%(e))
            self.release_db_connect()    
            return []
    
    def send_purchase_sales_list(self, purchase_id, sales_list):
        self.get_db_connect()
        sql = 'insert into help_purchase_sales (sales_phone,ph_id,create_time) values (%s,%s,%s)'
        try:
            create_time = str(datetime.now())
            total_input_list = []
            for sales_phone in sales_list:
                input_list = []
                input_list.append(sales_phone)
                input_list.append(purchase_id)
                input_list.append(create_time)
                total_input_list.append(input_list)
            count = self.cursor.executemany(sql, total_input_list)
            sql = 'update help_purchase set is_send_b=1 where id=%s'
            count = self.cursor.execute(sql, [purchase_id])
            self.conn.commit()
            self.release_db_connect()
            return True
        except Exception,e:
            if self.logger:
                self.logger.error('send_purchase_sales_list except %s'%(e))
            self.release_db_connect()    
            return False
    
    def sales_get_purchase_list(self, user_name, start, num):
        self.get_db_connect()
        sql = 'select hp.id,hp.user_phone,hp.category,hp.brand_name,hp.content,hp.pic,hp.budget_amount,hp.type,hp.last_reply_time,hp.unit from help_purchase_sales hps inner join help_purchase hp on hps.ph_id=hp.id where hps.sales_phone=%s and hp.is_send_b=1 order by hps.update_time desc limit %s,%s'
        try:
            ret_list = []
            count = self.cursor.execute(sql, [user_name, start, num])
            if count == 0:
                return []
            self.cursor.scroll(0, mode='absolute')
            results = self.cursor.fetchall()
            for result in results:
                ret_dict = {}
                ret_dict['id'] = result[0]
                ret_dict['user_phone'] = result[1]
                ret_dict['category'] = result[2]
                ret_dict['brand_name'] = result[3]
                ret_dict['content'] = result[4]
                pics = result[5]
                if not pics:
                    ret_dict['images'] = []
                else:
                    ret_dict['images'] = pics.split(',')
                ret_dict['budget_amount'] = result[6]
                ret_dict['type'] = result[7]
                ret_dict['update_time'] =  0 if not result[8] else int(time.mktime(result[8].timetuple()))
                ret_dict['unit'] = result[9] if result[9] else ''
                ret_list.append(ret_dict)
            self.release_db_connect()
            return ret_list
        except Exception,e:
            if self.logger:
                self.logger.error('sales_get_purchase_list except %s'%(e))
            self.release_db_connect()    
            return []
            
    def customer_get_purchase_reply_detail(self, id):
        self.get_db_connect()
        sql = 'select hpr.id,hpr.type,hpr.sales_phone,hpr.goods_name,hpr.category,hpr.brand_name,hpr.quote,hpr.quote_end_time,hpr.unit,hpr.content,hpr.pic,hpr.is_send_c,hpr.reject,hpr.update_time,hpr.goods_id,hpr.shop_id,sai.channel_id from help_purchase_reply hpr left join newshop.shop_address_info sai on sai.id=hpr.shop_id where hp_id=%s and is_send_c=1 order by update_time desc'
        try:
            ret_list = []
            count = self.cursor.execute(sql, [id])
            if count == 0:
                return []
            self.cursor.scroll(0, mode='absolute')
            results = self.cursor.fetchall()
            for result in results:
                ret_dict = {}
                ret_dict['id'] = result[0]
                ret_dict['type'] = result[1]
                ret_dict['sales_phone'] = result[2]
                ret_dict['title'] = result[3] if result[3] else ''
                ret_dict['category'] = result[4] if result[4] else ''
                ret_dict['brand_name'] = result[5] if result[5] else ''
                ret_dict['money'] = result[6]
                ret_dict['money_available_time'] =  0 if not result[7] else int(time.mktime(result[7].timetuple()))
                ret_dict['unit'] = result[8]
                ret_dict['content'] = result[9]
                pics = result[10]
                if not pics:
                    ret_dict['images'] = []
                else:
                    ret_dict['images'] = pics.split(',')
                    
                ret_dict['state'] = result[11]
                ret_dict['reject'] = result[12] if result[12] else ''
                ret_dict['update_time'] = 0 if not result[13] else int(time.mktime(result[13].timetuple()))
                ret_dict['goods_id'] = result[14]
                ret_dict['shop_id'] = result[15] if result[15] else 0
                ret_dict['cooperation'] = 1 if result[16] else 0
                ret_list.append(ret_dict)
            self.release_db_connect()
            return ret_list
        except Exception,e:
            if self.logger:
                self.logger.error('customer_get_purchase_reply_detail except %s'%(e))
            self.release_db_connect()    
            return []
            
    def sales_get_purchase_reply_detail(self, id, sales_phone):
        self.get_db_connect()
        sql = 'select id,type,sales_phone,goods_name,category,brand_name,quote,quote_end_time,unit,content,pic,is_send_c,reject,update_time,goods_id from help_purchase_reply where hp_id=%s and type=0 and sales_phone=%s order by update_time desc'
        try:
            ret_list = []
            count = self.cursor.execute(sql, [id, sales_phone])
            if count == 0:
                return []
            self.cursor.scroll(0, mode='absolute')
            results = self.cursor.fetchall()
            for result in results:
                ret_dict = {}
                ret_dict['id'] = result[0]
                ret_dict['type'] = result[1]
                ret_dict['sales_phone'] = result[2]
                ret_dict['title'] = result[3] if result[3] else ''
                ret_dict['category'] = result[4] if result[4] else ''
                ret_dict['brand_name'] = result[5] if result[5] else ''
                ret_dict['money'] = result[6]
                ret_dict['money_available_time'] =  0 if not result[7] else int(time.mktime(result[7].timetuple()))
                ret_dict['unit'] = result[8]
                
                ret_dict['content'] = result[9]
                pics = result[10]
                if not pics:
                    ret_dict['images'] = []
                else:
                    ret_dict['images'] = pics.split(',')
                    
                ret_dict['state'] = result[11]
                ret_dict['reject'] = result[12] if result[12] else ''
                ret_dict['update_time'] = 0 if not result[13] else int(time.mktime(result[13].timetuple()))
                ret_dict['goods_id'] = result[14]

                ret_list.append(ret_dict)
            self.release_db_connect()
            return ret_list
        except Exception,e:
            if self.logger:
                self.logger.error('sales_get_purchase_reply_detail except %s'%(e))
            self.release_db_connect()    
            return []
            
    def update_reply_by_id(self, id, sales_phone, title, brand_name, content, pic, quote, quote_end_time,unit):
        self.get_db_connect()
        sql = 'update help_purchase_reply set is_send_c=0,brand_name=%s,content=%s,pic=%s,quote=%s,quote_end_time=%s,unit=%s where id=%s'
        try:
            input_list = []
            input_list.append(brand_name)
            input_list.append(content)
            input_list.append(pic)
            input_list.append(quote)
            input_list.append(quote_end_time)
            input_list.append(unit)
            input_list.append(id)
            
            count = self.cursor.execute(sql, input_list)
            self.conn.commit()
            self.release_db_connect()
            return True
        except Exception,e:
            if self.logger:
                self.logger.error('update_reply_by_id except %s'%(e))
            self.release_db_connect()    
            return False
    
    def get_recommend_help_purchase(self, num):
        self.get_db_connect()
        sql = 'select hpr.id,hpr.goods_name,hpr.brand_name,hpr.quote,hpr.update_time,hp.user_phone,bd.logo,sai.shop_name from help_purchase_reply hpr inner join help_purchase hp on hp.id=hpr.hp_id inner join newshop.brand bd on bd.title=hpr.brand_name inner join newshop.shopusers_beg sb on sb.telephone=hpr.sales_phone inner join  newshop.channel_beg_address cba on sb.shopaddrbeg_id=cba.id inner join newshop.shop_address_info sai on sai.id=cba.shop_id where recommend=1 order by hpr.update_time desc limit %s'
        try:
            ret_list = []
            count = self.cursor.execute(sql, [num])
            if count == 0:
                return []
            self.cursor.scroll(0, mode='absolute')
            results = self.cursor.fetchall()
            for result in results:
                ret_dict = {}

                ret_dict['id'] = result[0]
                ret_dict['title'] = result[1]
                ret_dict['brand_name'] = result[2]
                ret_dict['money'] = result[3] if result[3] else 0
                ret_dict['update_time'] = 0 if not result[4] else int(time.mktime(result[4].timetuple()))
                phone = '%s*****%s'%(result[5][:3], result[5][-3:])
                ret_dict['user_phone'] = phone
                ret_dict['logo'] = result[6]
                if not ret_dict['brand_name'] or not ret_dict['logo']:
                    continue                
                shop_name = result[7]
                shop_name_info = shop_name.split(' ')
                if len(shop_name_info) == 2:
                    shop_name = shop_name_info[1]
                ret_dict['shop_name'] = shop_name
                ret_list.append(ret_dict)
            self.release_db_connect()
            return ret_list
        except Exception,e:
            if self.logger:
                self.logger.error('get_recommend_help_purchase except %s'%(e))
            self.release_db_connect()    
            return []
    
    def get_system_purchase_num(self):
        self.get_db_connect()
        sql = 'select count(*) from help_purchase'
        try:
            ret_list = []
            count = self.cursor.execute(sql)
            result = self.cursor.fetchone()
            self.release_db_connect()
            return result[0]
        except Exception,e:
            if self.logger:
                self.logger.error('get_system_purchase_num except %s'%(e))
            self.release_db_connect()    
            return 0
    
    def get_purchase_reply_detail(self, id):
        self.get_db_connect()
        sql = 'select id, sales_phone, category, brand_name, goods_name,quote,quote_end_time,unit,content,pic,goods_id,update_time from help_purchase_reply where id=%s'
        try:
            count = self.cursor.execute(sql, [id])
            if count == 0:
                return {}
            result = self.cursor.fetchone()
            ret_dict = {}
            ret_dict['id'] = result[0]
            ret_dict['sales_phone'] = result[1]
            ret_dict['category'] = result[2]
            ret_dict['brand_name'] = result[3]
            ret_dict['title'] = result[4]
            ret_dict['money'] = result[5]
            ret_dict['money_available_time'] =  0 if not result[6] else int(time.mktime(result[6].timetuple()))
            ret_dict['unit'] = result[7] if result[7] else ''
            ret_dict['content'] = result[8]
            pics = result[9]
            if not pics:
                ret_dict['images'] = []
            else:
                ret_dict['images'] = pics.split(',')
            ret_dict['goods_id'] = result[10]
            ret_dict['update_time'] =  0 if not result[11] else int(time.mktime(result[11].timetuple()))
            
            self.release_db_connect()
            return ret_dict
        except Exception,e:
            if self.logger:
                self.logger.error('get_purchase_reply_detail except %s'%(e))
            self.release_db_connect()    
            return {}
    
class HelpPurchaseUtil():
    def __init__(self, database):
        self.info_logger = database['mobile_logger']
        self.gearman_config = database['gearman_config']
        self.redis = database['cache_redis']
        self.mobile_db = database['mobile_db']
        self.database = database
        self.get_mongo_connect()
            
    def get_mongo_connect(self):
        self.mongo_db = MongoDatabase().get_database()
        self.collection = self.mongo_db[SALES_PURCHASE_COLECTION]
        
    def customer_create_purchase(self, user_phone, category, brand_name, content, pic, type,unit='', budget_amount=0):
        create_time = str(datetime.now())
        handler = DbHelpPurchaseUtil(self.mobile_db, self.info_logger)
        return handler.customer_create_purchase(user_phone, category, brand_name, content, pic, type, create_time,unit,budget_amount)
    
    def get_customer_purchase_list(self, user_phone):
        handler = DbHelpPurchaseUtil(self.mobile_db, self.info_logger)
        return handler.get_customer_purchase_list(user_phone)
        
    def sales_reply_purchase(self, purchase_id, sales_phone, goods_name, category, brand_name, content, pic, money, deadline,unit,goods_id,shop_id=0):
        create_time = str(datetime.now())
        handler = DbHelpPurchaseUtil(self.mobile_db, self.info_logger)
        return handler.sales_reply_purchase(purchase_id, sales_phone, goods_name, category, brand_name, content, pic, money, deadline,unit,create_time,goods_id,shop_id)
    
    def get_purchase_sales_list(self, purchase_id):
        handler = DbHelpPurchaseUtil(self.mobile_db, self.info_logger)
        purchase_detail = handler.get_purchase_base_info(purchase_id)
        category = purchase_detail.get('category','')
        brand_name = purchase_detail.get('brand_name','')
        return handler.get_sales_by_category_brand(category, brand_name)
            
    def send_purchase_sales_list(self, purchase_id, sales_list):
        if not sales_list or not purchase_id:
            return False
        handler = DbHelpPurchaseUtil(self.mobile_db, self.info_logger)
        self.info_logger.info('send_purchase_sales_list %s'%(str(sales_list)))
        to_user_list = copy.deepcopy(sales_list)
        for i in range(0,100):
            handler.send_purchase_sales_list(purchase_id, to_user_list[:50])
            del to_user_list[:50]
            if not to_user_list:
                break
        
    def sales_get_purchase_list(self, user_name, start, num):
        handler = DbHelpPurchaseUtil(self.mobile_db, self.info_logger)
        return handler.sales_get_purchase_list(user_name, start, num)
    
    def get_purchase_base_info(self, id):
        handler = DbHelpPurchaseUtil(self.mobile_db, self.info_logger)
        ret_dict = handler.get_purchase_base_info(id)
        return ret_dict
        
    def customer_get_purchase_detail(self, id):
        handler = DbHelpPurchaseUtil(self.mobile_db, self.info_logger)
        ret_dict = handler.get_purchase_base_info(id)
        if not ret_dict:
            return {}
        ret_dict['last_reply_time'] = ret_dict['create_time']
        ret_dict['items'] = handler.customer_get_purchase_reply_detail(id)
        return ret_dict
        
    def sales_get_purchase_detail(self, id, sales_phone):
        handler = DbHelpPurchaseUtil(self.mobile_db, self.info_logger)
        ret_dict = handler.get_purchase_base_info(id)
        if not ret_dict:
            return {}
        ret_dict['items'] = handler.sales_get_purchase_reply_detail(id, sales_phone)
        return ret_dict
        
    def update_reply_by_id(self, id, sales_phone, title, brand_name, content, pic, quote, quote_end_time,unit):
        handler = DbHelpPurchaseUtil(self.mobile_db, self.info_logger)
        return handler.update_reply_by_id(id, sales_phone, title, brand_name, content, pic, quote, quote_end_time,unit)
    
    def get_recommend_help_purchase(self, num):
        handler = DbHelpPurchaseUtil(self.mobile_db, self.info_logger)
        return handler.get_recommend_help_purchase(num)
    
    def get_purchase_reply_detail(self, id):
        handler = DbHelpPurchaseUtil(self.mobile_db, self.info_logger)
        return handler.get_purchase_reply_detail(id)
        
    def get_system_purchase_num(self):
        handler = DbHelpPurchaseUtil(self.mobile_db, self.info_logger)
        return handler.get_system_purchase_num()
        
if __name__ == '__main__':
    business_user_list = [
    '13822678953',
    '13833678953',
    ]
    handler = InstanceMessageV2Util(settings.COMMON_DATA)
