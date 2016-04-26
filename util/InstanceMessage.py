#coding=utf-8

import urllib,os,time,sys
import pymongo

if __name__ == '__main__':
    G_PATH = os.path.split(os.path.realpath(__file__))[0]
    sys.path.append(G_PATH + '/../../')
    os.environ['DJANGO_SETTINGS_MODULE'] = 'MobileService.settings'
    
    from django.conf import settings
    
from MobileService.util.mongodb_util import *
from MobileService.util.DbUtil import DbUtil
from MobileService.util.GearmanUtil import *
from MobileService.util.RecordInquire import RecordInquireUtil

CLIENT_COLLECTION = 'c_in'
BUSINESS_COLLECTION = 'b_in'
GROUP_COLLECTION = 'g_in'
RECORD_GROUP_COLLECTION = 'g_r_in'
INQUIRE_HISTORY_COLLECTION = 'i_h_in'

ITEM_MONGO_SESSION = 'session'
ITEM_MONGO_MAIL = 'mail'
ITEM_MONGO_GROUP_INFO = 'group'

KEY_KEY = '_id'
KEY_CONTENT = 'CT'
KEY_SESSION_LAST_REPLY_CONTENT = 'LRCT'
KEY_SESSION_CREATE_TIME = 'CM'
KEY_SESSION_UPDATE_TIME = 'UPT'
KEY_SESSION_TYPE = 'SE'
KEY_SESSION_STATE = 'ST'
KEY_SESSION_GROUP_ID = 'GID'
KEY_SESSION_DEST_PHONE = 'DPE'
KEY_SESSION_SEND_NUM = 'SNUM'

KEY_USER_NAME = 'NAME'
KEY_USER_BRAND_NAME = 'UBN'
KEY_USER_COOPERATION = 'COO'

KEY_MAIL_FROM_PHONE = 'FPE'
KEY_MAIL_CREATE_TIME = 'CM'
KEY_MAIL_CONTENT = 'CT'
KEY_MAIL_STATE = 'ST'
KEY_MAIL_TYPE = 'TE'

KEY_GROUP_USER_PHONE = 'user_phone'
KEY_GROUP_DEST_USER_PHONE = 'dest_phone'
KEY_GROUP_GROUP_ID = 'group_id'
KEY_GROUP_STATE = 'state'
KEY_GROUP_DETAIL = 'detail'
KEY_GROUP_GROUP_COUNT = 'count'

TYPE_SESSION_MULTI = 0
TYPE_SESSION_SIGLE = 1

TYPE_SESSION_STATE_NO_STATE = 0
TYPE_SESSION_STATE_REPLY_ONCE = 1
TYPE_SESSION_STATE_CAN_NOT_REPLY = 2
TYPE_SESSION_STATE_REPLY_FREEDOM = 3
TYPE_SESSION_STATE_REPLY_FORBID = 4

TYPE_MESSAGE_NORMAL = 0
TYPE_MESSAGE_POSITION = 1
TYPE_MESSAGE_NOTICE = 2

class InstanceMessageUtil():
    def __init__(self, database):
        self.info_logger = database['mobile_logger']
        self.gearman_config = database['gearman_config']
        self.redis = database['cache_redis']
        self.mobile_db = database['mobile_db']
        self.database = database
        self.get_mongo_connect()
    
    def get_business_name_brand(self, phone):
        handler = DbUtil(self.mobile_db, self.info_logger)
        return handler.get_business_name_brand(phone)
    
    def add_chat_group_info(self, user_phone, group_id, send_num, total_num, content, brand_name, state):
        handler = DbUtil(self.mobile_db, self.info_logger)
        ctime = int(time.time())
        return handler.add_chat_group_info(user_phone, group_id, send_num, total_num, content, brand_name, state, ctime)
    
    def update_chat_group_total_num(self, group_id):
        handler = DbUtil(self.mobile_db, self.info_logger)
        handler.update_chat_group_total_num(group_id)

    def send_task_event(self, phone, from_phone, is_c = True):
        #handler_push = GearmanUtil(self.gearman_config)
        #handler_push.send_inquire_talk(phone, from_phone, is_c)
        pass
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
    
    def update_session_total_num(self, user_phone, dest_phone, group_id):
        try:
            user_phone = int(user_phone)
            dest_phone = int(dest_phone)  
            group_id = int(group_id)
            update_group_id = ITEM_MONGO_SESSION + '.' + KEY_SESSION_GROUP_ID
            update_total_count = ITEM_MONGO_SESSION + '.$.' + KEY_GROUP_GROUP_COUNT
            ret_dict = {}
            ret_dict[update_total_count] = 1
            ret_data = self.c_collection.find_and_modify({KEY_KEY: user_phone, update_group_id: group_id}, {"$inc" : ret_dict})
            return True
        except Exception,e:
            self.info_logger.error('update_session_total_num except %s'%(e))
            return False   
            
    def get_mongo_connect(self):
        self.mongo_db = MongoDatabase().get_database()
        self.c_collection = self.mongo_db[CLIENT_COLLECTION]
        self.b_collection = self.mongo_db[BUSINESS_COLLECTION]
        self.g_collection = self.mongo_db[GROUP_COLLECTION]
        self.g_r_collection = self.mongo_db[RECORD_GROUP_COLLECTION]
        self.i_h_collection = self.mongo_db[INQUIRE_HISTORY_COLLECTION]
    
    def format_record_group(self, user_phone, dest_phone, group_id):     
        ret_dict = {}
        ret_dict[KEY_GROUP_USER_PHONE] = user_phone
        ret_dict[KEY_GROUP_DEST_USER_PHONE] = dest_phone
        ret_dict[KEY_GROUP_GROUP_ID] = group_id
        return ret_dict
        
    def format_session_history(self, ret_data):
        if not ret_data:
            return []
        ret_list = []
        for session in ret_data:
            ret_dict = {}
            ret_dict['content'] = session.get(KEY_SESSION_LAST_REPLY_CONTENT, '')
            ret_dict['create_time'] = session.get(KEY_SESSION_CREATE_TIME, 0)
            ret_dict['dest_phone'] = str(session.get(KEY_SESSION_DEST_PHONE, 0))
            ret_dict['send_num'] = session.get(KEY_SESSION_SEND_NUM, 0)
            ret_list.append(ret_dict)
        return ret_list
        
    def get_client_session_history_num(self):
        return self.i_h_collection.find().count()
        
    def get_client_session_history(self, start, num):
        ret_data = self.i_h_collection.find().sort(KEY_SESSION_CREATE_TIME, pymongo.DESCENDING).skip(start).limit(num)
        return self.format_session_history(ret_data)
        
    def record_client_session_history(self, user_phone, content, now, send_num):
        data_input = self.format_client_session(user_phone, content, now, send_num, False)
        try:
            self.i_h_collection.insert(data_input)
        except Exception,e:
            self.info_logger.error('record_client_session_history except %s'%(e))
            
    def record_group_id(self, user_phone, dest_phone, group_id):
        user_phone = int(user_phone)
        dest_phone = int(dest_phone)     
        ret_dict = self.format_record_group(user_phone, dest_phone, group_id)
        try:
            self.g_r_collection.find_and_modify({KEY_GROUP_USER_PHONE:user_phone, KEY_GROUP_DEST_USER_PHONE:dest_phone}, {"$set": ret_dict}, upsert=True)
            return True
        except Exception,e:
            self.info_logger.error('record_group_id except %s'%(e))
            return False
    
    def get_group_id(self, user_phone, dest_phone):
        user_phone = int(user_phone)
        dest_phone = int(dest_phone)
        try:
            ret_data = self.g_r_collection.find_one({KEY_GROUP_USER_PHONE:user_phone, KEY_GROUP_DEST_USER_PHONE:dest_phone}, fields = [KEY_GROUP_GROUP_ID])
            if not ret_data:
                return None
            return ret_data.get(KEY_GROUP_GROUP_ID, None)
        except Exception,e:
            self.info_logger.error('get_group_id except %s'%(e))
            return None        
        
    def format_mail_message(self, user_phone, dest_phone, content, state, type):
        ret_dict = {}
        now = int(time.time())
        ret_dict[KEY_MAIL_FROM_PHONE] = user_phone
        ret_dict[KEY_MAIL_CREATE_TIME] = now
        ret_dict[KEY_MAIL_CONTENT] = content
        ret_dict[KEY_MAIL_STATE] = state
        ret_dict[KEY_MAIL_TYPE] = type
        return ret_dict
        
    def push_message_mail(self, user_phone, dest_phone, content, is_c = True, state = TYPE_SESSION_STATE_REPLY_FREEDOM, type = TYPE_MESSAGE_NORMAL):
        user_phone = int(user_phone)
        dest_phone = int(dest_phone)
        if is_c:
            ret_dict = self.format_mail_message(user_phone, dest_phone, content, state, type)
            try:
                self.b_collection.find_and_modify({KEY_KEY: dest_phone}, {"$push" : {ITEM_MONGO_MAIL: {"$each": [ret_dict], "$sort": {KEY_MAIL_CREATE_TIME: -1}, '$slice': -200} }}, upsert=True)
                self.send_task_event(dest_phone, user_phone, is_c)
                return True
            except Exception,e:
                self.info_logger.error('push_message_mail except %s'%(e))
                return False
        else:
            ret_dict = self.format_mail_message(user_phone, dest_phone, content, state, type)
            try:
                self.c_collection.find_and_modify({KEY_KEY: dest_phone}, {"$push" : {ITEM_MONGO_MAIL: {"$each": [ret_dict], "$sort": {KEY_MAIL_CREATE_TIME: -1}, '$slice': -200} }}, upsert=True)
                self.send_task_event(dest_phone, user_phone, is_c)
                return True
            except Exception,e:
                self.info_logger.error('push_message_mail except %s'%(e))
                return False        

    def update_session(self, user_phone, dest_phone, is_c, group_id, state, content = ''):
        user_phone = int(user_phone)
        dest_phone = int(dest_phone)
        talk_user = ITEM_MONGO_SESSION + '.' + KEY_SESSION_DEST_PHONE
        talk_state = ITEM_MONGO_SESSION + '.' + KEY_SESSION_STATE
        update_talk_state = ITEM_MONGO_SESSION + '.$.' + KEY_SESSION_STATE
        reply_content = ITEM_MONGO_SESSION + '.$.' + KEY_SESSION_LAST_REPLY_CONTENT
        update_group_id = ITEM_MONGO_SESSION + '.$.' + KEY_SESSION_GROUP_ID
        ret_dict = {}
        if content:
            ret_dict[reply_content] = content
        if update_group_id:
            ret_dict[update_group_id] = group_id
        ret_dict[update_talk_state] = state
        try:
            if is_c:
                ret_data = self.c_collection.find_and_modify({KEY_KEY: user_phone, talk_user: dest_phone}, {"$set" : ret_dict},  fields = [talk_state])
            else:
                ret_data = self.b_collection.find_and_modify({KEY_KEY: user_phone, talk_user: dest_phone}, {"$set" : ret_dict},  fields = [talk_state])
            if ret_data:
                return True
            else:
                return False
        except Exception,e:
            self.info_logger.error('update_business_session except %s'%(e))
            return False      
    
    def talk_to_business(self, user_phone, dest_phone, content):
        if not dest_phone:
            return False
        user_phone = int(user_phone)
        dest_phone = int(dest_phone)        
        self.create_client_session(user_phone, dest_phone, content)
        ###reverse phone, update business talk privilege
        self.update_session(dest_phone, user_phone, False, 0, TYPE_SESSION_STATE_REPLY_FREEDOM)
        try:
            self.record_message_count(dest_phone, False)
            self.update_user_session_seq(user_phone, dest_phone, False)
            handler = RecordInquireUtil(self.database)
            handler.record_talk_info(user_phone, dest_phone, 'wallet_client', '', content)
            return self.push_message_mail(user_phone, dest_phone, content)
        except Exception,e:
            self.info_logger.error('talk_to_business except %s'%(e))
            return False

    def format_client_group(self, dest_phone, content, group_id, now):
        ret_dict = {}
        ret_dict[KEY_SESSION_LAST_REPLY_CONTENT] = content
        ret_dict[KEY_SESSION_CREATE_TIME] = now
        ret_dict[KEY_SESSION_UPDATE_TIME] = now
        ret_dict[KEY_SESSION_GROUP_ID] = group_id
        ret_dict[KEY_SESSION_DEST_PHONE] = int(dest_phone)
        ret_dict[KEY_USER_NAME] = ''
        ret_dict[KEY_USER_BRAND_NAME] = ''
        ret_dict[KEY_USER_COOPERATION] = 0
        data_dict = self.get_business_name_brand(dest_phone)
        if data_dict:
            ret_dict[KEY_USER_NAME] = data_dict.get('name', '')
            ret_dict[KEY_USER_BRAND_NAME] = data_dict.get('brand_name', '')
            ret_dict[KEY_USER_COOPERATION] = data_dict.get('cooperation', '')
        return ret_dict
        
    def add_group_info(self, user_phone, dest_phone, group_id, content):
        user_phone = int(user_phone)
        dest_phone = int(dest_phone)
        now = int(time.time())
        try:
            ret_dict = self.format_client_group(dest_phone, content, group_id, now)
            self.g_collection.find_and_modify({KEY_GROUP_USER_PHONE: user_phone, KEY_GROUP_GROUP_ID: group_id}, {"$push" : {KEY_GROUP_DETAIL: {"$each": [ret_dict], "$sort": {KEY_SESSION_CREATE_TIME: -1}, '$slice': -200} }, '$inc': {KEY_GROUP_GROUP_COUNT: 1}}, upsert=True)            
            self.update_session_total_num(user_phone, dest_phone, group_id)
            self.update_chat_group_total_num(group_id)
            return True
        except Exception,e:
            self.info_logger.error('add_group_info except %s'%(e))
            return False
    
    def format_group_info(self, ret_data):
        if not ret_data:
            return []
        session_list = ret_data.get(KEY_GROUP_DETAIL, [])
        if not session_list:
            return []
        ret_list = []
        for session in session_list:
            ret_dict = {}
            ret_dict['content'] = session.get(KEY_SESSION_LAST_REPLY_CONTENT, '')
            ret_dict['create_time'] = session.get(KEY_SESSION_CREATE_TIME, 0)
            ret_dict['group_id'] = session.get(KEY_SESSION_GROUP_ID, 0)
            ret_dict['dest_phone'] = str(session.get(KEY_SESSION_DEST_PHONE, 0))
            ret_dict['name'] = session.get(KEY_USER_NAME, '')
            ret_dict['brand_name'] = session.get(KEY_USER_BRAND_NAME, '')
            ret_dict['cooperation'] = session.get(KEY_USER_COOPERATION, 0)
            ret_list.append(ret_dict)
        return ret_list
        
    def get_group_info(self, user_phone, group_id, start=0, num=20):
        user_phone = int(user_phone)
        group_id = int(group_id)
        try:
            if start != 0:
                ret_data = self.g_collection.find_one({KEY_GROUP_USER_PHONE: user_phone, KEY_GROUP_GROUP_ID: group_id}, {KEY_GROUP_DETAIL: {"$slice" : [start, num]}})
                
            else:
                ret_data = self.g_collection.find_one({KEY_GROUP_USER_PHONE: user_phone, KEY_GROUP_GROUP_ID: group_id}, {KEY_GROUP_DETAIL: {"$slice" : num}})
            return self.format_group_info(ret_data)
        except Exception,e:
            self.info_logger.error('get_group_info except %s'%(e))
            return []
    
    def format_user_mail(self, ret_data):
        if not ret_data:
            return []
        ret_list = []
        mail_list = ret_data.get(ITEM_MONGO_MAIL, [])
        for mail in mail_list:
            ret_dict = {}
            ret_dict['dest_phone'] = str(mail.get(KEY_MAIL_FROM_PHONE, ''))
            ret_dict['create_time'] = mail.get(KEY_MAIL_CREATE_TIME, '')
            ret_dict['content'] = mail.get(KEY_MAIL_CONTENT, '')
            ret_dict['state'] = mail.get(KEY_MAIL_STATE, '')
            ret_dict['type'] = mail.get(KEY_MAIL_TYPE, TYPE_MESSAGE_NORMAL)
            ret_list.append(ret_dict)
        return ret_list
    
    def get_user_mail(self, user_phone, is_c = True):
        user_phone = int(user_phone)
        ret_fileds = []
        ret_fileds.append(ITEM_MONGO_MAIL)
        if is_c:
            ret_data = self.c_collection.find_one({KEY_KEY: user_phone}, fields = ret_fileds)
            self.c_collection.update({KEY_KEY: user_phone}, {'$unset' : {ITEM_MONGO_MAIL: ''}})
        else:
            ret_data = self.b_collection.find_one({KEY_KEY: user_phone}, fields = ret_fileds)
            self.b_collection.update({KEY_KEY: user_phone}, {'$unset' : {ITEM_MONGO_MAIL: ''}})
        if ret_data:
            self.clear_message_count(user_phone, is_c)
        return self.format_user_mail(ret_data)
        
    def get_session_group_id(self, user_phone, dest_phone, is_c = False):
        try:
            user_phone = int(user_phone)
            dest_phone = int(dest_phone)
            talk_user = ITEM_MONGO_SESSION + '.' + KEY_SESSION_DEST_PHONE
            talk_group_id = ITEM_MONGO_SESSION + '.' + KEY_SESSION_GROUP_ID
            ret_fileds = []
            ret_fileds.append(talk_group_id)
            ret_fileds.append(talk_user)
            if is_c:
                ret_data = self.c_collection.find_one({KEY_KEY: user_phone, talk_user: dest_phone}, fields = ret_fileds)
            else:
                ret_data = self.b_collection.find_one({KEY_KEY: user_phone, talk_user: dest_phone}, fields = ret_fileds)
            print ret_data
            if not ret_data:
                return {}
            state_info_list = ret_data.get(ITEM_MONGO_SESSION, [])
            if not state_info_list or len(state_info_list) != 1:
                return {}
            ret_dict = {}
            
            ret_dict['group_id'] = state_info_list[0].get(KEY_SESSION_GROUP_ID, 0)
            return ret_dict
        except Exception,e:
            self.info_logger.error('get_session_group_id except %s'%(e))
            return {}
            
    def get_session_info(self, user_phone, dest_phone, is_c = False):
        try:
            user_phone = int(user_phone)
            dest_phone = int(dest_phone)
            talk_user = ITEM_MONGO_SESSION + '.' + KEY_SESSION_DEST_PHONE
            talk_state = ITEM_MONGO_SESSION + '.' + KEY_SESSION_STATE
            talk_group_id = ITEM_MONGO_SESSION + '.' + KEY_SESSION_GROUP_ID
            talk_session_type = ITEM_MONGO_SESSION + '.' + KEY_SESSION_TYPE
            ret_fileds = []
            ret_fileds.append(talk_state)
            ret_fileds.append(talk_group_id)
            ret_fileds.append(talk_session_type)
            
            if is_c:
                ret_data = self.c_collection.find_one({KEY_KEY: user_phone, talk_user: dest_phone}, fields = ret_fileds)
            else:
                ret_data = self.b_collection.find_one({KEY_KEY: user_phone, talk_user: dest_phone}, fields = ret_fileds)
            print ret_data
            if not ret_data:
                return {}
            state_info_list = ret_data.get(ITEM_MONGO_SESSION, [])
            if not state_info_list or len(state_info_list) != 1:
                return {}
            ret_dict = {}
            
            ret_dict['state'] = state_info_list[0].get(KEY_SESSION_STATE, TYPE_SESSION_STATE_CAN_NOT_REPLY)
            ret_dict['group_id'] = state_info_list[0].get(KEY_SESSION_GROUP_ID, 0)
            ret_dict['session_type'] = state_info_list[0].get(KEY_SESSION_TYPE, 0)
            ret_dict['user_phone'] = user_phone
            ret_dict['dest_phone'] = dest_phone
            return ret_dict
        except Exception,e:
            self.info_logger.error('get_session_info except %s'%(e))
            return {}
            
    def check_session(self, user_phone, dest_phone, state_list = [], is_c = False):
        try:
            user_phone = int(user_phone)
            dest_phone = int(dest_phone)
            talk_user = ITEM_MONGO_SESSION + '.' + KEY_SESSION_DEST_PHONE
            talk_state = ITEM_MONGO_SESSION + '.' + KEY_SESSION_STATE
            if is_c:
                if not state_list:
                    ret_data = self.c_collection.find_one({KEY_KEY: user_phone, talk_user: dest_phone}, fields = [KEY_KEY])
                else:
                    ret_data = self.c_collection.find_one({KEY_KEY: user_phone, ITEM_MONGO_SESSION: {"$elemMatch": {KEY_SESSION_DEST_PHONE:dest_phone, KEY_SESSION_STATE:{"$in":state_list}}}}, fields = [KEY_KEY])
 
            else:
                if not state_list:
                    ret_data = self.b_collection.find_one({KEY_KEY: user_phone, talk_user: dest_phone}, fields = [KEY_KEY])
                else:    
                    #ret_data = self.b_collection.find_one({KEY_KEY: user_phone, talk_user: dest_phone, talk_state: {"$in":state_list}}, fields = [KEY_KEY])
                    ret_data = self.b_collection.find_one({KEY_KEY: user_phone, ITEM_MONGO_SESSION: {"$elemMatch": {KEY_SESSION_DEST_PHONE:dest_phone, KEY_SESSION_STATE:{"$in":state_list}}}}, fields = [KEY_KEY])
                   
            #self.info_logger.info('check_session %s'%(str(ret_data)))
            if not ret_data:
                return False
            else:
                return True
        except Exception,e:
            self.info_logger.error('check_session except %s'%(e))
            return False
    
    def forbid_business_talk(self, user_phone, dest_phone):
        return self.update_session(dest_phone, user_phone, False, 0, TYPE_SESSION_STATE_REPLY_FORBID)
        
    def check_business_talk_privilege(self, user_phone, dest_phone):
        user_phone = int(user_phone)
        dest_phone = int(dest_phone)
        state_list = []
        state_list.append(TYPE_SESSION_STATE_REPLY_ONCE)
        state_list.append(TYPE_SESSION_STATE_REPLY_FREEDOM)
        return self.check_session(user_phone, dest_phone, state_list)     
    
    def update_user_session_seq(self, user_phone, dest_phone, is_c = True):
        user_phone = int(user_phone)
        dest_phone = int(dest_phone)
        talk_user = ITEM_MONGO_SESSION + '.' + KEY_SESSION_DEST_PHONE
        update_time = ITEM_MONGO_SESSION + '.$.' + KEY_SESSION_UPDATE_TIME
        ret_dict = {}
        ret_dict[update_time] = int(time.time())
        try:
            if is_c:
                ret_data = self.c_collection.find_and_modify({KEY_KEY: dest_phone, talk_user: user_phone}, {"$set" : ret_dict})
                self.c_collection.find_and_modify({KEY_KEY: dest_phone}, {"$push" : {ITEM_MONGO_SESSION: {"$each": [], "$sort": {KEY_SESSION_UPDATE_TIME: -1}} }})
                
            else:
                ret_data = self.b_collection.find_and_modify({KEY_KEY: dest_phone, talk_user: user_phone}, {"$set" : ret_dict})
                self.b_collection.find_and_modify({KEY_KEY: dest_phone}, {"$push" : {ITEM_MONGO_SESSION: {"$each": [], "$sort": {KEY_SESSION_UPDATE_TIME: -1}} }})
                
            if ret_data:
                return True
            else:
                return False
        except Exception,e:
            self.info_logger.error('update_user_session_seq except %s'%(e))
            return False

    def talk_to_custom(self, user_phone, dest_phone, content, type = TYPE_MESSAGE_NORMAL):
        user_phone = int(user_phone)
        dest_phone = int(dest_phone)
        if not dest_phone:
            return TYPE_SESSION_STATE_CAN_NOT_REPLY
        if not self.check_business_talk_privilege(user_phone, dest_phone):
            self.info_logger.info('talk_to_custom %s to %s no privilege'%(str(user_phone),str(dest_phone)))
            return TYPE_SESSION_STATE_REPLY_FORBID
        group_id = self.get_group_id(dest_phone, user_phone)
        if self.check_session(user_phone, dest_phone, [TYPE_SESSION_STATE_REPLY_ONCE]):
            if type == TYPE_MESSAGE_NORMAL:
                self.info_logger.info('%s talk %s add multi session'%(str(user_phone), str(dest_phone)))
                self.add_group_info(dest_phone, user_phone, group_id, content)
                self.update_session(user_phone, dest_phone, False, group_id, TYPE_SESSION_STATE_REPLY_FREEDOM)
            else:
                return TYPE_SESSION_STATE_REPLY_ONCE
        try:
            self.record_message_count(dest_phone, True)
            self.push_message_mail(user_phone, dest_phone, content, False, TYPE_SESSION_STATE_REPLY_FREEDOM, type)
            self.update_user_session_seq(user_phone, dest_phone)
            handler = RecordInquireUtil(self.database)
            handler.record_talk_info(user_phone, dest_phone, 'wallet_business', '', content)
            return TYPE_SESSION_STATE_REPLY_FREEDOM
        except Exception,e:
            self.info_logger.error('talk_to_custom except %s'%(e))
            return TYPE_SESSION_STATE_REPLY_FREEDOM             

    def format_business_session(self, dest_phone, content, now, group_id):
        ret_dict = {}
        ret_dict[KEY_SESSION_LAST_REPLY_CONTENT] = content
        ret_dict[KEY_SESSION_CREATE_TIME] = now
        ret_dict[KEY_SESSION_UPDATE_TIME] = now
        ret_dict[KEY_SESSION_TYPE] = TYPE_SESSION_SIGLE
        ret_dict[KEY_SESSION_STATE] = TYPE_SESSION_STATE_REPLY_ONCE
        ret_dict[KEY_SESSION_DEST_PHONE] = int(dest_phone)
        ret_dict[KEY_SESSION_GROUP_ID] = group_id
        return ret_dict       
        
    def _create_business_session(self, user_phone, dest_phone, content, group_id):
        user_phone = int(user_phone)
        dest_phone = int(dest_phone)
        now = int(time.time())
        if self.check_session(user_phone, dest_phone):
            self.update_session(user_phone, dest_phone, False, group_id, TYPE_SESSION_STATE_REPLY_ONCE, content)
            return True
        ret_dict = self.format_business_session(dest_phone, content, now, group_id)
        try:
            self.b_collection.find_and_modify({KEY_KEY: user_phone}, {"$push" : {ITEM_MONGO_SESSION: {"$each": [ret_dict], "$sort": {KEY_SESSION_UPDATE_TIME: -1}, '$slice': -200} }}, upsert=True)
            return True
        except Exception,e:
            self.info_logger.error('create_business_session except %s'%(e))
            return False

    def format_client_session(self, dest_phone, content, now, send_num=0, multi=True):
        ret_dict = {}
        ret_dict[KEY_SESSION_LAST_REPLY_CONTENT] = content
        ret_dict[KEY_SESSION_CREATE_TIME] = now
        ret_dict[KEY_SESSION_UPDATE_TIME] = now
        if multi:
            ret_dict[KEY_SESSION_TYPE] = TYPE_SESSION_MULTI
        else:
            ret_dict[KEY_SESSION_TYPE] = TYPE_SESSION_SIGLE
        ret_dict[KEY_SESSION_STATE] = TYPE_SESSION_STATE_REPLY_ONCE
        ret_dict[KEY_SESSION_SEND_NUM] = send_num
        if multi:
            ret_dict[KEY_SESSION_GROUP_ID] = now
            ret_dict[KEY_USER_NAME] = ''
            ret_dict[KEY_USER_BRAND_NAME] = ''            
        else:
            ret_dict[KEY_SESSION_GROUP_ID] = 0
            ret_dict[KEY_USER_NAME] = ''
            ret_dict[KEY_USER_BRAND_NAME] = ''             
            ret_dict[KEY_SESSION_DEST_PHONE] = int(dest_phone)
            data_dict = self.get_business_name_brand(dest_phone)
            if data_dict:
                ret_dict[KEY_USER_NAME] = data_dict.get('name', '')
                ret_dict[KEY_USER_BRAND_NAME] = data_dict.get('brand_name', '')
                ret_dict[KEY_USER_COOPERATION] = data_dict.get('cooperation', '')
        return ret_dict
        
    def create_client_session(self, user_phone, dest_phone, content):
        now = int(time.time())
        user_phone = int(user_phone)
        dest_phone = int(dest_phone)
        if self.check_session(user_phone, dest_phone, [], True):
            return True
        try:
            ret_dict = self.format_client_session(dest_phone, content, now, 0, False)
            self.c_collection.find_and_modify({KEY_KEY: user_phone}, {"$push" : {ITEM_MONGO_SESSION: {"$each": [ret_dict], "$sort": {KEY_SESSION_UPDATE_TIME: -1}, '$slice': -200} }}, upsert=True)            
            return True
        except Exception,e:
            self.info_logger.error('create_client_session except %s'%(e))
            return False
    
    def send_inquire_to_business(self, user_phone, dest_phone_list, content, group_id):
        for dest_phone in dest_phone_list:
            dest_phone = int(dest_phone)
            state = TYPE_SESSION_STATE_REPLY_ONCE
            self._create_business_session(dest_phone, user_phone, content, group_id)
            self.record_group_id(user_phone, dest_phone, group_id)
            self.push_message_mail(user_phone, dest_phone, content, True, state)
            self.update_user_session_seq(user_phone, dest_phone, False)
            time.sleep(0.01)
        
    def create_client_multi_session(self, user_phone, dest_phone_list, content, create_time, category = ''):
        user_phone = int(user_phone)
        now = create_time
        group_id = now
        ret_dict = self.format_client_session('', content, now, len(dest_phone_list), True)
        try:
            self.c_collection.find_and_modify({KEY_KEY: user_phone}, {"$push" : {ITEM_MONGO_SESSION: {"$each": [ret_dict], "$sort": {KEY_SESSION_UPDATE_TIME: -1}, '$slice': -200} }}, upsert=True)
            #self.send_inquire_to_business(user_phone, dest_phone_list, content, group_id)
            self.record_client_session_history(user_phone, content, now, len(dest_phone_list))
            self.add_chat_group_info(user_phone, group_id, len(dest_phone_list), 0, content, '', 1)
            handler = RecordInquireUtil(self.database)
            handler.record_create_session(user_phone, category, content)
            return True
        except Exception,e:
            self.info_logger.error('create_client_multi_session except %s'%(e))
            return False
    
    def format_session_list(self, ret_data):
        if not ret_data:
            return []
        session_list = ret_data.get(ITEM_MONGO_SESSION, [])
        if not session_list:
            return []
        ret1_dict = {}
        
        ret_list = []
        for session in session_list:
            ret_dict = {}
            ret_dict['content'] = session.get(KEY_SESSION_LAST_REPLY_CONTENT, '')
            ret_dict['create_time'] = session.get(KEY_SESSION_CREATE_TIME, 0)
            ret_dict['update_time'] = session.get(KEY_SESSION_UPDATE_TIME, 0)
            ret_dict['type'] = session.get(KEY_SESSION_TYPE, 0)
            ret_dict['state'] = session.get(KEY_SESSION_STATE, 0)
            ret_dict['group_id'] = session.get(KEY_SESSION_GROUP_ID, 0)
            ret_dict['dest_phone'] = str(session.get(KEY_SESSION_DEST_PHONE, 0))
            ret_dict['send_num'] = session.get(KEY_SESSION_SEND_NUM, 0)
            ret_dict['name'] = session.get(KEY_USER_NAME, '')
            ret_dict['brand_name'] = session.get(KEY_USER_BRAND_NAME, '') 
            ret_dict['total_num'] = session.get(KEY_GROUP_GROUP_COUNT, 0)
            ret_dict['cooperation'] = session.get(KEY_USER_COOPERATION, 0)
            ret_list.append(ret_dict)
        return ret_list
        
    def get_user_session_list(self, user_phone, is_c, start=0, num=20, type = -1):
        try:
            user_phone = int(user_phone)
            if is_c:
                if start != 0:
                    ret_data = self.c_collection.find_one({KEY_KEY: user_phone}, {ITEM_MONGO_SESSION: {"$slice" : [start, num]}})
                    
                else:
                    ret_data = self.c_collection.find_one({KEY_KEY: user_phone}, {ITEM_MONGO_SESSION: {"$slice" : num}})
            else:
                if start != 0:
                    ret_data = self.b_collection.find_one({KEY_KEY: user_phone}, {ITEM_MONGO_SESSION: {"$slice" : [start, num]}})
                    
                else:
                    ret_data = self.b_collection.find_one({KEY_KEY: user_phone}, {ITEM_MONGO_SESSION: {"$slice" : num}})
            
            return self.format_session_list(ret_data)
        except Exception,e:
            self.info_logger.error('get_user_session_list except %s'%(e))
            return []
        
if __name__ == '__main__':
    business_user_list = [
    '13822678953',
    '13833678953',
    ]
    handler = InstanceMessageUtil(settings.COMMON_DATA)
    #handler.create_client_multi_session('13811678953', business_user_list, u'我去马桶怎么卖？')
    #handler.talk_to_custom('13822678953', '13811678953', '100kua')
    handler.talk_to_business('13811678953', '13822678953', '你们在?')
    # handler.create_client_multi_session('13822678953', '13811678953', 'sdfsdf',1)
    # handler._create_business_session('13822678953', '13811678853', 'wod',1)
    # print handler.get_user_session_list('13822678953', False)
    # handler.get_session_info('13822678953', '13811678854')
    #
    # print handler.check_business_talk_privilege('13822678953', '13811678953')
    # print handler.check_business_talk_privilege('13822678956', '13811678953')
    # print handler.check_business_talk_privilege('13822678856', '13811678953')
