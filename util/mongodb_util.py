#coding=utf-8

import time
from datetime import datetime, date, timedelta
from pymongo import Connection, MongoClient, MongoReplicaSetClient,GEO2D
from pymongo.read_preferences import ReadPreference
from pymongo.database import Database

if __name__ == '__main__':
    import os,sys
    G_PATH = os.path.split(os.path.realpath(__file__))[0]
    sys.path.append(G_PATH + '/../../')
    os.environ['DJANGO_SETTINGS_MODULE'] = 'MobileService.settings'

from django.conf import settings

class MongoDatabase():
    def __init__(self, host = None, port = None, db = None):
        mongo_config = settings.COMMON_DATA['mongo_db']
        if 1:
            self.use_replica_set = False
            if not host:
                self.host = mongo_config[0]
            else:
                self.host = host
            if not port:
                self.port = int(mongo_config[1])
            else:
                self.port = port
            if not db:
                self.db = mongo_config[2]
            else:
                self.db = db
        else:
            self.use_replica_set = True
            self.relica_set = global_variables.MONGODB_REPLICA_SET
            if not db:
                self.db = global_variables.KAKER_MONGODB_DATABASE
            else:
                self.db = db            
    def get_database(self, secondary_read = 0):
        if not self.use_replica_set:
            return Database(Connection(self.host, self.port), self.db)
        else:
            client = MongoReplicaSetClient(self.relica_set, replicaSet='xinwo')
            db = client[self.db]
            if secondary_read != 0:
                db.read_preference = ReadPreference.SECONDARY_PREFERRED
            return db
            
class ShopLocation():
    def __init__(self):
        self.mongo_db = MongoDatabase().get_database()
        self.collection = self.mongo_db['shop_location']
        self.malls_collection = self.mongo_db['malls_location']
        
    def save_shop_location(self, shop_id, longitude, latitude, data= {}):
        loc = {"loc": [longitude, latitude], "data": data}
        try:
            self.collection.find_and_modify({'_id' : shop_id}, { "$set" : loc}, upsert=True)
        except Exception,e:
            pass

    def save_malls_location(self, mall_name, longitude, latitude, data= {}):
        loc = {"loc": [longitude, latitude], "data": data}
        try:
            self.malls_collection.find_and_modify({'mall_name' : mall_name}, { "$set" : loc}, upsert=True)
        except Exception,e:
            pass
            
    def ensure_index(self):
        try:
            self.collection.ensure_index([('loc',GEO2D)])
            self.malls_collection.ensure_index([('loc',GEO2D)])
        except Exception,e:
            print e
    
    def format_find_shops_dict(self, filter, district = '', mall = ''):
        ret_dict = {}
        if filter & 0x1:
            ret_dict['data.can_use_coupon'] = 1
        if filter & 0x2:
            ret_dict['data.can_give_coupon'] = 1
        if filter & 0x4:
            ret_dict['data.has_discount'] = 1
        if district:
            ret_dict['data.district'] = district
        if mall:
            ret_dict['data.mall'] = mall
            
        return ret_dict
            
    def find_shops(self, longitude, latitude, num=10, filter=0):
        try:
            ret_dict = {'loc': {'$near': [longitude, latitude]}}
            ret_dict.update(self.format_find_shops_dict(filter))
            #results = self.collection.find({'loc': {'$near': [longitude, latitude]}}).limit(num)
            
            results = self.collection.find(ret_dict).limit(num)
            
        except Exception,e:
            print e
            return []
        else:
            shop_list = []
            if not results:
                return []
            print results
            for result in results:
                shop_list.append(result['data'])
            return shop_list

    def find_shops_by_category_brand(self, category_id, brand_id, num=10, filter=0, district='', mall=''):
        try:
            filter_dict = self.format_find_shops_dict(filter, district, mall)
            if category_id and brand_id:
                base_dict = {'data.category_brand':{"$elemMatch":{'c_id': category_id, 'b_id': brand_id}}}
                base_dict.update(filter_dict)
                results = self.collection.find(base_dict)
            elif category_id:
                base_dict = {'data.category_brand.c_id': category_id}
                base_dict.update(filter_dict)
                print base_dict
                results = self.collection.find(base_dict)
            elif brand_id:
                base_dict = {'data.category_brand.b_id': brand_id}
                base_dict.update(filter_dict)
                results = self.collection.find(base_dict)
            else:
                base_dict = {}
                base_dict.update(filter_dict)
                print base_dict
                results = self.collection.find(base_dict)
                
        except Exception,e:
            print e
            return []
        else:
            shop_list = []
            if not results:
                return []
            for result in results:
                shop_list.append(result['data'])
            return shop_list
            
    def find_shop(self, shop_id):
        try:
            result = self.collection.find({'_id' : shop_id})
            if not result:
                return {}
            else:
                return result['data']
        except Exception,e:
            print e
            return {}
            
    def find_malls(self, longitude, latitude, category, num=10):
        try:
            reg_condition = '.*' + category + '.*'
            ret_dict = {'loc': {'$near': [longitude, latitude]}}
            if category:
                ret_dict['data.category'] = {'$regex': reg_condition, '$options':'i'}
            results = self.malls_collection.find(ret_dict).limit(num)
        except Exception,e:
            print e
            return []
        else:
            shop_list = []
            if not results:
                return []
            print results
            for result in results:
                shop_list.append(result['data'])
            return shop_list        
    def remove_malls(self):
        try:
            result = self.malls_collection.remove()
            return True
        except Exception,e:
            print e
            return False
            
    def remove_shops(self):
        try:
            result = self.collection.remove()
            return True
        except Exception,e:
            print e
            return False
            
    def search_shop(self, keyword):
        try:
            reg_condition = '.*' + keyword + '.*'
            results = self.collection.find({'data.shop_name' : {'$regex': reg_condition, '$options':'i'}})
            shop_list = []
            for result in results:
                shop_list.append(result['data'])
            return shop_list
        except Exception, e:
            print e
            return []

class MongoMessage():
    def __init__(self, collection):
        self.mongo_db = MongoDatabase().get_database()
        self.collection = self.mongo_db[collection]

    def send_messsage(self, user_id, title, content):
        message_dict = {}
        message_dict['title'] = title
        message_dict['content'] = content
        message_dict['create_time'] = int(time.time())
        try:
            self.collection.find_and_modify({'_id':int(user_id)}, {"$inc" : {'message_num' : 1}, "$push" : {'messages': {"$each": [message_dict], "$sort": {'create_time': -1}, '$slice': -100}}}, upsert=True)
            return True
        except Exception,e:
            self.info_logger.error('send_messsage except %s'%(e))
            return False
        
    def get_messages(self, user_id):
        ret_map = {}
        noticifation_map = self.collection.find_one({"_id": int(user_id)})
        if noticifation_map:
            self.collection.remove({"_id": int(user_id)})
            ret_map['messages'] = noticifation_map['messages']
            ret_map['messages_num'] = noticifation_map['message_num']
        else:
            ret_map['messages'] = []
            ret_map['messages_num'] = 0
        return ret_map

    def get_message_count(self, user_id):
        total_num = 0
        try:
            ret_data = self.collection.find_one({"_id": int(user_id)}, fields = ['message_num'])
            if not ret_data:
                return 0
            total_num = ret_data.get('message_num', 0)
        except Exception,e:
            print e
        return total_num
        
if __name__ == '__main__':
    shop = ShopLocation()
    print shop.find_shops_by_category_brand(0, 350, 10)