#coding=utf-8

import urllib,os,time,random,uuid,hashlib

if __name__ == '__main__':
    import os,sys
    G_PATH = os.path.split(os.path.realpath(__file__))[0]
    sys.path.append(G_PATH + '/../../')
    os.environ['DJANGO_SETTINGS_MODULE'] = 'MobileService.settings'

from django.conf import settings    
from MobileService.util.DbUtil import *
from MobileService.util.TestUserUtil import TestUserUtil
from MobileService.message.util_message import *
from MobileService.util.note_send import *

AWARD_CONSUME_MONEY = 2000
TEST_AWARD_CONSUME_MONEY = 0.1
    
class ConsumeUtil():
    def __init__(self,database):
        self.mobile_db = database['mobile_db']
        self.shop_db = database['shop_db']
        self.info_logger = database['mobile_logger']
        self.database = database
        self.gearman_config = database['gearman_config']
        self.environment = database['environment']
    
    def send_award_message(self, user_phone, sales_phone, type, money, consume_money):
        handler = DbUtil(self.mobile_db, self.info_logger)
        handler_message = MessageUtil(self.database)
        title = '奖励通知：'
        if sales_phone:
            user_info = handler.get_userinfo_by_user_name(sales_phone)
            if user_info:
                user_id = user_info[0]
                #content = '您获得了200元返现金额，可到奖励金额中申请取现'
                #handler_message.send_user_messsage(user_id, title, content)
                handler_push = GearmanUtil(self.gearman_config)
                handler_push.send_award_user_message(sales_phone, user_phone, type, money, consume_money)
                note_handler = NoteSendUtil(self.database)
                note_handler.send_order_payed(sales_phone, user_phone)

    def get_reward_config_time(self):
        if self.environment == 'normal':
            ###2015.4.29
            return 1430236800
        else:
            ###2015.4.27
            return 1430064000

    def record_user_consume(self, user_phone, money):
        return False
        handler = DbUtil(self.mobile_db, self.info_logger)
        consume_info = handler.get_user_consume_info(user_phone)
        if not consume_info:
            self.info_logger.info('record_user_consume not found user_phone %s'%(str(user_phone)))
            return False
        elif consume_info.get('create_time', 1430409600) > self.get_reward_config_time():
            return False
        old_consume_money = consume_info.get('consume_money', 0)
        new_consume_money = handler.update_user_consume(user_phone, money)
        ####cancel reward function
        #return True
        reward_2000 = consume_info.get('reward_2000', 'undo')
        if reward_2000 == 'do':
            self.info_logger.info('record_user_consume has consume 2000 user_phone %s'%(str(user_phone)))
            return False
        test_user_handler = TestUserUtil(self.database)
        reward_money = AWARD_CONSUME_MONEY
        if test_user_handler.is_client_test_user(user_phone):
            #reward_money = TEST_AWARD_CONSUME_MONEY
            reward_money = AWARD_CONSUME_MONEY
            self.info_logger.info('record_user_consume %s test user get 200 money'%(str(user_phone)))
        sales_phone = consume_info.get('sales_phone', '')
        commision_info = handler.get_commision_info_by_user_type(user_phone, sales_phone, 0)
        if not commision_info:
            return False
        last_reward_money = commision_info[2]
        check_money = str(int(commision_info[2]))
        if new_consume_money > 0 and new_consume_money < reward_money and check_money != '50' and check_money != '10':
            reward_type = '6' + datetime.now().strftime('%H%M%S')
            re_money = int(money * 10 / float(100))
            handler.add_order_payed_commision_info(user_phone, sales_phone, re_money, reward_type)
            self.send_award_message(user_phone, sales_phone, 6, re_money, money)

        if new_consume_money >= reward_money:
            if reward_money > old_consume_money and old_consume_money and check_money != '50' and check_money != '10':
                cons_money = float(reward_money) - float(old_consume_money)
                re_money = int(cons_money * 10 / float(100))
                reward_type = '6' + datetime.now().strftime('%H%M%S')
                handler.add_order_payed_commision_info(user_phone, sales_phone, re_money, reward_type)
                handler.verify_commision_info(user_phone, sales_phone, 0, 0)
                self.send_award_message(user_phone, sales_phone, 7, re_money, cons_money)

            else:
                self.info_logger.info('record_user_consume %s user consume 2000 first'%(str(user_phone)))
                need_send_message = True
            
                ##current policy reward 200
                if last_reward_money > 199:
                    handler.verify_commision_info(user_phone, sales_phone, 0, 1)
                ##first policy reward 50 + 150
                elif last_reward_money > 49:
                    settle_mode, settle_account = handler.get_settle_mode_account(sales_phone)
                    handler.record_user_commision(user_phone, sales_phone, 150, settle_mode, settle_account)
                ##middle policy reward 10 + 200
                elif last_reward_money > 9:
                    settle_mode, settle_account = handler.get_settle_mode_account(sales_phone)
                    handler.record_user_commision(user_phone, sales_phone, 200, settle_mode, settle_account)
                else:
                    need_send_message = False
                if need_send_message:
                    self.send_award_message(user_phone, sales_phone, type=1, money=200, consume_money=0)

        
if __name__ == '__main__':
    handler = ConsumeUtil(settings.COMMON_DATA)
    handler.record_user_consume('13600001111', 500)
    #handler.send_award_message('13811678953', '13811678953', '')
