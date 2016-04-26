#coding=utf-8

import urllib,os,sys,time,hashlib,urllib,re
import simplejson as json
from xml.etree import ElementTree

if __name__ == '__main__':
    G_PATH = os.path.split(os.path.realpath(__file__))[0]
    sys.path.append(G_PATH + '/../../')
    os.environ['DJANGO_SETTINGS_MODULE'] = 'MobileService.settings'

from django.conf import settings
from MobileService.util.DbUtil import *
from MobileService.util.mobile_errors import *
from MobileService.promote.db_promote import *
from MobileService.business_user.db_business_user import *
from MobileService.shop.db_shop import DbShop
from MobileService.util.PercentCoupon import PercentCouponUtil
from MobileService.util.OrderCutoff import OrderCutoffUtil

PAY_STATE_NOT_PAYED = 0
PAY_STATE_SUBSCRIBE_PAYED = 1
PAY_STATE_PAYED = 2
PAY_STATE_CANCELED = 3
PAY_STATE_GOODS_BACK = 4

BUSINESS_ORDER_CHANGE_NUM_PREFIX = 'b_o_c_n_'
BUSINESS_CHANNEL_ORDER_CHANGE_NUM_PREFIX = 'b_c_o_c_n_'

BUSINESS_ORDER_SALES_RECENTLY_LIST = 'b_o_s_r_l_'
BUSINESS_ORDER_SALES_UNPAYED_LIST = 'b_o_s_up_l_'
BUSINESS_ORDER_SALES_PAYED_LIST = 'b_o_s_pd_l_'
BUSINESS_ORDER_SALES_ALL_LIST = 'b_o_s_a_l_'


BUSINESS_ORDER_CHANNEL_RECENTLY_LIST = 'b_o_ch_r_l_'
BUSINESS_ORDER_CHANNEL_UNPAYED_LIST = 'b_o_ch_up_l_'
BUSINESS_ORDER_CHANNEL_PAYED_LIST = 'b_o_ch_pd_l_'
BUSINESS_ORDER_CHANNEL_ALL_LIST = 'b_o_ch_a_l_'


EXPIRE_ORDER_CHANGE = 3600 * 24 * 3

getcontext().prec = 3

TOTAL_QUOTA = 5000

DEFAULT_USER_CHANNEL_QUOTA = 200000

USER_SHOP_ORDER_FLAG_ALL = 0
USER_SHOP_ORDER_FLAG_USE_COUPON = 0x01
USER_SHOP_ORDER_FLAG_GET_COUPON = 0x02
USER_SHOP_ORDER_FLAG_WALLET = 0x04
USER_SHOP_ORDER_FLAG_BY_STAGES = 0x08
USER_SHOP_ORDER_FLAG_RANDOM_CUTOFF = 0x10

class DbOrderUtil(DbUtil):
    def __init__(self, database, logger=None):
        DbUtil.__init__(self, database, logger)

    def format_shop_coupon(self, results):
        ret_list = []
        for result in results:
            ret_dict = {}
            ret_dict['money'] = result[0]
            ret_dict['type'] = result[1]
            ret_dict['shop_id'] = result[2]
            ret_dict['verify_state'] = result[3]
            ret_list.append(ret_dict)
        return ret_list

    def get_user_shop_recieved_coupon(self, user_id):
        self.get_db_connect()
        sql = 'select usi.money, usi.type, os.shop_id,usi.verify_state from user_score_info usi left join orders os on os.order_number=usi.order_number where usi.user_id=%s and usi.verify_state!=2 and usi.type in (0,1,2,3,5) order by usi.id'%(str(user_id))
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                self.cursor.scroll(0, mode='absolute')
                results = self.cursor.fetchall()
                self.release_db_connect()
                return self.format_shop_coupon(results)   
            else:
                return []
        except Exception,e:
            if self.logger:
                self.logger.error('get_user_shop_recieved_coupon except %s'%(e))
            self.release_db_connect()
            return []

    def get_user_current_coupon(self, user_id):
        self.get_db_connect()
        sql = 'select money from user_score where user_id=%s'%(str(user_id))
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                result = self.cursor.fetchone()
                self.release_db_connect()
                return result[0]  
            else:
                return 0
        except Exception,e:
            if self.logger:
                self.logger.error('get_user_current_coupon except %s'%(e))
            self.release_db_connect()
            return 0

    def get_order_coupons(self, order_number, type = None):
        self.get_db_connect()
        if type is None:
            sql = 'select id,money,type,state,verify_state from user_score_info where order_number="%s"'%(str(order_number))
        else:
            sql = 'select id,money,type,state,verify_state from user_score_info where order_number="%s" and type=%s'%(str(order_number), str(type))
        try:
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
                self.logger.error('get_order_coupons except %s'%(e))
            self.release_db_connect()
            return []
        
    def create_user_score_info_v2(self, user_id, money, type, order_number = ''):
        self.get_db_connect()
        try:
            sql = 'insert into user_score_info (user_id, money, type, order_number, verify_state, state) values (%s, %s, %s, "%s", 1, 1)' \
                %(str(user_id), str(money), str(type), str(order_number))        
            count = self.cursor.execute(sql)
            sql = 'insert into user_score (user_id, money) values (%s,%s) on duplicate key update money=money+%s'%(str(user_id), str(money), str(money))
            count = self.cursor.execute(sql)
            sql = 'update orders set given_coupon=%s where order_number="%s"'%(str(money), str(order_number))
            print sql
            count = self.cursor.execute(sql)
            self.conn.commit()
            self.release_db_connect()
            return True
        except Exception,e:
            self.conn.rollback()
            if self.logger:
                self.logger.error('create_user_score_info_v2 except %s'%(e))
            self.release_db_connect()
            return False
    
    def do_order_coupon_sucess(self, user_id, remove_id_list, delta_coupon):
        self.get_db_connect()
        try:
            if remove_id_list:
                remove_id_list = [ str(i) for i in remove_id_list ]
                sql = 'delete from user_score_info where id in (%s)'%(','.join(remove_id_list))        
                count = self.cursor.execute(sql)
                
            sql = 'update user_score set money=money+%s where user_id=%s'%(str(delta_coupon), str(user_id))
            count = self.cursor.execute(sql)
            self.conn.commit()
            self.release_db_connect()
            return True
        except Exception,e:
            self.conn.rollback()
            if self.logger:
                self.logger.error('do_order_coupon_sucess except %s'%(e))
            self.release_db_connect()
            return False
    
    def do_order_coupon_failed(self, user_id, order_number, return_coupon, cutoff_coupon, use_cutoff_coupon, need_return):
        self.get_db_connect()
        try:
            return_coupon = float(return_coupon)
            cutoff_coupon = float(cutoff_coupon)
            use_cutoff_coupon = float(use_cutoff_coupon)
            self.logger.info('do_order_coupon_failed %s %s %s %s %s'%(str(order_number), str(return_coupon), str(cutoff_coupon), str(type(return_coupon)), str(type(cutoff_coupon))))
            print 'hahhaha'
            if need_return:
                sql = 'insert into user_score_info (user_id, money, type, state, order_number) values (%s,%s,%s,%s,%s)'       
                count = self.cursor.execute(sql, [user_id, return_coupon, 7, 1, order_number])
                
            print cutoff_coupon
            if cutoff_coupon:
                sql = 'insert into user_score_info (user_id, money, type, state, order_number) values (%s,%s,%s,%s,%s)'
                #disable cutoff coupon temp
                #count = self.cursor.execute(sql, [user_id, cutoff_coupon, 6, 1, order_number])
                print 'hahhaha11111'
            delta_coupon = return_coupon - use_cutoff_coupon
            #disable cutoff coupon temp
            delta_coupon = return_coupon
            sql = 'update user_score set money=money+%s where user_id=%s'%(str(delta_coupon), str(user_id))
            count = self.cursor.execute(sql)
            self.conn.commit()
            self.release_db_connect()
            return True
        except Exception,e:
            self.conn.rollback()
            if self.logger:
                self.logger.error('do_order_coupon_failed except %s'%(e))
            self.release_db_connect()
            return False
            
    def update_order_state(self, order_number, state):
        self.get_db_connect()
        try:
            sql = 'update orders set state=%s where order_number=%s'       
            count = self.cursor.execute(sql, [state, order_number])            
            self.conn.commit()
            self.release_db_connect()
            return True
        except Exception,e:
            if self.logger:
                self.logger.error('update_order_state except %s'%(e))
            self.release_db_connect()
            return False
    
    def has_sent_coupon(self, user_id, order_number):
        self.get_db_connect()
        sql = 'select id from user_score_info where user_id=%s and order_number="%s" and type=5'%(str(user_id), str(order_number))
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                return True
            else:
                return False
        except Exception,e:
            if self.logger:
                self.logger.error('has_sent_coupon except %s'%(e))
            self.release_db_connect()
            return True
            
class OrderUtil():
    def __init__(self, database):
        self.redis = database['cache_redis']
        self.shop_db = database['shop_db']
        self.mobile_db = database['mobile_db']
        self.info_logger = database['mobile_logger']
        self.user_db = database['user_db']
        self.database = database
        
    def check_pay_type(self, type):
        if type != PAY_ORDER_TYPE_ALL and type != PAY_ORDER_TYPE_SUBSCRIBE and type != PAY_ORDER_TYPE_TAIL:
            return False
        else:
            return True
    
    def get_cutoff_rate(self):
        return 0
    def check_customer_pay_privilege(self, user_phone):
        handler = DbUtil(self.mobile_db, self.info_logger)
        user_info = handler.get_user_info(0, user_phone)
        if not user_info:
            return False
        pay_flag = user_info.get('pay_flag', 0)
        if pay_flag:
            return True
        else:
            return False

    def get_order_pay_cut_money_info(self, user_id, order_number, current_price, pay_type=2, percent_coupon_id=0):
        current_price = float(current_price)
        handler = DbUtil(self.mobile_db, self.info_logger)
        order_detail = handler.get_order_detail(order_number)
        contract_price = float(order_detail.get('order_detail', 0))
        price_total = float(order_detail.get('price_total', 0))
        shop_id = order_detail.get('shop_id', 0)
        user_phone = order_detail.get('user_phone', '')
        if (abs(contract_price - current_price) < 0.001) and price_total < 0.001:
            type = 0
        elif price_total < 0.001 and (contract_price - current_price > 10):
            type = 1
        else:
            type = 0
            
        coupon = 0
        ###pay_type 2 pay_coupon 3 pay_percent_coupon 6 random_cutoff 7 full_pay
        if pay_type == 2:
            cutoff_rate = self.get_cutoff_rate()
            coupon = float('%.2f'%(self.get_order_coupon_usage(user_id, order_number, current_price)))
            money = float('%.2f'%(current_price * (100 - cutoff_rate) / 100 - coupon))
            
        elif pay_type == 3:
            handler = PercentCouponUtil(self.database)
            pecent_detail = handler.get_user_coupon_detail(percent_coupon_id)
            percent = pecent_detail['percent']
            max_cut_money = pecent_detail['max_cut_money']
            
            non_cut_money = max(current_price - float(max_cut_money), 0)
            if non_cut_money:
                money = float('%.2f'%(non_cut_money + max_cut_money * float(percent) / 10))
            else:
                money = float('%.2f'%(current_price * float(percent) / 10))
        elif pay_type == 6:
            cutoff_handler = OrderCutoffUtil(self.database)
            money = cutoff_handler.get_user_shop_cutoff_money(user_phone, shop_id, current_price)
        elif pay_type == 7:
            money = current_price
        elif pay_type == 5:
            money = current_price
        else:
            money = 0
        
        self.info_logger.info('get_order_pay_cut_money_info get money %s coupon %s type %s by %s'%(str(money),str(coupon),str(type),order_number))
        return (money, coupon, type)
        
    def check_order_pay_cut_money(self, user_phone, sales_phone, total_money, money, coupon, version= None):
        quota_info = self.get_user_channel_pay_info(user_phone, sales_phone, 0)
        restrict = quota_info.get('restrict', 0)
        left_quota = quota_info.get('left_quota', TOTAL_QUOTA)
            
        if version is None or version >= '2.1.2':
            if not restrict:
                if abs(float('%.3f'%(total_money * float(95) / 100)) - coupon - money) > 1:
                    return ERROR_ORDER_INVALID_REAL_PAY_MONEY
            else:
                if left_quota >= total_money and abs(float('%.3f'%(total_money * float(95) / 100)) - coupon - money) > 1:
                    return ERROR_ORDER_INVALID_REAL_PAY_MONEY
                if left_quota < total_money and abs(float('%.3f'%((total_money-left_quota) + left_quota * float(95) / 100)) - coupon - money) > 1:
                    return ERROR_ORDER_INVALID_REAL_PAY_MONEY
        else:        
            if not restrict:
                if abs(float('%.3f'%((total_money-coupon) * float(95) / 100)) - money) > 1:
                    return ERROR_ORDER_INVALID_REAL_PAY_MONEY
            else:
                if left_quota >= total_money - coupon and abs(float('%.3f'%((total_money-coupon) * float(95) / 100)) - money) > 1:
                    return ERROR_ORDER_INVALID_REAL_PAY_MONEY
                if left_quota < total_money - coupon and abs(float('%.3f'%((total_money-coupon-left_quota) + left_quota * float(95) / 100)) - money) > 1:
                    return ERROR_ORDER_INVALID_REAL_PAY_MONEY
                
        return ERROR_NO_ERROR
        
    def check_order_pay(self, user_id, order_number, total_money, money, coupon):
        handler = DbUtil(self.mobile_db, self.info_logger)
        order_detail = handler.get_order_detail(order_number)
        if not order_detail:
            return ERROR_ORDER_NOT_FOUND
        order_user_id = order_detail.get('user_id', 0)
        shop_id = order_detail.get('shop_id', 0)
        if shop_id == 0:
            return ERROR_PAY_ONLINE_FOR_PRE_COOPERATION_SALES
        order_state = order_detail.get('state', 0)
        if int(order_state) in [PAY_STATE_PAYED, PAY_STATE_CANCELED, PAY_STATE_GOODS_BACK]:
            return ERROR_ORDER_PAYED
        contract_price = order_detail.get('contract_price', 0)
        if contract_price == 0:
            return ERROR_NO_ERROR
        price_total = order_detail.get('price_total', 0)
        if float(price_total) + float(total_money) > float(contract_price) + 1:
            return ERROR_ORDER_PAY_MONEY_BIG_THAN_CONTRACT
        return ERROR_NO_ERROR
    
    def check_order_pay_v2(self, user_id, order_number, current_price, pay_type=2, percent_coupon_id=0):
        handler = DbUtil(self.mobile_db, self.info_logger)
        order_detail = handler.get_order_detail(order_number)
        if not order_detail:
            return ERROR_ORDER_NOT_FOUND
        
        order_state = order_detail.get('state', 0)
        shop_id = order_detail.get('shop_id', 0)
        creator = order_detail.get('creator', 0)
        user_phone = order_detail.get('user_phone', '')
        wish_flag = order_detail.get('wish_flag', '')
        if int(order_state) in [PAY_STATE_PAYED, PAY_STATE_CANCELED, PAY_STATE_GOODS_BACK]:
            return ERROR_ORDER_PAYED
        contract_price = order_detail.get('contract_price', 0)
        if current_price > contract_price:
            return ERROR_ORDER_PAY_MONEY_BIG_THAN_CONTRACT
            
        if wish_flag == USER_SHOP_ORDER_FLAG_RANDOM_CUTOFF and pay_type!=6:
            return ERROR_ORDER_CAN_NOT_PAYED
        if wish_flag == USER_SHOP_ORDER_FLAG_GET_COUPON:
            return ERROR_ORDER_CAN_NOT_PAYED
        price_total = order_detail.get('price_total', 0)
        if float(price_total) + float(current_price) > float(contract_price) + 1:
            return ERROR_ORDER_PAY_MONEY_BIG_THAN_CONTRACT
            
        if pay_type not in (2,3,5,6,7):
            return ERROR_ORDER_ORDER_NUMBER_EMPTY
        if pay_type == 3:
            handler = PercentCouponUtil(self.database)
            if not percent_coupon_id or not handler.check_user_can_use_coupon(user_phone, percent_coupon_id, shop_id, 10000):
                return ERROR_ORDER_CAN_NOT_USE_THIS_PERCENT_COUPON
        elif pay_type == 6 and creator == 0:
            return ERROR_ORDER_CAN_NOT_PAYED
            
        return ERROR_NO_ERROR
        
    def get_user_sales_pay_info(self, user_phone, sales_phone):
        handler = DbUtil(self.mobile_db, self.info_logger)
        bind_info = handler.get_pre_bind_info(user_phone)
        ret_dict = {}
        ret_dict['restrict'] = 0
        ret_dict['left_quota'] = 0
        if not bind_info or not sales_phone:
            return ret_dict
        bind_sales_phone = bind_info.get('sales_phone', '')
        pay_shop_id = handler.get_business_shop_id(sales_phone)
        bind_shop_id = handler.get_business_shop_id(bind_sales_phone)
        if (pay_shop_id or bind_shop_id) and pay_shop_id != bind_shop_id:
            return ret_dict
        elif pay_shop_id == 0 and bind_shop_id == 0:
            shop_handler = DbUtil(self.shop_db, self.info_logger)
            shop_users = shop_handler.get_cooperation_sales_same_shop(sales_phone)
            if bind_sales_phone not in shop_users:
                return ret_dict
            ret_dict['restrict'] = 1
            payed_money = handler.get_user_payed_money_by_sales(user_phone, shop_users)
            left = TOTAL_QUOTA - float(payed_money)
            left = left if left >= 0 else 0
            ret_dict['left_quota'] = left
        elif pay_shop_id and bind_shop_id:
            ret_dict['restrict'] = 1
            payed_money = handler.get_user_payed_money_by_shop_id(user_phone, pay_shop_id)
            left = TOTAL_QUOTA - float(payed_money)
            left = left if left >= 0 else 0
            ret_dict['left_quota'] = left
        return ret_dict

    ###@return 0  新窝顾客
    ###@return 1  店面顾客
    def get_customer_type(self, user_phone, sales_phone, shop_id):
        handler = DbUtil(self.mobile_db, self.info_logger)
        user_handler = DbUtil(self.user_db, self.info_logger)
        ###未注册的用户都是门店顾客
        if not user_handler.check_user_exits(user_phone):
            return 1
        bind_info = handler.get_pre_bind_info(user_phone)
        ##新窝顾客
        if not bind_info:
            return 0
        bind_sales_phone = bind_info.get('sales_phone', '')
        handler = DbBusinessUser(self.mobile_db, self.info_logger)
        bind_sales_info = handler.get_business_user_by_phone(bind_sales_phone)
        if not bind_sales_info:
            return 0
        if not shop_id and sales_phone:
            sales_info = handler.get_business_user_by_phone(sales_phone)
            shop_id = sales_info.get('shop_id', 0)
        bind_shop_id = bind_sales_info.get('shop_id', 0)
        bind_channel_id = bind_sales_info.get('channel_id', 0)
        shop_handler = DbShop(self.shop_db, self.info_logger)
        if bind_shop_id == 0 and shop_id == 0:
            shop_users = shop_handler.get_cooperation_sales_same_shop(sales_phone)
            shop_users.append(sales_phone)
            if bind_sales_phone not in shop_users:
                return 0
            else:
                return 1
        if bind_shop_id and shop_id:
            if str(bind_shop_id) == str(shop_id):
                return 1
            channel_id = shop_handler.get_shop_channel_id(shop_id)
            ###相同供应商,认为是店面顾客
            if str(bind_channel_id) == str(channel_id):
                return 1
            return 0
        return 0
    
    def get_user_use_coupon_times(self, user_phone, sales_phone, pay_shop_id):
        handler = DbShop(self.mobile_db, self.info_logger)
        if sales_phone and not pay_shop_id:
            pay_shop_id = handler.get_business_shop_id(sales_phone)
        
        if pay_shop_id:
            results = handler.get_user_pay_times_by_shop_id(user_phone, pay_shop_id)
            return len(results)
        
        else:
            shop_handler = DbShop(self.shop_db, self.info_logger)
            shop_users = shop_handler.get_cooperation_sales_same_shop(sales_phone)
            results = shop_handler.get_user_pay_times_by_sales(user_phone, shop_users)
            return len(results)
    
    def get_user_channel_pay_info(self, user_phone, sales_phone, pay_shop_id, default_quota = DEFAULT_USER_CHANNEL_QUOTA):
        handler = DbShop(self.mobile_db, self.info_logger)
        shop_handler = DbShop(self.shop_db, self.info_logger)        
        ret_dict = {}
        ret_dict['restrict'] = 1
        ret_dict['left_quota'] = default_quota
        base_quota = default_quota
        if sales_phone and not pay_shop_id:
            pay_shop_id = handler.get_business_shop_id(sales_phone)
        if pay_shop_id:
            channel_id = shop_handler.get_shop_channel_id(pay_shop_id)
        else:
            channel_id = -1
            
        quota_list = handler.get_user_channel_quota(user_phone)
        for quota_info in quota_list:
            quota_channel_id = quota_info.get('channel_id', 0)
            quota_sales_phone = quota_info.get('sales_phone', 0)
            pay_quota = quota_info.get('pay_quota', 0)
            if quota_channel_id == channel_id or quota_sales_phone == sales_phone:
                base_quota = pay_quota + default_quota
                break
        
        if pay_shop_id == 0:
            shop_users = shop_handler.get_cooperation_sales_same_shop(sales_phone)
            if not shop_users:
                shop_users.append(sales_phone)
            payed_money = handler.get_user_payed_money_by_sales(user_phone, shop_users)

        else:
            payed_money = handler.get_user_payed_money_by_channel_id(user_phone, channel_id)
        print payed_money
        left = float(base_quota) - float(payed_money)
        left = left if left >= 0 else 0
        ret_dict['left_quota'] = left
        return ret_dict
        
    def get_current_quota(self, order_number):
        handler = DbUtil(self.mobile_db, self.info_logger)
        order_info = handler.get_order_detail(order_number)
        user_phone = order_info.get('user_phone', '')
        sales_phone = order_info.get('sales', '')
        #return self.get_user_sales_pay_info(user_phone, sales_phone)
        return self.get_user_channel_pay_info(user_phone, sales_phone, 0)
        
    def handle_money_payed(self, order_number, total_money, money, coupon):
        return True
        if not order_number:
            return False
        handler = DbUtil(self.mobile_db, self.info_logger)
        order_detail = handler.get_order_detail(order_number)
        pre_cooperation = order_detail.get('pre_cooperation', 0)
        sales = order_detail.get('sales', '')
        promote_shop_handler = DbPromote(self.shop_db, self.info_logger)
        if not promote_shop_handler.update_pre_cooperation_times(sales):
            sales_list = promote_shop_handler.get_pre_cooperation_sales_list(sales)
            if sales_list:
                self.info_logger.info('update not pre_cooperation %s'%(','.join(sales_list)))
                promote_mobile_handler = DbPromote(self.mobile_db, self.info_logger)
                promote_mobile_handler.update_sales_not_pre_cooperation(sales_list)
            else:
                self.info_logger.error('update not pre_cooperation but no user')
        return True
    
    def has_sent_coupon(self, user_id, order_number):
        handler = DbOrderUtil(self.mobile_db, self.info_logger)
        return handler.has_sent_coupon(user_id, order_number)
        
    def send_order_coupon(self, user_id, order_number, total_money, quota_left_dict):
        try:
            handler = DbUtil(self.mobile_db, self.info_logger)
            if not quota_left_dict:
                return False
            left_quota = quota_left_dict.get('left_quota', 0)
            restrict = int(quota_left_dict.get('restrict', 0))
            total_money = float(total_money)
            left_quota = float(left_quota)
            tmp_score_money = 0
            if restrict == 0:
                score_money = float(total_money * 3 / float(100))
            elif restrict == 1:
                tmp_score_money = min(total_money, left_quota)
                score_money = float(tmp_score_money * 3 / float(100))
            else:
                return False
            if score_money >= 0.01:
                self.info_logger.info('send_order_coupon score_money %s %s %s %s'%(str(score_money), str(total_money), str(left_quota),str(tmp_score_money)))
                handler.create_user_score_info(user_id, score_money, 5, order_number)
                return True
            else:
                return False
        except Exception,e:
            self.info_logger.error('send_order_coupon except %s'%(e))
            return False

    def send_order_coupon_v2(self, user_id, order_number, total_money):
        try:
            ###send coupon not any more
            return True
            handler = DbOrderUtil(self.mobile_db, self.info_logger)
            total_money = float(total_money)
            score_money = float(total_money * 10 / float(100))

            if score_money >= 0.01:
                handler.create_user_score_info_v2(user_id, score_money, 5, order_number)
                return True
            else:
                return False
        except Exception,e:
            self.info_logger.error('send_order_coupon_v2 except %s'%(e))
            return False

    def is_old_coupon_version(self, order_number, total_money, money, coupon):
        try:
            total_money = float(total_money)
            money = float(money)
            coupon = float(coupon)
            if abs(total_money - money - coupon) < 0.01:
                self.info_logger.info('is_old_coupon_version new %s %s %s %s'%(str(order_number), str(total_money), str(money),str(coupon)))
                return False
            else:
                self.info_logger.info('is_old_coupon_version old %s %s %s %s'%(str(order_number), str(total_money), str(money),str(coupon)))
                return True
        except Exception,e:
            self.info_logger.error('is_old_coupon_version except %s'%(e))
            return False
    
    def remove_item_from_shopping_list(self, shopping_id):
        if not shopping_id:
            return False
        handler = DbUtil(self.mobile_db, self.info_logger)
        return handler.remove_item_from_shopping_list(shopping_id)
        
    def check_pay_state(self, order_info, type, money):
        state = order_info['state']
        price_real = order_info['price_real']
        price_total = order_info['price_total']
        price_pre = order_info['price_pre']
        pre_flag = order_info['pre_flag']
        ## not payed
        if state == PAY_STATE_NOT_PAYED:
            if type == PAY_ORDER_TYPE_TAIL:
                return False
            else:
                return True
        ## subscribe payed
        if state == PAY_STATE_SUBSCRIBE_PAYED:
            if type == PAY_ORDER_TYPE_TAIL or type == PAY_ORDER_TYPE_SUBSCRIBE:
                return True
            else:
                return False
        return False

    def get_order_coupon_usage(self, user_id, order_number, current_price):
        if not order_number:
            return 0
        handler = DbOrderUtil(self.mobile_db, self.info_logger)
        order_detail = handler.get_order_detail(order_number)        
        if not order_detail:
            return 0
        contract_coupon = float(current_price) * 10 / 100
        user_phone = order_detail.get('user_phone', '')
        if str(user_phone) in ['15810171718']:
            contract_coupon = contract_coupon * 2
        current_coupon = float(handler.get_user_current_coupon(user_id))
        
        return min(contract_coupon, current_coupon)
        
        ###
        sales_phone = order_detail.get('sales', '')
        shop_id = order_detail.get('shop_id', 0)
        
        # if self.get_customer_type(user_phone, sales_phone, shop_id) == 1:
            # return 0
        
        if not shop_id:
            return 0
        
        get_total = 0
        get_from_this = 0
        usage = 0
        
        ###在当前店员首次消费之前，获取全部消费，首次之后，只获取当前店铺的消费
        usage_total = 1
        
        coupon_infos = handler.get_user_shop_recieved_coupon(user_id)
        print coupon_infos
        ####'积分类型 0 消费获取类 1 赠送类 2 消费记录类 3 晒单类 4邀请消费类 5 需要审核的消费获取类'
        for coupon in coupon_infos:
            coupon_money = float(coupon['money'])
            coupon_type = coupon['type']
            coupon_shop_id = coupon['shop_id']
            verify_state = coupon['verify_state']
            if coupon_type in [0,1,3,5,7] and verify_state != 2:
                if str(shop_id) == str(coupon_shop_id):
                    get_from_this += coupon_money
                    usage_total = 0
                    self.info_logger.info('get_order_coupon_usage consume from same shop get %s'%(str(coupon_money)))
                else:
                    get_total += coupon_money
            elif coupon_type == 2 and usage_total:
                usage += coupon_money
                # if str(shop_id) == str(coupon_shop_id):
                    # usage_total = 0
            elif coupon_type == 2 and usage_total == 0 and str(shop_id) == str(coupon_shop_id):
                usage += coupon_money
        
        can_usage = get_total - usage
        
        self.info_logger.info('get_order_coupon_usage get_total %s usage %s can_usage %s current_coupon %s contract_coupon %s'%(str(get_total), str(usage), str(can_usage), str(current_coupon), str(contract_coupon)))

        if current_coupon >= 0:
            can_usage = min(current_coupon, can_usage)
        if contract_coupon >= 0:
            can_usage = min(can_usage, contract_coupon)
        if can_usage < 0:
            can_usage = 0
        return can_usage

    def verify_order_coupon_sucess(self, order_number, orig_verify_state):
        if orig_verify_state is None or orig_verify_state == 3:
            return False
            
        handler = DbOrderUtil(self.mobile_db, self.info_logger)
        order_detail = handler.get_order_detail(order_number)
        user_phone = order_detail.get('user_phone', '')
        if not user_phone:
            return False
        passport_handler = DbOrderUtil(self.user_db, self.info_logger)
        customer_info = passport_handler.get_userinfo_by_user_name(user_phone)
        if not customer_info:
            return False
        user_id = customer_info[0]
        if not user_id:
            return False
        
        used_coupon = order_detail.get('coupon', 0)
        coupons = handler.get_order_coupons(order_number)
        if len(coupons) == 1:
            handler.pull_order_score(user_id, order_number)
            return False
        cutoff_coupon = 0
        return_coupon = 0
        cutoff_id = 0
        return_id = 0
        delta_coupon = 0
        remove_id_list = []
        for coupon in coupons:
            if coupon[2] == 6:
                cutoff_coupon = coupon[1]
                cutoff_id = coupon[0]
            elif coupon[2] == 7:
                return_coupon = coupon[1]
                return_id = coupon[0]
        if cutoff_coupon == 0:
            return False
        delta_coupon = cutoff_coupon - return_coupon
        
        pay_type = order_detail.get('pay_type', 0)
        state = order_detail.get('state', 0)
        if pay_type != 4 and state == 4:
            handler.update_order_state(order_number, 2)
        if cutoff_id:
            remove_id_list.append(cutoff_id)
        if return_id:
            remove_id_list.append(return_id)
        print user_id, order_number
        
        return handler.do_order_coupon_sucess(user_id, remove_id_list, delta_coupon)

    def verify_order_coupon_failed(self, order_number, orig_verify_state):
        try:
            if orig_verify_state is None or orig_verify_state == 4:
                return False
            handler = DbOrderUtil(self.mobile_db, self.info_logger)
            order_detail = handler.get_order_detail(order_number)
            user_phone = order_detail.get('user_phone', '')
            
            pay_type = order_detail.get('pay_type', 0)
            #no need update state
            # if pay_type != 4:
                # handler.update_order_state(order_number, 4)
                
            if not user_phone:
                return False
            passport_handler = DbOrderUtil(self.user_db, self.info_logger)
            customer_info = passport_handler.get_userinfo_by_user_name(user_phone)
            if not customer_info:
                return False
            user_id = customer_info[0]
            if not user_id:
                return False
                
            return_coupon = order_detail.get('coupon', 0)
            coupons = handler.get_order_coupons(order_number, 5)
            if len(coupons) != 1:
                return False
            coupon_info = coupons[0]
            type = coupon_info[2]
            state = coupon_info[3]
            verify_state = coupon_info[4]
            cutoff_coupon = float(coupon_info[1])
            if state == 0 and verify_state == 2:
                use_cutoff_coupon = 0
            else:
                use_cutoff_coupon = float(coupon_info[1])
            coupons = handler.get_order_coupons(order_number, 2)
            need_return = True
            if len(coupons) == 0:
                need_return = False

            return handler.do_order_coupon_failed(user_id, order_number, return_coupon, cutoff_coupon, use_cutoff_coupon, need_return)
        except Exception,e:
            print e
            self.logger.error('verify_order_coupon_failed except %s'%(e))
            return False
    def format_content(self, type, content):
        if not content:
            return ''
        if type == PAY_ORDER_TYPE_ALL:
            new_content = u'这是全款支付|' + content
        elif type == PAY_ORDER_TYPE_SUBSCRIBE:
            new_content = u'这是订金支付|' + content
        elif type == PAY_ORDER_TYPE_TAIL:
            new_content = u'这是尾款支付|' + content
        else:
            return ''
        return new_content
        
    def record_order_change(self, business_name):
        key = BUSINESS_ORDER_CHANGE_NUM_PREFIX + str(business_name)
        if not self.redis.exists(key):
            self.redis.save_expire(key, EXPIRE_ORDER_CHANGE, 1)
        else:
            self.redis.incr(key)
        return True

    def get_order_change(self, business_name):
        key = BUSINESS_ORDER_CHANGE_NUM_PREFIX + str(business_name)
        num = self.redis.get(key)
        self.redis.delete(key)
        if not num:
            return 0
        else:
            return int(num)

    def record_channel_order_change(self, channel_id):
        key = BUSINESS_CHANNEL_ORDER_CHANGE_NUM_PREFIX + str(channel_id)
        if not self.redis.exists(key):
            self.redis.save_expire(key, EXPIRE_ORDER_CHANGE, 1)
        else:
            self.redis.incr(key)
        return True

    def get_channel_order_change(self, channel_id):
        key = BUSINESS_CHANNEL_ORDER_CHANGE_NUM_PREFIX + str(channel_id)
        num = self.redis.get(key)
        self.redis.delete(key)
        if not num:
            return 0
        else:
            return int(num)
    
    def clear_sales_list_cache(self, user_name):
        prefixs = []
        prefixs.append(BUSINESS_ORDER_SALES_RECENTLY_LIST + str(user_name))
        prefixs.append(BUSINESS_ORDER_SALES_UNPAYED_LIST + str(user_name))
        prefixs.append(BUSINESS_ORDER_SALES_PAYED_LIST + str(user_name))
        prefixs.append(BUSINESS_ORDER_SALES_ALL_LIST + str(user_name))
        return self.redis.delete_prefixs(prefixs)

    def clear_channel_list_cache(self, channel_id):
        prefixs = []
        prefixs.append(BUSINESS_ORDER_CHANNEL_RECENTLY_LIST + str(channel_id))
        prefixs.append(BUSINESS_ORDER_CHANNEL_UNPAYED_LIST + str(channel_id))
        prefixs.append(BUSINESS_ORDER_CHANNEL_PAYED_LIST + str(channel_id))
        prefixs.append(BUSINESS_ORDER_CHANNEL_ALL_LIST + str(channel_id))
        return self.redis.delete_prefixs(prefixs)

    def cache_sales_recently_order_list(self, user_name, num, cache_data):
        key = BUSINESS_ORDER_SALES_RECENTLY_LIST + str(user_name) + '_' + str(num)
        return self.redis.save_expire(key, EXPIRE_ORDER_CHANGE, cache_data)
    
    def get_sales_recently_order_list(self, user_name, num):
        key = BUSINESS_ORDER_SALES_RECENTLY_LIST + str(user_name) + '_' + str(num)
        return self.redis.get(key)

    def cache_sales_unpayed_order_list(self, user_name, start, num, cache_data):
        key = BUSINESS_ORDER_SALES_UNPAYED_LIST + str(user_name) + '_' + str(start) + '_' + str(num)
        return self.redis.save_expire(key, EXPIRE_ORDER_CHANGE, cache_data)
    
    def get_sales_unpayed_order_list(self, user_name, start, num):
        key = BUSINESS_ORDER_SALES_UNPAYED_LIST + str(user_name) + '_' + str(start) + '_' + str(num)
        return self.redis.get(key)

    def cache_sales_payed_order_list(self, user_name, start, num, cache_data):
        key = BUSINESS_ORDER_SALES_PAYED_LIST + str(user_name) + '_' + str(start) + '_' + str(num)
        return self.redis.save_expire(key, EXPIRE_ORDER_CHANGE, cache_data)
    
    def get_sales_payed_order_list(self, user_name, start, num):
        key = BUSINESS_ORDER_SALES_PAYED_LIST + str(user_name) + '_' + str(start) + '_' + str(num)
        return self.redis.get(key)

    def cache_sales_all_order_list(self, user_name, start, num, cache_data):
        key = BUSINESS_ORDER_SALES_ALL_LIST + str(user_name) + '_' + str(start) + '_' + str(num)
        return self.redis.save_expire(key, EXPIRE_ORDER_CHANGE, cache_data)
    
    def get_sales_all_order_list(self, user_name, start, num):
        key = BUSINESS_ORDER_SALES_ALL_LIST + str(user_name) + '_' + str(start) + '_' + str(num)
        return self.redis.get(key)
        
    def cache_channel_recently_order_list(self, channel, num, cache_data):
        key = BUSINESS_ORDER_CHANNEL_RECENTLY_LIST + str(channel) + '_' + str(num)
        return self.redis.save_expire(key, EXPIRE_ORDER_CHANGE, cache_data)
    
    def get_channel_recently_order_list(self, channel, num):
        key = BUSINESS_ORDER_CHANNEL_RECENTLY_LIST + str(channel) + '_' + str(num)
        return self.redis.get(key)

    def cache_channel_unpayed_order_list(self, channel, start, num, cache_data):
        key = BUSINESS_ORDER_CHANNEL_UNPAYED_LIST + str(channel) + '_' + str(start) + '_' + str(num)
        return self.redis.save_expire(key, EXPIRE_ORDER_CHANGE, cache_data)
    
    def get_channel_unpayed_order_list(self, channel, start, num):
        key = BUSINESS_ORDER_CHANNEL_UNPAYED_LIST + str(channel) + '_' + str(start) + '_' + str(num)
        return self.redis.get(key)

    def cache_channel_payed_order_list(self, channel, start, num, cache_data):
        key = BUSINESS_ORDER_CHANNEL_PAYED_LIST + str(channel) + '_' + str(start) + '_' + str(num)
        return self.redis.save_expire(key, EXPIRE_ORDER_CHANGE, cache_data)
    
    def get_channel_payed_order_list(self, channel, start, num):
        key = BUSINESS_ORDER_CHANNEL_PAYED_LIST + str(channel) + '_' + str(start) + '_' + str(num)
        return self.redis.get(key)

    def cache_channel_all_order_list(self, channel, start, num, cache_data):
        key = BUSINESS_ORDER_CHANNEL_ALL_LIST + str(channel) + '_' + str(start) + '_' + str(num)
        return self.redis.save_expire(key, EXPIRE_ORDER_CHANGE, cache_data)
    
    def get_channel_all_order_list(self, channel, start, num):
        key = BUSINESS_ORDER_CHANNEL_ALL_LIST + str(channel) + '_' + str(start) + '_' + str(num)
        return self.redis.get(key)
    
        
if __name__ == '__main__':
    order_handler = OrderUtil(settings.COMMON_DATA)
    #print order_handler.get_order_coupon_usage(75175, '1441529575751752878', 331)
    print order_handler.verify_order_coupon_failed('1441888702751089888', 1)
    ##print order_handler.is_old_coupon_version('345345345', 500, 100, 400)
    #print order_handler.do_order_coupon_failed(23434, '234234', 45, 65)
