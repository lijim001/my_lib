#coding=utf-8

import urllib,os,time,sys
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
from MobileService.util.RecordInquire import RecordInquireUtil

ITEM_MONGO_SESSION = 'session'
ITEM_MONGO_MAIL = 'mail'

CLIENT_COLLECTION_V2 = 'c_in_v2'
ITEM_MONGO_CLIENT_PHONE = '_id'
ITEM_MONGO_CLIENT_TALK_USERS = 'talk_user'
ITEM_MONGO_CLIENT_FORBID_USERS = 'forbid_user'

SESSION_COLLECTION = 's_in_v2'
ITEM_MONGO_SESSION_ID = '_id'
ITEM_MONGO_SESSION_GOODS = 'goods'

KEY_GOODS_ID = 'id'
KEY_GOODS_SENDER = 'phone'
KEY_GOODS_SHOP_ID = 'shop_id'
KEY_GOODS_MONEY = 'money'
KEY_GOODS_DESC = 'desc'
KEY_GOODS_CREATE_TIME = 'create_time'
KEY_GOODS_UPDATE_TIME = 'update_time'
KEY_GOODS_IMAGE1 = 'image1'
KEY_GOODS_IMAGE2 = 'image2'
KEY_GOODS_IMAGE3 = 'image3'
KEY_GOODS_IMAGE1_THUMBNAIL = 'image1_thumbnail'
KEY_GOODS_IMAGE2_THUMBNAIL = 'image2_thumbnail'
KEY_GOODS_IMAGE3_THUMBNAIL = 'image3_thumbnail'
KEY_GOODS_CUTOFF_MONEY  = 'cutoff_money'
KEY_GOODS_CUTOFF_RATE  = 'cutoff_rate'
KEY_GOODS_COMMENT_NUM = 'comment_num'

BUSINESS_COLLECTION_V2 = 'b_in_v2'
ITEM_MONGO_BUSINESS_PHONE = '_id'
ITEM_MONGO_BUSINESS_SESSION = 'session'
ITEM_MONGO_BUSINESS_ANSWERED = 'answered'
ITEM_MONGO_BUSINESS_ANSWER_NUM = 'answered_num'

KEY_MESSAGE_CREATE_TIME = 'create_time'

AUTO_ID_COLLECTION = 'auto_in'
KEY_AUTO_ID_ITEM = 'auto_id'
KEY_AUTO_SESSION_ID = 's_id'

BUSINESS_MAIL_COLLECTION = 'b_mail'
CUSTOMER_MAIL_COLLECTION = 'c_mail'

TYPE_MESSAGE_TEXT = 0
TYPE_MESSAGE_POSITION = 1
TYPE_MESSAGE_NOTICE = 2
TYPE_MESSAGE_INQUIRE = 3
TYPE_MESSAGE_IMAGE = 4
TYPE_MESSAGE_GOODS = 5
TYPE_MESSAGE_FORBID_TALK = 6

KEY_MAIL_TYPE_V2 = 'type'
KEY_MAIL_CONTENT_V2 = 'content'
KEY_MAIL_PHONE_V2 = 'phone'
KEY_MAIL_CREATE_TIME_V2 = 'create_time'


class InstanceMessageV2Util():
    def __init__(self, database):
        self.info_logger = database['mobile_logger']
        self.gearman_config = database['gearman_config']
        self.redis = database['cache_redis']
        self.mobile_db = database['mobile_db']
        self.database = database
        self.get_mongo_connect()
    
    def record_session_create(self, from_phone, category, content, platform='android', session_id = 0):
        handler = RecordInquireUtil(self.database)
        handler.record_create_session(from_phone, category, content, platform, session_id)
    
    def record_sales_send_goods_in_session(self, sales_phone, session_id, goods_id):
        handler = RecordInquireUtil(self.database)
        handler.record_talk_info(sales_phone, '', 'wallet_business', '', '我家的商品：', 'android', session_id, goods_id)
    
    def record_talk_info(self, user_phone, sales_phone, content, type, is_c = True):
        if is_c:
            app = 'wallet_client'
        else:
            app = 'wallet_business'
            
        handler = RecordInquireUtil(self.database)
        if type == TYPE_MESSAGE_TEXT:
            if is_c:
                handler.record_talk_info(user_phone, sales_phone, app, '', content)
            else:
                pass
                ##comment temporary
                handler.record_talk_info(sales_phone, user_phone, app, '', content)
        elif type == TYPE_MESSAGE_POSITION:
            handler.record_talk_info(sales_phone, user_phone, app, '', '我的位置是：')
        elif type == TYPE_MESSAGE_IMAGE:
            image_url = content.get('url', '')
            if is_c:
                handler.record_talk_info(user_phone, sales_phone, app, '', image_url)
            else:
                handler.record_talk_info(sales_phone, user_phone, app, '', image_url)
        elif type == TYPE_MESSAGE_GOODS:
            goods_id = content.get('id', 0)
            if is_c:
                pass
            else:
                pass
                ##comment temporary
                handler.record_talk_info(sales_phone, user_phone, app, '', '商品信息：', 'android', 0, goods_id)
        
    def add_chat_group_info(self, user_phone, session_id, send_num, total_num, content, brand_name, state, goods, platform):
        handler = DbUtil(self.mobile_db, self.info_logger)
        ctime = int(time.time())
        if not platform:
            platform = 0
        elif platform == 'android':
            platform = 2
        elif platform == 'h5':
            platform = 1
        elif platform == 'pc':
            platform = 4
        else:
            platform = 3
        return handler.add_chat_group_info_v2(user_phone, session_id, send_num, total_num, content, brand_name, state, ctime, goods, platform)
    
    def add_chat_single_info(self, send_phone, receive_phone, content, state):
        if send_phone.startswith('12') or send_phone.startswith('400') or receive_phone.startswith('12') or receive_phone.startswith('400'):
            return False
        handler = DbUtil(self.mobile_db, self.info_logger)
        handler.add_chat_single_info(send_phone, receive_phone, content, state)
    
    def update_chat_group_total_num(self, session_id):
        handler = DbUtil(self.mobile_db, self.info_logger)
        handler.update_chat_group_total_num_v2(session_id)
        
    def get_business_name_brand(self, phone):
        handler = DbUtil(self.mobile_db, self.info_logger)
        return handler.get_business_name_brand(phone)

    def send_task_event(self, phone, from_phone, is_c = True):
        handler_push = GearmanUtil(self.gearman_config,TASK_NAME_INQUIRE)
        handler_push.send_inquire_talk(phone, from_phone, is_c)
        
    def record_message_count(self, user_phone, is_c = True):
        if is_c:
            key = 'c_' + str(user_phone)
        else:
            key = 'b_' + str(user_phone)
        self.redis.incr(key)

    def get_message_count(self, user_phone, is_c = True):
        if is_c:
            key = 'c_' + str(user_phone)
        else:
            key = 'b_' + str(user_phone)
        count = self.redis.get(key)
        if not count:
            count == 0
        # else:
            # self.redis.delete(key)
        return count
    
    def clear_message_count(self, user_phone, is_c = True):
        if is_c:
            key = 'c_' + str(user_phone)
        else:
            key = 'b_' + str(user_phone)
        self.redis.delete(key)
            
    def get_mongo_connect(self):
        self.mongo_db = MongoDatabase().get_database()
        self.c_collection = self.mongo_db[CLIENT_COLLECTION_V2]
        self.b_collection = self.mongo_db[BUSINESS_COLLECTION_V2]
        self.auto_id_collection = self.mongo_db[AUTO_ID_COLLECTION]
        self.session_collection = self.mongo_db[SESSION_COLLECTION]
        self.b_mail_collection = self.mongo_db[BUSINESS_MAIL_COLLECTION]
        self.c_mail_collection = self.mongo_db[CUSTOMER_MAIL_COLLECTION]
    
    def add_session_goods_list(self, session_id, phone, goods_id, goods_info, is_auto = 0):
        handler = DbUtil(self.mobile_db, self.info_logger)
        money = float(goods_info.get('money', 0))
        cutoff_money = goods_info.get('cutoff_money', money)
        create_time = goods_info.get('create_time', 0)
        create_time = datetime.fromtimestamp(create_time)
        if not cutoff_money or cutoff_money < 0.00001:
            cutoff_money = money
        cutoff_rate = (1.00 - (money - cutoff_money) / money) * 10
        extra = json.dumps(goods_info)
        handler.add_session_goods_list(session_id, phone, goods_id, create_time, money, cutoff_money, cutoff_rate, extra, is_auto)
        
    def add_session_goods(self, sales_phone, session_id, goods_id, is_auto = 0):
        handler = DbUtil(self.mobile_db, self.info_logger)
        goods_info = handler.get_goods_info_by_id(goods_id)
        if not goods_info:
            return False
        sales_info = handler.get_goods_sales_info(sales_phone)
        now = int(time.time())
        goods_info.update(sales_info)
        goods_info['create_time'] = now
        try:
            self.session_collection.find_and_modify({ITEM_MONGO_SESSION_ID: session_id}, {"$push" : {ITEM_MONGO_SESSION_GOODS: {"$each": [goods_info], "$sort": {KEY_GOODS_CREATE_TIME: -1}, '$slice': 200} }}, upsert=True)
            self.record_sales_send_goods_in_session(sales_phone, session_id, goods_id)
            self.add_session_goods_list(session_id, sales_phone, goods_id, goods_info, is_auto)
            return True
        except Exception,e:
            self.info_logger.error('add_session_goods except %s'%(e))
            return False
    
    def add_client_talk_user(self, user_phone, sales_phone):
        pass
    
    def check_business_talk_privilege(self, user_phone, sales_phone):
        try:
            if self.c_collection.find_one({ITEM_MONGO_CLIENT_PHONE: user_phone, ITEM_MONGO_CLIENT_FORBID_USERS : {'$in': [sales_phone]}}):
                return False
            else:
                return True
        except Exception,e:
            self.info_logger.error('check_business_talk_privilege except %s'%(e))
            return False
    
    def check_business_session_talked(self, sales_phone, session_id, goods_id):
        try:
            goods_id = int(goods_id)
            phone_key = ITEM_MONGO_SESSION_GOODS + '.' + KEY_GOODS_SENDER
            goods_id_key = ITEM_MONGO_SESSION_GOODS + '.' + KEY_GOODS_ID
            check_dict = {}
            check_dict[ITEM_MONGO_SESSION_ID] = session_id
            check_dict[phone_key] = sales_phone
            check_dict[goods_id_key] = goods_id
            if self.session_collection.find_one(check_dict, fields= [phone_key]):
                return False
            return True
        except Exception,e:
            self.info_logger.error('check_business_session_talked except %s'%(e))
            return False
    
    def add_client_forbid_user(self, user_phone, sales_phone):
        try:
            if self.c_collection.find_one({ITEM_MONGO_CLIENT_PHONE: user_phone, ITEM_MONGO_CLIENT_FORBID_USERS : {'$in': [sales_phone]}}):
                return True
            self.c_collection.find_and_modify({ITEM_MONGO_CLIENT_PHONE: user_phone}, { "$push": { ITEM_MONGO_CLIENT_FORBID_USERS: sales_phone } }, upsert=True)
            return True
        except Exception,e:
            self.info_logger.error('add_client_forbid_user except %s'%(e))
            return False
    
    def unforbid_user(self, user_phone, sales_phone):
        try:
            if self.c_collection.find_one({ITEM_MONGO_CLIENT_PHONE: user_phone, ITEM_MONGO_CLIENT_FORBID_USERS : {'$nin': [sales_phone]}}):
                return True
            self.c_collection.find_and_modify({ITEM_MONGO_CLIENT_PHONE: user_phone}, { "$pop": { ITEM_MONGO_CLIENT_FORBID_USERS: sales_phone } }, upsert=True)
            return True
        except Exception,e:
            self.info_logger.error('unforbid_user except %s'%(e))
            return False
    
    def format_mail_message(self, phone, content, type):
        ret_dict = {}
        now = int(time.time())
        ret_dict[KEY_MAIL_PHONE_V2] = phone
        ret_dict[KEY_MAIL_CREATE_TIME_V2] = now
        ret_dict[KEY_MAIL_CONTENT_V2] = content
        ret_dict[KEY_MAIL_TYPE_V2] = type
        return ret_dict
        
    def push_message_mail(self, user_phone, sales_phone, content, type, is_c = True):
        self.record_talk_info(user_phone, sales_phone, content, type, is_c)
        if is_c:
            ret_dict = self.format_mail_message(user_phone, content, type)
            try:
                self.b_mail_collection.find_and_modify({ITEM_MONGO_BUSINESS_PHONE: sales_phone}, {"$push" : {ITEM_MONGO_MAIL: {"$each": [ret_dict], "$sort": {KEY_MAIL_CREATE_TIME_V2: -1}, '$slice': 200} }}, upsert=True)
                return True
            except Exception,e:
                self.info_logger.error('push_message_mail except %s'%(e))
                return False
        else:
            handler = DbUtil(self.mobile_db, self.info_logger)
            sales_info = handler.get_goods_sales_info(sales_phone)
            ret_dict = self.format_mail_message(sales_phone, content, type)
            ret_dict.update(sales_info)
            try:
                self.c_mail_collection.find_and_modify({ITEM_MONGO_CLIENT_PHONE: user_phone}, {"$push" : {ITEM_MONGO_MAIL: {"$each": [ret_dict], "$sort": {KEY_MAIL_CREATE_TIME_V2: -1}, '$slice': 200} }}, upsert=True)
                return True
            except Exception,e:
                self.info_logger.error('push_message_mail except %s'%(e))
                return False
                
    def add_client_goods_message(self, user_phone, sales_phone, goods_id, money = None, session_id = 0):
        handler = DbUtil(self.mobile_db, self.info_logger)
        goods_info = handler.get_goods_info_by_id(goods_id)
        if not goods_info:
            return False
        sales_info = handler.get_goods_sales_info(sales_phone)
        if money:
            goods_info['money'] = money
        goods_info['session_id'] = session_id
        goods_info.update(sales_info)
        goods_id_list = [goods_id]
        comment_dict = handler.get_goods_comment_nums(goods_id_list)
        if comment_dict:
            goods_info[KEY_GOODS_COMMENT_NUM] = comment_dict.get(goods_id, 0)
        else:
            goods_info[KEY_GOODS_COMMENT_NUM] = 0
        if session_id:
            self.update_chat_group_total_num(session_id)
        else:
            self.add_chat_single_info(sales_phone, user_phone, goods_id, 2)
        return self.push_message_mail(user_phone, sales_phone, goods_info, TYPE_MESSAGE_GOODS, False)
        
    def add_client_text_message(self, user_phone, sales_phone, text):
        ret = self.push_message_mail(user_phone, sales_phone, text, TYPE_MESSAGE_TEXT, False)
        self.add_chat_single_info(sales_phone, user_phone, text, 1)
        return ret
        
    def add_client_image_message(self, user_phone, sales_phone, url):
        ret_dict = {}
        ret_dict['url'] = url
        ret = self.push_message_mail(user_phone, sales_phone, ret_dict, TYPE_MESSAGE_IMAGE, False)
        self.add_chat_single_info(sales_phone, user_phone, url, 3)
        return ret
        
    def add_client_position_message(self, user_phone, sales_phone, position_info):
        ret = self.push_message_mail(user_phone, sales_phone, position_info, TYPE_MESSAGE_POSITION, False)
        self.add_chat_single_info(sales_phone, user_phone, position_info, 4)
        return ret
        
    def add_business_session(self, user_phone, sales_phone, content, goods, session_id, create_time = 0):
        try:
            handler = DbUtil(self.mobile_db, self.info_logger)
            user_info = handler.get_user_info(0, user_phone)
            ret_dict = {}
            ret_dict['id'] = session_id
            ret_dict['content'] = content
            ret_dict['goods'] = goods
            ret_dict['phone'] = user_phone
            if create_time == 0:
                ret_dict['create_time'] = int(time.time())
            else:
                ret_dict['create_time'] = int(create_time)
            if user_info:
                ret_dict['covered_area'] = user_info.get('covered_area', '')
                ret_dict['house_type'] = user_info.get('house_type', '')
            else:
                ret_dict['covered_area'] = ''
                ret_dict['house_type'] = ''
            self.b_collection.find_and_modify({ITEM_MONGO_BUSINESS_PHONE: sales_phone}, {"$push" : {ITEM_MONGO_BUSINESS_SESSION: {"$each": [ret_dict], "$sort": {KEY_GOODS_CREATE_TIME: -1}, '$slice': 200} }}, upsert=True)
            return True
        except Exception,e:
            self.info_logger.error('add_business_session except %s'%(e))
            return False
            
    def add_business_goods_message(self, user_phone,sales_phone, goods_id):
        handler = DbUtil(self.mobile_db, self.info_logger)
        goods_info = handler.get_goods_info_by_id(goods_id)
        if not goods_info:
            return False
        ret = self.push_message_mail(user_phone, sales_phone, goods_info, TYPE_MESSAGE_GOODS, True)
        self.add_chat_single_info(user_phone, sales_phone, goods_id, 2)
        return ret
        
    def add_business_text_message(self, user_phone, sales_phone, text):
        ret = self.push_message_mail(user_phone, sales_phone, text, TYPE_MESSAGE_TEXT, True)
        self.add_chat_single_info(user_phone, sales_phone, text, 1)
        return ret
        
    def add_business_image_message(self, user_phone, sales_phone, url):
        ret_dict = {}
        ret_dict['url'] = url
        ret = self.push_message_mail(user_phone, sales_phone, ret_dict, TYPE_MESSAGE_IMAGE, True)
        self.add_chat_single_info(user_phone, sales_phone, url, 3)
        return ret

    def add_business_forbid_talk_message(self, user_phone, sales_phone):
        ret_dict = {}
        ret_dict['user_phone'] = user_phone
        return self.push_message_mail(user_phone, sales_phone, ret_dict, TYPE_MESSAGE_FORBID_TALK, True)
        
    def add_business_inquire_message(self, user_phone, sales_phone, content, goods, session_id):
        ret_dict = {}
        ret_dict['phone'] = user_phone
        ret_dict['content'] = content
        ret_dict['goods'] = goods
        ret_dict['session_id'] = session_id
        return True
        return self.push_message_mail(user_phone, sales_phone, ret_dict, TYPE_MESSAGE_INQUIRE, True)        
    
    def remove_session_goods(self, sales_phone, session_id, goods_id):
        try:
            session_id = int(session_id)
            goods_id = int(goods_id)
            self.session_collection.update({ITEM_MONGO_SESSION_ID: session_id}, {"$pull": {ITEM_MONGO_SESSION_GOODS: {KEY_GOODS_SENDER:sales_phone, KEY_GOODS_ID:goods_id}}})
            return True
        except Exception,e:
            self.info_logger.error('remove_session_goods except %s'%(e))
            return False
            
    def do_create_session(self, user_phone, dest_phone_list, content, goods, session_id, create_time = 0):
        for sales_phone in dest_phone_list:
            self.add_business_inquire_message(user_phone, sales_phone, content, goods, session_id)
            self.add_business_session(user_phone, sales_phone, content, goods, session_id, create_time)
            time.sleep(0.01)    

    def get_new_session_id(self):
        return self.get_new_key_id(KEY_AUTO_SESSION_ID)
        
    def get_new_key_id(self, key):
        self.get_mongo_connect()
        ret_data = self.auto_id_collection.find_and_modify({'_id': key}, { "$inc": { KEY_AUTO_ID_ITEM: 1}}, new = True, upsert=True, fields= [KEY_AUTO_ID_ITEM])
        return ret_data.get(KEY_AUTO_ID_ITEM, 0)
        
    def customer_create_session(self, user_phone, dest_phone_list, content, goods, platform=''):
        session_id = self.get_new_session_id()
        self.add_chat_group_info(user_phone, session_id, len(dest_phone_list), 0, content, '', 1,goods, platform)
        self.record_session_create(user_phone, goods, content, 'android', session_id)
        return session_id

    def get_user_mail(self, user_phone, is_c = True):
        ret_fileds = []
        ret_fileds.append(ITEM_MONGO_MAIL)
        if is_c:
            ret_data = self.c_mail_collection.find_one({ITEM_MONGO_CLIENT_PHONE: user_phone}, fields = ret_fileds)
            self.c_mail_collection.update({ITEM_MONGO_CLIENT_PHONE: user_phone}, {'$unset' : {ITEM_MONGO_MAIL: ''}})
        else:
            ret_data = self.b_mail_collection.find_one({ITEM_MONGO_BUSINESS_PHONE: user_phone}, fields = ret_fileds)
            self.b_mail_collection.update({ITEM_MONGO_BUSINESS_PHONE: user_phone}, {'$unset' : {ITEM_MONGO_MAIL: ''}})
        if not ret_data:
            return []
        ret_data = ret_data.get('mail', [])
        if ret_data:
            self.clear_message_count(user_phone, is_c)
        return ret_data
    
    def format_business_session_list(self, sales_phone, session_list):
        for session in session_list:
            session_id = session.get('id', 0)
            ret_dict = self.check_sales_session_info(sales_phone, session_id)
            session['goods_num'] = ret_dict.get('goods_num', 0)
            session['sent'] = ret_dict.get('reply', 0)
        return session_list
        
    def business_get_session_list(self, sales_phone, start = 0, num = 20):
        try:
            if start != 0:
                ret_data = self.b_collection.find_one({ITEM_MONGO_BUSINESS_PHONE: sales_phone}, {ITEM_MONGO_BUSINESS_SESSION: {"$slice" : [start, num]}})
                
            else:
                ret_data = self.b_collection.find_one({ITEM_MONGO_BUSINESS_PHONE: sales_phone}, {ITEM_MONGO_BUSINESS_SESSION: {"$slice" : num}})
            if not ret_data:
                return []
            ret_data = ret_data.get('session', [])
            self.format_business_session_list(sales_phone, ret_data)
            return ret_data
        except Exception,e:
            self.info_logger.error('business_get_session_list except %s'%(e))
            return []
    
    def get_images_num(self, goods_dict):
        if goods_dict.get('image6', ''):
            return 6
        elif goods_dict.get('image5', ''):
            return 5
        elif goods_dict.get('image4', ''):
            return 4
        elif goods_dict.get('image3', ''):
            return 3
        elif goods_dict.get('image2', ''):
            return 2
        elif goods_dict.get('image1', ''):
            return 1

    def format_session_goods_infos(self, goods_list):
        for goods in goods_list:
            if not goods.has_key(KEY_GOODS_COMMENT_NUM):
                goods[KEY_GOODS_COMMENT_NUM] = 1
            if not goods.has_key(KEY_GOODS_CUTOFF_MONEY):
                goods[KEY_GOODS_CUTOFF_MONEY] = goods.get(KEY_GOODS_MONEY)
            if not goods.has_key(KEY_GOODS_CUTOFF_RATE):
                goods[KEY_GOODS_CUTOFF_RATE] = 10.00 - (goods.get(KEY_GOODS_MONEY) - goods[KEY_GOODS_CUTOFF_MONEY]) / goods.get(KEY_GOODS_MONEY)
        return goods_list
        
    def get_session_infos(self, session_id, start = 0, num = 20):
        try:
            if start != 0:
                ret_data = self.session_collection.find_one({ITEM_MONGO_SESSION_ID: session_id}, {ITEM_MONGO_SESSION_GOODS: {"$slice" : [start, num]}})
                
            else:
                ret_data = self.session_collection.find_one({ITEM_MONGO_SESSION_ID: session_id}, {ITEM_MONGO_SESSION_GOODS: {"$slice" : num}})
            if not ret_data:
                return []
            ret_data = ret_data.get('goods', [])
            for session_info in ret_data:
                session_info['image_num'] = self.get_images_num(session_info)
            ret_data = self.format_session_goods_infos(ret_data)
            return ret_data
        except Exception,e:
            self.info_logger.error('get_session_infos except %s'%(e))
            return []
    
    def check_sales_session_info(self, sales_phone, session_id):
        handler = DbUtil(self.mobile_db, self.info_logger)
        sales_list = handler.get_session_sales_info(sales_phone, session_id)
        reply = 0
        if sales_phone in sales_list:
            reply = 1
        ret_dict = {}
        ret_dict['reply'] = reply
        ret_dict['goods_num'] = len(sales_list)
        return ret_dict
    
    def get_goods_comment_nums(self, goods_list):
        goods_id_list = []
        for goods in goods_list:
            goods_id_list.append(str(goods.get('id', 0)))
        handler = DbUtil(self.mobile_db, self.info_logger)
        comment_dict = handler.get_goods_comment_nums(goods_id_list)
        for goods in goods_list:
            if not comment_dict.has_key(goods.get('id', 0)):
                goods[KEY_GOODS_COMMENT_NUM] = 0
            else:
                goods[KEY_GOODS_COMMENT_NUM] = comment_dict[goods.get('id', 0)]
        return goods_list
    
    def get_images_num(self, goods_dict):
        if goods_dict.get('image6', ''):
            return 6
        elif goods_dict.get('image5', ''):
            return 5
        elif goods_dict.get('image4', ''):
            return 4
        elif goods_dict.get('image3', ''):
            return 3
        elif goods_dict.get('image2', ''):
            return 2
        elif goods_dict.get('image1', ''):
            return 1
            
    def get_session_infos_v2(self, session_id, start = 0, num = 20, filter_auto = 0, using_fix_content = 0, sorting = 0):
        try:
            handler = DbUtil(self.mobile_db, self.info_logger)
            results = handler.get_session_infos_v2(session_id, start, num, filter_auto, sorting)
            ret_list = []
            for goods in results:
                goods_info = goods[0]
                cutoff_money = goods[1]
                cutoff_rate = goods[2]
                goods_dict = json.loads(goods_info)
                if using_fix_content and goods[3]:
                    goods_dict['desc'] = goods[3]
                goods_dict[KEY_GOODS_CUTOFF_MONEY] = cutoff_money
                goods_dict[KEY_GOODS_CUTOFF_RATE] = cutoff_rate
                goods_dict['image_num'] = self.get_images_num(goods_dict)
                ret_list.append(goods_dict)
            return self.get_goods_comment_nums(ret_list)
        except Exception,e:
            self.info_logger.error('get_session_infos_v2 except %s'%(e))
            return []
            
    def get_session_goods_num(self, session_id):
        try:
            ret_data = self.session_collection.find_one({ITEM_MONGO_SESSION_ID: session_id})
            if not ret_data:
                return 0
            ret_data = ret_data.get('goods', [])
            return len(ret_data)
        except Exception,e:
            self.info_logger.error('get_session_goods_num except %s'%(e))
            return 0
    
    def fix_session_goods_infos(self, start_session_id, end_session_id):
        session_id = start_session_id
        handler = DbUtil(self.mobile_db, self.info_logger)
        failed_ids = []
        while start_session_id < end_session_id:
            try:
                ret_data = self.session_collection.find_one({ITEM_MONGO_SESSION_ID: session_id})
                if not ret_data:
                    failed_ids.append(session_id)
                    session_id += 1
                    continue
                ret_data = ret_data.get('goods', [])
                for goods in ret_data:
                    goods_id = goods.get('id')
                    sales_phone = goods.get('phone')
                    goods_info = handler.get_goods_info_by_id(goods_id)
                    if not goods_info:
                        failed_ids.append(session_id)
                        session_id += 1
                        continue
                    sales_info = handler.get_goods_sales_info(sales_phone)
                    #now = int(time.time())
                    goods_info.update(sales_info)
                    #goods_info['create_time'] = now
                    self.add_session_goods_list(session_id, sales_phone, goods_id, goods_info)
            except Exception,e:
                self.info_logger.error('fix_session_goods_infos except %s'%(e))
                failed_ids.append(session_id)
                session_id += 1
                continue
            session_id += 1
            print 'fix session %s ok'%(str(session_id))
            if session_id % 10 == 0:
                time.sleep(0.1)
if __name__ == '__main__':
    business_user_list = [
    '13822678953',
    '13833678953',
    ]
    handler = InstanceMessageV2Util(settings.COMMON_DATA)
    #print handler.get_new_session_id()
    #handler.add_session_goods(34, '13811678953', 2)
    #handler.add_client_forbid_user('13811678953', '11111111111');
    #handler.add_client_goods_message('13811678953', '13811678953', 2, None, 3)
    #handler.add_business_goods_message('13811678953', '13811678953', 2)
    #handler.customer_create_session('13811678953', ['13811678954', '13811678955'], u'我想买个马桶', u'马桶')
    #handler.unforbid_user('13811678953', '13811678953')
    #print handler.check_business_session_talked('13811678953',2,40)
    #handler.fix_session_goods_infos(1,6500)
    #handler.check_sales_session_info('18610886514', 1203)
