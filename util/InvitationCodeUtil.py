#coding=utf-8

import urllib,os,time,random,uuid,hashlib

if __name__ == '__main__':
    import os,sys
    G_PATH = os.path.split(os.path.realpath(__file__))[0]
    sys.path.append(G_PATH + '/../../')
    os.environ['DJANGO_SETTINGS_MODULE'] = 'MobileService.settings'

from django.conf import settings    
from MobileService.util.DbUtil import *

TRY_CREATE_TIMES = 15
MAX_INVITATION_CODE_USAGE_TIMES = 5
    
class InvitationCodeUtil():
    def __init__(self,database):
        self.mobile_db = database['mobile_db']
        self.shop_db = database['shop_db']
        self.info_logger = database['mobile_logger']
    
    def create_invitation_code(self, from_code = 0):
        handler = DbUtil(self.mobile_db, self.info_logger)
        if from_code:
            code_info = handler.get_invitation_by_code(from_code)
            if not code_info:
                return (None, from_code)
            # if int(code_info.get('type', 0)) == 1 and code_info.get('code_usage_times', 0) >= MAX_INVITATION_CODE_USAGE_TIMES:
                # self.info_logger.error('create_invitation_code failed reach max usage time %s'%(str(from_code)))
                # return (None, from_code)
        for i in range(TRY_CREATE_TIMES):
            new_code = hashlib.md5(str(uuid.uuid1())).hexdigest()[0:6]
            if handler.create_invitation_code(new_code, from_code):
                return (new_code, from_code)
        return (None, from_code)
    
    def get_info_by_from_code(self, from_code):
        handler = DbUtil(self.mobile_db, self.info_logger)
        return handler.get_invitation_by_from_code(from_code)

    def get_info_by_code(self, code):
        handler = DbUtil(self.mobile_db, self.info_logger)
        return handler.get_invitation_by_code(code)
        
    def get_info_from_phone(self, sales_phone):
        handler = DbUtil(self.mobile_db, self.info_logger)
        return handler.get_invitation_from_phone(sales_phone)
        
    def get_relate_info_by_code(self, code):
        pass
        
    def create_top_invitation_code(self):
        handler = DbUtil(self.shop_db, self.info_logger)
        mobile_handler = DbUtil(self.mobile_db, self.info_logger)
        channel_id_list = handler.get_all_channels()
        for channel_id in channel_id_list:
            (code, from_code) = mobile_handler.get_invitation_by_channel_id(channel_id)
            if code:
                continue
            (code, from_code) = self.create_invitation_code()
            channel_name = handler.get_channel_name_by_id(channel_id)
            #print channel_name
            mobile_handler.add_invitation_tops(code, channel_id, channel_name)
            time.sleep(1)

    def update_invitation(self, code, channel_id, channel_name):
        mobile_handler = DbUtil(self.mobile_db, self.info_logger)
        return mobile_handler.update_invitation(code, channel_id, channel_name)

        
    def create_private_invitation_code(self, channel_id, channel_name):
        (code, from_code) = self.create_invitation_code()
        if code:
            return self.update_invitation(code, channel_id, channel_name)
        else:
            self.info_logger.error('create_private_invitation_code failed.')
            return False
    
    def update_top_invitation_code(self):
        handler = DbUtil(self.shop_db, self.info_logger)
        mobile_handler = DbUtil(self.mobile_db, self.info_logger)
        channel_id_list = handler.get_all_channels()
        for channel_id in channel_id_list:
        
            (code, from_code) = mobile_handler.get_invitation_by_channel_id(channel_id)
            if int(from_code) != 0:
                continue

            channel_name = handler.get_channel_name_by_id(channel_id)
            print channel_id
            print channel_name.encode('utf8', 'ignore')
            mobile_handler.add_invitation_tops(code, channel_id, channel_name)
        
if __name__ == '__main__':
    handler = InvitationCodeUtil(settings.COMMON_DATA)
    handler.create_top_invitation_code()
    # tmp = 0
    # handler.create_private_invitation_code(10021, 'xwa019')
    # handler.create_private_invitation_code(10022, 'xwa020')
    # sys.exit(1) 
    # for i in range(10021,10023):
        # channel_id = i
        # tmp += 1
        # if tmp < 10:
            # prefix = 'xwa00'
        # else:
            # prefix = 'xwa0'
        # channel_name = prefix + str(tmp)
        # print channel_id
        # print channel_name
        # handler.create_private_invitation_code(channel_id, channel_name)
