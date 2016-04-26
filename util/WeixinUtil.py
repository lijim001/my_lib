#coding=utf-8

import urllib,os,sys,time,hashlib,urllib,re,random
import simplejson as json
from xml.etree import ElementTree

if __name__ == '__main__':
    import os,sys
    G_PATH = os.path.split(os.path.realpath(__file__))[0]
    sys.path.append(G_PATH + '/../../')
    os.environ['DJANGO_SETTINGS_MODULE'] = 'MobileService.settings'

from django.conf import settings
from MobileService.util.HttpUtil import *
from MobileService.util.RedisUtil import MyRedis

TOKEN_GET_URL_PREFIX = 'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential'
PRE_PAY_ORDER_PREFIX = 'https://api.weixin.qq.com/pay/genprepay?access_token='
WEIXIN_TOKEN_REDIS_KEY = 'weixin_access_token'
EXPIRE_WEIXIN_TOKEN = 5400

XML_TXT = '''
<xml>
<OpenId><![CDATA[oUpF8uN95-Ptaags6E_roPHg7AG0]]></OpenId>
<AppId><![CDATA[wx2421b1c4370ec43b]]></AppId>
<IsSubscribe>1</IsSubscribe>
<TimeStamp>1398835924</TimeStamp>
<NonceStr><![CDATA[1n0TsqoVMnCSkjyS]]></NonceStr>
<AppSignature><![CDATA[3b00e45a02018dd25bc1ef7a2b4101cba435cbab]]></AppSignature>
<SignMethod><![CDATA[sha1]]></SignMethod>
</xml>
'''
class WeixinUtil():
    def __init__(self, database):
        weixin_config = database['weixin_config']
        self.info_logger = database['mobile_logger']
        self.app_key = weixin_config[0]
        self.app_secret = weixin_config[1]
        self.partnerid = weixin_config[2]
        self.partnerkey = weixin_config[3]
        #self.trace_id = weixin_config[4]
        self.trace_id = ''.join(random.sample('abcdefghijklmnopqrstuvwxyz1234567890',10))
        self.paysignkey = weixin_config[5]
        self.redis = database['cache_redis']
        self.get_token()

    def unicode_encode(self, str):
        """
        Detect if a string is unicode and encode as utf-8 if necessary
        """
        return isinstance(str, unicode) and str.encode('utf-8') or str

    def sort_params(self, params = None):
        return "&".join(["%s=%s" % (self.unicode_encode(x), self.unicode_encode(params[x])) for x in sorted(params.keys())])
    
    def make_package_material(self, params = None, need_key = True):
        if need_key:
            return self.sort_params(params) + '&key=' + self.partnerkey
        else:
            return self.sort_params(params)
        
    def hash_params(self, params = None):
        str_hash_input = self.make_package_material(params)
        print 'str_hash_input %s'%(str_hash_input)
        hasher = hashlib.md5(str_hash_input).hexdigest().upper()
        return hasher
        
    def make_package(self, params):
        hasher = self.hash_params(params)
        packet_dict = self.my_url_encode(params)
        #packet_dict = params
        return (self.make_package_material(packet_dict, False) + '&sign=' + hasher, hasher)
    
    def make_app_signature(self, params):
        return hashlib.sha1(self.sort_params(params)).hexdigest()
    
    def save_redis_token(self):
        if self.redis:
            self.redis.save_expire(WEIXIN_TOKEN_REDIS_KEY, EXPIRE_WEIXIN_TOKEN, self.access_token)
    
    def get_redis_token(self):
        if self.redis:
            return self.redis.get(WEIXIN_TOKEN_REDIS_KEY)
        else:
            return None
            
    def clear_redis_token(self):
        if self.redis:
            return self.redis.delete(WEIXIN_TOKEN_REDIS_KEY)
        else:
            return None
            
    def get_token(self):
        self.access_token = self.get_redis_token()
        if self.access_token:
            return True
        url = TOKEN_GET_URL_PREFIX + '&appid=' + self.app_key + '&secret=' + self.app_secret
        for i in range(3):
            ret_data = OpenUrl(url)
            if not ret_data:
                continue
            else:
                ret_dict = json.loads(ret_data)
                print ret_dict
                if ret_dict.has_key('errcode'):
                    continue
                self.access_token = ret_dict.get('access_token', None)
                self.expires = ret_dict.get('expires_in', None)
                self.save_redis_token()
                return True
        return False
    
    def my_url_encode(self, input_dict):
        ret_dict = {}
        attach = ''
        # if input_dict.has_key('attach'):
            # attach = input_dict['attach']
            # del input_dict['attach']
        params = urllib.urlencode(input_dict)
        items_list = params.split('&')
        for item in items_list:
            sub_item = item.split('=')
            ret_dict[sub_item[0]] = sub_item[1]
        # if attach:
            # ret_dict['attach'] = attach
        print '====='
        print ret_dict
        return ret_dict
        
    def create_pre_pay_order(self, noncestr, body, order_number, money, clientip, timestamp, notify_url='http://mobile.xinwo.com/weixin/pay_notify/'):
        packet_dict = {}
        packet_dict['bank_type'] = 'WX'
        packet_dict['body'] = body
        packet_dict['fee_type'] = '1'
        packet_dict['input_charset'] = 'UTF-8'
        packet_dict['partner'] = str(self.partnerid)
        packet_dict['notify_url'] = notify_url
        packet_dict['out_trade_no'] = order_number
        packet_dict['spbill_create_ip'] = clientip
        packet_dict['total_fee'] = str(int(money * 100))
        #packet_dict['body'] = 'line_type=off&goods_type=phy&goods_class=02&deliver=unlog&seller_type=mer'
        packet_dict['desc'] = 'line_type=off&goods_type=phy&goods_class=02&deliver=unlog&seller_type=mer'

        (packet,sign) = self.make_package(packet_dict)
        print 'packet is %s'%(packet)
        print sign
        signature_dict = {}
        signature_dict['appid'] = self.app_key
        signature_dict['appkey'] = self.paysignkey
        signature_dict['traceid'] = self.trace_id
        signature_dict['noncestr'] = noncestr
        signature_dict['timestamp'] = timestamp
        signature_dict['package'] = packet
        
        
        app_signature = self.make_app_signature(signature_dict)
        
        ret_dict = {}

        ret_dict['appid'] = self.app_key
        ret_dict['traceid'] = self.trace_id
        ret_dict['noncestr'] = noncestr
        ret_dict['timestamp'] = timestamp
        ret_dict['app_signature'] = app_signature        
        ret_dict['package'] = packet        
        ret_dict['sign_method'] = 'sha1'

        post_url = PRE_PAY_ORDER_PREFIX + self.access_token
        ret_data = PostUrlStringData(post_url, json.dumps(ret_dict))
        print 'weixin back data:'
        print ret_data
        if not ret_data:
            return None
        ret_dict = json.loads(ret_data)
        errorcode = int(ret_dict.get('errcode', 0))
        if errorcode != 0:
            if errorcode == 40001:
                self.clear_redis_token()
            return None
        prepayid = ret_dict.get('prepayid')
        final_ret_dict = {}
        final_ret_dict['appid'] = self.app_key
        final_ret_dict['appkey'] = self.paysignkey
        final_ret_dict['noncestr'] = noncestr
        final_ret_dict['package'] = 'Sign=WXPay'
        final_ret_dict['partnerid'] = self.partnerid
        final_ret_dict['prepayid'] = prepayid
        final_ret_dict['timestamp'] = timestamp
        
        sign_new = self.make_app_signature(final_ret_dict)
        final_ret_dict['sign'] = sign_new
        print sign_new
        final_ret_dict['inner_sign'] = sign
        return final_ret_dict
        

    def parse_notify_body(self, xml):
        ret_dict = {}
        try:
            root = ElementTree.fromstring(xml)
            ret_dict['open_id'] = root.find('OpenId').text
            ret_dict['app_id'] = root.find('AppId').text
            ret_dict['is_subscribe'] = root.find('IsSubscribe').text
            ret_dict['timestamp'] = root.find('TimeStamp').text
            ret_dict['noncestr'] = root.find('NonceStr').text
            ret_dict['app_signature'] = root.find('AppSignature').text
            print ret_dict
        except Exception,e:
            self.info_logger.error('weixin parse_notify_body except %s'%(e))
        finally:
            return ret_dict
    
    def check_signature(self, ret_dict):
        packet_dict = {}
        packet_dict['bank_type'] = 'WX'
        packet_dict['body'] = body
        packet_dict['fee_type'] = 1
        packet_dict['input_charset'] = 'UTF-8'
        packet_dict['partner'] = self.partnerid
        packet_dict['notify_url'] = notify_url
        packet_dict['out_trade_no'] = order_number
        packet_dict['spbill_create_ip'] = clientip
        packet_dict['total_fee'] = money * 100        
    
    def check_notify_sign(self, params):
        self.info_logger.info('weixin check_notify_sign input %s'%(params))
        item_list = params.split('&')
        ret_dict = {}
        input_sign = ''
        for item in item_list:
            param = item.split('=')
            key = param[0]
            value = param[1]
            if key == 'sign':
                input_sign = value
                continue
            ret_dict[key] = value
        (packet,sign) = self.make_package(ret_dict)
        if sign == input_sign:
            return True
        else:
            return False
            
    def parser_notify(self, request):
        ret_dict = {}
        result = self.check_notify_sign(request.META['QUERY_STRING'])
        if not result:
            self.info_logger.error('weixin check_notify_sign failed')
            return None
        ret_dict['sign_type'] = request.REQUEST.get('sign_type', 'MD5')
        ret_dict['input_charset'] = request.REQUEST.get('input_charset', 'GBK')
        ret_dict['trade_mode'] = request.REQUEST.get('trade_mode', '')
        ret_dict['trade_state'] = request.REQUEST.get('trade_state', '')
        ret_dict['partner'] = request.REQUEST.get('partner', '')
        ret_dict['bank_type'] = request.REQUEST.get('bank_type', '')
        ret_dict['bank_billno'] = request.REQUEST.get('bank_billno', '')
        ret_dict['total_fee'] = request.REQUEST.get('total_fee', '')
        ret_dict['fee_type'] = request.REQUEST.get('fee_type', '')
        ret_dict['notify_id'] = request.REQUEST.get('notify_id', '')
        ret_dict['transaction_id'] = request.REQUEST.get('transaction_id', '')
        ret_dict['out_trade_no'] = request.REQUEST.get('out_trade_no', '')
        ret_dict['time_end'] = request.REQUEST.get('time_end', '')
        ret_dict['sign'] = request.REQUEST.get('sign', '')

        raw_data = request.raw_post_data
        ret_dict.update(self.parse_notify_body(raw_data))
        return ret_dict
        
if __name__ == '__main__':
    test_dict = {}
    test_dict['test1'] = 'ssdf'
    test_dict['set'] = 1
    test_dict['aaa'] = 'abd'
    manager = WeixinUtil(settings.COMMON_DATA)
    print manager.check_notify_sign('bank_type=0&discount=0&fee_type=1&input_charset=UTF-8&notify_id=qc6S7lFDlRcd4Be2OT7sLlPMu8nyNYaDFogu4J4BIUqsOFvqfwtHhrSp1uy47wtmAzyyL2ByPxWS1FpU8j6f2sQnLmgacKKR&out_trade_no=142579587570034907949518&partner=1223005701&product_fee=95&sign=D303CF49643A867B750E66F78AA0C5A0&sign_type=MD5&time_end=20150308142938&total_fee=95&trade_mode=1&trade_state=0&transaction_id=1223005701201503086014919706&transport_fee=0')
    print manager.parse_notify_body('<xml><OpenId><![CDATA[oWCIes8Ndw3tomDLOVxkO8xUxZEM]]></OpenId>\n<AppId><![CDATA[wxbc84001985db072c]]></AppId>\n<IsSubscribe>0</IsSubscribe>\n<TimeStamp>1425807239</TimeStamp>\n<NonceStr><![CDATA[XsUXh71IVwUeyJ2B]]></NonceStr>\n<AppSignature><![CDATA[1814af6e1b86bd2ec7f797652c47547084d7d57a]]></AppSignature>\n<SignMethod><![CDATA[sha1]]></SignMethod>\n</xml>')
    #noncestr = ''.join(random.sample('abcdefghijklmnopqrstuvwxyz1234567890',30))
    #print manager.create_pre_pay_order(noncestr, 'slkdjfsdfsdfs', '12312312312311', 0.2, '127.0.0.1', int(time.time()))
    #print manager.make_package(test_dict)
    
        
    