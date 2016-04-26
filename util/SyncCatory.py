#coding=utf-8

import urllib,os,time,random,uuid,hashlib

if __name__ == '__main__':
    import os,sys
    G_PATH = os.path.split(os.path.realpath(__file__))[0]
    sys.path.append(G_PATH + '/../../')
    os.environ['DJANGO_SETTINGS_MODULE'] = 'MobileService.settings'

from django.conf import settings    
from MobileService.util.DbUtil import DbUtil

class DbSyncCategory(DbUtil):
    def __init__(self, database, logger=None):
        DbUtil.__init__(self, database, logger)
    
    def SyncCategory(self, category_name, brand_name_list):
        cont = ''
        for brand_name in brand_name_list:
            cont += '("' + category_name + '","' + brand_name + '"),'
        sql = 'insert into brand_info (category_name,brand_name) values ' + cont[:-1]

        self.get_db_connect()
        try:
            count = self.cursor.execute(sql)
            self.conn.commit()
            self.release_db_connect()
            return True
        except Exception,e:
            if self.logger:
                self.logger.error('SyncCategory except %s'%(e))
            self.release_db_connect()    
            return False        

    def SyncOneCategory(self, category_name, brand_name):
        if not category_name or not brand_name:
            print 'empty'
            return False
        category_name = category_name.strip()
        brand_name = brand_name.strip()
        sql = 'insert into brand_info (category_name,brand_name) values ("%s", "%s")'%(category_name, brand_name)

        self.get_db_connect()
        try:
            count = self.cursor.execute(sql)
            self.conn.commit()
            self.release_db_connect()
            return True
        except Exception,e:
            if self.logger:
                self.logger.error('SyncOneCategory except %s'%(e))
            self.release_db_connect()    
            return False
            
    def get_category_title_brand_id(self, brand_id):
        sql = 'select sss.title from sort s inner join sort ss inner join sort sss inner join brand_sort bs where s.id in (select sort_id from brand_sort where brand_id=%s) and s.parentid=ss.id and ss.parentid=sss.id group by sss.title'%(str(brand_id))
        self.get_db_connect()
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                result = self.cursor.fetchone()
                self.release_db_connect()
                return result[0]
            else:
                self.release_db_connect()
                return None
        except Exception,e:
            if self.logger:
                self.logger.error('get_category_title_brand_id except %s'%(e))
            self.release_db_connect()
            return None
                
class SyncCategoryUtil():
    def __init__(self,database):
        self.mobile_db = database['mobile_db']
        self.shop_db = database['shop_db']
        self.info_logger = database['mobile_logger']
    
    def do(self, file):
        fp = open(file)
        line = fp.readline()
        handler = DbSyncCategory(self.mobile_db, self.info_logger)
        while line:
            data_list = line.split('\t')
            if len(data_list) != 2:
                print line
                line = fp.readline()
                continue
            category_name = data_list[0]
            brand_names = data_list[1]
            brand_list = brand_names.split(',')
            for brand in brand_list:
                handler.SyncOneCategory(category_name, brand)
            line = fp.readline()
    def do_category(self, file):
        fp = open(file)
        line = fp.readline()
        handler = DbSyncCategory(self.shop_db, self.info_logger)
        while line:
            data_list = line.split('|')
            #print data_list
            channel_id = data_list[1].strip()
            brand_id =  data_list[2].strip()
            name = data_list[3].strip()
            phone = data_list[4].strip()
            brand_name = data_list[5].strip()
            shop_name = data_list[6].strip()
            category_name = handler.get_category_title_brand_id(brand_id)
            if not category_name:
                category_name = u'无'
            if channel_id != '0':
                stype = u'合作'
            else:
                stype = u'非合作'
            #print category_name.encode('utf8','ignore')
            #print name
            print '%s|%s|%s|%s|%s|%s|%s|%s'%(category_name.encode('utf8','ignore'), stype.encode('utf8','ignore'), str(channel_id), str(brand_id), name, str(phone), brand_name, shop_name)
            line = fp.readline()
            
if __name__ == '__main__':
    handler = SyncCategoryUtil(settings.COMMON_DATA)
    #handler.do('/root/brand.txt')
    handler.do_category('/root/33.txt')
