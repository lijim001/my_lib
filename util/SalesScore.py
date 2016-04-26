#coding=utf-8

import urllib,os,time,random,uuid,hashlib

if __name__ == '__main__':
    import os,sys
    G_PATH = os.path.split(os.path.realpath(__file__))[0]
    sys.path.append(G_PATH + '/../../')
    os.environ['DJANGO_SETTINGS_MODULE'] = 'MobileService.settings'

from django.conf import settings    
from MobileService.util.DbUtil import *

SCORE_TYPE_OPEN_PRIVILEGE = 1
SCORE_TYPE_UPLOAD_PORTRAIT = 2
SCORE_TYPE_VIEW_METHOD_ORDER = 3
SCORE_TYPE_VIEW_METHOD_INQUIRE = 4
SCORE_TYPE_OFFLINE_ORDER_SUCCESS = 5
SCORE_TYPE_ONLINE_FIRST_ORDER_SUCCESS = 6
SCORE_TYPE_ONLINE_OTHER_ORDER_SUCCESS = 7
SCORE_TYPE_CHEAT_ORDER = 8
SCORE_TYPE_ORDER_UNNORMAL = 9

SCORE_DICT = {
    SCORE_TYPE_OPEN_PRIVILEGE : [u'成为新窝店员', 10],
    SCORE_TYPE_UPLOAD_PORTRAIT : [u'上传个人工作照', 2],
    SCORE_TYPE_VIEW_METHOD_ORDER : [u'查看成单攻略', 2],
    SCORE_TYPE_VIEW_METHOD_INQUIRE : [u'查看比价攻略', 2],
    SCORE_TYPE_OFFLINE_ORDER_SUCCESS : [u'完成一笔门店收款', 10],
    SCORE_TYPE_ONLINE_FIRST_ORDER_SUCCESS : [u'首次完成线上收款', 30],
    SCORE_TYPE_ONLINE_OTHER_ORDER_SUCCESS : [u'完成一笔线上收款', 20],
    SCORE_TYPE_CHEAT_ORDER : [u'发生作弊订单', -30],
    SCORE_TYPE_ORDER_UNNORMAL : [u'发生不符合规定订单', -5],
}

class DbSalesScoreUtil(DbUtil):
    def __init__(self, database, logger=None):
        DbUtil.__init__(self, database, logger)
            
    def create_sales_score(self, sales_phone, score, type, content):
        self.get_db_connect()
        sql = 'insert into sales_score_info (sales_phone, score, type, content) values (%s,%s,%s,%s)'
        try:
            count = self.cursor.execute(sql, [sales_phone, score, type, content])
            new_id = self.cursor.lastrowid
            self.conn.commit()
            self.release_db_connect()
            return new_id
        except Exception,e:
            if self.logger:
                self.logger.error('create_sales_score except %s'%(e))
            self.release_db_connect()    
            return 0    
    
    def get_sales_score_list(self, sales_phone):
        self.get_db_connect()
        sql = 'select id, sales_phone,score,type,content from sales_score_info where sales_phone=%s'
        try:
            count = self.cursor.execute(sql, [str(sales_phone)])
            if count > 0:
                result = self.cursor.fetchone()
                self.release_db_connect()
                return result
            else:
                self.release_db_connect()
                return None
        except Exception, e:
            if self.logger:
                self.logger.error('get_sales_score_list except %s'%(e))
            self.release_db_connect()
            return None

class SalesScoreUtil():
    def __init__(self,database):
        self.mobile_db = database['mobile_db']
        self.shop_db = database['shop_db']
        self.user_db = database['user_db']
        self.info_logger = database['mobile_logger']
            
    def add_sales_score(self, sales_phone, type):
        handler = DbSalesScoreUtil(self.mobile_db, self.info_logger)
        score_info = SCORE_DICT.get(type)
        if not score_info:
            return False
        content = score_info[0]
        score = score_info[1]
        if handler.create_sales_score(sales_phone, score, type, content):
            return True
        else:
            return False
    
    
    
if __name__ == '__main__':
    handler = SalesScoreUtil(settings.COMMON_DATA)
    handler.add_sales_score('13811678953', 2)
    
