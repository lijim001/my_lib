#coding=utf-8

import random

if __name__ == '__main__':
    import os,sys
    G_PATH = os.path.split(os.path.realpath(__file__))[0]
    sys.path.append(G_PATH + '/../../')
    os.environ['DJANGO_SETTINGS_MODULE'] = 'MobileService.settings'
    from django.conf import settings
    
from MobileService.util.RedisUtil import MyRedis
from MobileService.util.HttpUtil import *
from MobileService.util.note_send import *
from MobileService.voice_notify.VoiceVerify import *
from MobileService.voice_notify.SendTemplateSMS import *

MIN_PIN_CODE = 1001
MAX_PIN_CODE = 9999

EXPIRE_PIN_CODE_TIME = 60 * 5
EXPIRE_TEST_PIN_CODE_TIME = 60 * 60 * 24
EXPIRE_MAX_TRY_TIMES = 3600 * 24

TPC_USER_REGISTER = 0
TPC_USER_CHANGE_LOGIN_PASSWD = 1
TPC_USER_WALLET_PASSWD = 2
TPC_USER_CHANGE_WALLET_PASSWD = 3
TPC_USER_FORGET_LOGIN_PASSWD = 4
TPC_USER_FORGET_WALLET_PASSWD = 5
TPC_USER_PROMOTE = 6
TPC_USER_LOGIN_REGISTER = 7

TPC_BUSSINESS_USER_REGISTER = 10
TPC_BUSSINESS_USER_FORGET_PASSWD = 11
TPC_BUSSINESS_USER_SET_INFO = 12
TPC_BUSSINESS_USER_LOGIN_REGISTER = 13

MAX_USER_PIN_CODE_TIMES_PREFIX = 'pin_code_use_times_'

PIN_CODE_PREFIX_DICT = {
        TPC_USER_REGISTER : 'pin_code_user_register_',
        TPC_USER_CHANGE_LOGIN_PASSWD : 'pin_code_user_c_login_p_',
        TPC_USER_FORGET_LOGIN_PASSWD : 'pin_code_user_f_login_p_',
        TPC_USER_WALLET_PASSWD : 'pin_code_s_wallet_p_',
        TPC_USER_CHANGE_WALLET_PASSWD : 'pin_code_c_wallet_p_',
        TPC_USER_FORGET_WALLET_PASSWD : 'pin_code_f_wallet_p_',
        TPC_USER_PROMOTE: 'pin_code_promote_',
        TPC_USER_LOGIN_REGISTER: 'pin_code_login_register_',
        
        TPC_BUSSINESS_USER_REGISTER: 'pin_code_b_user_register_',
        TPC_BUSSINESS_USER_FORGET_PASSWD: 'pin_code_b_user_f_login_p_',
        TPC_BUSSINESS_USER_SET_INFO: 'pin_code_b_user_s_info_',
        TPC_BUSSINESS_USER_LOGIN_REGISTER: 'pin_code_b_user_login_register_',
    }

class PinCodeManage():
    def __init__(self, database):
        self.redis = database['cache_redis']
        self.info_logger = database['mobile_logger']
        self.environment = database['environment']

    def create_pin_code(self):
        return random.randint(MIN_PIN_CODE, MAX_PIN_CODE)
        
    def save_pin_code(self, type, phone_number, pin_code):
        prefix = PIN_CODE_PREFIX_DICT.get(type, '')
        if not prefix:
            return None
        key = prefix + str(phone_number)
        if self.environment == 'test':
            return self.redis.save_expire(key, EXPIRE_PIN_CODE_TIME, pin_code)
        else:
            return self.redis.save_expire(key, EXPIRE_PIN_CODE_TIME, pin_code)
    
    def check_max_times_per_day(self, phone_number):
        key = MAX_USER_PIN_CODE_TIMES_PREFIX + str(phone_number)
        if not self.redis.exists(key):
            self.redis.save_expire(key, EXPIRE_MAX_TRY_TIMES, 1)
            return True
        else:
            current_times = self.redis.incr(key)
            if current_times >= 50:
                return False
            else:
                return True
    
    def get_pin_code(self, type, phone_number):
        prefix = PIN_CODE_PREFIX_DICT.get(type, '')
        if not prefix:
            return None        
        key = prefix + str(phone_number)
        r_pin_code = self.redis.get(key)
        if not r_pin_code:
            pin_code = self.create_pin_code()
            self.save_pin_code(type, phone_number, pin_code)
            return pin_code
        else:
            return r_pin_code
        
    def check_pin_code(self, type, phone_number, pin_code):
        prefix = PIN_CODE_PREFIX_DICT.get(type, '')
        if not prefix:
            return False        
        key = prefix + str(phone_number)
        r_pin_code = self.redis.get(key)
        if not r_pin_code:
            print 'redis no key'
            return False
        else:
            if str(r_pin_code) == str(pin_code):
                print 'redis check pin code ok'
                return True
            else:
                print 'redis get pin code %s'%(str(r_pin_code))
                print 'user pin code %s'%(str(pin_code))
                return False
        
    def send_pin_code_to_phone_old(self, phone_number, pin_code):
        message = '验证码为：%s。请在客户端输入以完成验证。有问题请致电400-890-0988'%(str(pin_code))
        url = 'http://shop.xinwo.com/index.php?module=api&action=ytx&fn=send&fr=mxinwo&mobile=%s&message='%(str(phone_number))
        url = url + message
        OpenUrl(url)
        
    def send_pin_code_to_phone(self, phone_number, pin_code):
        message = '动态密码：%s。有问题请致电400-890-0988'%(str(pin_code))    
        handler = YiMeiUtil('9SDK-EMY-0999-JBXMR', 'b4bb2d221a2d9cf55fa7e2904cd648ee', logger = self.info_logger)
        #handler.send_message(phone_number, message)
        
        sendTemplateSMS(phone_number, [str(pin_code)], 22879)
        
    def send_voice_pin_code_to_phone(self, phone_number, pin_code):
        voiceVerify(pin_code, 3, phone_number, '4008900988', '')

if __name__ == '__main__':
    manager =PinCodeManage(settings.COMMON_DATA)
    manager.send_pin_code_to_phone('13811678953', 123456)
