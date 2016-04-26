#coding=utf-8

import urllib,os,time,random,uuid,hashlib

if __name__ == '__main__':
    import os,sys
    G_PATH = os.path.split(os.path.realpath(__file__))[0]
    sys.path.append(G_PATH + '/../../')
    os.environ['DJANGO_SETTINGS_MODULE'] = 'MobileService.settings'

from django.conf import settings    
from MobileService.util.DbUtil import *

ACTION_CREATE_SESSION = "create_session"
ACTION_TALK = "talk"

class DbRecordInquire(DbUtil):
    def __init__(self, database, logger=None):
        DbUtil.__init__(self, database, logger)
        
    def add_session_info(self, from_phone, category, content, platform='android', session_id=0):
        self.get_db_connect()
        try:
            sql = 'insert into user_inquire_record (source_phone, app, action, category, content, platform,session_id) values ("%s", "wallet_client", "%s", "%s","%s","%s",%s)' \
            %(str(from_phone), ACTION_CREATE_SESSION, category, content, platform, str(session_id))        
            count = self.cursor.execute(sql)
            self.conn.commit()
            self.release_db_connect()
            return True
        except Exception,e:
            if self.logger:
                self.logger.error('add_session_info except %s'%(e))
            self.release_db_connect()    
            return False

    def add_talk_info(self, from_phone, to_phone, app, category, content, platform='android', session_id=0, goods_id=0):
        self.get_db_connect()
        try:
            sql = 'insert into user_inquire_record (source_phone, dest_phone, app, action, category, content, platform, session_id, goods_id) values ("%s", "%s", "%s", "%s", "%s","%s","%s",%s,%s)' \
            %(str(from_phone), str(to_phone), app, ACTION_TALK, category, content, platform, str(session_id), str(goods_id))
            count = self.cursor.execute(sql)
            self.conn.commit()
            self.release_db_connect()
            return True
        except Exception,e:
            if self.logger:
                self.logger.error('add_talk_info except %s'%(e))
            self.release_db_connect()    
            return False
            
class RecordInquireUtil():
    def __init__(self, database):
        self.mobile_db = database['mobile_db']
        self.log_db = database['log_db']
        self.info_logger = database['mobile_logger']
        self.database = database
    
    def record_create_session(self, from_phone, category, content, platform='android', session_id=0):
        handler = DbRecordInquire(self.log_db, self.info_logger)
        handler.add_session_info(from_phone, category, content, platform, session_id)
        
    def record_talk_info(self, from_phone, to_phone, app, category, content, platform='android', session_id=0, goods_id=0):
        handler = DbRecordInquire(self.log_db, self.info_logger)
        handler.add_talk_info(from_phone, to_phone, app, category, content, platform, session_id, goods_id)
        
if __name__ == '__main__':
    handler = RecordInquireUtil(settings.COMMON_DATA)
    #handler.record_user_consume('13811678953', 2500)
    handler.record_create_session('13811678953', '马桶', '马桶多少钱')
    handler.record_talk_info('13811678954', '13811678953', 'wallet_client', '马桶', '马桶100')