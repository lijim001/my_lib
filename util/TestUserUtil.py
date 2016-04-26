#coding=utf-8

import urllib,os,time,random,uuid,hashlib

if __name__ == '__main__':
    import os,sys
    G_PATH = os.path.split(os.path.realpath(__file__))[0]
    sys.path.append(G_PATH + '/../../')
    os.environ['DJANGO_SETTINGS_MODULE'] = 'MobileService.settings'

from django.conf import settings
from MobileService.util.DbUtil import *

class DbTestUser(DbUtil):
    def __init__(self, database, logger=None):
        DbUtil.__init__(self, database, logger)

    def format_test_user_info(self, result):
        ret_dict = {}
        if not result:
            return ret_dict
        ret_dict['name'] = result[0]
        ret_dict['telephone'] = result[1]
        ret_dict['client'] = result[2]
        ret_dict['businness'] = result[3]
        return ret_dict
        
    def get_test_user_info(self, phone):
        sql = 'select name,telephone, client,businness from test_user where telephone="%s"'%(str(phone))
        self.get_db_connect()
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                result = self.cursor.fetchone()
                self.release_db_connect()
                return self.format_test_user_info(result)
            else:
                self.release_db_connect()
                return {}
        except Exception,e:
            if self.logger:
                self.logger.error('get_test_user_info except %s'%(e))         
            self.release_db_connect()
            return {}
    
    def has_company_user(self, phone_list):
        phone_list = [ str(i) for i in phone_list ]
        sql = 'select telephone from company_user where telephone in (%s)'%(','.join(phone_list))
        self.get_db_connect()
        try:
            count = self.cursor.execute(sql)
            self.release_db_connect()
            if count > 0:
                return True
            else:
                return False
        except Exception,e:
            if self.logger:
                self.logger.error('has_company_user except %s'%(e))         
            self.release_db_connect()
            return False
            
    def add_test_user(self, name, telephone, client, businness):
        sql = 'insert into test_user (name, telephone, client, businness) values ("%s","%s",%s,%s)' \
        %(name, str(telephone), str(client), str(businness))
        print telephone
        self.get_db_connect()
        try:
            count = self.cursor.execute(sql)
            self.conn.commit()
            self.release_db_connect()
            return True
        except Exception,e:
            if self.logger:
                self.logger.error('add_test_user except %s'%(e))
            self.release_db_connect()
            return False 

    def update_test_user(self, id, name, telephone, client, businness):
        self.get_db_connect()
        try:
            if name:
                sql = 'update test_user set name="%s" where id=%s'%(name, str(id))
                count = self.cursor.execute(sql)
            if telephone:
                sql = 'update test_user set telephone="%s" where id=%s'%(str(telephone), str(id))
                count = self.cursor.execute(sql)
            if client:
                sql = 'update test_user set client=%s where id=%s'%(str(client), str(id))
                count = self.cursor.execute(sql)
            if businness:
                sql = 'update test_user set businness=%s where id=%s'%(str(businness), str(id))
                count = self.cursor.execute(sql)
                
            self.conn.commit()
            self.release_db_connect()
            return True
        except Exception,e:
            if self.logger:
                self.logger.error('update_test_user except %s'%(e))
            self.release_db_connect()
            return False 

    def delete_test_user(self, id):
        self.get_db_connect()
        try:
            sql = 'delete from test_user where id=' + str(id)
            count = self.cursor.execute(sql)
                
            self.conn.commit()
            self.release_db_connect()
            return True
        except Exception,e:
            if self.logger:
                self.logger.error('delete_test_user except %s'%(e))
            self.release_db_connect()
            return False 
            
    def get_test_user_list(self, type = 0):
        if type == 0:
            sql = 'select name,telephone, client,businness from test_user'
        elif type == 1:
            sql = 'select name,telephone, client,businness from test_user where client=1'
        elif type == 2:
            sql = 'select name,telephone, client,businness from test_user where businness=1'
        else:
            return []
        self.get_db_connect()
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                self.cursor.scroll(0, mode='absolute')
                results = self.cursor.fetchall()
                self.release_db_connect()
                ret_list = []
                for result in results:
                    ret_list.append(self.format_test_user_info(result))
                return ret_list
            else:
                self.release_db_connect()
                return []
        except Exception,e:
            if self.logger:
                self.logger.error('get_test_user_list except %s'%(e))         
            self.release_db_connect()
            return []
        
class TestUserUtil():
    def __init__(self,database):
        self.mobile_db = database['mobile_db']
        self.shop_db = database['shop_db']
        self.info_logger = database['mobile_logger']
        self.database = database
    
    def is_client_test_user(self, phone):
        handler = DbTestUser(self.mobile_db, self.info_logger)
        test_user_info = handler.get_test_user_info(phone)
        if not test_user_info:
            return False
        return int(test_user_info['client']) == 1
    
    def is_business_test_user(self, phone):
        handler = DbTestUser(self.mobile_db, self.info_logger)
        test_user_info = handler.get_test_user_info(phone)
        if not test_user_info:
            return False
        return int(test_user_info['businness']) == 1
    
    def get_test_user_list(self, type = 0):
        handler = DbTestUser(self.mobile_db, self.info_logger)
        return handler.get_test_user_list(type)
        
    def add_test_user(self, name, telephone, client, businness):
        handler = DbTestUser(self.mobile_db, self.info_logger)
        return handler.add_test_user(name, telephone, client, businness)
        
    def update_test_user(self, id, name, telephone, client, businness):
        handler = DbTestUser(self.mobile_db, self.info_logger)
        return handler.update_test_user(id, name, telephone, client, businness)
        
    def delete_test_user(self, id):
        handler = DbTestUser(self.mobile_db, self.info_logger)
        return handler.delete_test_user(id)
        
    def has_company_user(self, phone_list):
        handler = DbTestUser(self.mobile_db, self.info_logger)
        return handler.has_company_user(phone_list)
        
        
if __name__ == '__main__':
    pass
