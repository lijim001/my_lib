#coding=utf-8

import os,sys,string,hashlib
from datetime import datetime, timedelta
import simplejson as json

G_PUSH_BAIDU_PATH = os.path.split(os.path.realpath(__file__))[0]

if __name__ == '__main__':
    sys.path.append(G_PUSH_BAIDU_PATH + '/../../')
    os.environ['DJANGO_SETTINGS_MODULE'] = 'MobileService.settings'
    from django.conf import settings

from apns_clerk import *    
from MobileService.util.DbUtil import DbUtil
from MobileService.business_user.db_business_user import *
from MobileService.push_baidu.Channel import Channel
from MobileService.push_jpush.JpushUtil import JpushUtil

APP_BUSINESS = 'wallet_business'
APP_CLIENT = 'wallet_client'

KEY_TYPE_ORDER_STATE_CHANGED = 1
KEY_TYPE_AWARD = 2
KEY_TYPE_OPERATION = 3
KEY_TYPE_TASK = 4
KEY_TYPE_NOTICE_ACTION = 5
KEY_TYPE_RECIEVE_ORDER = 6
KEY_TYPE_PAY_MONEY = 7
KEY_TYPE_ORDER_PAYED_BUSINESS = 8
KEY_TYPE_COMMISION_SETTLED = 9
KEY_TYPE_COMMENT = 10
KEY_TYPE_ORDER_VERIFY_FAILED_BUSINESS = 11
KEY_TYPE_OPEN_APP = 12
KEY_TYPE_NOTICE_COUNT = 13
KEY_TYPE_SUBSCRIBE_SHOP_TO_SALES = 14
KEY_TYPE_SUBSCRIBE_SHOP_TO_CUSTOMER = 15
KEY_TYPE_PURCHASE = 16

KEY_ACTION_INQUIRE = 'inquire'
KEY_ACTION_OPEN_URL = 'open_url'
KEY_ACTION_OPEN_AWARD = 'open_award'
KEY_ACTION_OPEN_AWARD_DETAIL = 'open_award_detail'

KEY_ACTION_PAY_ORDER = 'pay_order'
KEY_ACTION_ORDER_DETAIL = 'order_detail'
KEY_ACTION_COMMENT = 'goods_detail'
KEY_ACTION_NOTICE_COUNT = 'notice_count'
KEY_ACTION_SUBSCRIBE_SHOP_LIST = 'sub_shop_list'
KEY_ACTION_OPEN_PURCHASE = 'open_purchase'

ACTION_TO_MAIN_TRANSACTION = 'm_transaction'
ACTION_TO_MAIN_INQUIRE = 'm_inquire'
ACTION_TO_MAIN_RECOMMANED = 'm_recommend'
ACTION_TO_MAIN_ACCOUNT = 'm_account'

KEY_SUB_TYPE_OPERATION_RED_AWARD = 1
KEY_SUB_TYPE_OPERATION_XINWO_NOTICE = 2

PUSH_LIST = [
    '18600595575',
]
class DbBaiduPush(DbUtil):
    def __init__(self, database, logger=None):
        DbUtil.__init__(self, database, logger)
        
    def get_push_info_by_id(self, user_id, app):
        self.get_db_connect()
        sql = 'select baidu_user_id,baidu_channel_id,platform,device_token,channel from push_baidu where user_id="%s" and app="%s"'%(str(user_id), str(app))
        try:
            count = self.cursor.execute(sql)
            ret_list = []
            if count == 0:
                self.release_db_connect()
                return []
            if count > 0:
                self.cursor.scroll(0, mode='absolute')
                results = self.cursor.fetchall()
                for result in results:
                    ret_list.append((result[0],result[1],result[2],result[3],result[4]))
                self.release_db_connect()
            return ret_list
        except Exception,e:
            if self.logger:
                self.logger.error('get_push_info_by_id except %s'%(e))
            self.release_db_connect()
            return []

    def get_ios_push_info(self, app, start=0, num=20):
        self.get_db_connect()
        if app == 'wallet_business':
            if start == 0:
                sql = 'select pj.id,device_token,channel,us.id from push_baidu pj left join user_shop us on us.telephone=pj.user_phone where app="%s" and pj.platform="iphone" and us.user_state=2 order by pj.id limit %s'%(str(app), str(num))
            else:
                sql = 'select pj.id,device_token,channel,us.id from push_baidu pj left join user_shop us on us.telephone=pj.user_phone where app="%s" and pj.platform="iphone" and us.user_state=2 and pj.id > %s order by pj.id limit %s'%(str(app), str(start), str(num))
        else:
            if start == 0:
                sql = 'select id,device_token,channel,1 from push_baidu where app="%s" and platform="iphone" order by id limit %s'%(str(app), str(num))
            else:
                sql = 'select id,device_token,channel,1 from push_baidu where app="%s" and platform="iphone" and id > %s order by id limit %s'%(str(app), str(start), str(num))
        try:
            count = self.cursor.execute(sql)
            ret_list = []
            if count == 0:
                self.release_db_connect()
                return []
            if count > 0:
                self.cursor.scroll(0, mode='absolute')
                results = self.cursor.fetchall()
                for result in results:
                    ret_list.append((result[0], result[1], result[2], result[3]))
                self.release_db_connect()
            return ret_list
        except Exception,e:
            if self.logger:
                self.logger.error('get_ios_push_info except %s'%(e))
            self.release_db_connect()    
            return []
            
    def get_push_info_by_phone(self, user_phone, app, platform='iphone'):
        self.get_db_connect()
        sql = 'select baidu_user_id,baidu_channel_id, platform,device_token,channel from push_baidu where user_phone="%s" and app="%s" and platform="%s"'%(str(user_phone), str(app), platform)
        try:
            count = self.cursor.execute(sql)
            ret_list = []
            if count == 0:
                self.release_db_connect()
                return []
            if count > 0:
                self.cursor.scroll(0, mode='absolute')
                results = self.cursor.fetchall()
                for result in results:
                    ret_list.append((result[0], result[1],result[2],result[3],result[4]))
                self.release_db_connect()
            return ret_list
        except Exception,e:
            if self.logger:
                self.logger.error('get_push_info_by_phone except %s'%(e))
            self.release_db_connect()    
            return []

    def get_ios_push_infos_by_phones(self, user_phone_list, app):
        self.get_db_connect()
        if not user_phone_list:
            return {}
        sql = 'select device_token,channel from push_baidu where user_phone in (%s) and app="%s" and platform="iphone"'%(','.join(user_phone_list), str(app))
        try:
            count = self.cursor.execute(sql)
            ret_dict = {}
            if count == 0:
                self.release_db_connect()
                return {}
            if count > 0:
                self.cursor.scroll(0, mode='absolute')
                results = self.cursor.fetchall()
                for result in results:
                    if ret_dict.has_key(result[1]):
                        ret_dict[result[1]].append(result[0])
                    else:
                        ret_dict[result[1]] = [result[0]]
                self.release_db_connect()
            return ret_dict
        except Exception,e:
            if self.logger:
                self.logger.error('get_ios_push_infos_by_phones except %s'%(e))
            self.release_db_connect()    
            return {}
            
    def get_jpush_info_by_phone(self, user_phone, app):
        self.get_db_connect()
        sql = 'select distinct(jpush_alias) from push_jpush where user_phone="%s" and app="%s"'%(str(user_phone), str(app))
        try:
            count = self.cursor.execute(sql)
            ret_list = []
            if count == 0:
                self.release_db_connect()
                return []
            if count > 0:
                self.cursor.scroll(0, mode='absolute')
                results = self.cursor.fetchall()
                for result in results:
                    ret_list.append(result[0])
                self.release_db_connect()
            return ret_list
        except Exception,e:
            if self.logger:
                self.logger.error('get_jpush_info_by_phone except %s'%(e))
            self.release_db_connect()
            return []

    def get_jpush_info_by_phones(self, user_phone_list, app):
        if not user_phone_list:
            return []
        user_phone_list = [ str(i) for i in user_phone_list ]
        self.get_db_connect()
        sql = 'select distinct(jpush_alias) from push_jpush where user_phone in ("%s") and app="%s"'%('","'.join(user_phone_list), str(app))
        print sql
        try:
            count = self.cursor.execute(sql)
            ret_list = []
            if count == 0:
                self.release_db_connect()
                return []
            if count > 0:
                self.cursor.scroll(0, mode='absolute')
                results = self.cursor.fetchall()
                for result in results:
                    ret_list.append(result[0])
                self.release_db_connect()
            return ret_list
        except Exception,e:
            if self.logger:
                self.logger.error('get_jpush_info_by_phones except %s'%(e))
            self.release_db_connect()
            return []
            
class PushBaiduBaseUtil():
    def __init__(self, config, app= APP_BUSINESS,logger=None):
        self.logger = config['mobile_logger']
        if app == APP_BUSINESS:
            self.app_key = config['business_push_baidu'][0]
            self.app_secret = config['business_push_baidu'][1]
            self.jpush_app_key = config['business_push_jpush'][0]
            self.jpush_app_secret = config['business_push_jpush'][1]
        else:
            self.app_key = config['client_push_baidu'][0]
            self.app_secret = config['client_push_baidu'][1]
            self.jpush_app_key = config['client_push_jpush'][0]
            self.jpush_app_secret = config['client_push_jpush'][1]

        self.app = app
        self.db_config = config['mobile_db']
        self.db_shop = config['shop_db']
        self.environment = config['environment']
        
    def get_message_keys(self, message):
        return hashlib.md5(message).hexdigest()

    def send_message_one_user_with_jpush(self, jpush_info_list, message_dict = {}):
        try:
            jpush = JpushUtil(self.jpush_app_key, self.jpush_app_secret)
            audience = tuple(jpush_info_list)
            if self.logger:
                self.logger.info(audience)
            ret = jpush.pushMessage(audience, message_dict)
            if ret:
                if self.logger:
                    self.logger.info('jpush success')
                    self.logger.info(ret)
            return ret
        except Exception,e:
            if self.logger:
                self.logger.error('send_message_one_user_with_jpush except %s'%(e))
            return False

    def send_message_one_user(self, channel_id, user_id, platform, message_dict = {}):
        c = Channel(self.app_key, self.app_secret)
        push_type = 1
        optional = dict()
        optional[Channel.CHANNEL_ID] = channel_id
        optional[Channel.USER_ID] = user_id
        
        message = json.dumps(message_dict)
        message_key = self.get_message_keys(message)
        ret = False
        if platform == 'android':
            optional[Channel.DEVICE_TYPE] = 3
            ret = c.pushMessage(push_type, message, message_key, optional)
            success_amount = 0
            if ret:
                response_info = ret.get('response_params', {})
                if response_info:
                    success_amount = response_info.get('success_amount', 0)
                if self.logger:
                    self.logger.info('baidu push %s %s'%(str(message_dict), str(success_amount)))

        elif platform == 'iphone':
            optional[Channel.DEVICE_TYPE] = 4
            ret = c.pushMessage(push_type, message, message_key, optional)
        return ret

    def send_ios_message(self, app, device_token_list, channel, message_dict = {}):
        for i in range(0,2):
            try:
                cert_file = str(app)
                if channel and self.environment != 'test':
                    cert_file += '_' + str(channel)
                if self.environment == 'test':
                    cert_file = cert_file + '_test'
                cert_file = cert_file + '.pem'
                self.logger.info('send ios message using %s'%(str(cert_file)))
                cert_file = os.path.join(G_PUSH_BAIDU_PATH, cert_file)

                session = Session()
                if self.environment == 'test':
                    con = session.get_connection(("gateway.sandbox.push.apple.com", 2195), cert_file=cert_file)
                else:
                    con = session.get_connection(("gateway.push.apple.com", 2195), cert_file=cert_file)
                title = message_dict.get('content','')
                message = Message(device_token_list, alert=title, extra=message_dict)
                srv = APNs(con)
                res = srv.send(message)
                error = 0
                for token, reason in res.failed.items():
                    code, errmsg = reason
                    error = 1
                    if self.logger:
                        self.logger.error("Device faled: {0}, reason: {1}".format(token, errmsg))
                # Check failures not related to devices.
                for code, errmsg in res.errors:
                    error = 1
                    if self.logger:
                        self.logger.error(errmsg)
                if self.logger and error == 0:
                    self.logger.info('Push ios success %s %s'%(str(message_dict), str(device_token_list)))
                if error == 0:
                    return True
            except Exception,e:
                self.logger.error('send_ios_message except %s'%(e))
        return False
        
    def send_message_tag_users(self, tag_name, message_dict = {}):
        c = Channel(self.app_key, self.app_secret)
        push_type = 2
        optional = dict()
        optional[Channel.TAG_NAME] = tag_name
        
        message = json.dumps(message_dict)
        message_key = self.get_message_keys(message)
        optional[Channel.DEVICE_TYPE] = 3
        ret1 = c.pushMessage(push_type, message, message_key, optional)
        optional[Channel.DEVICE_TYPE] = 4
        ret2 = c.pushMessage(push_type, message, message_key, optional)
        return ret1 and ret2
        
    def send_message_all(self, message_dict = {}):
        c = Channel(self.app_key, self.app_secret)
        push_type = 3
        optional = dict()
        message = json.dumps(message_dict)
        message_key = self.get_message_keys(message)        
        ret = c.pushMessage(push_type, message, message_key, optional)
        print ret

    def send_messages_all_with_jpush(self, message_dict = {}):
        jpush = JpushUtil(self.jpush_app_key, self.jpush_app_secret)
        ret = jpush.pushMessage('all', message_dict)
        if ret:
            self.logger.info(ret)
            if self.logger:
                self.logger.info('jpush success')
        return ret


class PushBaiduUtil(PushBaiduBaseUtil):
    def __init__(self, push_baidu_config, app= APP_BUSINESS, logger=None):
        PushBaiduBaseUtil.__init__(self, push_baidu_config, app, logger)
    
    def send_message_one_user_phone(self, user_phone, message_dict = {}):
        if self.app == APP_BUSINESS:
            app_name = 'wallet_business'
        elif self.app == APP_CLIENT:
            app_name = 'wallet_client'
        else:
            return False
        handler = DbBaiduPush(self.db_config, self.logger)
        try:
            channel_token_dict = handler.get_ios_push_infos_by_phones([user_phone], self.app)
            for channel, token_list in channel_token_dict.items():
                self.send_ios_message(self.app, token_list, channel, message_dict)
            push_jpush_info_list = handler.get_jpush_info_by_phone(user_phone, self.app)           
            if push_jpush_info_list:
                self.send_message_one_user_with_jpush(push_jpush_info_list, message_dict)
            if not channel_token_dict and not push_jpush_info_list:
                self.logger.error('send_message_one_user_phone no find user %s'%(str(user_phone)))
        except Exception,e:
            self.logger.error('send_message_one_user_phone except %s'%e)
        return True

    def send_message_user_phones(self, user_phone_list, message_dict = {}):
        if self.app == APP_BUSINESS:
            app_name = 'wallet_business'
        elif self.app == APP_CLIENT:
            app_name = 'wallet_client'
        else:
            return False
        handler = DbBaiduPush(self.db_config, self.logger)
        try:
            channel_token_dict = handler.get_ios_push_infos_by_phones(user_phone_list, self.app)
            for channel, token_list in channel_token_dict.items():
                token_list = list(set(token_list))
                self.send_ios_message(self.app, token_list, channel, message_dict)
            push_jpush_info_list = handler.get_jpush_info_by_phones(user_phone_list, self.app)
            if push_jpush_info_list:
                self.send_message_one_user_with_jpush(push_jpush_info_list, message_dict)
                self.logger.info('jpush to %s'%(str(push_jpush_info_list)))
        except Exception,e:
            print e
        return True
        
    def send_message_one_user_id(self, user_id, message_dict = {}):
        if self.app == APP_BUSINESS:
            app_name = 'wallet_business'
        elif self.app == APP_CLIENT:
            app_name = 'wallet_client'
        else:
            return False
        handler = DbBaiduPush(self.db_config, self.logger)
        push_info_list = handler.get_push_info_by_id(user_id, self.app)
        for (baidu_user_id,baidu_channel_id,platform,device_token,channel) in push_info_list:
            print baidu_user_id,baidu_channel_id
            if not baidu_user_id:
                continue
            if platform == 'iphone':
                if not device_token:
                    continue            
                self.send_ios_message(self.app, [device_token], channel, message_dict)
            else:
                self.send_message_one_user(baidu_channel_id, baidu_user_id, platform, message_dict)
        return True

    def send_message_all_android_users(self, message_dict = {}):
        if self.app == APP_BUSINESS:
            app_name = 'wallet_business'
        elif self.app == APP_CLIENT:
            app_name = 'wallet_client'
        else:
            return False
        self.send_message_all(message_dict)
        return True

    def send_message_all_android_users_with_jpush(self, message_dict={}):
        if self.app == APP_BUSINESS:
            app_name = 'wallet_business'
        elif self.app == APP_CLIENT:
            app_name = 'wallet_client'
        else:
            return False
        self.send_messages_all_with_jpush(message_dict)
        return True

    def send_message_all_ios_users(self, message_dict = {}):
        if self.app == APP_BUSINESS:
            app_name = 'wallet_business'
        elif self.app == APP_CLIENT:
            app_name = 'wallet_client'
        else:
            return False
        handler = DbBaiduPush(self.db_config, self.logger)
        start = 0
        total_sent_device = 0
        while 1:
            token_channel_list = handler.get_ios_push_info(self.app, start, 20)
            if not token_channel_list:
                break
            token_list = []
            for id, device_token, channel, other_id in token_channel_list:
                if id > start:
                    start = id
                if channel != 'normal' or other_id is None:
                    continue
                token_list.append(device_token)
            if token_list:
                self.send_ios_message(self.app, token_list, channel, message_dict)
                total_sent_device += len(token_list)
        self.logger.info('send_message_all_ios_users sent to %s device ok'%(str(total_sent_device)))
        return True
        
    def send_message_channel_users(self, channel_id, message_dict = {}):
        if self.app == APP_BUSINESS:
            tag_name = 'ch' + str(channel_id)
        else:
            return False
        return self.send_message_tag_users(tag_name, message_dict)

    def send_message_shop_users(self, shop_id, message_dict = {}):
        if self.app == APP_BUSINESS:
            tag_name = 'sh' + str(shop_id)
        else:
            return False
        return self.send_message_tag_users(tag_name, message_dict)
    
    def init_notify_data(self):
        info_dict = {}
        info_dict['type'] = -1
        info_dict['action'] = ''
        info_dict['title'] = ''
        info_dict['content'] = ''
        info_dict['sub_type'] = -1
        info_dict['save'] = 0
        info_dict['extra'] = {}
        return info_dict
    
    def send_new_award_notify(self, award_type, send_phone, content):
        info_dict = self.init_notify_data()
        info_dict['type'] = KEY_TYPE_AWARD
        info_dict['extra'] = { 'award_type' : award_type }
        info_dict['action'] = KEY_ACTION_OPEN_AWARD
        info_dict['save'] = 1
        info_dict['title'] = u'钱包通知'
        info_dict['content'] = content
        self.send_message_one_user_phone(send_phone, info_dict)
    
    ##send to business
    def send_award_notify(self, send_phone, award_type, content):
        info_dict = self.init_notify_data()
        info_dict['type'] = KEY_TYPE_AWARD
        info_dict['extra'] = { 'award_type' : award_type }
        info_dict['action'] = KEY_ACTION_OPEN_AWARD
        info_dict['save'] = 1
        info_dict['title'] = u'钱包通知'
        info_dict['content'] = content
        if award_type == 12:
            pass
        else:
            return
        
        self.send_message_one_user_phone(send_phone, info_dict)

    ##send to business
    def send_award_reject_notify(self, send_phone):
        info_dict = self.init_notify_data()
        info_dict['type'] = KEY_TYPE_AWARD
        info_dict['extra'] = { 'award_type' : 11 }
        info_dict['action'] = KEY_ACTION_OPEN_AWARD
        info_dict['save'] = 1
        info_dict['title'] = u'奖励领取'

        info_dict['content'] = u'您选择的提现方式信息有误，无法为您返现，请及时更改。'
        self.send_message_one_user_phone(send_phone, info_dict)
        
    ##send to customer
    def send_order_been_created(self, send_phone, from_phone, order_number):
        info_dict = self.init_notify_data()
        handler = DbBusinessUser(self.db_config, self.logger)
        user_info = handler.get_business_user_by_phone(from_phone)
        if not user_info:
            self.logger.errror('send_order_been_created failed can not found user info for %s'%(str(from_phone)))
            return
        brand_name = user_info.get('brand_name', '')
        if not brand_name:
            self.logger.errror('send_order_been_created failed can not found brand_name info for %s'%(str(from_phone)))
            return
        info_dict['type'] = KEY_TYPE_RECIEVE_ORDER
        info_dict['action'] = KEY_ACTION_PAY_ORDER
        info_dict['title'] = u'订单通知'
        info_dict['order_number'] = str(order_number)
        info_dict['extra'] = { 'order_number' : str(order_number) }
        info_dict['content'] = u'%s的店员为您创建了订单'%(brand_name)
        self.logger.info('send_order_been_created to %s'%(str(send_phone)))
        self.send_message_one_user_phone(send_phone, info_dict)

    ##send to customer
    def send_pay_money_message(self, send_phone, from_phone, money=0, order_number=''):
        info_dict = self.init_notify_data()
        info_dict['type'] = KEY_TYPE_PAY_MONEY
        info_dict['action'] = KEY_ACTION_PAY_ORDER
        info_dict['sales'] = from_phone
        info_dict['title'] = u'新窝钱包'
        info_dict['money'] = money
        info_dict['order_number'] = order_number
        info_dict['extra'] = { 'order_number' : str(order_number) , 'sales' : from_phone, 'money' : money }
        info_dict['content'] = u'店员%s发来一个订单'%(str(from_phone))
        self.logger.info('send_pay_money_message to %s'%(str(send_phone)))
        self.send_message_one_user_phone(send_phone, info_dict)

    ##send to business    
    def send_order_payed_message(self, send_phone, order_number, content):
        if not content:
            return False
        info_dict = self.init_notify_data()
        info_dict['type'] = KEY_TYPE_ORDER_PAYED_BUSINESS
        info_dict['action'] = KEY_ACTION_ORDER_DETAIL
        info_dict['save'] = 1
        info_dict['title'] = u'交易通知'
        info_dict['order_number'] = order_number
        info_dict['extra'] = { 'order_number' : str(order_number) }
        info_dict['content'] = content
        self.logger.info('send_order_payed_message to %s'%(str(send_phone)))
        self.send_message_one_user_phone(send_phone, info_dict)
        return True
        
    ##send to business    
    def send_order_verify_failed_message(self, send_phone, order_number=''):
        info_dict = self.init_notify_data()
        info_dict['type'] = KEY_TYPE_ORDER_VERIFY_FAILED_BUSINESS
        info_dict['action'] = KEY_ACTION_ORDER_DETAIL
        info_dict['save'] = 1
        info_dict['title'] = u'交易通知'
        info_dict['extra'] = { 'order_number' : str(order_number) }
        info_dict['content'] = u'您有一笔订单需补充资料，请在48小时内提供，查看详情。'
        self.logger.info('send_order_verify_message to %s'%(str(send_phone)))
        self.send_message_one_user_phone(send_phone, info_dict)
        
    ##send to business    
    def send_commision_settled_message(self, id, send_phone, content):
        info_dict = self.init_notify_data()
        info_dict['type'] = KEY_TYPE_COMMISION_SETTLED
        info_dict['action'] = KEY_ACTION_OPEN_AWARD
        info_dict['save'] = 1
        info_dict['title'] = u'钱包通知'
        info_dict['content'] = content
        info_dict['extra'] = { 'id' : id }
        self.logger.info('send_commision_settled_message to %s'%(str(send_phone)))
        self.send_message_one_user_phone(send_phone, info_dict)
    
    ##send to business and customer    
    def send_action(self, send_phone, action, title, content, sub_type=1):
        info_dict = self.init_notify_data()
        info_dict['type'] = KEY_TYPE_NOTICE_ACTION
        info_dict['sub_type'] = sub_type
        info_dict['action'] = action
        info_dict['save'] = 0
        info_dict['title'] = title
        info_dict['content'] = content
        self.send_message_one_user_phone(send_phone, info_dict)
        
    ##send to customer only    
    def send_open_app(self, send_phone, action, title, content, sub_type=1):
        info_dict = self.init_notify_data()
        info_dict['type'] = KEY_TYPE_OPEN_APP
        info_dict['sub_type'] = sub_type
        info_dict['action'] = action
        info_dict['save'] = 0
        info_dict['title'] = title
        info_dict['content'] = content
        print info_dict
        self.send_message_one_user_phone(send_phone, info_dict)

    def send_open_apps(self, action, content, multi_type='all'):
        info_dict = self.init_notify_data()
        info_dict['type'] = KEY_TYPE_OPEN_APP
        info_dict['sub_type'] = 1
        info_dict['action'] = action
        info_dict['save'] = 0
        info_dict['title'] = u'新窝消息'
        info_dict['content'] = content
        if multi_type == 'all':
            self.send_message_all_android_users_with_jpush(info_dict)
            self.send_message_all_ios_users(info_dict)
        elif multi_type == 'ios':
            self.send_message_all_ios_users(info_dict)
        elif multi_type == 'android':
            self.send_message_all_android_users_with_jpush(info_dict)
        else:
            print 'error type'
            return False
        return True
        
    ##send to business only
    ### sub_type 1 表示大本营计数增加
    def send_notice_count(self, send_phone, title, content, sub_type=1):
        info_dict = self.init_notify_data()
        info_dict['type'] = KEY_TYPE_NOTICE_COUNT
        info_dict['sub_type'] = sub_type
        info_dict['action'] = KEY_ACTION_NOTICE_COUNT
        info_dict['save'] = 0
        info_dict['title'] = title
        info_dict['content'] = content
        print info_dict
        self.send_message_one_user_phone(send_phone, info_dict)    
    
    ##send to business and customer    
    def send_sales_action(self, send_phone_list, action, title, content, sub_type=0):
        info_dict = self.init_notify_data()
        info_dict['type'] = KEY_TYPE_NOTICE_ACTION
        info_dict['sub_type'] = sub_type
        info_dict['action'] = action
        info_dict['save'] = 0
        info_dict['title'] = title
        info_dict['content'] = content
        self.send_message_user_phones(send_phone_list, info_dict)
        
    ##send to business and customer    
    def send_operation_notify(self, send_phone, title='', content= '', url='http://mobile.xinwo.com/static/square.html', sub_type = KEY_SUB_TYPE_OPERATION_RED_AWARD, action = KEY_ACTION_OPEN_URL):
        info_dict = self.init_notify_data()
        info_dict['type'] = KEY_TYPE_OPERATION
        info_dict['action'] = action
        info_dict['save'] = 1
        if not title:
            if sub_type == KEY_SUB_TYPE_OPERATION_RED_AWARD:
                title = u'交易红包'
            else:
                title = u'新窝公告'
        info_dict['title'] = title
        info_dict['content'] = content
        info_dict['url'] = url
        info_dict['sub_type'] = sub_type
        info_dict['extra'] = { 'url' : url }
        self.send_message_one_user_phone(send_phone, info_dict)

    ##send to business only    
    def send_subscribe_shop_sales_notify(self, shop_id, order_time, sub_type=0):
        info_dict = self.init_notify_data()
        handler = DbBusinessUser(self.db_shop, self.logger)
        user_list = handler.get_cooperation_shop_users(shop_id)
        user_list = [ str(i['phone']) for i in user_list ]
        info_dict['type'] = KEY_TYPE_SUBSCRIBE_SHOP_TO_SALES
        info_dict['action'] = KEY_ACTION_SUBSCRIBE_SHOP_LIST
        info_dict['save'] = 0
        info_dict['title'] = u'顾客预约'
        ###subscribe sucess
        if sub_type == 0:
            info_dict['content'] = u'一名新窝顾客预约' + order_time + u'到您门店购物。点击查看。'
        ###subscribe canceled    
        elif sub_type == 1:
            info_dict['content'] = u'一名新窝顾客已取消' + order_time + u'到店购物。点击查看。'
        info_dict['sub_type'] = sub_type
        info_dict['extra'] = {}
        print 'push sales %s %s'%(str(user_list), str(info_dict))
        self.send_message_user_phones(user_list, info_dict)

    ##send to business only    
    def send_purchase_reject_sales(self, sales_phone, reject_id):
        info_dict = self.init_notify_data()
        user_list = [ sales_phone ]
        info_dict['type'] = KEY_TYPE_PURCHASE
        info_dict['action'] = KEY_ACTION_OPEN_PURCHASE
        info_dict['save'] = 0
        info_dict['title'] = u'比价通知'
        info_dict['content'] = u'您提供的商品信息需要优化，点击查看详情'
        info_dict['sub_type'] = 1
        info_dict['extra'] = { 'id' : reject_id }
        print 'push sales %s %s'%(str(user_list), str(info_dict))
        self.send_message_user_phones(user_list, info_dict)

    ##send to business only    
    def send_new_purchase_sales(self, sales_phone_list, reject_id):
        info_dict = self.init_notify_data()
        user_list = sales_phone_list
        info_dict['type'] = KEY_TYPE_PURCHASE
        info_dict['action'] = KEY_ACTION_OPEN_PURCHASE
        info_dict['save'] = 0
        info_dict['title'] = u'比价通知'
        info_dict['content'] = u'有一名顾客向您求购商品，查看详情'
        info_dict['sub_type'] = 1
        info_dict['extra'] = { 'id' : reject_id }
        self.logger.info('send_new_purchase_sales %s'%(str(reject_id)))
        print user_list
        self.send_message_user_phones(user_list, info_dict)
        
    ##send to customer only    
    def send_purchase_reply_customer(self, user_phone, id, content):
        info_dict = self.init_notify_data()
        user_list = [ user_phone ]
        info_dict['type'] = KEY_TYPE_PURCHASE
        info_dict['action'] = KEY_ACTION_OPEN_PURCHASE
        info_dict['save'] = 0
        info_dict['title'] = u'比价通知'
        info_dict['content'] = content
        info_dict['sub_type'] = 1
        info_dict['extra'] = { 'id' : id }
        print 'push sales %s %s'%(str(user_list), str(info_dict))
        self.send_message_user_phones(user_list, info_dict)
        
    ##send to customer only    
    def send_subscribe_shop_customer_notify(self, user_phone, brand_name, shop_name, order_time, sub_type=0):
        info_dict = self.init_notify_data()
        info_dict['type'] = KEY_TYPE_SUBSCRIBE_SHOP_TO_CUSTOMER
        info_dict['action'] = KEY_ACTION_SUBSCRIBE_SHOP_LIST
        info_dict['save'] = 0
        info_dict['title'] = u'新窝钱包'
        
        ###subscribe ok    
        if sub_type == 0:
            info_dict['content'] = u'您已成功预约' + str(order_time.month) + u'月' + str(order_time.day) + u'日到'+ brand_name + u'（' + shop_name + u'）使用新窝钱包，去查看！'
        ###subscribe not ok
        elif sub_type == 1:
            info_dict['content'] = u'您未成功预约到' + brand_name + u'（' + shop_name + u'）使用新窝钱包，请重新选择其他门店预约'
        info_dict['sub_type'] = sub_type
        info_dict['extra'] = {}
        self.send_message_one_user_phone(user_phone, info_dict)

        
    def send_operation_notify_all(self, title='', content= '', url='http://mobile.xinwo.com/static/square.html'):
        info_dict = self.init_notify_data()
        info_dict['type'] = KEY_TYPE_OPERATION
        info_dict['action'] = KEY_ACTION_OPEN_URL
        info_dict['save'] = 1
        if not title:
            title = u'新窝公告'
        info_dict['title'] = title
        info_dict['content'] = content
        info_dict['url'] = url
        info_dict['sub_type'] = KEY_SUB_TYPE_OPERATION_XINWO_NOTICE
        
        self.send_message_all_android_users_with_jpush(info_dict)
        self.send_message_all_ios_users(info_dict)

    def send_operation_notify_ios(self, title='', content= '', url='http://mobile.xinwo.com/static/square.html'):
        info_dict = self.init_notify_data()
        info_dict['type'] = KEY_TYPE_OPERATION
        info_dict['action'] = KEY_ACTION_OPEN_URL
        info_dict['save'] = 1
        if not title:
            title = u'新窝公告'
        info_dict['title'] = title
        info_dict['content'] = content
        info_dict['url'] = url
        info_dict['sub_type'] = KEY_SUB_TYPE_OPERATION_XINWO_NOTICE        
        self.send_message_all_ios_users(info_dict)
        
    def send_operation_notify_all_with_jpush(self, title='', content='', url='http://mobile.xinwo.com/static/square.html'):
        info_dict = self.init_notify_data()
        info_dict['type'] = KEY_TYPE_OPERATION
        info_dict['action'] = KEY_ACTION_OPEN_URL
        info_dict['save'] = 1
        if not title:
            title = u'新窝公告'
        info_dict['title'] = title
        info_dict['content'] = content
        info_dict['url'] = url
        info_dict['sub_type'] = KEY_SUB_TYPE_OPERATION_XINWO_NOTICE
        
        self.send_message_all_android_users_with_jpush(info_dict)

    def send_comment_notify(self, send_phone, from_phone, session_id, goods_id, sales, title='', content=''):
        info_dict = self.init_notify_data()
        info_dict['type'] = KEY_TYPE_COMMENT
        info_dict['action'] = KEY_ACTION_COMMENT
        info_dict['save'] = 1
        if not title:
            title = u'购物咨询'
        info_dict['title'] = title
        info_dict['content'] = content
        info_dict['goods_id'] = goods_id
        info_dict['extra'] = {'goods_id': goods_id, 'from_phone' : from_phone, 'sales_phone': sales, 'session_id' : session_id}
        self.send_message_one_user_phone(send_phone, info_dict)

if __name__ == '__main__':
    client_handler = PushBaiduUtil(settings.COMMON_DATA,APP_CLIENT)
    server_handler = PushBaiduUtil(settings.COMMON_DATA,APP_BUSINESS)
    #client_handler.send_order_been_created('13370104670', '13811678953', '123345345345345345345')
    #client_handler.send_order_been_created('13720052994', '13811678953', '1233453453453453453456')
    
    # client_handler.send_open_app('19977778888', ACTION_TO_MAIN_TRANSACTION, u'跳转到交易', 'hahah', 1)
    # client_handler.send_open_app('13370104670', ACTION_TO_MAIN_TRANSACTION, u'跳转到交易', 'hahahah', 1)

    # client_handler.send_open_app('19977778888', ACTION_TO_MAIN_INQUIRE, u'跳转到询价', 'hahah', 1)
    # client_handler.send_open_app('13370104670', ACTION_TO_MAIN_INQUIRE, u'跳转到询价', 'hahahah', 1)

    # client_handler.send_open_app('19977778888', ACTION_TO_MAIN_RECOMMANED, u'跳转到推荐', 'hahah', 1)
    # client_handler.send_open_app('13370104670', ACTION_TO_MAIN_RECOMMANED, u'跳转到推荐', 'hahahah', 1)

    # client_handler.send_open_app('19977778888', ACTION_TO_MAIN_ACCOUNT, u'跳转到账号', 'hahah', 1)
    # client_handler.send_open_app('13370104670', ACTION_TO_MAIN_ACCOUNT, u'跳转到账号', 'hahahah', 1)

    
    #client_handler.send_action('18618281170', KEY_ACTION_INQUIRE, '您收到一条询价应答', '我们是')
    #client_handler.send_action('13720052994', KEY_ACTION_INQUIRE, '您收到一条询价应答', '我们是')
    
    
    message_dict = {}
    message_dict['type'] = 3
    message_dict['title'] = u'新窝钱包'
    message_dict['content'] = u'跟鸟叔学装修-这些钱千万不能省！'
    message_dict['url'] = 'http://t.cn/RwdRv1u'
    #client_handler.send_message_one_user_phone('13681081694',message_dict);
    #client_handler.send_message_all_android_users_with_jpush(message_dict);
    #server_handler.send_action('13681081694', KEY_ACTION_INQUIRE, '您收到一条询价请求', '我们是')
    #server_handler.send_commision_settled_message('13681081694', u'结算成功')
    #server_handler.send_commision_settled_message('13269009199', u'结算成功')
    #server_handler.send_operation_notify('13718280354', content= u'哈哈哈哈哈哈哈我的神add顶顶顶顶顶顶顶顶顶顶顶顶顶顶顶大顶顶顶顶', sub_type= KEY_SUB_TYPE_OPERATION_XINWO_NOTICE)
    server_handler.send_operation_notify('15011133157', content= u'哈哈哈哈哈哈哈我的神add顶顶顶顶顶顶顶顶顶顶顶顶顶顶顶大顶顶顶顶', sub_type= KEY_SUB_TYPE_OPERATION_XINWO_NOTICE)
    #server_handler.send_order_payed_message('13681081694', 1, money=0, order_number='1436961066651292292')
    #server_handler.send_award_notify('13681081694', 4, '13811678953', 40, 10)
    #server_handler.send_action('15010322289', KEY_ACTION_INQUIRE, '您收到一条询价请求', '我们是')
    #server_handler.send_operation_notify_all_with_jpush(content=u'测试群发')
    # handler.send_order_notify('18612111315', '13811678953', '11111111', 0)
    # handler.send_order_notify('18612111315', '13811678953', '11111111', 1)
    #handler.send_award_notify('13681081694', 0, '13811678953', 50)
    #for user in PUSH_LIST:

    #######
    #client_handler.send_operation_notify_ios(content=u'十一为您精选了150件最值得买的商品，详情查看推荐:)', url ='http://static.mobile.xinwo.com/static/html/huodong/20150924/goods_t.html')    
