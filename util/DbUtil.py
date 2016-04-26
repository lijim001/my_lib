#coding=utf-8

import MySQLdb,time,random,hashlib
from datetime import datetime,timedelta
import simplejson as json
from decimal import *

getcontext().prec = 2

if __name__ == '__main__':
    import os,sys
    G_PATH = os.path.split(os.path.realpath(__file__))[0]
    sys.path.append(G_PATH + '/../../')
    os.environ['DJANGO_SETTINGS_MODULE'] = 'MobileService.settings'
    from django.conf import settings
  
ORDER_TYPE_BAO = 1
ORDER_TYPE_IMM = 2

ORDER_CREATE_TYPE_GOODS_LOOK = 1
ORDER_CREATE_TYPE_OFFLINE = 2

TYPE_DB_CREATE_PRICE_TOTAL = 0
TYPE_DB_CREATE_PRICE_PRE = 1

TYPE_MY_ORDER_ALL = 0
TYPE_MY_ORDER_PRE_PAYED = 1
TYPE_MY_ORDER_UNPAYED = 2
TYPE_MY_ORDER_PAYED = 3
TYPE_MY_ORDER_RECENT = 10

PAY_ORDER_TYPE_ALL = 0
PAY_ORDER_TYPE_SUBSCRIBE = 1
PAY_ORDER_TYPE_TAIL = 2

STATE_ORDER_UNPAYED = 0
STATE_ORDER_SUBSCRIBE_PAYED = 1
STATE_ORDER_PAYED = 2
STATE_ORDER_CANCELED = 3
STATE_ORDER_GOODS_BACK = 4

SELECT_ORDER_PREFIX = 'select user_id,order_number,channel_id,channel_name,shop_id,shop_name,sales,price_total,price_pre,price_real,flag,state,shipping_id,id,pre_flag,shop_address,content,sales_name,brand_id,brand_name,contract_images,create_time,user_phone,contract_price,current_price,creator,coupon,pre_cooperation,shopping_id, customer_type, pay_time,verify_state,settle_state,reject,given_coupon,settle_time,verify_time,stages_return,wish_flag,wish_percent_coupon,percent_coupon_id from orders '
class DbUtil():
    def __init__(self, db_config, logger = None):
        self.db = db_config
        self.logger = logger
        self.cursor = None
        self.conn = None
        
    def get_db_connect(self):
        (host, user, passwd, db) = self.db
        if not self.cursor and not self.conn:
            self.conn = MySQLdb.connect(host=host, user=user, passwd=passwd, db=db, charset="utf8")  
            self.cursor = self.conn.cursor()
        
    def release_db_connect(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        self.cursor = None
        self.conn = None
        
    def do_select_one(self, sql, func_name = ''):
        self.get_db_connect()        
        try:
            count = self.cursor.execute(sql)
            if count == 0:
                self.release_db_connect()
                return None
            result = self.cursor.fetchone()
            self.release_db_connect()
            return result
        except Exception,e:
            if self.logger:
                self.logger.error('%s do_select_one except %s'%(str(func_name), e))
            self.release_db_connect()    
            return None         

    def do_select_bool(self, sql, func_name = ''):
        self.get_db_connect()        
        try:
            count = self.cursor.execute(sql)
            if count == 0:
                self.release_db_connect()
                return False
            self.release_db_connect()
            return True
        except Exception,e:
            if self.logger:
                self.logger.error('%s do_select_bool except %s'%(str(func_name), e))
            self.release_db_connect()    
            return False 

    def do_update(self, sql, func_name = ''):
        self.get_db_connect()        
        try:
            count = self.cursor.execute(sql)
            self.conn.commit()
            self.release_db_connect()
            return True
        except Exception,e:
            if self.logger:
                self.logger.error('%s do_update except %s'%(str(func_name), e))
            self.release_db_connect()    
            return False 
            
    def do_select_multi(self, sql, func_name = ''):
        self.get_db_connect()
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                self.cursor.scroll(0, mode='absolute')
                results = self.cursor.fetchall()
                self.release_db_connect()
                return results
            else:
                return None
        except Exception,e:
            if self.logger:
                self.logger.error('%s do_select_multi except %s'%(str(func_name), e))
            self.release_db_connect()
            return None
    
    def format_phone_list(self, phone_list):
        if not phone_list:
            return ''
        ret_str = ''
        for phone in phone_list:
            if not phone:
                continue
            ret_str += '"' + str(phone) + '",'
        return ret_str[:-1]
        
    def get_company_user_list(self):
        sql = 'select telephone from company_user'
        return self.do_select_multi(sql, 'get_company_user_list')
    
    def check_user_exits(self, user_name):
        self.get_db_connect()
        sql_prefix = 'select uid from xw_user where mobile=%s'
        try:
            count = self.cursor.execute(sql_prefix, [user_name])
            if count == 0:
                self.release_db_connect()
                return False
            else:
                self.release_db_connect()
                return True
        except Exception,e:
            if self.logger:
                self.logger.error('check_user_exits except %s'%(e))
            self.release_db_connect()    
            return True

    def update_settle_callback_state(self, award_id):
        self.get_db_connect()
        try:
            sql = 'select settle_id from commision_info where id=%s'%(str(award_id))
            count = self.cursor.execute(sql)
            if count == 0:
                return False
            result = self.cursor.fetchone()
            settle_id = result[0]
            if not settle_id:
                return False
            sql = 'select callback_state from commision_info where settle_id=%s'%(str(settle_id))
            count = self.cursor.execute(sql)
            callback_state = 1
            if count == 0:
                return False
            self.cursor.scroll(0, mode='absolute')
            results = self.cursor.fetchall()
            for result in results:
                callback_state = callback_state & result[0]
            if callback_state == 0:
                return False
            sql = 'update commision_settle set callback_state=1 where id=%s'%(str(settle_id))
            count = self.cursor.execute(sql)
            self.conn.commit()
            self.release_db_connect()
            return True
        except Exception,e:
            self.conn.rollback()
            if self.logger:
                self.logger.error('update_settle_callback_state except %s'%(e))
            self.release_db_connect()    
            return False
    
    def record_promote_channel_info(self, phone, name, action, promote_id):
        self.get_db_connect()        
        try:
            sql = 'select keyword from promote_keywords where id=%s'
            count = self.cursor.execute(sql, [promote_id])
            if count == 0:
                self.release_db_connect()
                return False
            if phone:
                sql = 'insert into promote_channel_stat (sales_phone, name,action, promote_keywords_id) values (%s,%s,%s,%s)'
                count = self.cursor.execute(sql, [phone, name, action, promote_id])
            else:
                sql = 'insert into promote_keyword_stat (action, promote_keywords_id) values (%s,%s)'
                count = self.cursor.execute(sql, [action, promote_id])
            self.conn.commit()
            self.release_db_connect()
            return True
        except Exception,e:
            if self.logger:
                self.logger.error('record_promote_channel_info except %s'%(e))
            self.release_db_connect()    
            return False
    
    def format_select_commision_info(self, user_phone, user_role):
        if user_role == 'wallet_business':
            sql = 'select id from commision_info where user_phone="%s" and type in (3,4)'%(str(user_phone))
        else:
            sql = 'select id from commision_info where user_phone="%s" and type=0'%(str(user_phone))
        return sql

    def get_commision_info_by_user_type(self, user_phone, sales_phone, type):
        self.get_db_connect()        
        try:
            sql = 'select user_phone, sales_phone, money, callback_state, settle_state, settle_id from commision_info where user_phone="%s" and sales_phone="%s" and type=%s'%(str(user_phone), str(sales_phone), str(type))
            count = self.cursor.execute(sql)
            if count == 0:
                self.release_db_connect()
                return None
            result = self.cursor.fetchone()
            self.release_db_connect()
            return result
        except Exception,e:
            if self.logger:
                self.logger.error('get_commision_info_by_user_type except %s'%(e))
            self.release_db_connect()    
            return None
            
    def verify_commision_info(self, user_phone, sales_phone, type, enable):
        self.get_db_connect()
        try:
            sql = 'update commision_info set callback_state=1, settle_state=2, enable=%s, update_time=%s where user_phone="%s" and sales_phone="%s" and type=%s'%(str(enable),str(int(time.time())), str(user_phone), str(sales_phone), str(type))
            count = self.cursor.execute(sql)
            
            sql = 'update user_consume_info set reward_2000="do" where user_phone="%s"'%(str(user_phone))
            count = self.cursor.execute(sql)
            
            self.conn.commit()
            self.release_db_connect()
            return True
        except Exception,e:
            self.conn.rollback()
            if self.logger:
                self.logger.error('verify_commision_info except %s'%(e))
            self.release_db_connect()    
            return False

    def add_order_payed_commision_info(self, user_phone, sales_phone, money, type):
        self.get_db_connect()
        try:
            sql = 'insert into commision_info (money, user_phone, sales_phone, type, callback_state, settle_state, update_time) values (%s, "%s", "%s", %s, %s, %s, %s)' \
            %(str(money), user_phone, sales_phone, str(type), '1', '2', str(int(time.time())))
            count = self.cursor.execute(sql)
            self.conn.commit()
            self.release_db_connect()
            return True
        except Exception,e:
            self.conn.rollback()
            if self.logger:
                self.logger.error('add_order_payed_commision_info except %s'%(e))
            self.release_db_connect()    
            return False
            
    def update_commision_info(self, award_id, enable, settle_state,callback_state,commision_content,content_creator,content_state,custom_state,purchase_name,user_phone,user_role):
        self.get_db_connect()
        try:
            if not award_id and not user_phone:
                return (False, award_id)
            if not user_phone and award_id:
                sql = 'select user_phone, type from commision_info where id=%s'%(str(award_id))
                count = self.cursor.execute(sql)
                if count == 0:
                    return (True, award_id)
                result = self.cursor.fetchone()
                sales_phone = result[0]
                if result[1] == 3:
                    user_role = 'wallet_business'
                elif result[1] == 0:
                    user_role = 'wallet_client'
            else:
                sales_phone = user_phone
            
            action_time = str(int(time.time()))
            if settle_state is not None:
                sql = 'insert into user_action_time (user_phone, verify_time) values ("%s", %s) on duplicate key update verify_time=%s'%(str(sales_phone), action_time, action_time)
                count = self.cursor.execute(sql)
            if callback_state is not None:
                sql = 'insert into user_action_time (user_phone, callback_time) values ("%s", %s) on duplicate key update callback_time=%s'%(str(sales_phone), action_time, action_time)
                count = self.cursor.execute(sql)
            
            if user_role == 'wallet_business':
                if settle_state is not None:
                    sql = 'update user_shop set settle_state=%s where telephone="%s"'%(str(settle_state), str(sales_phone)) 
                    count = self.cursor.execute(sql)
                if callback_state is not None:
                    if int(callback_state) == 1 and content_state and int(content_state) == 102:
                        sql = 'update user_shop set callback_state=2 where telephone="%s"'%(str(sales_phone))
                    else:
                        sql = 'update user_shop set callback_state=%s where telephone="%s"'%(str(callback_state), str(sales_phone)) 
                    count = self.cursor.execute(sql)
                
            #if commision_content:
            sql = 'insert into commision_content (type,content_id,content,content_creator,callback_state,phone) values (%s,%s,"%s","%s",%s,"%s")' \
            %('0', str(award_id), commision_content, content_creator, str(content_state), str(sales_phone))
            count = self.cursor.execute(sql)
            self.conn.commit()
            
            if not award_id:
                sql = self.format_select_commision_info(user_phone, user_role)
                count = self.cursor.execute(sql)
                if count == 0:
                    return (True, award_id)
                result = self.cursor.fetchone()
                award_id = result[0]

            if enable is not None:
                sql = 'update commision_info set enable=%s where id=%s'%(str(enable), str(award_id)) 
                count = self.cursor.execute(sql)
            if settle_state is not None:
                sql = 'update commision_info set settle_state=%s where id=%s'%(str(settle_state), str(award_id)) 
                count = self.cursor.execute(sql)
            if callback_state is not None:
                sql = 'update commision_info set callback_state=%s where id=%s'%(str(callback_state), str(award_id)) 
                count = self.cursor.execute(sql)
            if custom_state is not None:
                sql = 'update commision_info set custom_state=%s where id=%s'%(str(custom_state), str(award_id)) 
                count = self.cursor.execute(sql)
            if purchase_name:
                sql = 'update commision_info set purchase_name="%s" where id=%s'%(purchase_name, str(award_id)) 
                count = self.cursor.execute(sql)
            sql = 'update commision_info set update_time=%s where id=%s'%(str(int(time.time())), str(award_id))
            count = self.cursor.execute(sql)
            self.conn.commit()
            self.release_db_connect()
            # if count > 0:
                # return True
            # else:
                # return False
            return (True, award_id)
        except Exception,e:
            self.conn.rollback()
            if self.logger:
                self.logger.error('update_commision_info except %s'%(e))
            self.release_db_connect()    
            return (False, award_id)

    def get_user_frozen_award(self, user_name):
        self.get_db_connect()
        sql = 'select sum(money) from commision_info where sales_phone="%s" and settle_state=0 and enable=1'%(user_name)        
        try:
            count = self.cursor.execute(sql)
            if count == 0:
                self.release_db_connect()
                return None
            result = self.cursor.fetchone()
            self.release_db_connect()
            return result[0]
        except Exception,e:
            if self.logger:
                self.logger.error('get_user_frozen_award except %s'%(e))
            self.release_db_connect()    
            return None

    #获取b邀请c，c交易奖励金额
    def get_user_consumer_award(self, user_name, phone):
        self.get_db_connect()
        if phone:
            sql = 'select sum(money) from commision_info where sales_phone="%s" and user_phone="%s" and settle_state = 2 and enable=1 and substring(type, 1,1) = 6'%(user_name, str(phone))
        else:
            sql = 'select sum(money) from commision_info where sales_phone="%s" and settle_state = 2 and enable=1 and substring(type, 1,1) = 6'%(user_name)

        try:
            count = self.cursor.execute(sql)
            if count == 0:
                self.release_db_connect()
                return None
            result = self.cursor.fetchone()
            self.release_db_connect()
            return result[0]
        except Exception,e:
            if self.logger:
                self.logger.error('get_user_frozen_award except %s'%(e))
            self.release_db_connect()
            return None

    def get_user_award(self, user_name):
        self.get_db_connect()
        sql = 'select sum(money) from commision_info where sales_phone="%s" and state=0 and enable=1'%(user_name)        
        try:
            count = self.cursor.execute(sql)
            if count == 0:
                self.release_db_connect()
                return None
            result = self.cursor.fetchone()
            self.release_db_connect()
            return result[0]
        except Exception,e:
            if self.logger:
                self.logger.error('get_user_award except %s'%(e))
            self.release_db_connect()    
            return None

    def get_user_reward_money(self, user_name):
        self.get_db_connect()
        sql = 'select sum(money) from commision_info where sales_phone="%s" and settle_state in (0, 2) and settle_id=0 and enable=1 and update_time > 0'%(user_name)
        try:
            count = self.cursor.execute(sql)
            if count == 0:
                self.release_db_connect()
                return None
            result = self.cursor.fetchone()
            self.release_db_connect()
            return result[0]
        except Exception, e:
            if self.logger:
                self.logger.error('get_user_reward_money %s'%(e))
            self.release_db_connect()
            return None

    def get_user_award_examine(self, user_name):
        self.get_db_connect()
        sql = 'select sum(money) from commision_info where sales_phone="%s" and state=1 and enable=1 and settle_state=0'%(user_name)        
        try:
            count = self.cursor.execute(sql)
            if count == 0:
                self.release_db_connect()
                return None
            result = self.cursor.fetchone()
            self.release_db_connect()
            return result[0]
        except Exception,e:
            if self.logger:
                self.logger.error('get_user_award_examine except %s'%(e))
            self.release_db_connect()    
            return None 
    
    def update_customer_usage_time(self, user_id, login_time = 0, see_goods_time = 0, transaction_time = 0):
        self.get_db_connect()
        try:
            if login_time:
                sql = 'update customer_user set last_login_time=%s where user_id=%s'%(str(login_time), str(user_id))
                count = self.cursor.execute(sql)

            if see_goods_time:
                sql = 'update customer_user set see_goods_time=%s where user_id=%s'%(str(see_goods_time), str(user_id))
                count = self.cursor.execute(sql)

            if transaction_time:
                sql = 'update customer_user set transaction_time=%s where user_id=%s'%(str(transaction_time), str(user_id))
                count = self.cursor.execute(sql)
                
            self.conn.commit()
            self.release_db_connect()
            return True
        except Exception,e:
            self.conn.rollback()
            if self.logger:
                self.logger.error('update_customer_usage_time except %s'%(e))
            self.release_db_connect()    
            return False
            
    def get_user_banner_info(self, user_name):
        self.get_db_connect()
        sql = 'select business_login,business_settle from ban_user_list where phone="%s"'%(str(user_name))        
        try:
            count = self.cursor.execute(sql)
            if count == 0:
                self.release_db_connect()
                return {}
            result = self.cursor.fetchone()
            ret_dict = {}
            ret_dict['business_login'] = result[0]
            ret_dict['business_settle'] = result[1]
            self.release_db_connect()
            return ret_dict
        except Exception,e:
            if self.logger:
                self.logger.error('get_user_banner_info except %s'%(e))
            self.release_db_connect()    
            return {}     
    
    def get_cooperation_sales_same_shop(self, sales):
        self.get_db_connect()
        sql = 'select sales_phone from pre_cooperation_users where pre_cooperation_id= (select pre_cooperation_id from pre_cooperation_users where sales_phone="%s")'%(str(sales))        
        try:
            count = self.cursor.execute(sql)
            if count == 0:
                self.release_db_connect()
                return []
            self.cursor.scroll(0, mode='absolute')
            results = self.cursor.fetchall()
            self.release_db_connect()
            ret_list = []
            for result in results:
                ret_list.append(result[0])
            return ret_list
        except Exception,e:
            if self.logger:
                self.logger.error('get_cooperation_sales_same_shop except %s'%(e))
            self.release_db_connect()    
            return []
    
    def get_user_payed_money_by_sales(self, user_phone, sales_list):
        if not sales_list:
            return 0
        sales_list = [ str(i) for i in sales_list ]
        self.get_db_connect()
        sql = 'select sum(price_total) from orders where user_phone=' + str(user_phone)
        sql += ' and sales in (' + ','.join(sales_list) + ') and state in (1,2)'  
        try:
            count = self.cursor.execute(sql)
            if count == 0:
                self.release_db_connect()
                return 0
            result = self.cursor.fetchone()
            self.release_db_connect()
            if not result[0]:
                return 0
            return result[0]
        except Exception,e:
            if self.logger:
                self.logger.error('get_user_payed_money_by_sales except %s'%(e))
            self.release_db_connect()    
            return 0

    def get_user_payed_money_by_shop_id(self, user_phone, shop_id):
        if not shop_id:
            return 0
        self.get_db_connect()
        sql = 'select sum(price_total) from orders where user_phone=' + str(user_phone)
        sql += ' and shop_id=%s and state in (1,2)'%(str(shop_id))  
        try:
            count = self.cursor.execute(sql)
            if count == 0:
                self.release_db_connect()
                return 0
            result = self.cursor.fetchone()
            self.release_db_connect()
            if not result[0]:
                return 0
            return result[0]
        except Exception,e:
            if self.logger:
                self.logger.error('get_user_payed_money_by_shop_id except %s'%(e))
            self.release_db_connect()    
            return 0

    def get_user_pay_times_by_sales(self, user_phone, sales_list):
        if not sales_list:
            return []
        sales_list = [ str(i) for i in sales_list ]
        self.get_db_connect()
        sql = 'select price_total from orders where user_phone=' + str(user_phone)
        sql += ' and sales in (' + ','.join(sales_list) + ') and state in (1,2,4)' 
        print sql
        try:
            count = self.cursor.execute(sql)
            if count == 0:
                self.release_db_connect()
                return []
            self.cursor.scroll(0, mode='absolute')
            results = self.cursor.fetchall()
            self.release_db_connect()
            return results
        except Exception,e:
            if self.logger:
                self.logger.error('get_user_pay_times_by_sales except %s'%(e))
            self.release_db_connect()    
            return []

    def get_sales_payed_order_num(self, sales):
        self.get_db_connect()
        sql = 'select count(*) from orders where sales=%s and user_phone not in (select telephone from company_user) and state in (1,2)' 
        try:
            count = self.cursor.execute(sql, [sales])
            if count == 0:
                self.release_db_connect()
                return 0
            result = self.cursor.fetchone()
            self.release_db_connect()
            return result[0]
        except Exception,e:
            if self.logger:
                self.logger.error('get_sales_payed_order_num except %s'%(e))
            self.release_db_connect()    
            return 0
            
    def get_user_pay_times_by_shop_id(self, user_phone, shop_id):
        if not shop_id:
            return []
        self.get_db_connect()
        sql = 'select price_total from orders where user_phone=' + str(user_phone)
        sql += ' and shop_id=%s and state in (1,2)'%(str(shop_id))  
        try:
            count = self.cursor.execute(sql)
            if count == 0:
                self.release_db_connect()
                return []
            self.cursor.scroll(0, mode='absolute')
            results = self.cursor.fetchall()
            self.release_db_connect()
            return results
        except Exception,e:
            if self.logger:
                self.logger.error('get_user_pay_times_by_shop_id except %s'%(e))
            self.release_db_connect()    
            return []
            
    def get_user_pay_coupon_by_sales(self, user_phone, sales_list):
        if not sales_list:
            return []
        sales_list = [ str(i) for i in sales_list ]
        self.get_db_connect()
        sql = 'select price_total from orders where user_phone=' + str(user_phone)
        sql += ' and sales in (' + ','.join(sales_list) + ') and state in (1,2) and coupon > 0'  
        try:
            count = self.cursor.execute(sql)
            if count == 0:
                self.release_db_connect()
                return []
            self.cursor.scroll(0, mode='absolute')
            results = self.cursor.fetchall()
            self.release_db_connect()
            return results
        except Exception,e:
            if self.logger:
                self.logger.error('get_user_pay_coupon_by_sales except %s'%(e))
            self.release_db_connect()    
            return []

    def get_user_pay_coupon_by_shop_id(self, user_phone, shop_id):
        if not shop_id:
            return []
        self.get_db_connect()
        sql = 'select price_total from orders where user_phone=' + str(user_phone)
        sql += ' and shop_id=%s and state in (1,2) and coupon > 0'%(str(shop_id))  
        try:
            count = self.cursor.execute(sql)
            if count == 0:
                self.release_db_connect()
                return []
            self.cursor.scroll(0, mode='absolute')
            results = self.cursor.fetchall()
            self.release_db_connect()
            return results
        except Exception,e:
            if self.logger:
                self.logger.error('get_user_pay_coupon_by_shop_id except %s'%(e))
            self.release_db_connect()    
            return []
            
    def get_user_payed_money_by_channel_id(self, user_phone, channel_id):
        if not channel_id:
            return 0
        self.get_db_connect()
        sql = 'select sum(price_total) from orders where user_phone=' + str(user_phone)
        sql += ' and channel_id=%s and state in (1,2)'%(str(channel_id))  
        try:
            count = self.cursor.execute(sql)
            if count == 0:
                self.release_db_connect()
                return 0
            result = self.cursor.fetchone()
            self.release_db_connect()
            if not result[0]:
                return 0
            return result[0]
        except Exception,e:
            if self.logger:
                self.logger.error('get_user_payed_money_by_channel_id except %s'%(e))
            self.release_db_connect()    
            return 0
            
    def get_upper_sales_pre_bind_info(self, sales_phone):
        sql = 'select sales_phone, create_time,upper_sales_phone from pre_bind_upper_sales where sales_phone="%s"'%(str(sales_phone))
        self.get_db_connect()    
        try:
            count = self.cursor.execute(sql)
            ret_dict = {}
            if count > 0:
                result = self.cursor.fetchone()
                ret_dict['sales_phone'] = result[0]
                ret_dict['create_time'] = result[1]
                ret_dict['upper_sales_phone'] = result[2]
                self.release_db_connect()
                return ret_dict
            else:
                self.release_db_connect()
                return {}
        except Exception,e:
            if self.logger:
                self.logger.error('get_upper_sales_pre_bind_info except %s'%(e))         
            self.release_db_connect()
            return {}
            
    def record_user_register(self, user_id, user_name):
        self.get_db_connect()
        try:
            sql = 'insert into customer_user (user_id, name) values (%s,%s)'
            insert_fileds = []
            insert_fileds.append(str(user_id))
            insert_fileds.append(str(user_name))

            count = self.cursor.execute(sql, insert_fileds)
            self.conn.commit()
            self.release_db_connect()
            return True
        except Exception,e:
            self.conn.rollback()
            if self.logger:
                self.logger.error('record_user_register except %s'%(e))
            self.release_db_connect()    
            return False        
    
    def get_user_info(self, user_id, user_name):
        self.get_db_connect()
        try:
            sql = 'select covered_area,house_type,pay_flag from customer_user where name="%s"'%(str(user_name))
            count = self.cursor.execute(sql)
            ret_dict = {}
            if count > 0:
                result = self.cursor.fetchone()
                ret_dict['covered_area'] = result[0]
                ret_dict['house_type'] = result[1]
                self.release_db_connect()
                ret_dict['user_phone'] = user_name
                ret_dict['pay_flag'] = result[2]
                return ret_dict
            else:            
                if not user_name.startswith('12') and user_id:
                    if self.logger:
                        self.logger.error('get_user_info add customer user for %s'%(str(user_name))) 
                    sql = 'insert into customer_user (user_id,name) values (%s,"%s")'%(str(user_id), str(user_name))
                    count = self.cursor.execute(sql)
                    self.conn.commit()
                self.release_db_connect()
                return {}
        except Exception,e:
            if self.logger:
                self.logger.error('get_user_info except %s'%(e))         
            self.release_db_connect()
            return {}
    
    def get_inquire_history_list_v2(self, goods_list, num=20):
        self.get_db_connect()
        try:
            input_goods = ''
            for goods in goods_list:
                input_goods += '"' + goods + '",'
            input_goods = input_goods[:-1]
            sql = 'select c_phone, session_id, content, goods, ctime from chat_group_info_v2 where goods in (%s) order by ctime desc limit %s'%(input_goods,num)
            if self.logger:
                self.logger.info('get_inquire_history_list_v2 sql %s'%(sql))
            count = self.cursor.execute(sql)
            ret_list = []
            if count > 0:
                self.cursor.scroll(0, mode='absolute')
                results = self.cursor.fetchall()
                self.release_db_connect()
                for result in results:
                    ret_dict = {}
                    ret_dict['phone'] = result[0]
                    ret_dict['session_id'] = result[1]
                    ret_dict['content'] = result[2]
                    ret_dict['goods'] = result[3]
                    ret_dict['create_time'] = result[4]
                    ret_list.append(ret_dict)
                return ret_list
            else:
                return []
        except Exception,e:
            if self.logger:
                self.logger.error('get_inquire_history_list_v2 except %s'%(e))
            self.release_db_connect()
            return []

    def get_session_infos_v2(self, session_id, start = 0, num = 20, filter_auto = 0, sorting = 0):
        self.get_db_connect()
        try:
            if sorting == 0:
                if filter_auto == 0:
                    if start == 0:
                        sql = 'select sgl.extra,sgl.cutoff_money,sgl.cutoff_rate,gl.group_content from session_goods_list sgl inner join goods_list gl on gl.id=sgl.goods_id where sgl.session_id=%s and sgl.enable=1 order by sgl.cutoff_rate, sgl.money desc, sgl.create_time desc limit %s'%(str(session_id), str(num))
                    else:
                        sql = 'select sgl.extra,sgl.cutoff_money,sgl.cutoff_rate,gl.group_content from session_goods_list sgl inner join goods_list gl on gl.id=sgl.goods_id where sgl.session_id=%s and sgl.enable=1 order by sgl.cutoff_rate, sgl.money desc, sgl.create_time desc limit %s,%s'%(str(session_id), str(start), str(num))
                else:
                    if start == 0:
                        sql = 'select sgl.extra,sgl.cutoff_money,sgl.cutoff_rate,gl.group_content from session_goods_list sgl inner join goods_list gl on gl.id=sgl.goods_id where sgl.session_id=%s and sgl.enable=1 and sgl.auto=0 order by sgl.cutoff_rate, sgl.money desc, sgl.create_time desc limit %s'%(str(session_id), str(num))
                    else:
                        sql = 'select sgl.extra,sgl.cutoff_money,sgl.cutoff_rate,gl.group_content from session_goods_list sgl inner join goods_list gl on gl.id=sgl.goods_id where sgl.session_id=%s and sgl.enable=1 and sgl.auto=0 order by sgl.cutoff_rate, sgl.money desc, sgl.create_time desc limit %s,%s'%(str(session_id), str(start), str(num))
            else:
                if filter_auto == 0:
                    if start == 0:
                        sql = 'select sgl.extra,sgl.cutoff_money,sgl.cutoff_rate,gl.group_content from session_goods_list sgl inner join goods_list gl on gl.id=sgl.goods_id where sgl.session_id=%s and sgl.enable=1 order by sgl.create_time desc limit %s'%(str(session_id), str(num))
                    else:
                        sql = 'select sgl.extra,sgl.cutoff_money,sgl.cutoff_rate,gl.group_content from session_goods_list sgl inner join goods_list gl on gl.id=sgl.goods_id where sgl.session_id=%s and sgl.enable=1 order by sgl.create_time desc limit %s,%s'%(str(session_id), str(start), str(num))
                else:
                    if start == 0:
                        sql = 'select sgl.extra,sgl.cutoff_money,sgl.cutoff_rate,gl.group_content from session_goods_list sgl inner join goods_list gl on gl.id=sgl.goods_id where sgl.session_id=%s and sgl.enable=1 and sgl.auto=0 order by sgl.create_time desc limit %s'%(str(session_id), str(num))
                    else:
                        sql = 'select sgl.extra,sgl.cutoff_money,sgl.cutoff_rate,gl.group_content from session_goods_list sgl inner join goods_list gl on gl.id=sgl.goods_id where sgl.session_id=%s and sgl.enable=1 and sgl.auto=0 order by sgl.create_time desc limit %s,%s'%(str(session_id), str(start), str(num))
            count = self.cursor.execute(sql)
            if count > 0:
                self.cursor.scroll(0, mode='absolute')
                results = self.cursor.fetchall()
                self.release_db_connect()
                return results
            else:
                return []
        except Exception,e:
            if self.logger:
                self.logger.error('get_session_infos_v2 except %s'%(e))
            self.release_db_connect()
            return []
    
    def get_goods_comment_nums(self, goods_id_list):
        if not goods_id_list:
            return {}
        goods_id_list = [ str(i) for i in goods_id_list ]
        self.get_db_connect()
        try:
            sql = 'select goods_id, count(*) from goods_comment where goods_id in (%s) and p_id=0 and status!=2 group by goods_id'%(','.join(goods_id_list))
            count = self.cursor.execute(sql)
            ret_dict = {}
            if count > 0:
                self.cursor.scroll(0, mode='absolute')
                results = self.cursor.fetchall()
                self.release_db_connect()
                for result in results:
                    ret_dict[result[0]] = result[1]
                return ret_dict
            else:
                return {}
        except Exception,e:
            if self.logger:
                self.logger.error('get_goods_comment_nums except %s'%(e))
            self.release_db_connect()
            return {}
            
    def set_user_info(self, user_name, covered_area, house_type):
        self.get_db_connect()
        try:
            sql = 'update customer_user set covered_area=%s,house_type=%s where name=%s'
            insert_fileds = []
            insert_fileds.append(covered_area)
            insert_fileds.append(house_type)
            insert_fileds.append(str(user_name))
            
            count = self.cursor.execute(sql, insert_fileds)
            self.conn.commit()
            self.release_db_connect()
            return True
        except Exception,e:
            self.conn.rollback()
            if self.logger:
                self.logger.error('set_user_info except %s'%(e))
            self.release_db_connect()    
            return False
    
    def add_user_ban(self, user_name, app, state):
        self.get_db_connect()
        try:
            sql = 'insert into ban_user_lists (phone,app,state) values (%s,%s,%s) on duplicate key update state=%s'
            count = self.cursor.execute(sql, [user_name, app, state, state])
            self.conn.commit()
            self.release_db_connect()
            return True
        except Exception,e:
            if self.logger:
                self.logger.error('add_user_ban except %s'%(e))
            self.release_db_connect()
            return False
    
    def get_user_ban_list(self, app):
        self.get_db_connect()
        try:
            sql = 'select phone from ban_user_lists where app=%s and state=1'
            count = self.cursor.execute(sql, [app])
            ret_list = []
            if count > 0:
                self.cursor.scroll(0, mode='absolute')
                results = self.cursor.fetchall()
                self.release_db_connect()
                for result in results:
                    ret_list.append(result[0])
            return ret_list
        except Exception,e:
            if self.logger:
                self.logger.error('get_user_ban_list except %s'%(e))
            self.release_db_connect()
            return []
            
    def add_user_banner_info(self, user_name, business_login = None, business_settle = None, business_disputed = None):
        self.get_db_connect()
        try:
            sql = 'select business_login,business_settle,business_disputed from ban_user_list where phone="%s"'%(str(user_name))
            count = self.cursor.execute(sql)
            if count == 0:
                sql = 'insert into ban_user_list (phone) values ("%s")'%(str(user_name))
                count = self.cursor.execute(sql)
            if business_login is not None:
                sql = 'update ban_user_list set business_login=%s where phone="%s"'%(str(business_login), str(user_name))
                count = self.cursor.execute(sql)
            if business_settle is not None:
                sql = 'update ban_user_list set business_settle=%s where phone="%s"'%(str(business_settle), str(user_name))
                count = self.cursor.execute(sql)
            if business_disputed is not None:
                sql = 'update ban_user_list set business_disputed=%s where phone="%s"'%(str(business_disputed), str(user_name))
                count = self.cursor.execute(sql)
            self.conn.commit()
            self.release_db_connect()
            return True
        except Exception,e:
            self.conn.rollback()
            if self.logger:
                self.logger.error('add_user_banner_info except %s'%(e))
            self.release_db_connect()    
            return False
    
    def get_sales_bind_info(self, phone):
        self.get_db_connect()
        sql = 'select sales_phone,upper_sales_phone,create_time from bind_upper_sales_info where sales_phone="%s"'%(str(phone))
        try:
            count = self.cursor.execute(sql)
            if count == 0:
                self.release_db_connect()
                return {}
            result = self.cursor.fetchone()
            ret_dict = {}
            ret_dict['sales_phone'] = result[0]
            ret_dict['upper_sales_phone'] = result[1]
            ret_dict['create_time'] = int(time.mktime(result[2].timetuple()))
            self.release_db_connect()
            return ret_dict
        except Exception,e:
            if self.logger:
                self.logger.error('get_sales_bind_info except %s'%(e))
            self.release_db_connect()    
            return {}
            
    def get_userinfo_by_user_name(self, user_name):
        self.get_db_connect()
        sql = 'select uid,password,salt,regtime from xw_user where mobile="%s"'%(str(user_name))
        try:
            count = self.cursor.execute(sql)
            if count == 0:
                self.release_db_connect()
                return None
            result = self.cursor.fetchone()
            self.release_db_connect()
            return result
        except Exception,e:
            if self.logger:
                self.logger.error('get_userinfo_by_user_name except %s'%(e))
            self.release_db_connect()    
            return None            

    def get_user_name_by_id(self, user_id):
        self.get_db_connect()
        sql = 'select name from xw_user where uid=%s'%(str(user_id))
        try:
            count = self.cursor.execute(sql)
            if count == 0:
                self.release_db_connect()
                return None
            result = self.cursor.fetchone()
            self.release_db_connect()
            return result[0]
        except Exception,e:
            if self.logger:
                self.logger.error('get_user_name_by_id except %s'%(e))
            self.release_db_connect()    
            return None  
            
    def get_userinfo_by_user_id(self, user_id):
        self.get_db_connect()
        sql = 'select uid,password,salt from xw_user where uid="%s"'%(user_id)
        try:
            count = self.cursor.execute(sql)
            if count == 0:
                self.release_db_connect()
                return None
            result = self.cursor.fetchone()
            self.release_db_connect()
            return result
        except Exception,e:
            if self.logger:
                self.logger.error('get_userinfo_by_user_id except %s'%(e))
            self.release_db_connect()    
            return None  
            
    def get_userinfo_by_user_passwd(self, user_name, passwd, fortest = 0):
        self.get_db_connect()
        if not fortest:
            sql = 'select id from xw_user where username="%s" and userpwd="%s"'%(user_name, passwd)
        else:
            sql = 'select id from xw_user where username="%s"'%(user_name)
        try:
            count = self.cursor.execute(sql)
            if count == 0:
                self.release_db_connect()
                return None
            result = self.cursor.fetchone()
            user_id = result[0]
            self.release_db_connect()
            return user_id
        except Exception,e:
            if self.logger:
                self.logger.error('get_userinfo_by_user_passwd except %s'%(e))
            self.release_db_connect()
            return None
    
    def save_pin_code(self, phone_number, pin_code):
        self.get_db_connect()
        sql = 'insert into user_pin_code (phone_number, pin_code) values (%s,%s)'%(str(phone_number), str(pin_code))
        try:
            count = self.cursor.execute(sql)
            self.conn.commit()
            self.release_db_connect()
            return True
        except Exception,e:
            if self.logger:
                self.logger.error('save_pin_code except %s'%(e))
            self.release_db_connect()    
            return False
            
    def change_user_password(self, user_id, password):
        self.get_db_connect()
        sql = 'update xw_user set password="%s" where uid=%s'%(str(password), str(user_id)) 
        try:
            count = self.cursor.execute(sql)
            self.conn.commit()
            self.release_db_connect()
            return True
        except Exception,e:
            if self.logger:
                self.logger.error('change_user_password except %s'%(e))
            self.release_db_connect()
            return False
    
    def get_user_available_score_money(self, user_id):
        if not user_id:
            return 0
        self.get_db_connect()
        sql = 'select money from user_score where user_id=%s'%(str(user_id))
        try:
            count = self.cursor.execute(sql)
            if count == 0:
                self.release_db_connect()
                return 0
            result = self.cursor.fetchone()
            return result[0]
        except Exception,e:
            if self.logger:
                self.logger.error('get_user_available_score_money except %s'%(e))
            self.release_db_connect()
            return 0
    
    def update_chat_group_total_num(self, group_id):
        self.get_db_connect()
        sql = 'update chat_group_info set total_num=total_num+1 where group_id=%s'%(str(group_id))
        try:
            count = self.cursor.execute(sql)
            self.conn.commit()
            return True
        except Exception,e:
            if self.logger:
                self.logger.error('update_chat_group_total_num except %s'%(e))
            self.release_db_connect()
            return False
            
    def add_chat_group_info(self, user_phone, group_id, send_num, total_num, content, brand_name, state, ctime):
        self.get_db_connect()
        sql = 'insert into chat_group_info (c_phone, group_id, send_num, total_num, content, brand_name, state, ctime) values ("%s",%s,%s,%s,"%s","%s",%s,%s)' \
        %(str(user_phone), str(group_id), str(send_num), str(total_num), content, brand_name, str(state), str(ctime))
        try:
            count = self.cursor.execute(sql)
            self.conn.commit()
            return True
        except Exception,e:
            if self.logger:
                self.logger.error('add_chat_group_info except %s'%(e))
            self.release_db_connect()
            return False

    def update_chat_group_total_num_v2(self, group_id):
        self.get_db_connect()
        sql = 'update chat_group_info_v2 set total_num=total_num+1 where session_id=%s'%(str(group_id))
        try:
            count = self.cursor.execute(sql)
            self.conn.commit()
            return True
        except Exception,e:
            if self.logger:
                self.logger.error('update_chat_group_total_num except %s'%(e))
            self.release_db_connect()
            return False
            
    def add_chat_group_info_v2(self, user_phone, session_id, send_num, total_num, content, brand_name, state, ctime, goods, platform):
        self.get_db_connect()
        sql = 'insert into chat_group_info_v2 (c_phone, session_id, send_num, total_num, content, brand_name, state, ctime,goods,platform) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'
        input_list = []
        input_list.append(str(user_phone))
        input_list.append(str(session_id))
        input_list.append(str(send_num))
        input_list.append(str(total_num))
        input_list.append(content)        
        input_list.append(brand_name)
        input_list.append(str(state))
        input_list.append(str(ctime))
        input_list.append(goods)
        input_list.append(platform)
        try:
            count = self.cursor.execute(sql, input_list)
            self.conn.commit()
            return True
        except Exception,e:
            if self.logger:
                self.logger.error('add_chat_group_info_v2 except %s'%(e))
            self.release_db_connect()
            return False

    def add_chat_single_info(self, send_phone, receive_phone, content, state):
        self.get_db_connect()
        ctime = int(time.time())
        sql = 'insert into chat_single_info_v2 (send_phone, receive_phone, content, state, ctime) values (%s,%s,%s,%s,%s)'
        input_list = []
        input_list.append(str(send_phone))
        input_list.append(str(receive_phone))
        input_list.append(content)
        input_list.append(str(state))
        input_list.append(ctime)
        try:
            count = self.cursor.execute(sql, input_list)
            self.conn.commit()
            return True
        except Exception,e:
            if self.logger:
                self.logger.error('add_chat_single_info except %s'%(e))
            self.release_db_connect()
            return False
            
    def get_chat_group_info_list_v2(self, num=20):
        self.get_db_connect()
        sql = 'select c_phone, session_id, content, ctime, goods from chat_group_info_v2 order by id desc limit %s'%(str(num))
        try:
            count = self.cursor.execute(sql)
            ret_list = []
            if count > 0:
                self.cursor.scroll(0, mode='absolute')
                results = self.cursor.fetchall()
                for result in results:
                    ret_dict = {}
                    ret_dict['phone'] = result[0]
                    ret_dict['id'] = result[1]
                    ret_dict['content'] = result[2]
                    ret_dict['create_time'] = result[3]
                    ret_dict['goods'] = result[4]
                    ret_list.append(ret_dict)
            return ret_list
        except Exception,e:
            if self.logger:
                self.logger.error('get_chat_group_info_list_v2 except %s'%(e))
            self.release_db_connect()
            return []
            
    def add_user_score_money(self, user_id, money, order_number):
        self.get_db_connect()
        sql = 'insert into user_score_info (user_id, money, type, order_number) values (%s,%s,1,"%s")'%(str(user_id), str(money), str(order_number))
        try:
            count = self.cursor.execute(sql)
            self.conn.commit()
        except Exception,e:
            if self.logger:
                self.logger.error('add_user_score_money except %s'%(e))
            self.release_db_connect()
            return 0

    def add_feed_info(self, user_phone, title, content, action, url='', create_time=None):
        self.get_db_connect()
        if not create_time:
            sql = 'insert into feed_list (user_phone, title, content, url, action) values("%s", "%s", "%s", "%s", "%s")'%(str(user_phone), title, content, url, str(action))
        else:
            sql = 'insert into feed_list (user_phone, title, content, url, action, create_time) values("%s", "%s", "%s", "%s", "%s", "%s")'%(str(user_phone), title, content, url, str(action), create_time)
        try:
            count = self.cursor.execute(sql)
            self.conn.commit()
        except Exception,e:
            if self.logger:
                self.logger.error('add_feed_info except %s'%(e))
            self.release_db_connect()
            return 0

    def add_timely(self, content):
        self.get_db_connect()
        sql = 'insert into timely (content) values("%s")' % (content)
        try:
            count = self.cursor.execute(sql)
            self.conn.commit()
        except Exception, e:
            if self.logger:
                self.logger.error('add_timely except %s'%(e))
            self.release_db_connect()
            return 0

    def format_business_info(self, phone_list, title, content, general_data, action):
        ret_list = []
        for phone in phone_list:
            ret_list.append((phone, title, content, general_data, action))

        return ret_list

    def add_feed_info_many(self, business_list, title, content, general_data, action):
        sql = 'insert into feed_list (user_phone, title, content, general_data, action) values(%s, %s, %s, %s,%s)'
        ret_list = self.format_business_info(business_list, title, content, general_data, action)
        try:
            self.get_db_connect()
            count = self.cursor.executemany(sql, ret_list)
            self.conn.commit()
            self.release_db_connect()
        except Exception,e:
            if self.logger:
                self.logger.error('add_feed_info_many except %s'%(e))
            self.release_db_connect()


    def get_band_name_by_sales_phone(self, sales_phone):
        self.get_db_connect()
        try:
            sql = 'select name from user_shop where telephone = "%s"' %(str(sales_phone))
            count = self.cursor.execute(sql)
            if count > 0:
                result = self.cursor.fetchone()
                return result[0]
            else:
                return ''
        except Exception, e:
            if self.logger:
                self.logger.error('get_band_name_by_sales_phone except %s'%(e))
            self.release_db_connect()
            return ''

    def add_user_score_images(self, user_id, phone, image_url_list, order_number, buy_time, buy_price,category, wish_percent_coupon):
        try:
            self.get_db_connect()
            if not order_number:
                order_number = str(int(time.time())) + str(user_id) + str(random.randint(1000,9999))
            sql = 'insert into user_upload_score_images (phone'
            for i in range(0, len(image_url_list)):
                sql += ',image' + str(i+1)
            sql += ',order_number,buy_time,money'
            sql += ') values ('
            sql += '"' + str(phone) + '"'
            for i in range(0, len(image_url_list)):
                image_url = image_url_list[i]
                sql += ',' + '"' + image_url + '"'
            sql += ',' + '"' + order_number + '"'
            sql += ',' + str(buy_time)
            sql += ',' + str(buy_price)
            # sql += ',' + category
            # sql += ',' + wish_percent_coupon
            sql += ')'
            count = self.cursor.execute(sql)

            new_id = self.cursor.lastrowid
            sql = 'update user_upload_score_images set category=%s,percent_coupons=%s where id=%s'
            count = self.cursor.execute(sql, [category, wish_percent_coupon, new_id])
            self.conn.commit()
            return new_id
        except Exception,e:
            self.conn.rollback()
            if self.logger:
                self.logger.error('add_user_score_images except %s'%(e))
            self.release_db_connect()
            return 0
    
    def add_user_score_activity_money(self, user_phone):
        self.get_db_connect()
        sql = 'insert into user_score_activity (user_phone, money, name) values ("%s",25,"inquire_price"),("%s",10,"around"),("%s",20,"recieve_order"),("%s",30,"create_order"),("%s",15,"wallet")' \
        %(str(user_phone),str(user_phone),str(user_phone),str(user_phone),str(user_phone))
        try:
            count = self.cursor.execute(sql)
            self.conn.commit()
            return True
        except Exception,e:
            if self.logger:
                self.logger.error('add_user_score_activity_money except %s'%(e))
            self.release_db_connect()
            return False

    def get_user_score_activity_money(self, user_phone):
        self.get_db_connect()
        try:
            sql = 'select id,money, name, create_time from user_score_activity where user_phone="%s" and state=0'%(str(user_phone))
            count = self.cursor.execute(sql)
            ret_list = []
            if count > 0:
                self.cursor.scroll(0, mode='absolute')
                results = self.cursor.fetchall()
                for result in results:
                    ret_dict = {}
                    ret_dict['id'] = result[0]
                    ret_dict['money'] = result[1]
                    ret_dict['name'] = result[2]
                    ret_dict['create_time'] = int(time.mktime(result[3].timetuple()))
                    ret_list.append(ret_dict)
                self.release_db_connect()
                return ret_list
            else:
                self.release_db_connect()
                return []
        except Exception,e:
            if self.logger:
                self.logger.error('get_user_score_activity_money except %s'%(e))
            self.release_db_connect()
            return []
            
    def draw_user_score_activity_money(self, user_id, user_phone, id):
        self.get_db_connect()
        try:
            sql = 'select money from user_score_activity where id=%s and user_phone="%s" and state=0'%(str(id),str(user_phone))
            count = self.cursor.execute(sql)
            if count <= 0:
                return False
            result = self.cursor.fetchone()
            money = result[0]
            sql = 'update user_score_activity set state=1 where id=%s and user_phone="%s"'%(str(id),str(user_phone))
            count = self.cursor.execute(sql)
            order_number = str(int(time.time())) + str(user_id) + str(random.randint(1000,9999))
            sql = 'insert into user_score_info (user_id, money, type, order_number) values (%s,%s,1,"%s")'%(str(user_id), str(money), str(order_number))
            count = self.cursor.execute(sql)
            self.conn.commit()
            self.release_db_connect()
            return True
        except Exception,e:
            self.conn.rollback()
            if self.logger:
                self.logger.error('draw_user_score_activity_money except %s'%(e))
            self.release_db_connect()
            return False
            
    def format_user_score(self, results, filter_flag):
        func_ret_dict = {}
        ret_unpick_list = []
        ret_picked_list = []
        total_money = 0
        picked_money = 0
        un_picked_money = 0
        filter_flag = int(filter_flag)
        for result in results:
            ret_dict = {}
            ret_dict['id'] = result[0]
            ret_dict['money'] = result[1]
            total_money = total_money + float(ret_dict['money'])
            ret_dict['type'] = result[2]
            ret_dict['state'] = result[3]
            if int(ret_dict['state']) == 1:
                picked_money = picked_money + float(ret_dict['money'])
            else:
                un_picked_money = un_picked_money + float(ret_dict['money'])
                
            ret_dict['create_time'] = int(time.mktime(result[4].timetuple()))
            ret_dict['order_number'] = result[5]
            ret_dict['shared'] = result[6]
            ret_dict['reposited'] = result[7]
            if filter_flag != 3:
                if int(ret_dict['state']) == 0:
                    if filter_flag == 0 or filter_flag == 1:
                        ret_unpick_list.append(ret_dict)
                else:
                    if filter_flag == 0 or filter_flag == 2:
                        ret_picked_list.append(ret_dict)
        ret_unpick_list.extend(ret_picked_list)
        func_ret_dict['items'] = ret_unpick_list
        func_ret_dict['total_money'] = Decimal('%.2f'%(total_money))
        func_ret_dict['picked_money'] = Decimal('%.2f'%(picked_money))
        func_ret_dict['un_picked_money'] = Decimal('%.2f'%(un_picked_money))
        return func_ret_dict
            
    def get_user_score_info(self, user_id, filter_flag = 0):
        self.get_db_connect()
        sql = 'select id, money, type, state, create_time, order_number, shared, reposited from user_score_info where user_id=%s and type < 2 order by id desc'%(str(user_id))
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                self.cursor.scroll(0, mode='absolute')
                results = self.cursor.fetchall()
                return self.format_user_score(results, filter_flag)
        except Exception,e:
            if self.logger:
                self.logger.error('get_coupon_info except %s'%(e))
            return {}

    def format_user_score_v2(self, results, filter_flag):
        func_ret_dict = {}
        ret_unpick_list = []
        ret_picked_list = []
        total_money = 0
        picked_money = 0
        un_picked_money = 0
        filter_flag = int(filter_flag)
        for result in results:
            ret_dict = {}
            ret_dict['id'] = result[0]
            ret_dict['money'] = result[1]
            total_money = total_money + float(ret_dict['money'])
            ret_dict['type'] = result[2]
            if ret_dict['type'] in [6]:
                continue
            ret_dict['state'] = result[3]
            if int(ret_dict['state']) == 1:
                picked_money = picked_money + float(ret_dict['money'])
            elif ret_dict['type'] != 2 and int(result[6]) == 0:
                un_picked_money = un_picked_money + float(ret_dict['money'])
                
            ret_dict['create_time'] = int(time.mktime(result[4].timetuple()))
            ret_dict['order_number'] = result[5]
            ret_dict['verify_state'] = result[6]
            ret_dict['reason'] = result[7]
            if not ret_dict['reason']:
                if ret_dict['verify_state'] == 1:
                    ret_dict['reason'] = u'金额待确定'
            if filter_flag != 3:
                if int(ret_dict['state']) == 0:
                    if filter_flag == 0 or filter_flag == 1:
                        ret_unpick_list.append(ret_dict)
                else:
                    if filter_flag == 0 or filter_flag == 2:
                        ret_picked_list.append(ret_dict)
        ret_unpick_list.extend(ret_picked_list)
        func_ret_dict['items'] = ret_unpick_list
        func_ret_dict['total_money'] = Decimal('%.2f'%(total_money))
        func_ret_dict['picked_money'] = Decimal('%.2f'%(picked_money))
        func_ret_dict['un_picked_money'] = Decimal('%.2f'%(un_picked_money))
        return func_ret_dict
        
    def get_user_score_info_v2(self, user_id, filter_flag = 0):
        self.get_db_connect()
        sql = 'select id, money, type, state, create_time, order_number, verify_state, reason from user_score_info where user_id=%s order by id desc'%(str(user_id))
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                self.cursor.scroll(0, mode='absolute')
                results = self.cursor.fetchall()
                return self.format_user_score_v2(results, filter_flag)
        except Exception,e:
            if self.logger:
                self.logger.error('get_user_score_info_v2 except %s'%(e))
            return {}
    
    ####0 消费获取类 1 赠送类 2 消费记录类 3 晒单类 4邀请消费类 5 需要审核的消费获取类 6 扣减类 7 返还
    def format_user_score_v3(self, results):
        ret_list = []
        for result in results:
            ret_dict = {}
            ret_dict['id'] = result[0]
            ret_dict['money'] = result[1]
            ret_dict['create_time'] = int(time.mktime(result[4].timetuple()))
            ret_dict['order_number'] = result[5]
            type = result[2]
            ret_dict['type'] = type
            if type in [0, 5]:
                ret_dict['desc'] = u'获取'
            elif type == 1:
                ret_dict['desc'] = u'赠送'
                ret_dict['order_number'] = ''
            elif type == 2:
                ret_dict['desc'] = u'立减付'
            elif type == 3:
                ret_dict['desc'] = u'获取（晒单）'
            elif type == 6:
                ret_dict['desc'] = u'扣减'
            elif type == 7:
                ret_dict['desc'] = u'返还'
            else:
                continue
            ret_list.append(ret_dict)
        
        return ret_list
        
    def get_user_score_info_v3(self, user_id):
        self.get_db_connect()
        sql = 'select id, money, type, state, create_time, order_number, verify_state, reason from user_score_info where user_id=%s order by id desc'%(str(user_id))
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                self.cursor.scroll(0, mode='absolute')
                results = self.cursor.fetchall()
                return self.format_user_score_v3(results)
            else:
                return []
        except Exception,e:
            if self.logger:
                self.logger.error('get_user_score_info_v3 except %s'%(e))
            return []

    def get_user_available_score(self, user_id):
        self.get_db_connect()
        sql = 'select money from user_score where user_id=%s'
        try:
            count = self.cursor.execute(sql, [str(user_id)])
            if count > 0:
                result = self.cursor.fetchone()
                return result[0]
            else:
                return 0
        except Exception,e:
            if self.logger:
                self.logger.error('get_user_available_score except %s'%(e))
            return 0
            
    def pull_order_score(self, user_id, order_number):
        if not order_number:
            return False
        self.get_db_connect()
        try:
            sql = 'select state, money, id, type from user_score_info where user_id=%s and order_number="%s" and state=0 and verify_state=0'%(str(user_id), str(order_number))
            count = self.cursor.execute(sql)
            if count == 0:
                self.release_db_connect()
                return False
            self.cursor.scroll(0, mode='absolute')
            results = self.cursor.fetchall()
            success_num = 0
            for result in results:
                id = result[2]
                type = result[3]
                ##type 2 is consume record info
                if int(type) == 2:
                    continue
                sql = 'update user_score_info set state=1 where user_id=%s and id=%s'%(str(user_id), str(id))
                count = self.cursor.execute(sql)
                if count == 0:
                    continue
                money = float(result[1])
                sql = 'insert into user_score (user_id, money) values (%s,%s) on duplicate key update money=money+%s'%(str(user_id), str(money), str(money))
                count = self.cursor.execute(sql)
                success_num += 1
            self.conn.commit()
            self.release_db_connect()
            if success_num > 0:
                return True
            else:
                if self.logger:
                    self.logger.error('pull_order_score failed %s has been pulled'%(str(order_number)))
                return False
        except Exception,e:
            self.conn.rollback()
            if self.logger:
                self.logger.error('pull_order_score except %s'%(e))
            self.release_db_connect()
            return False
    
    def get_given_coupon_info(self, order_number):
        self.get_db_connect()
        sql = 'select usi.money,ui.buy_time,ui.money,ui.verify_state from user_score_info usi inner join user_upload_score_images ui on ui.order_number=usi.order_number where usi.order_number="%s" and type=3'%(str(order_number))
        try:
            count = self.cursor.execute(sql)
            if count == 0:
                self.release_db_connect()
                return {}
            result = self.cursor.fetchone()
            ret_dict = {}
            ret_dict['given_coupon'] = result[0]
            ret_dict['buy_time'] = result[1]
            ret_dict['buy_money'] = result[2]
            ret_dict['state'] = result[3]
            return ret_dict
        except Exception,e:
            if self.logger:
                self.logger.error('get_given_coupon_info except %s'%(e))
            self.release_db_connect()
            return {}
            
    def get_pin_code(self, phone_number):
        self.get_db_connect()
        sql = 'select pin_code from user_pin_code where phone_number="%s"'%(str(phone_number))
        try:
            count = self.cursor.execute(sql)
            if count == 0:
                self.release_db_connect()
                return None
            result = self.cursor.fetchone()
            return result[0]
        except Exception,e:
            if self.logger:
                self.logger.error('save_pin_code except %s'%(e))
            self.release_db_connect()
            return None
    
    def clear_weixin_upop_orders(self):
        now = int(time.time()) - 3600 * 24 * 5
        self.get_db_connect()
        try:
            sql = 'delete from weixin_orders where create_time < %s and state=0'%(str(now))
            count = self.cursor.execute(sql)
            sql = 'delete from upop_orders where create_time < %s and state=0'%(str(now))
            count = self.cursor.execute(sql)            
            self.conn.commit()
            self.release_db_connect()
            return True
        except Exception,e:
            if self.logger:
                self.logger.error('clear_weixin_upop_orders except %s'%(e))
            self.release_db_connect()
            return False
            
    def get_my_pay_discount(self, user_id):
        self.get_db_connect()
        sql = 'select user_id, pay_real from user_stat where user_id=%s'%(str(user_id))
        try:
            count = self.cursor.execute(sql)
            if count == 0:
                self.release_db_connect()
                return (None, None)
            result = self.cursor.fetchone()
            self.release_db_connect()
            return (result[0],result[1])
        except Exception,e:
            if self.logger:
                self.logger.error('get_my_pay_discount except %s'%(e))
            self.release_db_connect()
            return (None, None)
    
    def get_coupon_info(self, user_id, user_name):
        ret_dict = {}
        self.get_db_connect()
        ret_dict['wallet_coupon_num'] = 0
        ret_dict['wallet_coupon_money'] = 0
        ret_dict['imm_coupon_num'] = 0
        ret_dict['imm_coupon_money'] = 0
        sql = 'select coupon from coupon where user_id=%s and state=0'%(str(user_id))
        try:
            count = self.cursor.execute(sql)
            ret_dict['wallet_coupon_num'] = count
            if count > 0:
                self.cursor.scroll(0, mode='absolute')
                results = self.cursor.fetchall()
                for result in results:
                    ret_dict['wallet_coupon_money'] += int(result[0])
        except Exception,e:
            if self.logger:
                self.logger.error('get_coupon_info except %s'%(e))            
            
        sql = 'select coupon from coupons where mobile="%s" and state=0'%(str(user_name))
        try:
            count = self.cursor.execute(sql)
            ret_dict['imm_coupon_num'] = count
            if count > 0:
                self.cursor.scroll(0, mode='absolute')
                results = self.cursor.fetchall()
                for result in results:
                    ret_dict['imm_coupon_money'] += int(result[0])
        except Exception,e:
            if self.logger:
                self.logger.error('get_coupon_info except %s'%(e))
        return ret_dict
                
    def do_register(self, user_name, passwd):
        salt_list = random.sample('zyxwvutsrqponmlkjihgfedcba',4)
        salt = ''.join(salt_list)
        password = hashlib.md5(passwd).hexdigest()
        password = hashlib.md5(password + salt).hexdigest()
        self.get_db_connect()
        sql = 'insert into xw_user (name, password, salt, mobile, status) values ("%s","%s","%s","%s","%s")'%(user_name, password, salt, user_name, '1')
        try:
            count = self.cursor.execute(sql)
            self.conn.commit()
            sql = 'select uid from xw_user where name="%s"'%(user_name)
            count = self.cursor.execute(sql)
            if count == 0:
                self.release_db_connect()
                return None
            result = self.cursor.fetchone()
            self.release_db_connect()
            return result[0]
        except Exception,e:
            if self.logger:
                self.logger.error('do_register except %s'%(e))
            self.release_db_connect()    
            return None
    
    def format_bank_list(self, results):
        ret_list = []
        for result in results:
            ret_dict = {}
            ret_dict['id'] = result[0]
            ret_dict['bank_name'] = result[1]
            ret_list.append(ret_dict)
        return ret_list
        
    
    def get_bank_list(self):
        self.get_db_connect()
        sql = 'select id, bank_name from bank_list'
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                self.cursor.scroll(0, mode='absolute')
                results = self.cursor.fetchall()
                self.release_db_connect()
                return self.format_bank_list(results)
            else:
                self.release_db_connect()
                return []
        except Exception,e:
            if self.logger:
                self.logger.error('get_bank_list except %s'%(e))
            self.release_db_connect()    
            return []
            
    def get_bank_name_by_id(self, id):
        self.get_db_connect()
        sql = 'select bank_name from bank_list where id=%s'%(str(id))
        try:
            count = self.cursor.execute(sql)
            if count == 0:
                self.release_db_connect()
                return None
            result = self.cursor.fetchone()
            self.release_db_connect()
            return result[0]
        except Exception,e:
            if self.logger:
                self.logger.error('get_bank_name_by_id except %s'%(e))
            self.release_db_connect()
            return None        

    def create_invitation_code(self, code, from_code = 0):
        sql = 'insert into invitation_code (code, from_code) values ("%s","%s")'%(str(code), str(from_code))
        self.get_db_connect()
        try:
            count = self.cursor.execute(sql)
            self.conn.commit()
            self.release_db_connect()
            return True
        except Exception,e:
            if self.logger:
                self.logger.error('create_invitation_code except %s'%(e))
            self.release_db_connect()
            return False
    
    def set_user_role(self, user_id, role, privilege = ''):
        sql = 'update user_shop set role="%s",privilege="%s" where user_id=%s'%(str(role), str(privilege), str(user_id))
        self.get_db_connect()        
        try:
            if role:
                sql = 'update user_shop set role="%s" where user_id=%s'%(str(role), str(user_id))
                count = self.cursor.execute(sql)
            if privilege:
                sql = 'update user_shop set privilege="%s" where user_id=%s'%(str(privilege), str(user_id))
                count = self.cursor.execute(sql)                
            self.conn.commit()
            self.release_db_connect() 
            return True    
        except Exception,e:
            if self.logger:
                self.logger.error('set_user_role except %s'%(e))
            self.release_db_connect()    
            return False
    
    def bind_upper_sales(self, sales_phone, upper_sales_phone):
        self.get_db_connect()        
        try:
            sql = 'insert into bind_upper_sales_info (sales_phone,upper_sales_phone) values ("%s","%s")'%(str(sales_phone), str(upper_sales_phone))
            count = self.cursor.execute(sql)
            sql = 'insert into commision_info (money, user_phone, sales_phone, type) values (%s, "%s", "%s", %s)' \
            %('50', sales_phone, upper_sales_phone, '3')
            count = self.cursor.execute(sql)
            self.conn.commit()
            self.release_db_connect() 
            return True    
        except Exception,e:
            self.conn.rollback()
            if self.logger:
                self.logger.error('bind_upper_sales except %s'%(e))
            self.release_db_connect()    
            return False

    def get_bind_upper_sales(self, sales_phone):
        self.get_db_connect()        
        try:
            sql = 'select upper_sales_phone from bind_upper_sales_info where sales_phone="%s"'%(str(sales_phone))
            count = self.cursor.execute(sql)
            if count > 0:
                result = self.cursor.fetchone()
                self.release_db_connect() 
                return result[0]
            else:
                self.release_db_connect()
                return ''
        except Exception,e:
            if self.logger:
                self.logger.error('get_bind_upper_sales except %s'%(e))
            self.release_db_connect()    
            return ''

    def update_business_card(self, user_id, business_card, name):
        self.get_db_connect()
          
        try:
            if name:
                sql = 'update user_shop set name="%s" where user_id=%s' \
                %(name, str(user_id))
                count = self.cursor.execute(sql)
            if business_card:
                sql = 'update user_shop set business_card="%s" where user_id=%s' \
                %(str(business_card), str(user_id))
                count = self.cursor.execute(sql)
            self.conn.commit()
            self.release_db_connect()
            return True
        except Exception,e:
            if self.logger:
                self.logger.error('update_business_card except %s'%(e))
            self.release_db_connect()
            return False
            
    def update_business_user(self, user_id, telephone, shop_id, shop_name,brand_id,brand_name, channel_id, qr_image_url, name='', user_cooperation=''):
        self.get_db_connect()
        try:
            sql = 'update user_shop set shop_id=%s, qr_image="%s",shop_name="%s",brand_id=%s,brand_name="%s",channel_id=%s where user_id=%s' \
            %(str(shop_id), str(qr_image_url), shop_name,str(brand_id),brand_name, str(channel_id), str(user_id))        
            count = self.cursor.execute(sql)
            if name:
                sql = 'update user_shop set name="%s" where user_id=%s'%(name, str(user_id))        
                count = self.cursor.execute(sql)
                
            if user_cooperation:
                sql = 'update user_shop set user_set_cooperation=%s where user_id=%s'%(str(user_cooperation), str(user_id))
                count = self.cursor.execute(sql)
                
            if shop_id:
                sql = 'update user_shop set user_cooperation=0 where user_id=%s'%(str(user_id))
                count = self.cursor.execute(sql)
                
            action_time = str(int(time.time()))
            sql = 'insert into user_action_time (user_phone, modify_material_time) values ("%s", %s) on duplicate key update modify_material_time=%s'%(str(telephone), action_time, action_time)
            count = self.cursor.execute(sql)
            
            self.conn.commit()
            self.release_db_connect()
            return True
        except Exception,e:
            if self.logger:
                self.logger.error('update_business_user except %s'%(e))
            self.release_db_connect()    
            return False

    def get_normal_business_num(self):
        self.get_db_connect()
        sql = 'select count(*) from user_shop where user_state=2'
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                result = self.cursor.fetchone()
                self.release_db_connect()
                return result[0]
            else:
                self.release_db_connect()
                return 0
        except Exception,e:
            if self.logger:
                self.logger.error('get_normal_business_num except %s'%(e))        
            self.release_db_connect()
            return 0
            
    def get_business_payed_order_num(self, user_phone):
        self.get_db_connect()
        sql = 'select count(*) from orders where sales="%s" and state in (1,2)'%(str(user_phone))
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                result = self.cursor.fetchone()
                self.release_db_connect()
                return result[0]
            else:
                self.release_db_connect()
                return 0
        except Exception,e:
            if self.logger:
                self.logger.error('get_business_payed_order_num except %s'%(e))        
            self.release_db_connect()
            return 0

    def get_business_shop_payed_order_num(self, shop_id):
        self.get_db_connect()
        sql = 'select count(*) from orders where shop_id=%s and state in (1,2)'%(str(shop_id))
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                result = self.cursor.fetchone()
                self.release_db_connect()
                return result[0]
            else:
                self.release_db_connect()
                return 0
        except Exception,e:
            if self.logger:
                self.logger.error('get_business_shop_payed_order_num except %s'%(e))        
            self.release_db_connect()
            return 0
            
    def get_business_payed_order_money(self, user_phone):
        self.get_db_connect()
        sql = 'select sum(price_total) from orders where sales="%s" and state in (1,2) and verify_state!=4'%(str(user_phone))
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                result = self.cursor.fetchone()
                self.release_db_connect()
                money = result[0]
                if not money:
                    money = 0
                return money
            else:
                self.release_db_connect()
                return 0
        except Exception,e:
            if self.logger:
                self.logger.error('get_business_payed_order_money except %s'%(e))        
            self.release_db_connect()
            return 0
            
    def get_business_payed_and_sent_order_num(self, user_phone):
        self.get_db_connect()
        sql = 'select count(*) from orders where sales="%s" and (state in (1,2,4) or (creator=1 and state=0 and contract_price > 0.1))'%(str(user_phone))
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                result = self.cursor.fetchone()
                self.release_db_connect()
                return result[0]
            else:
                self.release_db_connect()
                return 0
        except Exception,e:
            if self.logger:
                self.logger.error('get_business_payed_order_num except %s'%(e))        
            self.release_db_connect()
            return 0
            
    def get_business_name_brand(self, phone):
        self.get_db_connect()
        sql = 'select name,brand_name,shop_id, shop_name from user_shop where telephone="%s"'%(str(phone))
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                self.cursor.scroll(0, mode='absolute')
                result = self.cursor.fetchone()
                self.release_db_connect()
                ret_dict = {}
                ret_dict['name'] = result[0]
                brand_name = result[1]
                brand_list = brand_name.split(',')
                brand_name = brand_list[0]
                ret_dict['brand_name'] = result[1]
                ret_dict['shop_name'] = result[3]
                if int(result[2]) > 0:
                    ret_dict['cooperation'] = 1
                else:
                    ret_dict['cooperation'] = 0
                return ret_dict
            else:
                self.release_db_connect()
                return {}
        except Exception,e:
            if self.logger:
                self.logger.error('get_business_name_brand except %s'%(e))        
            self.release_db_connect()
            return {}

    def get_business_shop_id(self, phone):
        self.get_db_connect()
        sql = 'select shop_id from user_shop where telephone="%s"'%(str(phone))
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                self.cursor.scroll(0, mode='absolute')
                result = self.cursor.fetchone()
                self.release_db_connect()
                return result[0]
            else:
                self.release_db_connect()
                return 0
        except Exception,e:
            if self.logger:
                self.logger.error('get_business_shop_id except %s'%(e))        
            self.release_db_connect()
            return 0

    def get_business_user_pre_cooperation(self, phone):
        self.get_db_connect()
        sql = 'select shop_id,shop_name,brand_name,brand_id,channel_id from user_shop where telephone="%s"'%(str(phone))
        try:
            count = self.cursor.execute(sql)
            ret_dict = {}
            if count > 0:
                result = self.cursor.fetchone()
                self.release_db_connect()
                ret_dict['shop_id'] = result[0]
                ret_dict['shop_address'] = result[1]
                ret_dict['brand_name'] = result[2]
                ret_dict['brand_id'] = result[3]
                ret_dict['channel_id'] = result[4]
                ret_dict['channel_name'] = ''
                ret_dict['shop_name'] = ''
                return ret_dict
            else:
                self.release_db_connect()
                return {}
        except Exception,e:
            if self.logger:
                self.logger.error('get_business_user_pre_cooperation except %s'%(e))        
            self.release_db_connect()
            return {}
    
    def get_business_users(self, channel_id=0, last_user_id=0, num=100):
        self.get_db_connect()
        if channel_id:
            sql = 'select user_id from user_shop where channel_id=%s and user_id > %s order by id limit %s'%(str(channel_id), str(last_user_id), str(num))
        else:
            sql = 'select user_id from user_shop where user_id > %s order by id limit %s'%(str(last_user_id), str(num))
        try:
            ret_list = []
            count = self.cursor.execute(sql)
            if count > 0:
                self.cursor.scroll(0, mode='absolute')
                results = self.cursor.fetchall()
                self.release_db_connect()
                for result in results:
                    ret_list.append(result[0])
                return ret_list
            else:
                self.release_db_connect()
                return []
        except Exception,e:
            if self.logger:
                self.logger.error('get_business_users except %s'%(e))        
            self.release_db_connect()
            return []            

    def get_business_phones(self, channel_id=0, last_user_id=0, num=100):
        self.get_db_connect()
        if channel_id:
            sql = 'select user_id,telephone from user_shop where channel_id=%s and user_id > %s order by id limit %s'%(str(channel_id), str(last_user_id), str(num))
        else:
            sql = 'select user_id,telephone from user_shop where user_id > %s order by id limit %s'%(str(last_user_id), str(num))
        try:
            ret_list = []
            max_id = 0
            count = self.cursor.execute(sql)
            if count > 0:
                self.cursor.scroll(0, mode='absolute')
                results = self.cursor.fetchall()
                self.release_db_connect()
                for result in results:
                    if max_id < int(result[0]):
                        max_id = int(result[0])
                    ret_list.append(result[1])
                return (ret_list, max_id)
            else:
                self.release_db_connect()
                return ([], None)
        except Exception,e:
            if self.logger:
                self.logger.error('get_business_phones except %s'%(e))        
            self.release_db_connect()
            return ([], None)

    def get_customer_phones(self, last_user_id=0, num=100):
        self.get_db_connect()
        sql = 'select user_id,name from customer_user where user_id > %s order by id limit %s'%(str(last_user_id), str(num))
        try:
            ret_list = []
            max_id = 0
            count = self.cursor.execute(sql)
            if count > 0:
                self.cursor.scroll(0, mode='absolute')
                results = self.cursor.fetchall()
                self.release_db_connect()
                for result in results:
                    if max_id < int(result[0]):
                        max_id = int(result[0])
                    ret_list.append(result[1])
                return (ret_list, max_id)
            else:
                self.release_db_connect()
                return ([], None)
        except Exception,e:
            if self.logger:
                self.logger.error('get_customer_phones except %s'%(e))        
            self.release_db_connect()
            return ([], None)
            
    def get_invite_num(self, phone):
        self.get_db_connect()
        sql = 'select count(*) from bind_upper_sales_info where upper_sales_phone="%s"'%(str(phone))
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                result = self.cursor.fetchone()
                self.release_db_connect()
                return result[0]
            else:
                self.release_db_connect()
                return 0
        except Exception,e:
            if self.logger:
                self.logger.error('get_invite_num except %s'%(e))        
            self.release_db_connect()
            return 0

    def get_business_user_platform(self, phone):
        self.get_db_connect()
        sql = 'select platform from user_shop where telephone="%s"'%(str(phone))
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                result = self.cursor.fetchone()
                self.release_db_connect()
                return result[0]
            else:
                self.release_db_connect()
                return ''
        except Exception,e:
            if self.logger:
                self.logger.error('get_business_user_platform except %s'%(e))        
            self.release_db_connect()
            return ''

    def get_inquire_business_users(self, category_name):
        self.get_db_connect()
        if len(category_name) == 1:
            sql = 'select telephone from user_shop where user_state in(1,2) and shop_name!="" and category like "%' + category_name[0].encode('utf8','ignore') + '%"'
        elif len(category_name) == 2 and category_name[1]:
            sql = 'select telephone from user_shop where user_state in(1,2) and shop_name!="" and (category like "%' + category_name[0].encode('utf8','ignore') + '%" or category like "%' + category_name[1].encode('utf8','ignore') + '%")'
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                self.cursor.scroll(0, mode='absolute')
                results = self.cursor.fetchall()
                self.release_db_connect()
                ret_list = []
                for result in results:
                    ret_list.append(result[0])
                return ret_list
            else:
                self.release_db_connect()
                return []
        except Exception,e:
            if self.logger:
                self.logger.error('get_inquire_business_users except %s'%(e))        
            self.release_db_connect()
            return []

    def get_inquire_business_users_v2(self, commodity_name):
        self.get_db_connect()
        sql = 'select u.telephone from user_shop u, inner join category_commodity ca where u.category like concat('%',ca.category_name,'%') and ca.commodity_name = "%s" and u.shop_name != ""'%(commodity_name)
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                self.cursor.scroll(0, mode='absolute')
                results = self.cursor.fetchall()
                self.release_db_connect()
                ret_list = []
                for result in results:
                    ret_list.append(result[0])
                return ret_list
            else:
                self.release_db_connect()
                return []
        except Exception,e:
            if self.logger:
                self.logger.error('get_inquire_business_users except %s'%(e))
            self.release_db_connect()
            return []

    def get_talk_user_info(self, user_phone):
        self.get_db_connect()
        sql = 'select name,brand_name,shop_name,telephone,shop_id from user_shop where telephone="%s"'%(str(user_phone))
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                result = self.cursor.fetchone()
                self.release_db_connect()
                ret_dict = {}
                ret_dict['name'] = result[0]
                ret_dict['brand_name'] = result[1]
                ret_dict['shop_name'] = result[2]
                ret_dict['telephone'] = result[3]
                ret_dict['shop_id'] = result[4]
                return ret_dict
            else:
                self.release_db_connect()
                return {}
        except Exception,e:
            if self.logger:
                self.logger.error('get_talk_user_info except %s'%(e))        
            self.release_db_connect()
            return {}      
    def get_business_users_by_shop(self, shop_id, last_user_id=0, num=100):
        self.get_db_connect()
        sql = 'select user_id from user_shop where shop_id=%s and user_id > %s order by id limit %s'%(str(shop_id), str(last_user_id), str(num))

        try:
            ret_list = []
            count = self.cursor.execute(sql)
            if count > 0:
                self.cursor.scroll(0, mode='absolute')
                results = self.cursor.fetchall()
                self.release_db_connect()
                for result in results:
                    ret_list.append(result[0])
                return ret_list
            else:
                self.release_db_connect()
                return []
        except Exception,e:
            if self.logger:
                self.logger.error('get_business_users_by_shop except %s'%(e))        
            self.release_db_connect()
            return []             
        
    def format_order(self, results):
        ret_list = []
        for result in results:
            ret_dict = {}
            ret_dict['id'] = result[0]
            ret_dict['order_number'] = result[1]
            ret_dict['price'] = result[2]
            ret_dict['create_time'] = timeStamp = int(time.mktime(result[3].timetuple()))
            ret_dict['shipping_id'] = result[4]
            ret_dict['price_real'] = result[5]
            ret_list.append(ret_dict)
        return ret_list
    
    def format_order_query(self, user_id, type, start_order_id, order_num):
        if start_order_id == 0:
            sql = 'select id,order_number,price,create_time,shipping_id,price_real from orders where user_id=%s order by id desc limit %s' \
            %(str(user_id), str(order_num))
            
        else:
            sql = 'select id,order_number,price,create_time,shipping_id,price_real from orders where user_id=%s and id < %s order by id desc limit %s' \
            %(str(user_id), str(start_order_id), str(order_num))
            
        if type == ORDER_TYPE_BAO:
            if start_order_id == 0:
                sql = 'select id,order_number,price,create_time,shipping_id,price_real from orders where user_id=%s and flag=1 and pay_type=1 order by id desc limit %s' \
                %(str(user_id), str(order_num))
            else:
                sql = 'select id,order_number,price,create_time,shipping_id,price_real from orders where user_id=%s and id < %s and flag=1 and pay_type=1 order by id desc limit %s' \
                %(str(user_id), str(start_order_id), str(order_num))
        elif type == ORDER_TYPE_IMM:
            if start_order_id == 0:
                sql = 'select id,order_number,price,create_time,shipping_id,price_real from orders where user_id=%s and flag=1 and pay_type=2 order by id desc limit %s' \
                %(str(user_id), str(start_order_id), str(order_num))
            else:
                sql = 'select id,order_number,price,create_time,shipping_id,price_real from orders where user_id=%s and id < %s and flag=1 and pay_type=2 order by id desc limit %s' \
                %(str(user_id), str(start_order_id), str(order_num))                
        return sql
    
    def get_order_by_user_id(self, user_id, type, start_order_id, order_num):
        self.get_db_connect()
        if not start_order_id:
            start_order_id = 0

        sql = self.format_order_query(user_id, type, start_order_id, order_num)
        count = self.cursor.execute(sql)
        if count > 0:
            self.cursor.scroll(0, mode='absolute')
            results = self.cursor.fetchall()
            return self.format_order(results)
        else:
            return []
    
    def update_order_state(self, order_num, state):
        sql = 'update orders set state=%s where order_number="%s"'%(str(state), str(order_num))
        self.get_db_connect()
        try:
            count = self.cursor.execute(sql)
            self.conn.commit()
            self.release_db_connect()
            return True
        except Exception,e:
            if self.logger:
                self.logger.error('update_order_state except %s'%(e))
            self.release_db_connect()    
            return False        
        
    def get_shipping_info(self, max_id = 0, num = 5):
        self.get_db_connect()
        if max_id == 0:
            sql = 'select a.id,a.shop_id,a.user_id,s.channel_id,UNIX_TIMESTAMP(a.create_time),concat(s.city,s.county,s.detail),s.shop_name from shipping_log as a INNER JOIN shop_address_info as s where a.shop_id=s.id order by a.id limit %s'%(str(num))
        else:
            sql = 'select a.id,a.shop_id,a.user_id,s.channel_id,UNIX_TIMESTAMP(a.create_time),concat(s.city,s.county,s.detail),s.shop_name from shipping_log as a INNER JOIN shop_address_info as s where a.shop_id=s.id a.id > %s limit %s'%(str(max_id), str(num))
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                self.cursor.scroll(0, mode='absolute')
                results = self.cursor.fetchall()
                self.release_db_connect()
                return results
            else:
                self.release_db_connect()
                return []
        except Exception,e:
            self.release_db_connect()
            return []
    
    def check_shipping_sync(self, shipping_id, user_id):
        self.get_db_connect()
        sql = 'select id from orders where user_id=%s and shipping_id=%s'%(str(user_id), str(shipping_id))
        count = self.cursor.execute(sql)
        self.release_db_connect()
        if count == 0:
            return True
        else:
            return False
            
    def filter_shipping_info(self, info_list):
        useful_shipping_info = []
        for info in info_list:
            shipping_id = info[0]
            user_id = info[2]
            if not self.check_shipping_sync(shipping_id, user_id):
                continue
            useful_shipping_info.append(info)
        return useful_shipping_info
    
    def get_shop_shipping_name(self, shop_id):
        self.get_db_connect()
        sql = 'select s.shop_name,c.name from shop_address as s inner join channel as c where s.id=%s and s.channel_id=c.id'%(str(shop_id))
        try:
            count = self.cursor.execute(sql)
            if count == 0:
                self.release_db_connect()
                return (None, None)
            result = self.cursor.fetchone()
            self.release_db_connect()
            return (result[0], result[1])
        except Exception,e:
            self.release_db_connect()
            return (None, None)
        
    def format_sync_info(self, info_list):
        ret_list = []
        for info in info_list:
            shipping_id = info[0]
            shop_id = info[1]
            user_id = info[2]
            channel_id = info[3]
            create_time = info[4]
            shop_address = info[5]
            shop_name = info[6]
            order_number = str(create_time) + str(user_id) + str(random.randint(1000,9999))
            channel_shop_dict = self.get_channel_shop_info_by_shop_id(shop_id)
            #(shop_name, channel_name) = self.get_shop_shipping_name(shop_id)
            if not channel_shop_dict:
                continue
            ret_dict = {}
            ret_dict['shipping_id'] = shipping_id
            ret_dict['shop_id'] = shop_id
            ret_dict['user_id'] = user_id
            ret_dict['channel_id'] = channel_id
            ret_dict['order_number'] = order_number
            ret_dict['shop_name'] = shop_name
            ret_dict['channel_name'] = ''
            ret_dict['shop_address'] = shop_address
            ret_dict['brand_id'] = channel_shop_dict['brand_id']
            ret_dict['brand_name'] = channel_shop_dict['brand_name']
            
            ret_list.append(ret_dict)
        return ret_list
        
    def sync_shipping_order(self, info_list):
        self.get_db_connect()
        for info in info_list:
            try:
                sql = 'insert into orders (user_id,order_number,shipping_id,channel_id,channel_name,shop_id,shop_name,shop_address,brand_id,brand_name,user_phone) values (%s,"%s",%s,%s,"%s",%s,"%s","%s",%s,"%s","%s")' \
                %(info['user_id'],info['order_number'],info['shipping_id'],info['channel_id'],info['channel_name'],info['shop_id'],info['shop_name'],info['shop_address'],info['brand_id'],info['brand_name'],info['user_phone'])
                count = self.cursor.execute(sql)
                self.conn.commit()
            except Exception,e:
                if self.logger:
                    self.logger.error('sync_shipping_order except %s'%(e))            
        self.release_db_connect()
    
    def get_order_account_by_time(self, order_number, date):
        self.get_db_connect()
        sql = 'select id, price_total, state from orders_account where order_number="%s" and create_date="%s"'%(str(order_number), date)
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                self.cursor.scroll(0, mode='absolute')
                results = self.cursor.fetchall()
                self.release_db_connect()
                return results
            else:
                self.release_db_connect()
                return []
        except Exception,e:
            self.release_db_connect()
            return []
    
    def get_channel_rebate(self, shop_id):
        self.get_db_connect()
        sql = 'select rebate from channels cs inner join shop_address_info si where si.id=%s and si.channel_id=cs.id'
        try:
            count = self.cursor.execute(sql, [shop_id])
            if count == 0:
                self.release_db_connect()
                return None
            result = self.cursor.fetchone()
            self.release_db_connect()
            return result[0]
        except Exception,e:
            if self.logger:
                self.logger.error('get_channel_rebate except %s'%(e))
            self.release_db_connect()
            return None
            
    def add_order_account(self, order_number, price_total, rebate, state, user_id, user_phone,channel_id,channel_name,shop_id,shop_name,shop_address, sales_id, sales_name,sales,brand_id,brand_name,create_time,create_date):
        sql = 'insert into orders_account (order_number, price_total, rebate, state, user_id, user_phone,channel_id,channel_name,shop_id,shop_name,shop_address, sales_id, sales_name,sales,brand_id,brand_name,create_time,create_date, shipping_id) ' \
        'values ("%s", %s, %s, %s, %s, "%s", %s, "%s", %s, "%s", "%s",%s, "%s", "%s",%s,"%s","%s","%s", 0)' \
        %(order_number, str(price_total), str(rebate), str(state), str(user_id), str(user_phone), str(channel_id), channel_name, str(shop_id), shop_name, shop_address, str(sales_id), sales_name, str(sales), str(brand_id), brand_name, str(create_time), str(create_date))
        self.get_db_connect()
        try:
            count = self.cursor.execute(sql)
            self.conn.commit()
            self.release_db_connect()
            return True
        except Exception,e:
            if self.logger:
                self.logger.error('add_order_account except %s'%(e))
            self.release_db_connect()    
            return False    
    
    def update_order_account(self, order_number, price_total, state, create_date, rebate):
        self.get_db_connect()
        try:
            sql = 'update orders_account set price_total=price_total+%s, state=%s,rebate=%s where order_number="%s" and create_date="%s"' \
            %(str(price_total), str(state), str(rebate), str(order_number), str(create_date))
            count = self.cursor.execute(sql)
            self.conn.commit()
            self.release_db_connect()
            return True
        except Exception,e:
            if self.logger:
                self.logger.error('update_order_account except %s'%(e))
            self.release_db_connect()    
            return False
            
    def decode_contract_images(self, contract_images):
        return contract_images.split('|')
    
    def format_order_verify_state(self, ret_dict, verify_state, reject):
        ####0 表示认证中 1 认证通过 2 认证失败
        if verify_state in [0,1,2,5]:
            ret_dict['verify_state'] = 0
            ret_dict['reject'] = ''
            if verify_state == 2 or verify_state == 5:
                ret_dict['reject'] = reject
        elif verify_state in [3]:
            ret_dict['verify_state'] = 1
            ret_dict['reject'] = ''
        elif verify_state in [4]:
            ret_dict['verify_state'] = 2
            ret_dict['reject'] = reject
        return ret_dict
            
    def format_one_order(self, result, filter_cancel = True):
        if not result:
            return {}
        ret_dict = {}    
        ret_dict['user_id'] = result[0]
        ret_dict['order_number'] = result[1]
        ret_dict['channel_id'] = result[2]
        ret_dict['channel_name'] = result[3]
        ret_dict['shop_id'] = result[4]
        shop_name = result[5]
        shop_info = shop_name.split()
        if len(shop_info) == 2:
            shop_name = shop_info[1]
        ret_dict['shop_name'] = shop_name
        ret_dict['sales'] = result[6]
        ret_dict['price_total'] = result[7]
        ret_dict['price_pre'] = result[8]
        ret_dict['price_real'] = result[9]
        ret_dict['pay_type'] = result[10]
        ret_dict['state'] = result[11]
        if filter_cancel and ret_dict['state'] == 3:
            return {}
        if result[12]:
            ret_dict['create_type'] = ORDER_CREATE_TYPE_GOODS_LOOK
        else:
            ret_dict['create_type'] = ORDER_CREATE_TYPE_OFFLINE
        ret_dict['seq'] = result[13]
        ret_dict['pre_flag'] = result[14]
        ret_dict['shop_address'] = result[15]
        ret_dict['content'] = result[16]
        ret_dict['sales_name'] = result[17]
        ret_dict['brand_id'] = result[18]
        ret_dict['brand_name'] = result[19]
        ret_dict['contract_image1'] = ''
        ret_dict['contract_image2'] = ''
        ret_dict['contract_image3'] = ''
        if not result[20]:
            ret_dict['contract_image_num'] = 0
        else:
            contract_image_list = result[20].split('|')
            contract_image_list = contract_image_list[-3:]
            for i in range(len(contract_image_list)):
                key = 'contract_image' + str(i+1)
                ret_dict[key] = contract_image_list[i]
            ret_dict['contract_image_num'] = len(contract_image_list)
        if len(result) >= 22:
            ret_dict['create_time'] = result[21]
        if len(result) >= 23:
            ret_dict['user_phone'] = result[22]
        if len(result) >= 24:
            ret_dict['contract_price'] = result[23]
        if len(result) >= 25:
            ret_dict['current_price'] = result[24]
        if len(result) >= 26:
            ret_dict['creator'] = result[25]
        if len(result) >= 27:
            ret_dict['coupon'] = result[26]
        if len(result) >= 28:
            ret_dict['pre_cooperation'] = result[27]
        if len(result) >= 29:
            ret_dict['shopping_id'] = result[28]
        if len(result) >= 30:
            ret_dict['customer_type'] = result[29]
        if len(result) >= 31:
            ret_dict['pay_time'] = result[30]
            if ret_dict['pay_time'] == 0:
                ret_dict['pay_time'] = ret_dict['create_time']
        if len(result) >= 32:
            ret_dict['verify_state'] = result[31]
        if len(result) >= 33:
            ret_dict['settle_state'] = result[32]
        if len(result) >= 34:
            reject = result[33]
        if len(result) >= 35:
            given_coupon = float(result[34])
        else:
            given_coupon = 0
        if len(result) >= 36:
            ret_dict['settle_time'] = result[35]
        if len(result) >= 37:
            if result[36]:
                ret_dict['verify_time'] = int(time.mktime(result[36].timetuple()))
            else:
                ret_dict['verify_time'] = 0
        if len(result) >= 38:
            ret_dict['stages_return'] = result[37]
            if float(result[37]) < 0.1:
                ret_dict['stages_returned'] = 0
            else:
                ret_dict['stages_returned'] = 1
            ###only 1 current
            ret_dict['stages_returned'] = 1
        if len(result) >= 39:
            ret_dict['wish_flag'] = result[38]
        if len(result) >= 40:
            ret_dict['wish_percent_coupon'] = result[39] if result[39] else ''
        if len(result) >= 41:
            ret_dict['percent_coupon_id'] = result[40]
        ret_dict = self.format_order_verify_state(ret_dict, ret_dict['verify_state'], reject)
        if ret_dict['price_total'] > 0:
            ret_dict['given_coupon'] = float('%.3f'%(float(ret_dict['price_total']) * 3 / 100))
            ret_dict['xinwo_price'] = float('%.3f'%(float(ret_dict['price_total']) * 95 / 100))
        else:
            ret_dict['given_coupon'] = float('%.3f'%(float(ret_dict['contract_price']) * 3 / 100))
            ret_dict['xinwo_price'] = float('%.3f'%(float(ret_dict['contract_price']) * 95 / 100))
        ret_dict['given_coupon'] = given_coupon
        ret_dict['cut_rate'] = 3
        return ret_dict

    def format_shopping_list(self, results):
        ret_list = []
        for result in results:
            ret_dict = {}
            ret_dict['id'] = result[0]
            ret_dict['create_time'] = int(time.mktime(result[1].timetuple()))
            ret_dict['money'] = result[2]
            ret_dict['content'] = result[3]
            ret_dict['shop_id'] = result[4]
            #ret_dict['sales_phone'] = result[4]
            ret_dict['shop_name'] = result[6]
            ret_dict['brand_name'] = result[7]
            ret_dict['goods_id'] = result[8]
            ret_list.append(ret_dict)
        return ret_list
    
    def remove_item_from_shopping_list(self, shopping_id):
        sql = 'update shopping_list set enable=1 where id=%s'
        self.get_db_connect()
        try:
            count = self.cursor.execute(sql, [shopping_id])
            self.conn.commit()
            self.release_db_connect()
            return True
        except Exception,e:
            if self.logger:
                self.logger.error('remove_item_from_shopping_list except %s'%(e))
            self.release_db_connect()    
            return False 
    
    def get_user_shopping_list(self, user_name):
        self.get_db_connect()
        sql = 'select sl.id, sl.create_time,gl.money,gl.content,gl.shop_id,gl.owner,us.shop_name,us.brand_name,sl.goods_id from shopping_list sl inner join goods_list gl on gl.id=sl.goods_id inner join user_shop us on us.telephone=gl.owner where sl.user_phone=%s and sl.enable=0 order by sl.create_time desc'
        try:
            count = self.cursor.execute(sql, [user_name])
            if count > 0:
                self.cursor.scroll(0, mode='absolute')
                results = self.cursor.fetchall()
                self.release_db_connect()
                return self.format_shopping_list(results)
            else:
                self.release_db_connect()
                return []
        except Exception,e:
            if self.logger:
                self.logger.error('get_user_shopping_list except %s'%(e))         
            self.release_db_connect()
            return []
    
    def format_orders(self, results):
        ret_list = []
        for result in results:
            info = self.format_one_order(result)
            if not info:
                print 'format_orders filter order'
                continue
            ret_list.append(info)
        return ret_list
    
    def format_my_order_all_query(self, user_id, start_order_id, order_num = 5):
        if start_order_id == 0:
            sql = SELECT_ORDER_PREFIX + 'where user_id=%s order by id desc limit %s'%(str(user_id), str(order_num))
        else:
            sql = SELECT_ORDER_PREFIX + 'where user_id=%s and id < %s order by id desc limit %s'%(str(user_id), str(start_order_id), str(order_num))
        return sql    

    def format_my_order_pre_payed_query(self, user_id, start_order_id, order_num = 5):
        if start_order_id == 0:
            sql = SELECT_ORDER_PREFIX + 'where user_id=%s and state=1 order by id desc limit %s'%(str(user_id), str(order_num))
        else:
            sql = SELECT_ORDER_PREFIX + 'where user_id=%s  and state=1 and id < %s order by id desc limit %s'%(str(user_id), str(start_order_id), str(order_num))
        return sql 

    def format_my_order_payed_query(self, user_id, start_order_id, order_num = 5):
        if start_order_id == 0:
            sql = SELECT_ORDER_PREFIX + 'where user_id=%s and state in (1,2) order by id desc limit %s'%(str(user_id), str(order_num))
        else:
            sql = SELECT_ORDER_PREFIX + 'where user_id=%s  and state in (1,2) and id < %s order by id desc limit %s'%(str(user_id), str(start_order_id), str(order_num))
        return sql 
        
    def format_my_order_unpayed_query(self, user_id, start_order_id, order_num = 5):
        if start_order_id == 0:
            sql = SELECT_ORDER_PREFIX + 'where user_id=%s and state=0 order by id desc limit %s'%(str(user_id), str(order_num))
        else:
            sql = SELECT_ORDER_PREFIX + 'where user_id=%s  and state=0 and id < %s order by id desc limit %s'%(str(user_id), str(start_order_id), str(order_num))
        return sql 
        
    def get_my_order_list(self, user_id, start_order_id, order_num, type=0):
        if not start_order_id:
            start_order_id = 0
        self.get_db_connect()
        if type == TYPE_MY_ORDER_ALL:
            sql = self.format_my_order_all_query(user_id, start_order_id, order_num)
        elif type == TYPE_MY_ORDER_PRE_PAYED:
            sql = self.format_my_order_pre_payed_query(user_id, start_order_id, order_num)
        elif type == TYPE_MY_ORDER_UNPAYED:
            sql = self.format_my_order_unpayed_query(user_id, start_order_id, order_num)
        elif type == TYPE_MY_ORDER_PAYED:
            sql = self.format_my_order_payed_query(user_id, start_order_id, order_num)
        else:
            return []
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                self.cursor.scroll(0, mode='absolute')
                results = self.cursor.fetchall()
                self.release_db_connect()
                return self.format_orders(results)
            else:
                self.release_db_connect()
                return []
        except Exception,e:
            if self.logger:
                self.logger.error('get_my_order_list except %s'%(e))         
            self.release_db_connect()
            return []            

    def format_business_order_all_query(self, user_name, start_order_id, order_num = 5):
        if start_order_id == 0:
            sql = SELECT_ORDER_PREFIX + 'where sales="%s" order by id desc limit %s'%(str(user_name), str(order_num))
        else:
            sql = SELECT_ORDER_PREFIX + 'where sales="%s" and id < %s order by id desc limit %s'%(str(user_name), str(start_order_id), str(order_num))
        return sql    
        
    def format_business_order_recently_query(self, user_name, order_num = 10):
        sql = SELECT_ORDER_PREFIX + 'where sales="%s" order by update_time desc limit %s'%(str(user_name), str(order_num))
        return sql    

    def format_business_order_payed_query(self, user_name, start_order_id, order_num = 5):
        if start_order_id == 0:
            sql = SELECT_ORDER_PREFIX + 'where sales="%s" and (state=1 or state=2) order by id desc limit %s'%(str(user_name), str(order_num))
        else:
            sql = SELECT_ORDER_PREFIX + 'where sales="%s" and (state=1 or state=2) and id < %s order by id desc limit %s'%(str(user_name), str(start_order_id), str(order_num))
        return sql 

    def format_business_order_unpayed_query(self, user_name, start_order_id, order_num = 5):
        if start_order_id == 0:
            sql = SELECT_ORDER_PREFIX + 'where sales="%s" and state=0 order by id desc limit %s'%(str(user_name), str(order_num))
        else:
            sql = SELECT_ORDER_PREFIX + 'where sales="%s" and state=0 and id < %s order by id desc limit %s'%(str(user_name), str(start_order_id), str(order_num))
        return sql 
    
    def get_customer_order_count(self, user_name, user_phone):
        self.get_db_connect()
        try:
            sql = SELECT_ORDER_PREFIX + 'where sales="%s" and user_phone="%s"'%(str(user_name), str(user_phone))
            count = self.cursor.execute(sql)
            if count > 0:
                return count
            else:
                self.release_db_connect()
                return 0
        except Exception,e:
            if self.logger:
                self.logger.error('get_customer_order_count except %s'%(e))         
            self.release_db_connect()
            return 0

    def get_user_one_unpay_order(self, user_phone):
        if not user_phone:
            return {}
        sql = SELECT_ORDER_PREFIX + 'where user_phone=%s and state=0 and creator=1 and contract_price > 0 order by id desc limit 1'%(str(user_phone))
        self.get_db_connect()
        try:
            count = self.cursor.execute(sql)
            if count == 0:
                self.release_db_connect()
                return {}
            result = self.cursor.fetchone()
            self.release_db_connect()
            return self.format_one_order(result)
        except Exception,e:
            if self.logger:
                self.logger.error('get_user_one_unpay_order except %s'%(e))
            self.release_db_connect()
            return {}
            
    def get_system_payed_order_list(self, order_num = 20):
        self.get_db_connect()
        try:    
            sql = SELECT_ORDER_PREFIX + 'where state=2 and price_total > 100 and shop_id > 0 order by id desc limit %s'%(str(order_num))
            count = self.cursor.execute(sql)
            if count > 0:
                self.cursor.scroll(0, mode='absolute')
                results = self.cursor.fetchall()
                self.release_db_connect()
                return self.format_orders(results)
            else:
                self.release_db_connect()
                return []
        except Exception,e:
            if self.logger:
                self.logger.error('get_system_payed_order_list except %s'%(e))         
            self.release_db_connect()
            return []
            
    def get_customer_shop_order_count(self, user_name, shop_id):
        self.get_db_connect()
        try:
            sql = SELECT_ORDER_PREFIX + 'where user_phone="%s" and shop_id="%s"'%(str(user_name), str(shop_id))
            count = self.cursor.execute(sql)
            if count > 0:
                return count
            else:
                self.release_db_connect()
                return 0
        except Exception,e:
            if self.logger:
                self.logger.error('get_customer_shop_order_count except %s'%(e))         
            self.release_db_connect()
            return 0
            
    def get_customer_order_list(self, user_name, user_phone):
        sql = SELECT_ORDER_PREFIX + 'where sales="%s" and user_phone="%s" order by id desc'%(str(user_name), str(user_phone))
        self.get_db_connect()
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                self.cursor.scroll(0, mode='absolute')
                results = self.cursor.fetchall()
                self.release_db_connect()
                return self.format_orders(results)
            else:
                self.release_db_connect()
                return []
        except Exception,e:
            if self.logger:
                self.logger.error('get_customer_order_list except %s'%(e))         
            self.release_db_connect()
            return []

    def get_customer_shop_order_list(self, user_name, shop_id):
        sql = SELECT_ORDER_PREFIX + 'where user_phone="%s" and shop_id=%s order by id desc'%(str(user_name), str(shop_id))
        self.get_db_connect()
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                self.cursor.scroll(0, mode='absolute')
                results = self.cursor.fetchall()
                self.release_db_connect()
                return self.format_orders(results)
            else:
                self.release_db_connect()
                return []
        except Exception,e:
            if self.logger:
                self.logger.error('get_customer_shop_order_list except %s'%(e))         
            self.release_db_connect()
            return []

    def get_customer_business_order_pay_list(self, user_name, sales):
        sql = SELECT_ORDER_PREFIX + 'where user_phone=%s and sales=%s and state in (1,2) order by id desc'
        self.get_db_connect()
        try:
            count = self.cursor.execute(sql, [user_name, sales])
            if count > 0:
                self.cursor.scroll(0, mode='absolute')
                results = self.cursor.fetchall()
                self.release_db_connect()
                return self.format_orders(results)
            else:
                self.release_db_connect()
                return []
        except Exception,e:
            if self.logger:
                self.logger.error('get_customer_business_order_pay_list except %s'%(e))         
            self.release_db_connect()
            return []
            
    def get_customer_shop_payed_order_list(self, user_name, shop_id):
        sql = SELECT_ORDER_PREFIX + 'where user_phone="%s" and shop_id=%s and state in (1,2) order by id desc'%(str(user_name), str(shop_id))
        self.get_db_connect()
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                self.cursor.scroll(0, mode='absolute')
                results = self.cursor.fetchall()
                self.release_db_connect()
                return self.format_orders(results)
            else:
                self.release_db_connect()
                return []
        except Exception,e:
            if self.logger:
                self.logger.error('get_customer_shop_order_list except %s'%(e))         
            self.release_db_connect()
            return []

    def get_business_category(self, sales_phone):
        sql = 'select category from user_shop where telephone=%s'%(str(sales_phone))
        self.get_db_connect()
        try:
            count = self.cursor.execute(sql)
            if count == 0:
                self.release_db_connect()
                return None
            result = self.cursor.fetchone()
            self.release_db_connect()
            return result[0]
        except Exception,e:
            if self.logger:
                self.logger.error('get_business_category except %s'%(e))
            self.release_db_connect()
            return None

    def get_business_payed_shop_list(self, user_name):
        sql = 'select shop_id, shop_name, brand_name, price_total,create_time,sales,sales_name from orders where user_phone="%s" and state in (1,2) order by create_time'%(str(user_name))
        self.get_db_connect()
        try:
            count = self.cursor.execute(sql)
            ret_list = []
            if count > 0:
                self.cursor.scroll(0, mode='absolute')
                results = self.cursor.fetchall()
                self.release_db_connect()
                shop_dict = {}
                user_dict = {}
                for result in results:
                    ret_dict = {}
                    ret_dict['shop_id'] = result[0]
                    ret_dict['shop_name'] = result[1]
                    ret_dict['brand_name'] = result[2]
                    ret_dict['price_total'] = result[3]
                    ret_dict['create_time'] = result[4]
                    ret_dict['sales_phone'] = result[5]
                    ret_dict['sales_name'] = result[6]
		    if result[5]:
                        category = self.get_business_category(result[5])
                        ret_dict['category'] = category if category else ''
                    else:
                        ret_dict['category'] = ''
                    if ret_dict['shop_id'] == 0:
                        user_dict[ret_dict['sales_phone']] = ret_dict
                        #ret_list.append(ret_dict)
                    else:
                        shop_dict[ret_dict['shop_id']] = ret_dict
                for key, value in shop_dict.items():
                    ret_list.append(value)
                for key, value in user_dict.items():
                    ret_list.append(value)
                ret_list.sort(key = lambda x:x['create_time'],reverse=True) 
                
                return ret_list
            else:
                self.release_db_connect()
                return []
        except Exception,e:
            if self.logger:
                self.logger.error('get_business_payed_shop_list except %s'%(e))         
            self.release_db_connect()
            return []
    
    def get_order_sales_list(self, user_name):
        sql = 'select sales, shop_name, brand_name, sum(price_total) from orders where user_phone="%s" and state in (1,2) group by sales'%(str(user_name))
        self.get_db_connect()
        try:
            count = self.cursor.execute(sql)
            ret_list = []
            if count > 0:
                self.cursor.scroll(0, mode='absolute')
                results = self.cursor.fetchall()
                self.release_db_connect()
                for result in results:
                    ret_dict = {}
                    ret_dict['sales'] = result[0]
                    ret_dict['shop_name'] = result[1]
                    ret_dict['brand_name'] = result[2]
                    ret_dict['price_total'] = result[3]
                    ret_list.append(ret_dict)
                return ret_list
            else:
                self.release_db_connect()
                return []
        except Exception,e:
            if self.logger:
                self.logger.error('get_order_sales_list except %s'%(e))         
            self.release_db_connect()
            return []

    def get_user_payed_and_recieved_list(self, user_name):
        sql = SELECT_ORDER_PREFIX + 'where user_phone="%s" and (state in (1,2) or (creator=1 and contract_price > 0.1)) order by id desc'%(str(user_name))
        self.get_db_connect()
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                self.cursor.scroll(0, mode='absolute')
                results = self.cursor.fetchall()
                self.release_db_connect()
                return self.format_orders(results)
            else:
                self.release_db_connect()
                return []
        except Exception,e:
            if self.logger:
                self.logger.error('get_user_payed_and_recieved_list except %s'%(e))
            self.release_db_connect()
            return []

    def get_user_non_canceled_list(self, user_name):
        sql = SELECT_ORDER_PREFIX + 'where user_phone="%s" and state!=3 and contract_price > 0.1 order by id desc'%(str(user_name))
        self.get_db_connect()
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                self.cursor.scroll(0, mode='absolute')
                results = self.cursor.fetchall()
                self.release_db_connect()
                return self.format_orders(results)
            else:
                self.release_db_connect()
                return []
        except Exception,e:
            if self.logger:
                self.logger.error('get_user_non_canceled_list except %s'%(e))
            self.release_db_connect()
            return []
            
    def get_sales_orders(self, user_name, sales):
        sql = 'select sales, shop_name, brand_name, price_total,create_time,order_number from orders where user_phone="%s" and sales="%s" and state in (1,2)'%(str(user_name), str(sales))
        self.get_db_connect()
        try:
            count = self.cursor.execute(sql)
            ret_list = []
            if count > 0:
                self.cursor.scroll(0, mode='absolute')
                results = self.cursor.fetchall()
                self.release_db_connect()
                for result in results:
                    ret_dict = {}
                    ret_dict['sales'] = result[0]
                    ret_dict['shop_name'] = result[1]
                    ret_dict['brand_name'] = result[2]
                    ret_dict['price_total'] = result[3]
                    ret_dict['create_time'] = result[4]
                    ret_dict['order_number'] = result[5]
                    ret_list.append(ret_dict)
                return ret_list
            else:
                self.release_db_connect()
                return []
        except Exception,e:
            if self.logger:
                self.logger.error('get_sales_orders except %s'%(e))         
            self.release_db_connect()
            return []
    
    def get_payed_and_sent_order_list(self, user_name, start, num):
        self.get_db_connect()
        if start == 0:
            sql = SELECT_ORDER_PREFIX + 'where sales="%s" and (state in (1,2,4) or (creator=1 and state=0 and contract_price > 0.1)) order by id desc limit %s'%(str(user_name), str(num))
        else:
            sql = SELECT_ORDER_PREFIX + 'where sales="%s" and (state in (1,2,4) or (creator=1 and state=0 and contract_price > 0.1)) and id < %s order by id desc limit %s'%(str(user_name), str(start), str(num))
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                self.cursor.scroll(0, mode='absolute')
                results = self.cursor.fetchall()
                self.release_db_connect()
                return self.format_orders(results)
            else:
                self.release_db_connect()
                return []
        except Exception,e:
            if self.logger:
                self.logger.error('get_payed_and_sent_order_list except %s'%(e))         
            self.release_db_connect()
            return []
            
    def get_business_order_list(self, user_name, start_order_id, order_num, type=0):
        if not start_order_id:
            start_order_id = 0
        self.get_db_connect()
        if type == TYPE_MY_ORDER_ALL:
            sql = self.format_business_order_all_query(user_name, start_order_id, order_num)
        elif type == TYPE_MY_ORDER_PRE_PAYED:
            sql = self.format_business_order_payed_query(user_name, start_order_id, order_num)
        elif type == TYPE_MY_ORDER_UNPAYED:
            sql = self.format_business_order_unpayed_query(user_name, start_order_id, order_num)
        elif type == TYPE_MY_ORDER_RECENT:
            sql = self.format_business_order_recently_query(user_name, order_num)
        else:
            return []
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                self.cursor.scroll(0, mode='absolute')
                results = self.cursor.fetchall()
                self.release_db_connect()
                return self.format_orders(results)
            else:
                self.release_db_connect()
                return []
        except Exception,e:
            if self.logger:
                self.logger.error('get_business_order_list except %s'%(e))         
            self.release_db_connect()
            return []

    def format_business_shop_order_all_query(self, shop_id, start_order_id, order_num = 5):
        if start_order_id == 0:
            sql = SELECT_ORDER_PREFIX + 'where shop_id=%s order by id desc limit %s'%(str(shop_id), str(order_num))
        else:
            sql = SELECT_ORDER_PREFIX + 'where shop_id=%s and id < %s order by id desc limit %s'%(str(shop_id), str(start_order_id), str(order_num))
        return sql    
        
    def format_business_shop_order_recently_query(self, shop_id, order_num = 10):
        sql = SELECT_ORDER_PREFIX + 'where shop_id=%s order by update_time desc limit %s'%(str(shop_id), str(order_num))
        return sql    

    def format_business_shop_order_payed_query(self, shop_id, start_order_id, order_num = 5):
        if start_order_id == 0:
            sql = SELECT_ORDER_PREFIX + 'where shop_id=%s and (state=1 or state=2 or state=4) order by id desc limit %s'%(str(shop_id), str(order_num))
        else:
            sql = SELECT_ORDER_PREFIX + 'where shop_id=%s and (state=1 or state=2 or state=4) and id < %s order by id desc limit %s'%(str(shop_id), str(start_order_id), str(order_num))
        return sql 

    def format_business_shop_order_unpayed_query(self, shop_id, start_order_id, order_num = 5):
        if start_order_id == 0:
            sql = SELECT_ORDER_PREFIX + 'where shop_id=%s and state=0 order by id desc limit %s'%(str(shop_id), str(order_num))
        else:
            sql = SELECT_ORDER_PREFIX + 'where shop_id=%s and state=0 and id < %s order by id desc limit %s'%(str(shop_id), str(start_order_id), str(order_num))
        return sql 
        
    def get_business_shop_order_list(self, shop_id, start_order_id, order_num, type=0):
            if not start_order_id:
                start_order_id = 0
            self.get_db_connect()
            if type == TYPE_MY_ORDER_ALL:
                sql = self.format_business_shop_order_all_query(shop_id, start_order_id, order_num)
            elif type == TYPE_MY_ORDER_PRE_PAYED:
                sql = self.format_business_shop_order_payed_query(shop_id, start_order_id, order_num)
            elif type == TYPE_MY_ORDER_UNPAYED:
                sql = self.format_business_shop_order_unpayed_query(shop_id, start_order_id, order_num)
            elif type == TYPE_MY_ORDER_RECENT:
                sql = self.format_business_shop_order_recently_query(shop_id, order_num)
            else:
                return []
            try:
                count = self.cursor.execute(sql)
                if count > 0:
                    self.cursor.scroll(0, mode='absolute')
                    results = self.cursor.fetchall()
                    self.release_db_connect()
                    return self.format_orders(results)
                else:
                    self.release_db_connect()
                    return []
            except Exception,e:
                if self.logger:
                    self.logger.error('get_business_shop_order_list except %s'%(e))         
                self.release_db_connect()
                return []          
    
    def get_all_brands(self):
        sql = 'select id from brand'
        self.get_db_connect()
        ret_list = []
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                self.cursor.scroll(0, mode='absolute')
                results = self.cursor.fetchall()
                self.release_db_connect()
                for result in results:
                    ret_list.append(result[0])
                return ret_list
            else:
                self.release_db_connect()
                return []
        except Exception,e:
            if self.logger:
                self.logger.error('get_all_brands except %s'%(e))           
            self.release_db_connect()
            return []

    def get_all_channels(self):
        sql = 'select id from channels'
        self.get_db_connect()
        ret_list = []
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                self.cursor.scroll(0, mode='absolute')
                results = self.cursor.fetchall()
                self.release_db_connect()
                for result in results:
                    ret_list.append(result[0])
                return ret_list
            else:
                self.release_db_connect()
                return []
        except Exception,e:
            if self.logger:
                self.logger.error('get_all_channels except %s'%(e))           
            self.release_db_connect()
            return []
            
    def get_invitation_by_channel_id(self, channel_id):
        sql = 'select code,from_code from invitation_code where channel_id=%s'%(str(channel_id))
        self.get_db_connect()
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                result = self.cursor.fetchone()
                self.release_db_connect()
                code = result[0]
                from_code = result[1]
                return (code, from_code)
            else:
                self.release_db_connect()
                return (None, None)
        except Exception,e:
            if self.logger:
                self.logger.error('get_invitation_by_channel_id except %s'%(e))         
            self.release_db_connect()
            return (None, None)       

    def format_order_goods_detail(self, result):
        ret_dict = {}
        ret_dict['id'] = result[0]
        ret_dict['content'] = result[1]
        ret_dict['money'] = result[2]
        ret_dict['image1'] = result[3]
        ret_dict['image2'] = result[4]
        ret_dict['image3'] = result[5]
        ret_dict['image4'] = result[6]
        ret_dict['image5'] = result[7]
        ret_dict['image6'] = result[8]
        
        ret_dict['thumb1'] = result[9]
        ret_dict['thumb2'] = result[10]
        ret_dict['thumb3'] = result[11]
        ret_dict['thumb4'] = result[12]
        ret_dict['thumb5'] = result[13]
        ret_dict['thumb6'] = result[14]
        ret_dict['name'] = result[15]
        ret_dict['sales_phone'] = result[16]
        ret_dict['shop_name'] = result[17]
        return ret_dict
        
    def get_order_goods_detail(self, goods_id):
        self.get_db_connect()
        sql = 'select gl.id,gl.content,gl.money,image1,image2,image3,image4,image5,image6,thumb1,thumb2,thumb3,thumb4,thumb5,thumb6,us.name,us.telephone,us.shop_name from goods_list gl inner join user_shop us on us.telephone=gl.owner where gl.id=%s'
        try:
            count = self.cursor.execute(sql, [goods_id])
            if count == 0:
                self.release_db_connect()
                return {}
            result = self.cursor.fetchone()
            self.release_db_connect()
            return self.format_order_goods_detail(result)
        except Exception,e:
            if self.logger:
                self.logger.error('get_order_goods_detail except %s'%(e))
            self.release_db_connect()    
            return {}
    
    def format_invitation_code(self, result):
        if not result:
            return {}
        ret_dict = {}
        ret_dict['code'] = result[0]
        ret_dict['from_code'] = result[1]
        ret_dict['user_phone'] = result[2]
        ret_dict['channel_id'] = result[3]
        ret_dict['type'] = result[4]
        ret_dict['code_usage_times'] = result[5]
        return ret_dict
        
    def get_invitation_by_from_code(self, code):
        sql = 'select code,from_code,user_phone,channel_id,type,code_usage_times from invitation_code where from_code="%s"'%(str(code))
        self.get_db_connect()
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                result = self.cursor.fetchone()
                self.release_db_connect()
                return self.format_invitation_code(result)
            else:
                self.release_db_connect()
                return {}
        except Exception,e:
            if self.logger:
                self.logger.error('get_invitation_by_from_code except %s'%(e))         
            self.release_db_connect()
            return {}

    def get_invitation_by_code(self, code):
        sql = 'select code,from_code,user_phone,channel_id,type,code_usage_times from invitation_code where code="%s"'%(str(code))
        self.get_db_connect()
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                result = self.cursor.fetchone()
                self.release_db_connect()
                return self.format_invitation_code(result)
            else:
                self.release_db_connect()
                return {}
        except Exception,e:
            if self.logger:
                self.logger.error('get_invitation_by_code except %s'%(e))         
            self.release_db_connect()
            return {}

    def get_invitation_from_phone(self, user_phone):
        sql = 'select code,from_code,user_phone,channel_id,type,code_usage_times from invitation_code where user_phone="%s"'%(str(user_phone))
        self.get_db_connect()
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                result = self.cursor.fetchone()
                self.release_db_connect()
                return self.format_invitation_code(result)
            else:
                self.release_db_connect()
                return {}
        except Exception,e:
            if self.logger:
                self.logger.error('get_invitation_from_phone except %s'%(e))         
            self.release_db_connect()
            return {}
            
    def add_user_invitation(self, user_phone, code, from_code):
        sql = 'insert into invitation_code (user_phone,code,from_code,type) values (%s,"%s","%s",1) on duplicate key update user_phone="%s",from_code="%s",type=1' \
        %(str(user_phone), str(code), str(from_code), str(user_phone), str(from_code))
        self.get_db_connect()
        try:
            count = self.cursor.execute(sql)
            self.conn.commit()
            self.release_db_connect()
            return True
        except Exception,e:
            if self.logger:
                self.logger.error('add_user_invitation except %s'%(e))
            self.release_db_connect()    
            return False

    def update_invitation(self, code, channel_id, channel_name):
        sql = 'update invitation_code set channel_id=%s, channel_name="%s" where code="%s"' \
        %(str(channel_id), channel_name, str(code))
        self.get_db_connect()
        try:
            count = self.cursor.execute(sql)
            self.conn.commit()
            self.release_db_connect()
            return True
        except Exception,e:
            if self.logger:
                self.logger.error('update_invitation except %s'%(e))
            self.release_db_connect()    
            return False
            
    def add_invitation_tops(self, code, channel_id, channel_name):
        sql = 'insert into invitation_code (code,channel_id,from_code,channel_name) values ("%s",%s, 0,"%s") on duplicate key update channel_id=%s,channel_name="%s"'%(str(code), str(channel_id), channel_name, str(channel_id), channel_name)
        self.get_db_connect()
        try:
            count = self.cursor.execute(sql)
            self.conn.commit()
            self.release_db_connect()
            return True
        except Exception,e:
            if self.logger:
                self.logger.error('add_invitation_tops except %s'%(e))
            self.release_db_connect()    
            return False           
    
    def bind_user_code(self, user_phone, sales_phone, settle_mode, settle_account):
        self.get_db_connect()
        try:
            sql = 'insert into user_consume_info (user_phone, sales_phone) values ("%s","%s")' \
            %(user_phone, sales_phone)
            count = self.cursor.execute(sql)
            # sql = 'insert into commision_info (money,user_phone,sales_phone,type,settle_mode,settle_account,update_time) values (%s,"%s","%s",%s,%s,"%s",%s)' \
            # %('200', user_phone, sales_phone, '0', settle_mode, settle_account, str(int(time.time())))
            # count = self.cursor.execute(sql)
            self.conn.commit()
            self.release_db_connect()
            return True
        except Exception,e:
            self.conn.rollback()
            if self.logger:
                self.logger.error('bind_user_code except %s'%(e))
            self.release_db_connect()    
            return False
            
    def update_order_contract_image(self, contract_images, order_number, user_phone, sales):
        self.get_db_connect()
        try:
            sql = 'update orders set contract_images="%s" where order_number="%s"'%(contract_images, order_number)
            count = self.cursor.execute(sql)
            sql = 'select verify_state from orders where order_number="%s"'%(order_number)
            count = self.cursor.execute(sql)
            if count > 0:
                result = self.cursor.fetchone()
                verify_state = result[0]
                ####  '''0''=>''客服审核中'', ''1''=>''风控审核中'', ''2''=>''客服驳回''  ''5''=>''风控驳回'''
                if verify_state == 2 or verify_state == 5:
                    if verify_state == 2:
                        sql = 'update orders set verify_state=0,reject="" where order_number="%s"'%(order_number)
                        count = self.cursor.execute(sql)
                    elif verify_state == 5:
                        sql = 'update orders set verify_state=1,reject="" where order_number="%s"'%(order_number)
                        count = self.cursor.execute(sql)
                    sql = 'update commision_info set settle_state=0 where user_phone="%s" and sales_phone="%s" and order_number="%s"'%(str(user_phone), str(sales), str(order_number))
                    count = self.cursor.execute(sql)
            self.conn.commit()
            self.release_db_connect()
            return True
        except Exception,e:
            if self.logger:
                self.logger.error('update_order_contract_image except %s'%(e))
            self.release_db_connect()    
            return False

    def get_contract_images_by_order_number(self, order_number):
        sql = 'select contract_images from orders where order_number="%s"' % (order_number)
        self.get_db_connect()
        try:
            count = self.cursor.execute(sql)
            order_dict = {}
            if count > 0:
                result = self.cursor.fetchone()
                self.release_db_connect()
                order_dict['contract_images'] = result[0]
                return order_dict
            else:
                self.release_db_connect()
                return {}
        except Exception,e:
            if self.logger:
                self.logger.error('get_contract_images_by_order_number except %s'%(e))
            self.release_db_connect()
            return {}  

    def check_user_order(self, user_id, order_number, shop_id = 0):
        self.get_db_connect()
        sql = 'select user_id,shop_id from orders where order_number="%s"'%(str(order_number))
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                result = self.cursor.fetchone()
                self.release_db_connect()
                select_user_id = result[0]
                if str(select_user_id) == str(user_id):
                    return True
                else:
                    return False
                if str(shop_id) == str(result[1]):
                    return True
                else:
                    return False
            else:
                self.release_db_connect()
                return False
        except Exception,e:
            if self.logger:
                self.logger.error('check_user_order except %s'%(e))         
            self.release_db_connect()
            return False
    
    def get_user_consume_info(self, user_phone):
        self.get_db_connect()
        sql = 'select user_phone,sales_phone,upper_sales_phone,consume_money,reward_2000,create_time from user_consume_info where user_phone="%s"'%(str(user_phone))
        try:
            ret_dict = {}
            count = self.cursor.execute(sql)        
            if count > 0:
                result = self.cursor.fetchone()
                ret_dict['user_phone'] = result[0]
                ret_dict['sales_phone'] = result[1]
                ret_dict['upper_sales_phone'] = result[2]
                ret_dict['consume_money'] = result[3]
                ret_dict['reward_2000'] = result[4]
                ret_dict['create_time'] = int(time.mktime(result[5].timetuple()))
            self.release_db_connect()
            return ret_dict
        except Exception,e:
            if self.logger:
                self.logger.error('get_user_consume_info except %s'%(e))         
            self.release_db_connect()
            return {}
            
    def update_user_consume(self, user_phone, money):
        sql = 'update user_consume_info set consume_money=consume_money+%s where user_phone="%s"'%(str(money), str(user_phone))
        self.get_db_connect()
        try:
            count = self.cursor.execute(sql)
            self.conn.commit()
            if count > 0:
                sql = 'select consume_money from user_consume_info where user_phone="%s"'%(str(user_phone))
                count = self.cursor.execute(sql)
                if count > 0:
                    result = self.cursor.fetchone()
                    new_consume_money = float(result[0])
                else:
                    new_consume_money = 0
            else:
                new_consume_money = 0
            self.release_db_connect()
            return new_consume_money
        except Exception,e:
            if self.logger:
                self.logger.error('update_user_consume except %s'%(e))
            self.release_db_connect()    
            return 0
    
    def check_upper_sales_phone_commision(self, sales_phone, upper_sales_phone):
        self.get_db_connect()
        try:
            sql = 'select user_phone from user_consume_info where sales_phone="%s" and upper_sales_phone="%s" and reward_2000="do"'
            count = self.cursor.execute(sql)
            if count > 0:
                self.release_db_connect()
                return False
            self.release_db_connect()
            return True
        except Exception,e:
            if self.logger:
                self.logger.error('check_upper_sales_phone_commision except %s'%(e))
            self.release_db_connect()    
            return False
    
    def get_settle_mode_account(self, sales_phone):
        sql = 'select bank_number, zhifubao_account, phone_recharge from user_shop where telephone="%s"'%(str(sales_phone))
        self.get_db_connect()
        try:
            ret_dict = {}
            settle_mode = 2
            settle_account = str(sales_phone)
            count = self.cursor.execute(sql)
            if count > 0:
                result = self.cursor.fetchone()
                if result[0]:
                    settle_mode = 0
                    settle_account = result[0]
                if result[1]:
                    settle_mode = 1
                    settle_account = result[1]
                if result[2]:
                    settle_mode = 2
                    settle_account = result[2]
            self.release_db_connect()
            return (settle_mode, settle_account)
        except Exception,e:
            if self.logger:
                self.logger.error('get_settle_mode_account except %s'%(e))         
            self.release_db_connect()
            return ('', '')
            
    def record_user_commision(self, user_phone, sales_phone, money, settle_mode, settle_account):
        self.get_db_connect()
        try:
            if not sales_phone:
                return False
            sql = 'insert into commision_info (money,user_phone,sales_phone,type,callback_state,settle_state,settle_mode,settle_account,update_time) values (%s,"%s","%s",%s,%s,%s,"%s","%s",%s)' \
            %(str(money), str(user_phone), str(sales_phone), '1','1','2', str(settle_mode), str(settle_account), str(int(time.time())))        
            count = self.cursor.execute(sql)
            sql = 'update user_consume_info set reward_2000="do" where user_phone="%s"'%(str(user_phone))
            count = self.cursor.execute(sql)
            self.conn.commit()
            self.release_db_connect()
            return True
        except Exception,e:
            self.conn.rollback()
            if self.logger:
                self.logger.error('record_user_commision except %s'%(e))
            self.release_db_connect()    
            return False

    def get_commision_settle_phone(self, settle_id):
        self.get_db_connect()
        try:
            sql = 'select sales_phone from commision_settle where id=%s'%(str(settle_id))
            count = self.cursor.execute(sql)
            if count > 0:
                result = self.cursor.fetchone()
                return result[0]
            self.release_db_connect()
            return ''
        except Exception,e:
            if self.logger:
                self.logger.error('get_commision_settle except %s'%(e))
            self.release_db_connect()    
            return ''
    
    def get_order_reward_money(self, order_number):
        self.get_db_connect()
        sql = 'select substring_index(lottery_name,"|",1) from lottery_multi_list where order_number="%s" and state=1'%(str(order_number))
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                result = self.cursor.fetchone()
                self.release_db_connect()
                if not result[0]:
                    return 0
                return result[0]
            else:
                self.release_db_connect()
                return 0
        except Exception,e:
            if self.logger:
                self.logger.error('get_order_reward_money except %s'%(e))         
            self.release_db_connect()
            return 0
            
    def get_order_detail(self, order_number):
        self.get_db_connect()
        sql = SELECT_ORDER_PREFIX + 'where order_number="%s"'%(str(order_number))
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                result = self.cursor.fetchone()
                self.release_db_connect()
                return self.format_one_order(result, False)
            else:
                self.release_db_connect()
                return {}
        except Exception,e:
            if self.logger:
                self.logger.error('get_order_detail except %s'%(e))         
            self.release_db_connect()
            return {}
    
    def update_order(self, order_number, current_price = 0):
        self.get_db_connect()
        try:
            if current_price:
                sql = 'update orders set current_price=%s where order_number="%s"'%(str(current_price), str(order_number))
                count = self.cursor.execute(sql)
            self.conn.commit()
            self.release_db_connect()
            return True
        except Exception,e:
            if self.logger:
                self.logger.error('update_order except %s'%(e))
            self.release_db_connect()
            return False

    def format_shop_addr(self, city, county, detail):
        addr = ''
        if detail.find(city) == -1:
            addr += city
        if detail.find(county) == -1:
            addr += county
        addr += detail
        return addr
        
    def get_channel_shop_info_by_shop_id(self, shop_id):
        self.get_db_connect()
        ret_dict = {}
        sql = 'select s.shop_name,s.city,s.county,s.detail,s.channel_id,b.id,group_concat(b.title),cs.id from shop_address_info as s inner join shopaddr_brand as sb inner join brand as b left join channels cs on cs.id=s.channel_id where s.id=%s and s.id=sb.shopaddr_id and sb.brand_id=b.id group by s.detail'%(str(shop_id))
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                result = self.cursor.fetchone()
                self.release_db_connect()
                ret_dict['shop_name'] = result[0]
                #ret_dict['shop_address'] = result[1]
                ret_dict['shop_address'] = self.format_shop_addr(result[1], result[2], result[3])
                ret_dict['channel_id'] = result[4]
                ret_dict['channel_name'] = ''
                ret_dict['brand_id'] = result[5]
                brand_name = result[6]
                if brand_name:
                    brand_name = ','.join(list(set(brand_name.split(','))))
                ret_dict['brand_name'] = brand_name
                ret_dict['shop_id'] = shop_id
                if result[7]:
                    ret_dict['cooperation'] = 1
                else:
                    ret_dict['cooperation'] = 0
                return ret_dict
            else:
                self.release_db_connect()
                return {}
        except Exception,e:
            if self.logger:
                self.logger.error('get_channel_shop_info_by_shop_id except %s'%(e))        
            self.release_db_connect()
            return {}
            
    def create_order(self, user_id, channel_id, channel_name, shop_id, shop_name, shop_address, order_number, sales, content,sales_name,brand_id,brand_name,user_phone,contract_price=0,current_price=0, creator=0, pre_cooperation=0,customer_type=0,shopping_id=0, contract_images='', promoter=''):
        self.get_db_connect()
        if not contract_images:
            sql = 'insert into orders (user_id,order_number,channel_id,channel_name,shop_id,shop_name,sales,shop_address,content,sales_name,brand_id,brand_name,user_phone,create_time,contract_price,current_price,creator,pre_cooperation,customer_type,shopping_id,promoter) \
            values (%s,"%s",%s,"%s",%s,"%s","%s","%s","%s","%s",%s,"%s","%s",%s,%s,%s,%s,%s,%s,%s,"%s")' \
            %(user_id, order_number, channel_id, channel_name, shop_id, shop_name, sales,shop_address,content,sales_name, str(brand_id), brand_name, user_phone, str(int(time.time())), str(contract_price), str(current_price), str(creator), str(pre_cooperation), str(customer_type), str(shopping_id), str(promoter))
        else:
            sql = 'insert into orders (user_id,order_number,channel_id,channel_name,shop_id,shop_name,sales,shop_address,content,sales_name,brand_id,brand_name,user_phone,contract_images,create_time,contract_price,current_price,creator,pre_cooperation,customer_type,shopping_id,promoter) \
            values (%s,"%s",%s,"%s",%s,"%s","%s","%s","%s","%s",%s,"%s","%s","%s",%s,%s,%s,%s,%s,%s,%s,"%s")' \
            %(user_id, order_number, channel_id, channel_name, shop_id, shop_name, sales,shop_address,content,sales_name, str(brand_id), brand_name, user_phone, str(contract_images),str(int(time.time())), str(contract_price), str(current_price), str(creator), str(pre_cooperation), str(customer_type), str(shopping_id), str(promoter))
        try:
            self.logger.error(sql)
            count = self.cursor.execute(sql)
            self.conn.commit()
            self.release_db_connect()
            return True
        except Exception,e:
            if self.logger:
                self.logger.error('create_order except %s'%(e))
            self.release_db_connect()
            return False      

    def get_business_send_order_list(self, user_name):
        sql = self.format_business_send_order_list(user_name)
        self.get_db_connect()
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                self.cursor.scroll(0, mode='absolute')
                results = self.cursor.fetchall()
                self.release_db_connect()
                return self.format_orders(results)
            else:
                self.release_db_connect()
                return []
        except Exception,e:
            if self.logger:
                self.logger.error('get_business_send_order_list except %s'%(e))
            self.release_db_connect()    
            return []

    def format_business_send_order_list(self, user_name):
        sql = SELECT_ORDER_PREFIX + 'where user_phone="%s" and creator=1 and state=0 and create_time > 1433520000 order by update_time desc'%(str(user_name))
        return sql  
        
    def format_all_pay_sql(self, order_num, money, content, flag=1, total_money = 0, coupon = 0):
        if total_money == 0:
            total_money = money
        pay_time = int(time.time())
        if content:
            sql = 'update orders set state=2,price_total=%s,price_real=%s,price_pre=%s,content="%s",flag=%s,coupon=%s,pay_time=%s where order_number="%s"'%(str(total_money), str(money), str(money), content, str(flag), str(coupon), pay_time, order_num)
        else:
            sql = 'update orders set state=2,price_total=%s,price_real=%s,price_pre=%s,flag=%s,coupon=%s,pay_time=%s where order_number="%s"'%(str(total_money), str(money), str(money), str(flag),str(coupon), pay_time, order_num)
        return sql

    def format_subscribe_pay_sql(self, order_num, money, content, flag=1, total_money = 0, coupon = 0):
        if total_money == 0:
            total_money = money
        pay_time = int(time.time())
        if content:
                sql = 'update orders set state=1,price_total=price_total+%s,price_real=price_real+%s,price_pre=price_pre+%s,price_pre_detail=concat(price_pre_detail, "%s"),content="%s",pre_flag=1,flag=%s,coupon=coupon+%s,pay_time=%s where order_number="%s"'%(str(total_money), str(money), str(money), '|' + str(money), content, str(flag),str(coupon),pay_time, order_num)        
        else:
            sql = 'update orders set state=1,price_total=price_total+%s,price_real=price_real+%s,price_pre=price_pre+%s,price_pre_detail=concat(price_pre_detail, "%s"),pre_flag=1,flag=%s,coupon=coupon+%s,pay_time=%s where order_number="%s"'%(str(total_money), str(money), str(money), '|' + str(money), str(flag),str(coupon),pay_time, order_num)
        return sql

    def format_tail_pay_sql(self, order_num, money, content, flag=1, total_money = 0, coupon = 0):
        if total_money == 0:
            total_money = money    
        if content:
            sql = 'update orders set state=2,price_real=price_real+%s, price_total=price_total+%s, content="%s",flag=%s,coupon=coupon+%s where order_number="%s"'%(str(money),str(total_money), content, str(flag),str(coupon),order_num)        
        else:
            sql = 'update orders set state=2,price_real=price_real+%s, price_total=price_total+%s,flag=%s,coupon=coupon+%s where order_number="%s"'%(str(money), str(total_money), str(flag),str(coupon),order_num)
        return sql
    
    def format_orders_info_query(self, user_id, order_number,related_order_number,type,money,pay_type,coupon = 0, price_total=0):
        money = float(money)
        coupon = float(coupon)
        if type == 0:
            cut_money = 0
            cut_rate = 0
            settle_rate = 0
            settle_money = 0
            ###use coupon only
            if money < 0.00001 and coupon > 0:
                type = 3
        elif type == 1 or type == 4:
            cut_money = float('%.2f'%((money + coupon) / float(19))) + coupon
            cut_rate = 5
            settle_rate = 1
            settle_money = float('%.2f'%(money * settle_rate / float(100)))
            if settle_money < 0.08:
                settle_money = 0.08
        elif type == 2:
            cut_money = float('%.2f'%((money + coupon) / float(19))) + coupon
            cut_rate = 5
            settle_rate = 0.6
            settle_money = float('%.2f'%(money * settle_rate / float(100)))
            if settle_money < 0.08:
                settle_money = 0.08
        if self.logger:
            self.logger.info('format_orders_info_query %s'%(str(price_total)))        
        sql = 'insert into orders_info (user_id,order_number,related_order_number,type,money,pay_type,cut_money,cut_rate,settle_rate,settle_money,coupon,price_total) values (%s,"%s","%s",%s,%s,%s,%s,%s,%s,%s,%s,%s)' \
        %(str(user_id), str(order_number), str(related_order_number), str(type), str(money), str(pay_type), str(cut_money),str(cut_rate),str(settle_rate),str(settle_money),str(coupon),str(price_total))
        return sql
        
    def format_coupon_usage(self, user_id, coupon):
        return 'update user_score set money = money-%s where user_id=%s'%(str(coupon), str(user_id))
    
    def record_coupon_usage(self, user_id, coupon, cursor, order_number = ''):
        sql = 'update user_score set money = money-%s where user_id=%s'%(str(coupon), str(user_id))
        cursor.execute(sql)
        if not order_number:
            order_number = str(int(time.time())) + str(user_id) + str(random.randint(1000,9999))
        sql = 'insert into user_score_info (user_id, money, type, order_number) values (%s,%s,%s,"%s")' \
        %(str(user_id), str(coupon), '2', order_number)
        cursor.execute(sql)
        
    def check_order_commission(self, order_number):
        self.get_db_connect()
        try:
            sql = 'select order_number,settle_state,create_time from orders_info where related_order_number="%s"'%(str(order_number))
            count = self.cursor.execute(sql)
            if count == 0:
                if self.logger:
                    self.logger.info('check_order_commission can not find for %s'%(str(order_number)))              
                self.release_db_connect()
                return False
            result = self.cursor.fetchone()
            orig_order_number = result[0]
            settle_state = result[1]
            create_time = result[2]
            if settle_state != 'done':
                if self.logger:
                    self.logger.info('check_order_commission not done for %s'%(str(order_number)))  
                self.release_db_connect()
                return False
            current_create_time = create_time.date()
            tomorrow_create_time = current_create_time + timedelta(days=1)
            sql = 'select order_number, related_order_number, if(settle_state="undo", 0,1) from orders_info where order_number="%s" and create_time > "%s" and create_time < "%s"'%(str(orig_order_number), str(current_create_time), str(tomorrow_create_time))
            count = self.cursor.execute(sql)
            if count == 0:
                self.release_db_connect()
                return False
            self.cursor.scroll(0, mode='absolute')
            results = self.cursor.fetchall()
            total_settle_state = 1
            for result in results:
                total_settle_state &= result[2]
            if total_settle_state == 1:
                sql = 'update orders_account set state=4 where order_number="%s" and create_date="%s"'%(str(orig_order_number), current_create_time)
                count = self.cursor.execute(sql)
                settle_time = int(time.time())
                sql = 'update orders set settle_state=1,settle_time=%s where order_number="%s"'%(str(settle_time), str(orig_order_number))
                count = self.cursor.execute(sql)
                self.conn.commit()
        except Exception,e:
            if self.logger:
                self.logger.error('check_order_commission except %s'%(e))
            self.release_db_connect()
            return False
    
    def get_order_number_by_orders_info_related_order(self, order_number):
        self.get_db_connect()
        sql = 'select order_number from orders_info where related_order_number="%s"'%(str(order_number))
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                result = self.cursor.fetchone()
                self.release_db_connect()
                return result[0]
            else:
                self.release_db_connect()
                return ''
        except Exception,e:
            if self.logger:
                self.logger.error('get_order_number_by_orders_info_related_order except %s'%(e))        
            self.release_db_connect()
            return ''
            
    def change_order_commission(self, order_number, settle_state, settle_date, settle_content, invoice_state, invoice_date, sales_interest, order_type):
        self.get_db_connect()
        try:
            if settle_state:
                sql = 'update orders_info set settle_state="%s" where related_order_number="%s"'%(str(settle_state), str(order_number))
                count = self.cursor.execute(sql)
            if settle_date:
                sql = 'update orders_info set settle_date=%s where related_order_number="%s"'%(str(settle_date), str(order_number))
                count = self.cursor.execute(sql)  
            if settle_content:
                sql = 'update orders_info set settle_content="%s" where related_order_number="%s"'%(settle_content, str(order_number))
                count = self.cursor.execute(sql) 
            if invoice_state:
                sql = 'update orders_info set invoice_state="%s" where related_order_number="%s"'%(str(invoice_state), str(order_number))
                count = self.cursor.execute(sql) 
            if invoice_date:
                sql = 'update orders_info set invoice_date=%s where related_order_number="%s"'%(str(invoice_date), str(order_number))
                count = self.cursor.execute(sql) 
            if sales_interest:
                sql = 'update orders_info set sales_interest=%s where related_order_number="%s"'%(str(sales_interest), str(order_number))
                count = self.cursor.execute(sql) 
            if order_type:
                sql = 'update orders_info set order_type="%s" where related_order_number="%s"'%(str(order_type), str(order_number))
                count = self.cursor.execute(sql)                 
           
            self.conn.commit()
            self.release_db_connect()
            if self.logger:
                self.logger.info('change_order_commission ok')
            return True
        except Exception,e:
            if self.logger:
                self.logger.error('change_order_commission except %s'%(e))
            self.release_db_connect()
            return False
            
    def test_orders_info_data(self, user_id, order_number,related_order_number,type,money,pay_type):
        self.get_db_connect()
        sql = self.format_orders_info_query(user_id, order_number,related_order_number,type,money,pay_type)
        try:
            count = self.cursor.execute(sql)
            self.conn.commit()
            self.release_db_connect()
            if self.logger:
                self.logger.info('test_orders_info_data ok')
            return True
        except Exception,e:
            if self.logger:
                self.logger.error('test_orders_info_data except %s'%(e))
            self.release_db_connect()
            return False
            
    def pay_order_offline(self, user_id, order_num, total_money, money, type, content, coupon = 0, flag = 1):
        from warnings import filterwarnings  
        filterwarnings('error', category = MySQLdb.Warning) 
        self.get_db_connect()
        try:
            if type == PAY_ORDER_TYPE_ALL:
                sql = self.format_all_pay_sql(order_num, money, content, flag, total_money, coupon)
            elif type == PAY_ORDER_TYPE_SUBSCRIBE:
                sql = self.format_subscribe_pay_sql(order_num, money, content, flag, total_money, coupon)
            elif type == PAY_ORDER_TYPE_TAIL:
                sql = self.format_tail_pay_sql(order_num, money, content, flag, total_money, coupon)
            else:
                return False

            count = self.cursor.execute(sql)
            
            
            self.conn.commit()
            self.release_db_connect()
            if self.logger:
                self.logger.info('pay_order_offline ok')
            if count > 0:
                return True
            else:
                return False
        except MySQLdb.Warning,w:
            self.conn.rollback()
            if self.logger:
                self.logger.error('pay_order_offline except %s'%(w))
            self.release_db_connect()
            return False
        except Exception,e:
            self.conn.rollback()
            if self.logger:
                self.logger.error('pay_order_offline except %s'%(e))
            self.release_db_connect()
            return False

    def pay_order(self, user_id, order_num, total_money, money, type, content, coupon = 0, flag = 1):
        from warnings import filterwarnings  
        filterwarnings('error', category = MySQLdb.Warning) 
        self.get_db_connect()
        try:
            if type == PAY_ORDER_TYPE_ALL:
                sql = self.format_all_pay_sql(order_num, money, content, flag, total_money, coupon)
            elif type == PAY_ORDER_TYPE_SUBSCRIBE:
                sql = self.format_subscribe_pay_sql(order_num, money, content, flag, total_money, coupon)
            elif type == PAY_ORDER_TYPE_TAIL:
                sql = self.format_tail_pay_sql(order_num, money, content, flag, total_money, coupon)
            else:
                return False

            count = self.cursor.execute(sql)
            related_order_number = order_num + str(random.randint(10000,99999))
            sql = self.format_orders_info_query(user_id, order_num, related_order_number, 0, money, type, coupon, total_money)
            count = self.cursor.execute(sql)
            if coupon > 0.000001:
                self.record_coupon_usage(user_id, coupon, self.cursor, order_num)
            if money > 0:
                sql = 'insert into user_stat (user_id, wallet_consume) values (%s,%s) on duplicate key update wallet_consume= wallet_consume + %s'%(str(user_id), str(money), str(money))
                count = self.cursor.execute(sql)
            self.conn.commit()
            self.release_db_connect()
            if self.logger:
                self.logger.info('pay_order ok')
            return True
        except MySQLdb.Warning,w:
            self.conn.rollback()
            if self.logger:
                self.logger.error('pay_order except %s'%(w))
            self.release_db_connect()
            return False
        except Exception,e:
            self.conn.rollback()
            if self.logger:
                self.logger.error('pay_order except %s'%(e))
            self.release_db_connect()
            return False
            
    def modify_order(self, order_number, content, sales, sales_name):
        try:
            self.get_db_connect()
            self.modify_order_inner(order_number, content, sales, sales_name)
            self.conn.commit()
            self.release_db_connect()
            if self.logger:
                self.logger.info('modify_order ok')
            return True
        except Exception,e:
            if self.logger:
                self.logger.error('modify_order except %s'%(e))
            self.conn.rollback()
            self.release_db_connect()
            return False         

    def modify_order_inner(self, order_number, content, sales, sales_name):
        if not content and not sales and not sales_name:
            return False
        if content:
            sql = 'update orders set content="%s" where order_number="%s"'%(content, order_number)
            count = self.cursor.execute(sql)
        if sales:
            sql = 'update orders set sales="%s" where order_number="%s"'%(sales, order_number)
            count = self.cursor.execute(sql)
        if sales_name:
            sql = 'update orders set sales_name="%s" where order_number="%s"'%(sales_name, order_number)
            count = self.cursor.execute(sql)
        return True
            
    def cancel_order(self, order_number):
        sql = 'update orders set state=3 where order_number="%s"'%(order_number)
        self.get_db_connect()
        try:
            count = self.cursor.execute(sql)
            self.conn.commit()
            self.release_db_connect()
            if self.logger:
                self.logger.info('cancel_order ok')
            return True
        except Exception,e:
            if self.logger:
                self.logger.error('cancel_order except %s'%(e))
            self.release_db_connect()
            return False
    
    def format_user_stat(self, result):
        ret_dict = {}
        if not result:
            ret_dict['consume'] = 0.00
        else:
            ret_dict['consume'] = result[0]
        return ret_dict
        
    def get_user_stat(self, user_id):
        sql = 'select wallet_consume from user_stat where user_id=%s'%(str(user_id))
        self.get_db_connect()    
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                result = self.cursor.fetchone()
                self.release_db_connect()
                return self.format_user_stat(result)
            else:
                self.release_db_connect()
                return self.format_user_stat([])
        except Exception,e:
            if self.logger:
                self.logger.error('get_user_stat except %s'%(e))         
            self.release_db_connect()
            return self.format_user_stat([])   
    
    def get_order_stat(self, user_id):
        sql = 'select state,count(1) from orders where user_id=%s group by state'%(str(user_id))
        self.get_db_connect()
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                ret_list = []
                self.cursor.scroll(0, mode='absolute')
                results = self.cursor.fetchall()
                for result in results:
                    ret_dict = {}
                    ret_dict['state'] = result[0]
                    ret_dict['count'] = result[1]
                    ret_list.append(ret_dict)
                self.release_db_connect()
                return ret_list
            else:
                self.release_db_connect()
                return []
        except Exception,e:
            if self.logger:
                self.logger.error('get_order_stat except %s'%(e))
            self.release_db_connect()
            return []

    def get_user_un_payed_sales_sent_num(self, user_phone):
        sql = 'select count(*) from orders where user_phone=%s and state=0 and creator=1'
        self.get_db_connect()
        try:
            count = self.cursor.execute(sql, [str(user_phone)])
            if count > 0:
                result = self.cursor.fetchone()
                self.release_db_connect()
                return result[0]
            else:
                self.release_db_connect()
                return 0
        except Exception,e:
            if self.logger:
                self.logger.error('get_user_un_payed_sales_sent_num except %s'%(e))
            self.release_db_connect()
            return 0
            
    def get_order_stat_by_phone(self, user_phone):
        sql = 'select state,count(1) from orders where user_phone=%s group by state'
        self.get_db_connect()
        try:
            count = self.cursor.execute(sql, [str(user_phone)])
            if count > 0:
                ret_list = []
                self.cursor.scroll(0, mode='absolute')
                results = self.cursor.fetchall()
                for result in results:
                    ret_dict = {}
                    ret_dict['state'] = result[0]
                    ret_dict['count'] = result[1]
                    ret_list.append(ret_dict)
                self.release_db_connect()
                return ret_list
            else:
                self.release_db_connect()
                return []
        except Exception,e:
            if self.logger:
                self.logger.error('get_order_stat_by_phone except %s'%(e))
            self.release_db_connect()
            return []
            
    def get_order_sales_stat(self, user_name):
        sql = 'select state,count(*) from orders where sales="%s" group by state'%(str(user_name))
        self.get_db_connect()
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                ret_list = []
                self.cursor.scroll(0, mode='absolute')
                results = self.cursor.fetchall()
                for result in results:
                    ret_dict = {}
                    ret_dict['state'] = result[0]
                    ret_dict['count'] = result[1]
                    ret_list.append(ret_dict)
                self.release_db_connect()
                return ret_list
            else:
                self.release_db_connect()
                return []
        except Exception,e:
            if self.logger:
                self.logger.error('get_order_sales_stat except %s'%(e))
            self.release_db_connect()
            return []

    def get_order_shops_stat(self, channel_id):
        sql = 'select state,count(*) from orders where channel_id=%s group by state'%(str(channel_id))
        self.get_db_connect()
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                ret_list = []
                self.cursor.scroll(0, mode='absolute')
                results = self.cursor.fetchall()
                for result in results:
                    ret_dict = {}
                    ret_dict['state'] = result[0]
                    ret_dict['count'] = result[1]
                    ret_list.append(ret_dict)
                self.release_db_connect()
                return ret_list
            else:
                self.release_db_connect()
                return []
        except Exception,e:
            if self.logger:
                self.logger.error('get_order_shops_stat except %s'%(e))
            self.release_db_connect()
            return []
            
    def get_fix_order_list(self):
        sql = 'select id,user_id from orders where user_phone=""'
        self.get_db_connect()
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                self.cursor.scroll(0, mode='absolute')
                results = self.cursor.fetchall()

                self.release_db_connect()
                return results
            else:
                self.release_db_connect()
                return []
        except Exception,e:
            if self.logger:
                self.logger.error('fix_order except %s'%(e))
            self.release_db_connect()
            return []
            
    def record_send_message_history(self, user_id, name, role, scope, channel_id,title, content, create_time, to_user_id):
        sql = 'insert into message_send_history (user_id, name, channel_id,title, content, create_time,role,scope,to_user_id) values (%s,"%s",%s,"%s","%s",%s,"%s","%s",%s)' \
        %(str(user_id), str(name),str(channel_id), str(title),str(content), str(create_time),str(role),str(scope), str(to_user_id))
        self.get_db_connect()
        try:
            count = self.cursor.execute(sql)
            self.conn.commit()
            self.release_db_connect()
            if self.logger:
                self.logger.info('record_send_message_history ok')
            return True
        except Exception,e:
            if self.logger:
                self.logger.error('record_send_message_history except %s'%(e))
            self.release_db_connect()
            return False
    
    def get_need_commsion_settle_users(self, money):
        self.get_db_connect()
        try:
            sql = 'select sales_phone,sum(money) from commision_info where settle_id=0 and settle_state=2 and state=0 group by sales_phone having sum(money) >= %s'%(str(money))
            count = self.cursor.execute(sql)
            results = []
            if count > 0:
                self.cursor.scroll(0, mode='absolute')
                results = self.cursor.fetchall()
            self.release_db_connect()
            return results
        except Exception,e:
            if self.logger:
                self.logger.error('get_need_commsion_settle_users except %s'%(e))
            self.release_db_connect()
            return []
            
    def commision_settle(self, sales_phone, phone_fare, settle_mode=None, settle_account=None, sum_money=0, base=0, end_time=None):
        if not phone_fare:
            phone_fare = 0
        else:
            phone_fare = 1
        if end_time:
            sql = 'select id,money from commision_info where sales_phone="%s" and state=0 and enable=1 and settle_state=2 and settle_id=0 and create_time < "%s"'%(str(sales_phone), str(end_time))
        else:
            sql = 'select id,money from commision_info where sales_phone="%s" and state=0 and enable=1 and settle_state=2 and settle_id=0'%(str(sales_phone))
        self.get_db_connect()
        money = 0
        settle_money = 0
        real_settle_money = base * 50
        id_list = []
        all_list = []
        save_id = 0
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                self.cursor.scroll(0, mode='absolute')
                results = self.cursor.fetchall()
                all_list = [str(key) for key, value in results]
                for result in results:
                    id_list.append(str(result[0]))
                    money = money + float(result[1])
                    settle_money = money
                    if phone_fare:
                        if money >= real_settle_money:
                            settle_money = real_settle_money
                            save_id = str(result[0])
                            if money == float(result[1]):
                                mondity_money = real_settle_money
                            else:
                                mondity_money = real_settle_money - (money - float(result[1]))
                            break
                times = 0
                if len(id_list) > 0:
                    times = 1
                    sql = 'select max(times) from commision_settle where sales_phone="%s"'%(str(sales_phone))
                    count = self.cursor.execute(sql)
                    if count > 0:
                        result = self.cursor.fetchone()
                        times = result[0]
                        if not times:
                            times = 1
                        else:
                            times = int(times) + 1
                    save_list = list(set(all_list) - set(id_list))
                    sql = 'insert into commision_settle (money, sales_phone,times,phone_fare,callback_state,settle_state) values (%s, "%s", %s, %s, 1, 2)'%(str(settle_money), str(sales_phone), str(times), str(phone_fare))
                    count = self.cursor.execute(sql)
                    sql = 'select id from commision_settle where sales_phone="%s" and money=%s order by id desc limit 1'%(str(sales_phone), str(settle_money))
                    count = self.cursor.execute(sql)
                    if count > 0:
                        result = self.cursor.fetchone()
                        settle_id = result[0]
                    else:
                        #throw it
                        if self.logger:
                            self.logger.error('commision_settle.')

                    reward_type = '8' + datetime.now().strftime('%H%M%S')
                    left_money = float(sum_money) - float(real_settle_money)
                    if phone_fare and not sum_money == real_settle_money and sum_money != 0:
                        sql = 'insert into commision_info (money, user_phone, sales_phone, type, settle_state, callback_state,settle_mode,settle_account, update_time) values (%s, "%s", "%s", %s, %s, %s, %s, "%s", "%s")' \
                        %(left_money, sales_phone, sales_phone, reward_type ,'2','1', str(settle_mode), str(settle_account), str(int(time.time())))
                        count = self.cursor.execute(sql)
                        
                    sql = 'update commision_info set state = 1 where id in (%s)'%( ','.join(id_list))
                    count = self.cursor.execute(sql)
                    ###重复提现同步问题
                    if count == 0:
                        self.conn.rollback()
                        return (None, 0, 0) 
                    
                    sql = 'update commision_info set state = 1,settle_id=%s, settle_mode=%s, settle_account="%s", update_time=%s where id in (%s)'%(str(settle_id), str(settle_mode), str(settle_account), str(int(time.time())), ','.join(id_list))
                    count = self.cursor.execute(sql)


                    if save_id:
                        sql = 'update commision_info set money=%s, update_time=%s where id=%s'%(str(mondity_money), str(int(time.time())), str(save_id))
                        count = self.cursor.execute(sql)

                    if save_list:
                        sql = 'update commision_info set enable = 0, update_time=%s where id in (%s)'%(str(int(time.time())), ','.join(save_list))
                        count = self.cursor.execute(sql)

                    self.conn.commit()
                self.release_db_connect()
                return (money, times, settle_id)
            else:
                self.release_db_connect()
                return (0, 0, 0)

        except Exception,e:
            self.conn.rollback()
            if self.logger:
                self.logger.error('commision_settle except %s'%(e))
            self.release_db_connect()
            return (None, 0, 0)
            
    def save_commision_content(self, type, content_id, content, content_creator, callback_state, phone= ''):
        self.get_db_connect()
        try:
            if not phone:
                phone = str(content_id)
            sql = 'insert into commision_content (type, content_id, content, content_creator, phone, callback_state) values (%s, %s, "%s", "%s", "%s", %s)' \
            %(str(type), str(content_id), content, content_creator, str(phone), str(callback_state))
            count = self.cursor.execute(sql)
            self.conn.commit()
            self.release_db_connect()
            return True
        except Exception,e:
            if self.logger:
                self.logger.error('save_commision_content except %s'%(e))
            self.release_db_connect()
            return False

    def update_user_upload_score_images(self, order_number, money, comments, verify_state, reason):
        if not order_number:
            return (False, '')

        self.get_db_connect()
        try:
            sql = 'select phone from user_upload_score_images where order_number ="%s"' % (str(order_number))
            count = self.cursor.execute(sql)
            if count == 0:
                return (False, '')
            result = self.cursor.fetchone()
            phone = result[0]
            if not phone:
                return (False, '')
            if not money:
                sql = 'update user_upload_score_images set comments="%s", verify_state="%s", reason="%s" where order_number="%s"' %(comments, str(verify_state), reason, str(order_number))
            else:
                sql = 'update user_upload_score_images set comments="%s", money="%s", verify_state="%s", reason="%s" where order_number="%s"' %(comments, str(money), str(verify_state), reason, str(order_number))
            count = self.cursor.execute(sql)
            self.conn.commit()
            self.release_db_connect()
            return (True, phone)
        except Exception,e:
            if self.logger:
                self.logger.error('update_user_upload_score_images except %s'%(e))
            self.release_db_connect()
            return (False, '')

    def save_score_comment(self, order_number, creator, comments, reason, reason_type, phone, verify_state):
        self.get_db_connect()
        sql = 'insert into score_comment (creator, content, content_reason, content_reason_type, verify_state, order_number, phone) values ("%s","%s","%s","%s","%s","%s","%s")' \
        %(creator, comments, reason, str(reason_type), str(verify_state), str(order_number), str(phone))
        try:
            count = self.cursor.execute(sql)
            self.conn.commit()
            return True
        except Exception,e:
            if self.logger:
                self.logger.error('save_score_comment except %s'%(e))
            self.release_db_connect()
            return False

    def update_user_score_info(self, order_number, money, comments, verify_state, reason, type):
        self.get_db_connect()
        if not money:
            sql = 'update user_score_info set comments="%s", verify_state="%s", reason="%s" where order_number="%s" and type="%s"' % (comments, verify_state, reason, str(order_number), str(type))
        else:
            sql = 'update user_score_info set money="%s", comments="%s", verify_state="%s", reason="%s" where order_number="%s" and type="%s"' % (str(money), comments, verify_state, reason, str(order_number), str(type))

        try:
            count = self.cursor.execute(sql)
            self.conn.commit()
            self.release_db_connect()
            return True
        except Exception,e:
            if self.logger:
                self.logger.error('update_user_score_info except %s'%(e))
            self.release_db_connect()
            return False

    def get_commision_settle(self, id):
        pass
    def update_commision_settle(self, id, settle_time, content, settle_state, callback_state,commision_content,content_creator,content_state):
        self.get_db_connect()
        try:
            sql = 'select sales_phone from commision_settle where id=%s'%(str(id))
            count = self.cursor.execute(sql)
            if count == 0:
                return False
            result = self.cursor.fetchone()
            sales_phone = result[0]
            
            if settle_time and settle_state == 4:
                sql = 'update commision_settle set settle_time=%s where id=%s'%(str(settle_time), str(id))
                count = self.cursor.execute(sql)

            if content:
                sql = 'update commision_settle set content="%s" where id=%s'%(content, str(id))
                count = self.cursor.execute(sql)

            if settle_state is not None:
                sql = 'update commision_settle set settle_state=%s where id=%s'%(str(settle_state), str(id))
                count = self.cursor.execute(sql)

            if callback_state is not None:
                sql = 'update commision_settle set callback_state=%s where id=%s'%(str(callback_state), str(id))
                count = self.cursor.execute(sql)
            #if commision_content:
            sql = 'insert into commision_content (type,content_id,content,content_creator,callback_state,phone) values (%s,%s,"%s","%s",%s,"%s")' \
            %('1', str(id), commision_content, content_creator, str(content_state), str(sales_phone))
            count = self.cursor.execute(sql)
            self.conn.commit()
            self.release_db_connect()
            if count > 0:
                return True
            else:
                return False
        except Exception,e:
            self.conn.rollback()
            if self.logger:
                self.logger.error('update_commision_settle except %s'%(e))
            self.release_db_connect()
            return False            
            
    def get_channel_name_by_id(self, channel_id):
        sql = 'select name from channels where id=%s'%(str(channel_id))
        self.get_db_connect()    
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                result = self.cursor.fetchone()
                self.release_db_connect()
                return result[0]
            else:
                self.release_db_connect()
                return ''
        except Exception,e:
            if self.logger:
                self.logger.error('get_channel_name_by_id except %s'%(e))         
            self.release_db_connect()
            return ''  
    
    def get_brand_name_by_channel_id(self, channel_id):
        sql = 'select b.title from channel_brand as c inner join brand as b where c.channel_id=%s and c.brand_id=b.id'%(str(channel_id))
        self.get_db_connect()    
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                result = self.cursor.fetchone()
                self.release_db_connect()
                return result[0]
            else:
                self.release_db_connect()
                return ''
        except Exception,e:
            if self.logger:
                self.logger.error('get_brand_name_by_channel_id except %s'%(e))         
            self.release_db_connect()
            return ''    
        
    def record_sales_pre_bind(self, user_phone, sales_phone):
        sql = 'insert into pre_bind_sales_user (user_phone,sales_phone, code) values ("%s", "%s", "") on duplicate key update sales_phone="%s"' \
        %(str(user_phone), str(sales_phone), str(sales_phone))
        self.get_db_connect() 
        try:
            count = self.cursor.execute(sql)
            self.conn.commit()
            self.release_db_connect()
            return True
        except Exception,e:
            if self.logger:
                self.logger.error('record_sales_pre_bind except %s'%(e))
            self.release_db_connect()
            return False
            
    def get_pre_bind_info(self, user_phone):
        sql = 'select user_phone, code, create_time,sales_phone from pre_bind_sales_user where user_phone="%s"'%(str(user_phone))
        self.get_db_connect()    
        try:
            count = self.cursor.execute(sql)
            ret_dict = {}
            if count > 0:
                result = self.cursor.fetchone()
                ret_dict['user_phone'] = result[0]
                ret_dict['code'] = result[1]
                ret_dict['create_time'] = result[2]
                ret_dict['sales_phone'] = result[3]
                self.release_db_connect()
                return ret_dict
            else:
                self.release_db_connect()
                return {}
        except Exception,e:
            if self.logger:
                self.logger.error('get_pre_bind_info except %s'%(e))         
            self.release_db_connect()
            return {}
    
    def get_order_current_verify_state(self, order_number):
        if not order_number:
            return None
        sql = 'select verify_state from orders where order_number="%s"'%(str(order_number))
        self.get_db_connect()    
        try:
            count = self.cursor.execute(sql)
            ret_dict = {}
            if count > 0:
                result = self.cursor.fetchone()
                self.release_db_connect()
                return result[0]
            else:
                self.release_db_connect()
                return None
        except Exception,e:
            if self.logger:
                self.logger.error('get_order_current_verify_state except %s'%(e))         
            self.release_db_connect()
            return None
    
    
    def create_user_score_info(self, user_id, money, type, order_number = ''):
        self.get_db_connect()
        try:
            sql = 'insert into user_score_info (user_id, money, type, order_number, verify_state) values (%s, %s, %s, "%s", 1)' \
                  %(str(user_id), str(money), str(type), str(order_number))        
            count = self.cursor.execute(sql)
            sql = 'update orders set given_coupon=%s where order_number="%s"'%(str(money), str(order_number))
            count = self.cursor.execute(sql)
            self.conn.commit()
            self.release_db_connect()
            return True
        except Exception,e:
            if self.logger:
                self.logger.error('create_user_score_info except %s'%(e))
            self.release_db_connect()
            return False
    
    def add_push_baidu_info(self, user_id, user_phone, baidu_channel_id, baidu_user_id, device_token, platform, app, channel):
        sql = 'insert into push_baidu (user_id, user_phone, baidu_channel_id, baidu_user_id, platform, app,device_token,channel) values (%s,"%s","%s","%s","%s","%s","%s","%s") on duplicate key update user_id=%s,user_phone="%s",device_token="%s",channel="%s"' \
        %(str(user_id), str(user_phone), str(baidu_channel_id), str(baidu_user_id), str(platform), str(app),  str(device_token), str(channel),str(user_id), str(user_phone), str(device_token), str(channel))
        self.get_db_connect() 
        try:
            count = self.cursor.execute(sql)
            self.conn.commit()
            self.release_db_connect()
            return True
        except Exception,e:
            if self.logger:
                self.logger.error('add_push_baidu_info except %s'%(e))
            self.release_db_connect()
            return False

    def add_push_jpush_info(self, user_id, user_phone, device_token,jpush_alias, platform, app, channel):
        sql = 'insert into push_jpush (user_id, user_phone, platform, jpush_alias, app, device_token, channel) values (%s,"%s","%s","%s","%s","%s", "%s") on duplicate key update user_id=%s,user_phone="%s",device_token="%s", channel="%s"' \
        %(str(user_id), str(user_phone), str(platform),  str(jpush_alias), str(app),  str(device_token), str(channel), str(user_id), str(user_phone), str(device_token), str(channel))
        self.get_db_connect()
        try:
            count = self.cursor.execute(sql)
            self.conn.commit()
            self.release_db_connect()
            return True
        except Exception,e:
            if self.logger:
                self.logger.error('add_push_jpush_info except %s'%(e))
            self.release_db_connect()
            return False
            
    def test_create_user_score_info(self, user_id):
        for i in range(5):
            money = random.randint(50, 100)
            type = 0
            salt_list = random.sample('zyxwvutsrqponmlkjihgfedcba',20)
            salt = ''.join(salt_list)
            self.create_user_score_info(user_id, money, type, salt)
    
    def add_session_goods_list(self, session_id, phone, goods_id, create_time, money, cutoff_money, cutoff_rate, extra, auto=0):
        self.get_db_connect()
        sql = 'insert into session_goods_list (session_id, goods_id, phone, create_time, money, cutoff_money, cutoff_rate, extra, auto) values (%s,%s,%s,%s,%s,%s,%s,%s,%s)'
        try:
            input_info = []
            input_info.append(session_id)
            input_info.append(goods_id)            
            input_info.append(phone)
            input_info.append(create_time)
            input_info.append(money)
            input_info.append(cutoff_money)
            input_info.append(cutoff_rate)
            input_info.append(extra)
            input_info.append(auto)
            self.cursor.execute(sql, input_info)
            self.conn.commit()
            self.release_db_connect()
        except Exception,e:
            if self.logger:
                self.logger.error('add_session_goods_list except %s'%(e))         
            self.release_db_connect()
            return {}
            
    def get_session_sales_info(self, sales_phone, session_id):
        sql = 'select phone from session_goods_list where session_id=%s'
        self.get_db_connect()    
        try:
            count = self.cursor.execute(sql, [session_id])
            ret_list = []
            if count > 0:
                self.cursor.scroll(0, mode='absolute')
                results = self.cursor.fetchall()
                self.release_db_connect()
                for result in results:
                    ret_list.append(result[0])
                return ret_list
            else:
                self.release_db_connect()
                return []
        except Exception,e:
            if self.logger:
                self.logger.error('check_sales_session_info except %s'%(e))         
            self.release_db_connect()
            return []
    
    def get_goods_info_by_id(self, id):
        sql = 'select gl.id,owner,gl.create_time,gl.update_time,content,money,gl.shop_id,image1,image2,image3,image4,image5,image6,thumb1,thumb2,thumb3,thumb4,thumb5,thumb6,unit,cutoff_money,money_available_time,use_coupon,us.name,us.shop_name,gl.brand_name,gl.title from goods_list gl inner join user_shop us on gl.owner=us.telephone where gl.id=%s'%(str(id))
        self.get_db_connect()    
        try:
            count = self.cursor.execute(sql)
            ret_dict = {}
            if count > 0:
                result = self.cursor.fetchone()
                ret_dict['id'] = result[0]
                ret_dict['phone'] = result[1]
                ret_dict['create_time'] = int(time.mktime(result[2].timetuple()))
                ret_dict['update_time'] = int(time.mktime(result[3].timetuple()))
                ret_dict['desc'] = result[4]
                ret_dict['money'] = float(result[5])
                ret_dict['shop_id'] = result[6]
                ret_dict['image1'] = result[7]
                ret_dict['image2'] = result[8]
                ret_dict['image3'] = result[9]
                ret_dict['image4'] = result[10]
                ret_dict['image5'] = result[11]
                ret_dict['image6'] = result[12]
                ret_dict['thumb1'] = result[13]
                ret_dict['thumb2'] = result[14]
                ret_dict['thumb3'] = result[15]
                ret_dict['thumb4'] = result[16]
                ret_dict['thumb5'] = result[17]
                ret_dict['thumb6'] = result[18]
                ret_dict['unit'] = result[19]
                ret_dict['cutoff_money'] = float(result[20])
                ret_dict['money_available_time'] = result[21]
                ret_dict['use_coupon'] = result[22]
                money = ret_dict['money']
                cutoff_money = ret_dict['cutoff_money']
                if ret_dict['cutoff_money'] < 0.00001:
                    #ret_dict['cutoff_money'] = money
                    ret_dict['cutoff_money'] = ''
                    cutoff_money = money
                cutoff_rate = (1.00 - (money - cutoff_money) / money) * 10
                ret_dict['cutoff_rate'] = cutoff_rate
                ret_dict['name'] = result[23]
                ret_dict['shop_name'] = result[24]
                ret_dict['brand_name'] = result[25]
                ret_dict['title'] = result[26]
                self.release_db_connect()
                return ret_dict
            else:
                self.release_db_connect()
                return {}
        except Exception,e:
            if self.logger:
                self.logger.error('get_goods_info_by_id except %s'%(e))         
            self.release_db_connect()
            return {}

    def add_goods(self, phone, content, money, cutoff_money, shop_id, image_url_list, unit, use_coupon, money_available_time,title,brand_name):
        sql = 'insert into goods_list (owner, create_time,money,cutoff_money,shop_id'
        for i in range(1, len(image_url_list)+1):
            sql += ','
            sql += 'image' + str(i)
        for i in range(1, len(image_url_list)+1):
            sql += ','
            sql += 'thumb' + str(i)
        create_time = str(datetime.now())
        sql += ') values ("'
        sql += str(phone) + '",'
        sql += '"' + create_time + '",'
        sql += str(money) + ','
        sql += str(cutoff_money) + ','
        sql += str(shop_id) + ','
        for i in range(0, len(image_url_list)):
            sql += '"' + image_url_list[i][0] + '",'
        for i in range(0, len(image_url_list)):
            sql += '"' + image_url_list[i][1] + '",'
        sql = sql[:-1] + ')'
        self.get_db_connect()
        try:      
            count = self.cursor.execute(sql)
            new_id = self.cursor.lastrowid
            sql = 'update goods_list set content=%s, unit=%s,use_coupon=%s,money_available_time=%s,title=%s,brand_name=%s where id=%s'          
            count = self.cursor.execute(sql, [content, unit, use_coupon, money_available_time,title, brand_name,new_id])
            self.conn.commit()
            self.release_db_connect()
            return new_id
        except Exception,e:
            if self.logger:
                self.logger.error('add_goods except %s'%(e))
            self.release_db_connect()
            return 0
    
    def fix_goods_images(self, goods_id, fix_list):
        self.get_db_connect()
        try:
            for (fix_seq, use_seq) in fix_list:
                sql = 'update goods_list set image' + str(fix_seq) + '=image'+ str(use_seq) + ',thumb' + str(fix_seq) + '=thumb' + str(use_seq) + ' where id=%s'%(str(goods_id))
                count = self.cursor.execute(sql)
                sql = 'update goods_list set image' + str(use_seq) + '=""' + ',thumb' + str(use_seq) + '="" where id=%s'%(str(goods_id))
                count = self.cursor.execute(sql)
            self.conn.commit()
            self.release_db_connect()
            return True
        except Exception,e:
            if self.logger:
                self.logger.error('fix_goods_images except %s'%(e))
            self.release_db_connect()
            return False
    def update_goods(self, goods_id, phone, content, money, cutoff_money, use_coupon, money_available_time, unit, image_url_list, remove_image_list, modify_image_info_list, title, brand_name):
        self.get_db_connect()
        try:
            sql = 'update goods_list set modifier=%s where id=%s'
            count = self.cursor.execute(sql, (str(phone), str(goods_id)))
            
            if content:
                sql = 'update goods_list set content=%s where id=%s'
                count = self.cursor.execute(sql, (MySQLdb.escape_string(content.encode('utf8','ignore')), str(goods_id)))
            if money > 1:
                sql = 'update goods_list set money=%s where id=%s'
                count = self.cursor.execute(sql, (str(money), str(goods_id)))
            if cutoff_money > 0:
                sql = 'update goods_list set cutoff_money=%s where id=%s'
                count = self.cursor.execute(sql, (str(cutoff_money), str(goods_id)))
            if unit:
                sql = 'update goods_list set unit=%s where id=%s'
                count = self.cursor.execute(sql, (unit, str(goods_id)))
            if title:
                sql = 'update goods_list set title=%s where id=%s'
                count = self.cursor.execute(sql, (title, str(goods_id)))
            if brand_name:
                sql = 'update goods_list set brand_name=%s where id=%s'
                count = self.cursor.execute(sql, (brand_name, str(goods_id)))                
                
            sql = 'update goods_list set use_coupon=%s,money_available_time=%s where id=%s'
            count = self.cursor.execute(sql, [use_coupon, money_available_time, goods_id])
            upload_seq = 0
            for seq in remove_image_list:
                sql = 'update goods_list set image' + str(seq) + '="",thumb' + str(seq) + '="" where id=%s'%(str(goods_id))
                count = self.cursor.execute(sql)
            if image_url_list:
                modify_image_info_list.extend(remove_image_list)
                modify_image_info_list = [ int(i) for i in modify_image_info_list ]
                modify_image_info_list = list(set(modify_image_info_list))
                modify_image_info_list.sort()
                for seq in modify_image_info_list:
                    sql = 'update goods_list set image' + str(seq) + '="%s",thumb'%(image_url_list[upload_seq][0]) + str(seq) + '="%s" where id=%s'%(image_url_list[upload_seq][1],str(goods_id))
                    count = self.cursor.execute(sql) 
                    upload_seq += 1
                    if upload_seq >= len(image_url_list):
                        break
            self.conn.commit()
            self.release_db_connect()
            return True
        except Exception,e:
            if self.logger:
                self.logger.error('update_goods except %s'%(e))
            self.release_db_connect()
            return False
    
    def remove_goods(self, goods_id):
        self.get_db_connect()
        sql = 'delete from goods_list where id=%s'
        try:
            count = self.cursor.execute(sql, [goods_id])
            self.conn.commit()
            self.release_db_connect()
            return True
        except Exception,e:
            if self.logger:
                self.logger.error('remove_goods except %s'%(e))         
            self.release_db_connect()
            return False
            
    def disable_goods(self, goods_id):
        self.get_db_connect()
        sql = 'update goods_list set enable=0 where id=%s'
        try:
            count = self.cursor.execute(sql, [goods_id])
            self.conn.commit()
            self.release_db_connect()
            return True
        except Exception,e:
            if self.logger:
                self.logger.error('disable_goods except %s'%(e))         
            self.release_db_connect()
            return False
            
    def get_goods_sales_info(self, sales_phone):
        sql = 'select telephone,brand_name,name,shop_id,user_state,shop_name from user_shop where telephone="%s"'%(str(sales_phone))
        self.get_db_connect()    
        try:
            count = self.cursor.execute(sql)
            ret_dict = {}
            if count > 0:
                result = self.cursor.fetchone()
                ret_dict['phone'] = result[0]
                ret_dict['brand_name'] = result[1].split()[0]
                ret_dict['name'] = result[2]
                ret_dict['cooperative'] = 1 if result[3]!=0 else 0
                ret_dict['verified'] = 1 if result[4]==2 else 0
                ret_dict['shop_name'] = result[5]
                self.release_db_connect()
                return ret_dict
            else:
                self.release_db_connect()
                return {}
        except Exception,e:
            if self.logger:
                self.logger.error('get_goods_sales_info except %s'%(e))         
            self.release_db_connect()
            return {}
            
    def get_shopping_goods_info(self, shopping_id):
        sql = 'select user_phone, goods_id,create_time from shopping_list where id=%s'
        self.get_db_connect()    
        try:
            count = self.cursor.execute(sql, [shopping_id])
            ret_dict = {}
            if count > 0:
                result = self.cursor.fetchone()
                ret_dict['user_phone'] = result[0]
                ret_dict['goods_id'] = result[1]
                ret_dict['create_time'] = int(time.mktime(result[2].timetuple()))
                self.release_db_connect()
                return ret_dict
            else:
                self.release_db_connect()
                return {}
        except Exception,e:
            if self.logger:
                self.logger.error('get_shopping_goods_info except %s'%(e))         
            self.release_db_connect()
            return {}
    
    def get_session_info_v2(self, session_id):
        sql = 'select session_id,c_phone,content,ctime,goods,covered_area,house_type,send_num from chat_group_info_v2 cgi left join customer_user cu on cu.name=cgi.c_phone where session_id=%s'
        self.get_db_connect()    
        try:
            count = self.cursor.execute(sql, [session_id])
            ret_dict = {}
            if count > 0:
                result = self.cursor.fetchone()
                ret_dict['id'] = result[0]
                ret_dict['phone'] = result[1]
                ret_dict['content'] = result[2]
                ret_dict['create_time'] = result[3]
                ret_dict['goods'] = result[4]
                ret_dict['covered_area'] = result[5]
                ret_dict['house_type'] = result[6]
                ret_dict['send_num'] = result[7]
                self.release_db_connect()
                return ret_dict
            else:
                self.release_db_connect()
                return {}
        except Exception,e:
            if self.logger:
                self.logger.error('get_session_info_v2 except %s'%(e))         
            self.release_db_connect()
            return {}        
    
    def get_recommend_session_list_v2(self, category, total_category = ''):
        self.get_db_connect()
        try:
            if category == 'all':
                sql = 'select cgi.session_id, cgi.c_phone, cgi.content, cgi.recommend_index, cgi.goods, cgi.brand_name, cgi.total_num, cc.total_category_name from chat_group_info_v2 cgi inner join category_commodity cc on cgi.goods=cc.commodity_name where cgi.recommend_index > 0 group by cgi.session_id order by cgi.recommend_index desc limit 10'
                count = self.cursor.execute(sql)
            elif category:
                sql = 'select cgi.session_id, cgi.c_phone, cgi.content, cgi.recommend_category, cgi.goods, cgi.brand_name, cgi.total_num, cc.total_category_name from chat_group_info_v2 cgi inner join category_commodity cc on cgi.goods=cc.commodity_name where cgi.recommend_category > 0 and goods=%s group by cgi.session_id order by cgi.recommend_category desc limit 10'
                count = self.cursor.execute(sql, [category.encode('utf8', 'ignore')])
            else:
                sql = 'select cgi.session_id, cgi.c_phone, cgi.content, cgi.recommend_category, cgi.goods, cgi.brand_name, cgi.total_num, cc.total_category_name from chat_group_info_v2 cgi inner join category_commodity cc on cc.total_category_name=%s and cgi.goods=cc.commodity_name where cgi.recommend_category > 0  group by cgi.session_id order by cgi.recommend_category desc limit 10'
                count = self.cursor.execute(sql, [total_category.encode('utf8', 'ignore')])
            ret_list = []
            if count > 0:
                self.cursor.scroll(0, mode='absolute')
                results = self.cursor.fetchall()
                self.release_db_connect()
                for result in results:
                    ret_dict = {}
                    ret_dict['id'] = result[0]
                    phone = result[1].strip()
                    if not phone:
                        continue                    
                    send_char = '3' if phone[1] == '2' else phone[1]
                    ret_dict['phone'] = phone[0] + send_char + phone[2] + '*****%s'%(phone[-3:])
                    ret_dict['content'] = result[2]
                    ret_dict['create_time'] = result[3]
                    ret_dict['goods'] = result[4]
                    ret_dict['goods_num'] = result[6]
                    ret_dict['category'] = result[7]
                    ret_list.append(ret_dict)
                return ret_list
            else:
                return []
        except Exception,e:
            if self.logger:
                self.logger.error('get_recommend_session_list_v2 except %s'%(e))
            self.release_db_connect()
            return []

    def get_customer_session_list_v2(self, user_name):
        self.get_db_connect()
        try:
            sql = 'select cgi.session_id, cgi.c_phone, cgi.content, cgi.ctime, cgi.goods, cgi.brand_name, cgi.total_num, cc.total_category_name from chat_group_info_v2 cgi inner join category_commodity cc on cgi.goods=cc.commodity_name where c_phone=%s order by cgi.ctime desc'
            count = self.cursor.execute(sql, [user_name])
            ret_list = []
            if count > 0:
                self.cursor.scroll(0, mode='absolute')
                results = self.cursor.fetchall()
                self.release_db_connect()
                for result in results:
                    ret_dict = {}
                    ret_dict['id'] = result[0]
                    ret_dict['phone'] = result[1]
                    ret_dict['content'] = result[2]
                    ret_dict['create_time'] = result[3]
                    ret_dict['goods'] = result[4]
                    ret_dict['goods_num'] = result[6]
                    ret_dict['category'] = result[7]
                    ret_list.append(ret_dict)
                return ret_list
            else:
                return []
        except Exception,e:
            if self.logger:
                self.logger.error('get_customer_session_list_v2 except %s'%(e))
            self.release_db_connect()
            return []

    def get_lottery_id(self, user_phone, order_number):
        self.get_db_connect()
        sql = 'select lottery_identifying from lottery_multi_list where user_phone="%s" and order_number="%s" and type=13 and state = 0' %(str(user_phone), str(order_number))
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                result = self.cursor.fetchone()
                self.release_db_connect()
                return result[0]
            else:
                self.release_db_connect()
                return False
        except Exception,e:
            if self.logger:
                self.logger.error('get_lottery_id except %s'%(e))
            self.release_db_connect()
            return False

    def record_user_send_message_history(self, user_phone, sales_phone, name, brand_name, shop_name):
        self.get_db_connect()
        sql = 'insert into user_send_message_history (user_phone, sales_phone, name, brand_name, shop_name) values ("%s","%s","%s","%s","%s")'%(str(user_phone), str(sales_phone),name,brand_name,shop_name)
        try:
            count = self.cursor.execute(sql)
            self.conn.commit()
            self.release_db_connect()
            return True
        except Exception,e:
            self.conn.rollback()
            if self.logger:
                self.logger.error('record_user_send_message_history except %s'%(e))
            self.release_db_connect()
            return False

    def add_draw_lottery_feed_info(self, user_phone, title, content, action, url, general_data, create_time):
        self.get_db_connect()
        sql = 'insert into feed_list (user_phone, title, content, url, general_data, action, create_time) values("%s", "%s", "%s", "%s", %s, "%s", "%s")'%(str(user_phone), title, content, url, str(general_data), str(action), create_time)
        try:
            count = self.cursor.execute(sql)
            self.conn.commit()
            self.release_db_connect()
            return True
        except Exception,e:
            if self.logger:
                self.logger.error('add_draw_lottery_feed_info except %s'%(e))
            self.release_db_connect()
            return False
       
    def get_sales_orders_times(self, sales_phone):
        self.get_db_connect()
        sql = 'select count(order_number) from orders where sales=%s and state in (1, 2)' % (str(sales_phone))
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                result = self.cursor.fetchone()
                self.release_db_connect()
                return result[0]
            else:
                self.release_db_connect()
                return 0
        except Exception,e:
            if self.logger:
                self.logger.error('get_sales_orders_times except %s'%(e))
            self.release_db_connect()
            return 0

    def get_customer_orders_times(self, user_phone):
        self.get_db_connect()
        sql = 'select count(order_number) from orders where user_phone=%s and state in (1, 2)' % (str(user_phone))
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                result = self.cursor.fetchone()
                self.release_db_connect()
                return result[0]
            else:
                self.release_db_connect()
                return 0
        except Exception,e:
            if self.logger:
                self.logger.error('get_customer_orders_times except %s'%(e))
            self.release_db_connect()
            return 0

    def get_shop_purchase(self, shop_id):
        self.get_db_connect()
        sql = 'select pe.telephone from purchase pe inner join channels cs on cs.pur_id=pe.id inner join shop_address_info sai on sai.channel_id=cs.id where sai.id=%s' % (str(shop_id))
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                result = self.cursor.fetchone()
                self.release_db_connect()
                return result[0]
            else:
                self.release_db_connect()
                return ''
        except Exception,e:
            if self.logger:
                self.logger.error('get_shop_purchase except %s'%(e))
            self.release_db_connect()
            return ''
            
    def record_workflow(self, type, customer_type, mobile, content, bind_customer_service, extend):
        self.get_db_connect()
        sql = """insert into workflow (type, content, extend, customer_type, moblie, bind_customer_service) values('%s', '%s', '%s', '%s','%s', '%s')""" % (
str(type), content, extend, customer_type, str(mobile), bind_customer_service)
        try:
            count = self.cursor.execute(sql)
            self.conn.commit()
            self.release_db_connect()
            return True
        except Exception,e:
            if self.logger:
                self.logger.error('record_workflow except %s'%(e))
            self.release_db_connect()
            return False

    def get_customer_service_phone(self, mobile):
        self.get_db_connect()
        try:
            sql = 'select customer_service_phone from customer_user where name="%s"'%(str(mobile))
            count = self.cursor.execute(sql)
            if count > 0:
                result = self.cursor.fetchone()
                return result[0]
            else:
                return ''
        except Exception, e:
            if self.logger:
                self.logger.error('get_customer_service_phone except %s'%(e))
            self.release_db_connect()
            return ''

    def get_workflow_info(self, type, mobile):
        self.get_db_connect()
        try:
            sql = 'select id from workflow where type="%s" and moblie="%s"'%(str(type), str(mobile))
            count = self.cursor.execute(sql)
            if count > 0:
                result = self.cursor.fetchone()
                return result[0]
            else:
                return 0
        except Exception, e:
            if self.logger:
                self.logger.error('get_workflow_info except %s'%(e))
            self.release_db_connect()
            return 0

    def verify_offline_order(self, order_number, verify_state, comments, reason, creator):
        self.get_db_connect()
        try:
            money = 0
            sql = 'select sales, user_phone from orders where order_number="%s"' % (str(order_number))
            count = self.cursor.execute(sql)
            if count == 0:
                return False, money
            result = self.cursor.fetchone()
            sales, user_phone = result[0], result[1]
            if verify_state == 0:
                sql = 'update commision_info set settle_state=2 where user_phone="%s" and sales_phone="%s" and order_number="%s"'%(str(user_phone), str(sales), str(order_number))
            else:
                sql = 'update commision_info set settle_state=1 where user_phone="%s" and sales_phone="%s" and order_number="%s"'%(str(user_phone), str(sales), str(order_number))
            count = self.cursor.execute(sql)
            #if verify_state in [0,2]:
            if verify_state in [0]:
                sql = 'update user_score_info set comments="%s", verify_state="%s" where order_number="%s" and type="%s"' % (comments, verify_state, str(order_number), 5)
                count = self.cursor.execute(sql)
            # sql = 'update orders set verify_time=%s where order_number=%s'
            # count = self.cursor.execute(sql, [int(time.time()), order_number])
            # sql = 'insert into orders_comment (creator, content, content_reason, verify_state, order_number) values ("%s","%s","%s","%s","%s")' \
        # %(creator, comments, reason, str(verify_state), str(order_number))
            # count = self.cursor.execute(sql)

            sql = 'select money from commision_info where user_phone="%s" and sales_phone="%s" and order_number="%s"'%(str(user_phone), str(sales), str(order_number))
            count = self.cursor.execute(sql)
            if count > 0:
                result = self.cursor.fetchone()
                money = result[0]

            self.conn.commit()
            self.release_db_connect()
            return True, money
        except Exception, e:
            self.conn.rollback()
            if self.logger:
                self.logger.error('verify_offline_order except %s'%(e))
            self.release_db_connect()
            return False, 0

    def is_promote_user(self, phone):
        self.get_db_connect()
        try:
            sql = 'select name from backend_user where name=%s and enable=1'
            count = self.cursor.execute(sql, [phone])
            if count > 0:
                result = self.cursor.fetchone()
                return True
            else:
                return False
        except Exception, e:
            if self.logger:
                self.logger.error('is_promote_user except %s'%(e))
            self.release_db_connect()
            return False
    
    def create_pre_register_customer_user(self, user_phone, passwd):
        self.get_db_connect()
        salt_list = random.sample('zyxwvutsrqponmlkjihgfedcba',4)
        salt = ''.join(salt_list)
        password = hashlib.md5(passwd).hexdigest()
        password = hashlib.md5(password + salt).hexdigest()
        
        sql = 'insert into pre_register_customer_user (phone, password, salt) values(%s, %s, %s)'
        try:
            count = self.cursor.execute(sql, [user_phone, password, salt])
            self.conn.commit()
            self.release_db_connect()
            return True
        except Exception,e:
            if self.logger:
                self.logger.error('create_pre_register_customer_user except %s'%(e))
            self.release_db_connect()
            return False
            
    def get_pre_register_customer_user(self, user_phone):
        self.get_db_connect()
        try:
            sql = 'select phone,password,salt from pre_register_customer_user where phone=%s'
            count = self.cursor.execute(sql, [user_phone])
            if count > 0:
                return self.cursor.fetchone()
            else:
                return None
        except Exception, e:
            if self.logger:
                self.logger.error('get_pre_register_customer_user except %s'%(e))
            self.release_db_connect()
            return None
    
    def report_shop_issue(self, user_name, comment):
        self.get_db_connect()
        try:
            if comment:
                sql = 'insert into workflow (type, customer_type, content, moblie) values(%s, %s, %s, %s)'
                count = self.cursor.execute(sql, [10, u'顾客', comment, str(user_name)])
            else:
                sql = 'insert into workflow (type, customer_type, content, moblie) values(%s, %s, %s, %s)'
                count = self.cursor.execute(sql, [10, u'顾客', u'顾客产生了一个门店投诉', str(user_name)])
            self.conn.commit()
            self.release_db_connect()
            return True
        except Exception,e:
            if self.logger:
                self.logger.error('report_shop_issue except %s'%(e))
            self.release_db_connect()
            return False

    def record_pre_bind_channel(self, user_name, channel):
        self.get_db_connect()
        try:
            sql = 'insert into pre_bind_channel (user_phone, channel) values (%s,%s)'
            count = self.cursor.execute(sql, [user_name, channel])
            self.conn.commit()
            self.release_db_connect()
            return True
        except Exception,e:
            if self.logger:
                self.logger.error('report_shop_issue except %s'%(e))
            self.release_db_connect()
            return False
            
    def get_pre_bind_channel(self, user_name):
        self.get_db_connect()
        try:
            sql = 'select channel, create_time from pre_bind_channel where user_phone=%s'
            count = self.cursor.execute(sql, [str(user_name)])
            if count > 0:
                return self.cursor.fetchone()            
            self.release_db_connect()
            return None
        except Exception,e:
            if self.logger:
                self.logger.error('get_pre_bind_channel except %s'%(e))
            self.release_db_connect()
            return None

    def update_user_channel(self, user_name, channel):
        self.get_db_connect()
        try:
            sql = 'update customer_user set channel=%s where name=%s'
            count = self.cursor.execute(sql, [str(channel), str(user_name)])
            self.conn.commit()
            self.release_db_connect()
            return True
        except Exception,e:
            if self.logger:
                self.logger.error('update_user_channel except %s'%(e))
            self.release_db_connect()
            return False
            
    def add_user_timeline(self, user_phone, type, remark):
        self.get_db_connect()
        try:
            sql = 'insert into user_timeline (name,type,remark) values (%s,%s,%s)'
            count = self.cursor.execute(sql, [str(user_phone), str(type), remark])
            self.conn.commit()
            self.release_db_connect()
            return True
        except Exception,e:
            if self.logger:
                self.logger.error('add_user_timeline except %s'%(e))
            self.release_db_connect()
            return False
        
    def save_order_stages_info(self, order_number, stages_account, stages_bank, stages_number):
        self.get_db_connect()
        try:
            sql = 'insert into orders_option (order_number, stages_return_account, stages_return_bank, stages_return_number) values (%s,%s,%s,%s) on duplicate key update stages_return_account=%s,stages_return_bank=%s,stages_return_number=%s'
            count = self.cursor.execute(sql, [order_number, stages_account, stages_bank, stages_number, stages_account, stages_bank, stages_number])
            self.conn.commit()
            self.release_db_connect()
            return True
        except Exception,e:
            if self.logger:
                self.logger.error('save_order_stages_info except %s'%(e))
            self.release_db_connect()
            return False        
        
if __name__ == '__main__':
    handler = DbUtil(settings.COMMON_DATA['mobile_db'], settings.COMMON_DATA['mobile_logger'])
    #handler.add_user_score_activity_money('12005000009')
    #handler.verify_commision_info('12011678954', '13811678953', 0)
    #handler.check_order_commission('1426750070650688797631')
    #print handler.get_user_consumer_award('18618281170', None)
    #print handler.commision_settle('18618281170', 1, 2, '18618281170', 118.1, 2)
    #print handler.add_feed_info_many(['18618281170', '136000925'], u'顾客求购', u'有顾客发了询价', 'inquire_detail')
    #print handler.get_business_name_brand('18618281170')
    #print handler.record_workflow(0, u'店员', '18618281170', u'测试注册', '', '')
    handler.get_user_pay_times_by_sales('13811678953', ['11100000206', '13811678953'])
