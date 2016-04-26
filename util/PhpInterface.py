#coding=utf-8
import os, sys
import hashlib
import simplejson as json
G_PATH = os.path.split(os.path.realpath(__file__))[0]
sys.path.append(G_PATH + '/../../')

from MobileService.util.HttpUtil import *
from django.conf import settings

common_logger = settings.COMMON_DATA['mobile_logger']

USER_PIN = '4be31371a1b6c155d98d698f254061f2'
ENTRY = 'client'
API_IP = '127.0.0.1'
BAO_PAY_PIN = 'fb54f3c5992b96d001bb16e8e92d968d';
BAO_PAY_APPID = 'shop';

class PhpInterface():
    def get_token(self, input_hash, pin):
        return hashlib.md5(input_hash + pin).hexdigest()
        
    def do_register(self, user_name, passwd):
        url = 'http://i.passport.xinwo.com/inner/reg'
        input_hash = str(user_name) + ':' + str(passwd) + ':' + API_IP
        mid_hash = hashlib.md5(input_hash).hexdigest()
        token = self.get_token(mid_hash, USER_PIN)
        params = {}
        params['name'] = str(user_name)
        params['pwd'] = str(passwd)
        params['uip'] = API_IP
        params['mobile'] = str(user_name)
        params['entry'] = ENTRY
        params['token'] = token
        print params
        result = PostUrl(url, params)
        if not result:
            print 'no data'
            return None
        ret_dict = json.loads(result)
        print ret_dict
        if ret_dict['errno'] == 0:
            return ret_dict['data']['userid']
        else:
            return None
                
    def pay_using_wallet(self, user_id, money, paypasswd, order_number, shop_name, content, coupon=0):
        url = 'http://i.q.xinwo.com/cost/pay'
        input_hash = str(user_id) + ':' + API_IP + ':' + str(order_number) 
        mid_hash = hashlib.md5(input_hash).hexdigest()
        token = self.get_token(mid_hash, BAO_PAY_PIN)
        params = {}
        params['appid'] = str(BAO_PAY_APPID)
        params['user_id'] = str(user_id)
        params['uip'] = API_IP
        params['orderno'] = str(order_number)
        params['money'] = str(money)
        params['token'] = token
        params['paypwd'] = hashlib.md5(paypasswd).hexdigest()
        params['seller'] = shop_name
        params['content'] = content
        params['coupon'] = coupon
        print params
        result = PostUrl(url, params)
        common_logger.info('pay_using_wallet %s'%(str(result)))
        if not result:
            print 'no data'
            return (False, None)
        ret_dict = json.loads(result)
        print ret_dict
        if ret_dict['code'] == 0:
            return (True, 0)
        else:
            return (False, ret_dict['code'])    

if __name__ == '__main__':
    test = PhpInterface()
    test.pay_using_wallet(63037, 0.01, '820316@life', '1413775220630370001','闽龙陶瓷', '移动端测试支付')
    