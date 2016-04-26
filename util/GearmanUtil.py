#coding=utf-8

import os,sys,string
from datetime import datetime
import simplejson as json
import gearman

if __name__ == '__main__':
    G_PATH = os.path.split(os.path.realpath(__file__))[0]
    sys.path.append(G_PATH + '/../../')
    os.environ['DJANGO_SETTINGS_MODULE'] = 'MobileService.settings'
    
    from django.conf import settings

TASK_NAME_WALLET = 'wallet'
TASK_NAME_INQUIRE = 'inquire'

GEARMAN_JOB_NAME = 'message'

TYPE_GEARMAN_ALL = 0
TYPE_GEARMAN_CHANNEL = 1
TYPE_GEARMAN_ONE = 2
TYPE_GEARMAN_ORDER_CREATE = 3
TYPE_GEARMAN_ORDER_PAYED = 4
TYPE_GEARMAN_SHOP = 5
TYPE_GEARMAN_ORDER_CHANGED = 6
TYPE_GEARMAN_ORDER_CANCELED = 7
TYPE_GEARMAN_REWARD = 8
TYPE_GEARMAN_TASK = 9
TYPE_GEARMAN_BUSINESS_USER_REGISTERED = 10
TYPE_GEARMAN_CUSTOMER_USER_REGISTERED = 11
TYPE_GEARMAN_BUSINESS_SEND_ORDER = 12
TYPE_GEARMAN_INQUIRE_TALK = 13
TYPE_GEARMAN_INQUIRE_CREATE_BUSINESS_SESSION = 14
TYPE_GEARMAN_INQUIRE_CREATE_BUSINESS_SESSION_V2 = 15
TYPE_GEARMAN_INQUIRE_TALK_V2 = 16
TYPE_GEARMAN_PAY_MONEY_NOTIFY = 17
TYPE_GEARMAN_SALES_SET_CATEGORY_FIRST_TIME = 18
TYPE_GEARMAN_DRAW_ORDER_PAY_REWARD = 19
TYPE_GEARMAN_SAVE_COMMISION_SETTLEING = 20
TYPE_GEARMAN_SAVE_COMMISION_SETTLED = 21
TYPE_GEARMAN_ADD_TIMELY_INFO = 23
TYPE_GEARMAN_RECORD_WORKFLOW = 24
TYPE_GEARMAN_ORDER_OFFLINE_PAYED = 25
TYPE_GEARMAN_ORDER_OFFLINE_VERIFY = 26
TYPE_GEARMAN_COMMENT_VERIFY = 27
TYPE_GEARMAN_SUBSCRIBE_SHOP = 28
TYPE_GEARMAN_PURCHASE_SEND_SALES = 29
TYPE_GEARMAN_PURCHASE_REPLY_RESULT = 30

KEY_GEARMAN_MESSAGE_TYPE = 'type'
KEY_GEARMAN_MESSAGE_SUB_TYPE = 'stype'
KEY_GEARMAN_MONEY = 'money'
KEY_GEARMAN_PAY_TYPE = 'pay_type'
KEY_GEARMAN_ORDER_NUMBER = 'order_number'
KEY_GEARMAN_ORGIN_ORDER_NUMBER = 'orig_order_number'
KEY_GEARMAN_COUPON_MONEY = 'coupon_money'
KEY_GEARMAN_TOTAL_MONEY = 'total_money'
KEY_GEARMAN_FROM_PHONE = 'from_phone'
KEY_GEARMAN_PHONE = 'phone'
KEY_GEARMAN_AWARD_TYPE = 'award_type'
KEY_GEARMAN_TASK_TYPE = 'task_type'
KEY_GEARMAN_TASK_STATE = 'task_state'
KEY_GEARMAN_SENDER_IDENTITY = 'identity'
KEY_GEARMAN_DEST_PHONE_LIST = 'dest_phone_list'
KEY_GEARMAN_CONTENT = 'content'
KEY_GEARMAN_INQUIRE_CREATE_TIME = 'i_time'
KEY_GEARMAN_CONSUME_MONEY = 'consume_money'
KEY_GEARMAN_GOODS = 'goods'
KEY_GEARMAN_SESSION_ID = 'session_id'
KEY_GEARMAN_TALK_TYPE = 'talk_type'
KEY_GEARMAN_INQUIRE_TEXT = 'text'
KEY_GEARMAN_INQUIRE_GOODS_ID = 'goods_id'
KEY_GEARMAN_CATEGORY = 'category'
KEY_GEARMAN_REWARD_MONEY = 'reward_money'
KEY_GEARMAN_SETTLE_MODE = 'settle_mode'
KEY_GEARMAN_SETTLE_ACCOUNT = 'settle_account'
KEY_GEARMAN_INQUIRE_SUM = 'inquire_sum'
KEY_GEARMAN_INQUIRE_SEND = 'first_send'
KEY_GEARMAN_REWARD_URL = 'reward_url'
KEY_GEARMAN_PROMOTE_PHONE = 'promote_phone'
KEY_GEARMAN_COMPANY_NAME = 'company_name'
KEY_GEARMAN_WORKFLOW_TYPE = 'workflow_type'
KEY_GEARMAN_CUSTOMER_TYPE = 'customer_type'
KEY_GEARMAN_BIND_CUSTOMER_SERVICE = 'bind_customer_service'
KEY_GEARMAN_EXTEND = 'extend'
KEY_GEARMAN_OFFLINE_ORDER_VERIFY_STATE = 'verify_state'
KEY_GEARMAN_VERSION = 'version'
KEY_GEARMAN_RESULT = 'result'
KEY_GEARMAN_REASON = 'reason'

GEARMAN_PAY_TYPE_UPOP = 1
GEARMAN_PAY_TYPE_WEIXIN = 2
GEARMAN_PAY_TYPE_WALLET = 3
GEARMAN_PAY_TYPE_COUPON = 4
GEARMAN_PAY_TYPE_OFFLINE = 5

KEY_GEARMAN_IDENTITY_CLIENT = 'client'
KEY_GEARMAN_IDENTITY_BUSINESS = 'business'

EVENT_INQUIRE_SEND_TEXT = 0
EVENT_INQUIRE_SEND_INQUIRE = 1
EVENT_INQUIRE_SEND_IMAGE = 2
EVENT_INQUIRE_SEND_GOODS = 3
EVENT_INQUIRE_SEND_GOODS_IN_SESSION = 4
EVENT_INQUIRE_SEND_POSITION = 5

class CustomGearmanWorker(gearman.GearmanWorker):    
    def on_job_execute(self, current_job):    
        print "Job started"   
        return super(CustomGearmanWorker, self).on_job_execute(current_job) 

def wallet_callback(gearman_worker, job):    
    #print job.data   
    return job.data
    
class GearmanUtil():
    def __init__(self, gearman_config, task_name=TASK_NAME_WALLET, logger=None):
        self.gearman_config = [str(gearman_config[0]) + ':' + str(gearman_config[1])]
        self.logger = logger
        self.task_name = task_name
        
    def submit_task(self, params):
        try:
            new_client = gearman.GearmanClient(self.gearman_config)   
            current_request = new_client.submit_job(self.task_name, json.dumps(params), background=True, wait_until_complete=False)   
        except Exception,e:
            if self.logger:
                self.logger.error('submit_task except %s'%(e))
            return False
        return True
    
    def start_job_handle(self, func_callback):
        new_worker = CustomGearmanWorker(self.gearman_config)    
        new_worker.register_task(self.task_name, func_callback)    
        new_worker.work(poll_timeout=1)

    def send_order_created_message(self, order_number):
        params = {}
        params[KEY_GEARMAN_MESSAGE_TYPE] = GEARMAN_JOB_NAME
        params[KEY_GEARMAN_MESSAGE_SUB_TYPE] = TYPE_GEARMAN_ORDER_CREATE
        params[KEY_GEARMAN_ORDER_NUMBER] = order_number
        return self.submit_task(params)
        
    def send_order_payed_message(self, pay_type, order_number, orig_order_number, money, coupon_money = 0, total_money = 0):
        params = {}
        params[KEY_GEARMAN_MESSAGE_TYPE] = GEARMAN_JOB_NAME
        params[KEY_GEARMAN_MESSAGE_SUB_TYPE] = TYPE_GEARMAN_ORDER_PAYED
        params[KEY_GEARMAN_PAY_TYPE] = pay_type
        params[KEY_GEARMAN_ORDER_NUMBER] = order_number
        params[KEY_GEARMAN_ORGIN_ORDER_NUMBER] = orig_order_number
        params[KEY_GEARMAN_MONEY] = money
        params[KEY_GEARMAN_COUPON_MONEY] = coupon_money
        params[KEY_GEARMAN_TOTAL_MONEY] = total_money
        return self.submit_task(params)
    
    def send_order_changed_message(self, order_number):
        params = {}
        params[KEY_GEARMAN_MESSAGE_TYPE] = GEARMAN_JOB_NAME
        params[KEY_GEARMAN_MESSAGE_SUB_TYPE] = TYPE_GEARMAN_ORDER_CHANGED
        params[KEY_GEARMAN_ORDER_NUMBER] = order_number
        return self.submit_task(params)    

    def send_order_canceled_message(self, order_number):
        params = {}
        params[KEY_GEARMAN_MESSAGE_TYPE] = GEARMAN_JOB_NAME
        params[KEY_GEARMAN_MESSAGE_SUB_TYPE] = TYPE_GEARMAN_ORDER_CANCELED
        params[KEY_GEARMAN_ORDER_NUMBER] = order_number
        return self.submit_task(params)  

    def send_award_user_message(self, user_phone, from_phone, type, money, consume_money=0):
        params = {}
        params[KEY_GEARMAN_MESSAGE_TYPE] = GEARMAN_JOB_NAME
        params[KEY_GEARMAN_MESSAGE_SUB_TYPE] = TYPE_GEARMAN_REWARD
        params[KEY_GEARMAN_MONEY] = money
        params[KEY_GEARMAN_FROM_PHONE] = from_phone
        params[KEY_GEARMAN_PHONE] = user_phone
        params[KEY_GEARMAN_AWARD_TYPE] = type
        params[KEY_GEARMAN_CONSUME_MONEY] = consume_money
        return self.submit_task(params)

    def send_task_user_message(self, user_phone, from_phone, type, state):
        params = {}
        params[KEY_GEARMAN_MESSAGE_TYPE] = GEARMAN_JOB_NAME
        params[KEY_GEARMAN_MESSAGE_SUB_TYPE] = TYPE_GEARMAN_TASK
        params[KEY_GEARMAN_PHONE] = user_phone
        params[KEY_GEARMAN_FROM_PHONE] = from_phone
        params[KEY_GEARMAN_TASK_TYPE] = type
        params[KEY_GEARMAN_TASK_STATE] = state
        print 'send_task_user_message'
        return self.submit_task(params)

    def send_business_user_register_message(self, user_phone, from_phone= ''):
        params = {}
        params[KEY_GEARMAN_MESSAGE_TYPE] = GEARMAN_JOB_NAME
        params[KEY_GEARMAN_MESSAGE_SUB_TYPE] = TYPE_GEARMAN_BUSINESS_USER_REGISTERED
        params[KEY_GEARMAN_PHONE] = user_phone
        params[KEY_GEARMAN_FROM_PHONE] = from_phone
        return self.submit_task(params)

    def send_customer_user_register_message(self, user_phone, from_phone= ''):
        params = {}
        params[KEY_GEARMAN_MESSAGE_TYPE] = GEARMAN_JOB_NAME
        params[KEY_GEARMAN_MESSAGE_SUB_TYPE] = TYPE_GEARMAN_CUSTOMER_USER_REGISTERED
        params[KEY_GEARMAN_PHONE] = user_phone
        params[KEY_GEARMAN_FROM_PHONE] = from_phone
        return self.submit_task(params)

    def send_business_user_send_order(self, user_phone, from_phone, order_number):
        params = {}
        params[KEY_GEARMAN_MESSAGE_TYPE] = GEARMAN_JOB_NAME
        params[KEY_GEARMAN_MESSAGE_SUB_TYPE] = TYPE_GEARMAN_BUSINESS_SEND_ORDER
        params[KEY_GEARMAN_PHONE] = user_phone
        params[KEY_GEARMAN_FROM_PHONE] = from_phone
        params[KEY_GEARMAN_ORDER_NUMBER] = str(order_number)
        return self.submit_task(params)

    def send_inquire_talk(self, user_phone, from_phone, is_client = True):
        params = {}
        params[KEY_GEARMAN_MESSAGE_TYPE] = GEARMAN_JOB_NAME
        params[KEY_GEARMAN_MESSAGE_SUB_TYPE] = TYPE_GEARMAN_INQUIRE_TALK
        params[KEY_GEARMAN_PHONE] = user_phone
        params[KEY_GEARMAN_FROM_PHONE] = from_phone
        if is_client:
            params[KEY_GEARMAN_SENDER_IDENTITY] = KEY_GEARMAN_IDENTITY_CLIENT
        else:
            params[KEY_GEARMAN_SENDER_IDENTITY] = KEY_GEARMAN_IDENTITY_BUSINESS
        return self.submit_task(params)

    def send_inquire_talk_v2(self, user_phone, from_phone, talk_type, is_client = True, text = '', goods_id = ''):
        params = {}
        params[KEY_GEARMAN_MESSAGE_TYPE] = GEARMAN_JOB_NAME
        params[KEY_GEARMAN_MESSAGE_SUB_TYPE] = TYPE_GEARMAN_INQUIRE_TALK_V2
        params[KEY_GEARMAN_PHONE] = user_phone
        params[KEY_GEARMAN_FROM_PHONE] = from_phone
        params[KEY_GEARMAN_TALK_TYPE] = talk_type
        params[KEY_GEARMAN_INQUIRE_TEXT] = text
        params[KEY_GEARMAN_INQUIRE_GOODS_ID] = goods_id
        if is_client:
            params[KEY_GEARMAN_SENDER_IDENTITY] = KEY_GEARMAN_IDENTITY_CLIENT
        else:
            params[KEY_GEARMAN_SENDER_IDENTITY] = KEY_GEARMAN_IDENTITY_BUSINESS
        return self.submit_task(params)
        
    def send_inquire_create_business_session(self, user_phone, dest_phone_list, content, group_id):
        params = {}
        params[KEY_GEARMAN_MESSAGE_TYPE] = GEARMAN_JOB_NAME
        params[KEY_GEARMAN_MESSAGE_SUB_TYPE] = TYPE_GEARMAN_INQUIRE_CREATE_BUSINESS_SESSION
        params[KEY_GEARMAN_PHONE] = user_phone
        params[KEY_GEARMAN_DEST_PHONE_LIST] = dest_phone_list
        params[KEY_GEARMAN_CONTENT] = content
        params[KEY_GEARMAN_INQUIRE_CREATE_TIME] = group_id
        return self.submit_task(params)     

    def send_inquire_create_business_session_v2(self, user_phone, dest_phone_list, content, goods, session_id, sum=0, first=0):
        params = {}
        params[KEY_GEARMAN_MESSAGE_TYPE] = GEARMAN_JOB_NAME
        params[KEY_GEARMAN_MESSAGE_SUB_TYPE] = TYPE_GEARMAN_INQUIRE_CREATE_BUSINESS_SESSION_V2
        params[KEY_GEARMAN_PHONE] = user_phone
        params[KEY_GEARMAN_DEST_PHONE_LIST] = dest_phone_list
        params[KEY_GEARMAN_CONTENT] = content
        params[KEY_GEARMAN_GOODS] = goods
        params[KEY_GEARMAN_SESSION_ID] = session_id
        params[KEY_GEARMAN_INQUIRE_SUM] = sum
        params[KEY_GEARMAN_INQUIRE_SEND] = first
        return self.submit_task(params)
        
    def send_pay_money_notify(self, user_phone, from_phone, current_price=0, order_number=''):
        params = {}
        params[KEY_GEARMAN_MESSAGE_TYPE] = GEARMAN_JOB_NAME
        params[KEY_GEARMAN_MESSAGE_SUB_TYPE] = TYPE_GEARMAN_PAY_MONEY_NOTIFY
        params[KEY_GEARMAN_PHONE] = user_phone
        params[KEY_GEARMAN_FROM_PHONE] = from_phone
        params[KEY_GEARMAN_CONSUME_MONEY] = current_price
        params[KEY_GEARMAN_ORDER_NUMBER] = order_number
        return self.submit_task(params)
        
    def send_user_set_category_first(self, user_phone, category):
        params = {}
        params[KEY_GEARMAN_MESSAGE_TYPE] = GEARMAN_JOB_NAME
        params[KEY_GEARMAN_MESSAGE_SUB_TYPE] = TYPE_GEARMAN_SALES_SET_CATEGORY_FIRST_TIME
        params[KEY_GEARMAN_PHONE] = user_phone
        params[KEY_GEARMAN_CATEGORY] = category
        return self.submit_task(params)

    def draw_order_pay_reward(self, user_phone, current_money, reward_money, url=''):
        params = {}
        params[KEY_GEARMAN_MESSAGE_TYPE] = GEARMAN_JOB_NAME
        params[KEY_GEARMAN_MESSAGE_SUB_TYPE] = TYPE_GEARMAN_DRAW_ORDER_PAY_REWARD
        params[KEY_GEARMAN_PHONE] = user_phone
        params[KEY_GEARMAN_CONSUME_MONEY] = current_money
        params[KEY_GEARMAN_REWARD_MONEY] = reward_money
        params[KEY_GEARMAN_REWARD_URL] = url
        return self.submit_task(params)

    def save_commision_settleing(self, sales_phone, money):
        params = {}
        params[KEY_GEARMAN_MESSAGE_TYPE] = GEARMAN_JOB_NAME
        params[KEY_GEARMAN_MESSAGE_SUB_TYPE] = TYPE_GEARMAN_SAVE_COMMISION_SETTLEING
        params[KEY_GEARMAN_PHONE] = sales_phone
        params[KEY_GEARMAN_REWARD_MONEY] = money
        return self.submit_task(params)

    def save_commision_settled(self, id, sales_phone, money, settle_mode, settle_account):
        params = {}
        params[KEY_GEARMAN_MESSAGE_TYPE] = GEARMAN_JOB_NAME
        params[KEY_GEARMAN_MESSAGE_SUB_TYPE] = TYPE_GEARMAN_SAVE_COMMISION_SETTLED
        params[KEY_GEARMAN_SENDER_IDENTITY] = id
        params[KEY_GEARMAN_PHONE] = sales_phone
        params[KEY_GEARMAN_REWARD_MONEY] = money
        params[KEY_GEARMAN_SETTLE_MODE] = settle_mode
        params[KEY_GEARMAN_SETTLE_ACCOUNT] = settle_account
        return self.submit_task(params)

    def add_timely_info(self, promote, sales, company_name=''):
        params = {}
        params[KEY_GEARMAN_MESSAGE_TYPE] = GEARMAN_JOB_NAME
        params[KEY_GEARMAN_MESSAGE_SUB_TYPE] = TYPE_GEARMAN_ADD_TIMELY_INFO
        params[KEY_GEARMAN_PROMOTE_PHONE] = promote
        params[KEY_GEARMAN_PHONE] = sales
        params[KEY_GEARMAN_COMPANY_NAME] = company_name
        return self.submit_task(params)

    def record_workflow(self, type, customer_type, mobile, content, bind_customer_service, extend=''):
        params = {}
        params[KEY_GEARMAN_MESSAGE_TYPE] = GEARMAN_JOB_NAME
        params[KEY_GEARMAN_MESSAGE_SUB_TYPE] = TYPE_GEARMAN_RECORD_WORKFLOW
        params[KEY_GEARMAN_WORKFLOW_TYPE] = type
        params[KEY_GEARMAN_CUSTOMER_TYPE] = customer_type
        params[KEY_GEARMAN_PHONE] = mobile
        params[KEY_GEARMAN_CONTENT] = content
        params[KEY_GEARMAN_BIND_CUSTOMER_SERVICE] = bind_customer_service
        params[KEY_GEARMAN_EXTEND] = extend
        return self.submit_task(params)

    def send_order_offline_payed_message(self, version, pay_type, order_number, money, coupon_money = 0, total_money = 0):
        params = {}
        params[KEY_GEARMAN_MESSAGE_TYPE] = GEARMAN_JOB_NAME
        params[KEY_GEARMAN_MESSAGE_SUB_TYPE] = TYPE_GEARMAN_ORDER_OFFLINE_PAYED
        params[KEY_GEARMAN_PAY_TYPE] = pay_type
        params[KEY_GEARMAN_VERSION] = version
        params[KEY_GEARMAN_ORDER_NUMBER] = order_number
        params[KEY_GEARMAN_MONEY] = money
        params[KEY_GEARMAN_COUPON_MONEY] = coupon_money
        params[KEY_GEARMAN_TOTAL_MONEY] = total_money
        return self.submit_task(params)
        
    def send_order_offline_verify_message(self, order_number, verify_state, money):
        params = {}
        params[KEY_GEARMAN_MESSAGE_TYPE] = GEARMAN_JOB_NAME
        params[KEY_GEARMAN_MESSAGE_SUB_TYPE] = TYPE_GEARMAN_ORDER_OFFLINE_VERIFY
        params[KEY_GEARMAN_ORDER_NUMBER] = order_number
        params[KEY_GEARMAN_MONEY] = money
        params[KEY_GEARMAN_OFFLINE_ORDER_VERIFY_STATE] = verify_state
        return self.submit_task(params)

    def send_comment_verify_message(self, user_phone, sales_phone, goods_id, type, session_id):
        params = {}
        params[KEY_GEARMAN_MESSAGE_TYPE] = GEARMAN_JOB_NAME
        params[KEY_GEARMAN_MESSAGE_SUB_TYPE] = TYPE_GEARMAN_COMMENT_VERIFY
        params[KEY_GEARMAN_FROM_PHONE] = user_phone
        params[KEY_GEARMAN_PHONE] = sales_phone
        params[KEY_GEARMAN_INQUIRE_GOODS_ID] = goods_id
        params[KEY_GEARMAN_TALK_TYPE] = type
        params[KEY_GEARMAN_SESSION_ID] = session_id
        return self.submit_task(params)
        
    def send_subscribe_shop_message(self, id, result, reason= ''):
        params = {}
        params[KEY_GEARMAN_MESSAGE_TYPE] = GEARMAN_JOB_NAME
        params[KEY_GEARMAN_MESSAGE_SUB_TYPE] = TYPE_GEARMAN_SUBSCRIBE_SHOP
        params[KEY_GEARMAN_SENDER_IDENTITY] = id
        params[KEY_GEARMAN_RESULT] = result
        params[KEY_GEARMAN_REASON] = reason
        return self.submit_task(params)

    def send_purchaes_to_sales(self, id):
        params = {}
        params[KEY_GEARMAN_MESSAGE_TYPE] = GEARMAN_JOB_NAME
        params[KEY_GEARMAN_MESSAGE_SUB_TYPE] = TYPE_GEARMAN_PURCHASE_SEND_SALES
        params[KEY_GEARMAN_SENDER_IDENTITY] = id

        return self.submit_task(params)

    def send_purchase_reply_result(self, id, sales_phone, state):
        params = {}
        params[KEY_GEARMAN_MESSAGE_TYPE] = GEARMAN_JOB_NAME
        params[KEY_GEARMAN_MESSAGE_SUB_TYPE] = TYPE_GEARMAN_PURCHASE_REPLY_RESULT
        params[KEY_GEARMAN_SENDER_IDENTITY] = id
        params[KEY_GEARMAN_PHONE] = sales_phone
        params[KEY_GEARMAN_TASK_STATE] = state
        return self.submit_task(params)
        
if __name__ == '__main__':
    util = GearmanUtil(settings.COMMON_DATA['gearman_config'])
    #util.send_subscribe_shop_message(435, 0)
    #util.save_commision_settled('15011133157', 20, 1, '15011133157')
    #util.send_pay_money_notify('13811678953', '13811678953', current_price=1000, order_number='12345678')
    #util.send_order_payed_message(2, '1451579181750147331', '1451579181750147331', 222, coupon_money = 0, total_money = 222)
    #util.send_purchaes_to_sales(105)
    #util.send_order_offline_payed_message('2.2.5', 4, '1453860263752561855', 1000, 0, 1000)
    #util.send_order_payed_message(GEARMAN_PAY_TYPE_UPOP, '1454131441754114634761', '1454131441754114634', 9.9, 0, 11)
    util.send_order_offline_verify_message('145404916501025', 0, 0)
    