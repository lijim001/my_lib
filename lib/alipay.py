#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
支付宝
'''
import json
import urllib
import hashlib
import urllib2
import urlparse
import datetime
from lib.utils import rsa_sign_raw, rsa_verify_raw
from xml.etree import ElementTree


class AlipayClient(object):
    '''
    支付宝支付
    '''
    def __init__(self, conf):
        '''
        初始化配置
        @conf:{
            'partner':'合作者身份ID',
            'seller_id':'卖家支付宝账号',
            'notify_url':'服务器异步通知URL',
            'private':'我们的私钥',
            'ali_public':'支付宝的公钥',
        }
        '''
        self.conf = conf

    def create_mob_trade(self, out_trade_no, subject, total_fee, body):
        '''
        创建移动支付交易请求数据
        @out_trade_no: 交易号(在商户系统中唯一)
        @subject: 商品标题
        @total_fee: 商品价格, 单位: RMB－分
        @body: 商品描述
        return: 经过签名的移动支付请求参数
        '''
        param = {
            'service': 'mobile.securitypay.pay',
            '_input_charset': 'utf-8',
            'partner': self.conf['partner'],
            'notify_url': urllib.quote_plus(self.conf['notify_url']),
            'out_trade_no': out_trade_no,
            'subject': subject,
            'payment_type': '1',
            'seller_id': self.conf['seller_id'],
            'total_fee':float(total_fee)/100,
            'body':body,
        }
        temp, param_keys = '', param.keys()
        for k in param_keys:
            # 忽略没有值的参数
            if param[k] == '':
                continue
            # 这里的组织方式真蛋疼
            temp += '%s="%s"' % (k, param[k])
            if k != param_keys[-1]:
                temp += '&'
        sign = urllib.quote_plus(rsa_sign_raw(self.conf['private'], temp))
        return '%s&sign="%s"&sign_type="RSA"' % (temp, sign)

    def verify_notify_data(self, post_data):
        '''
        校验异步通知数据
        @post_data: 支付宝的通知POST原始数据
        return: 是否验证通过, 通知数据(DICT){
            'out_trade_no':'商户订单系统中的订单号',
            'trade_no':'该交易在支付宝系统中的交易流水号',
            'trade_status':'交易状态',
            'trade_id':'通知校验ID',
            'total_fee':'交易金额',
            'buyer_id':'买家支付宝用户号',
            'buyer_email':'买家支付宝账号',
            ...
        }
        '''
        raw, data = dict(urlparse.parse_qsl(post_data)), {}
        for k in raw:
            if k in ('sign', 'sign_type') or raw[k] == '':
                continue
            data[k] = raw[k]
        temp = '&'.join(['%s=%s' % (k, v) for k, v in sorted(data.items())])
        is_ok = rsa_verify_raw(self.conf['ali_public'], temp, raw['sign'])

        # 把元转化为分
        data['total_fee'] = int(float(data['total_fee']) * 100)

        return is_ok, data


class AlipayQRCodeClient(object):
    '''
    支付宝扫码支付
    '''
    def __init__(self, conf):
        '''
        初始化配置
        @conf:{
            'partner':'合作者身份ID',
            'gateway':'支付宝请求网关',
            'notify_url':'服务器异步通知URL',
            'return_url':'前端同步通知URL',
            'ali_secret':'支付宝秘钥'
        }
        '''
        self.conf = conf

    def request_qrcode(self, subject, total_fee):
        '''
        请求生成二维码
        @total_fee: 充值金额
        return: 0 or 1 or 2, {
            'qrcode':'二维码',
            'qrcode_img_url':'二维码图像地址'
            'result_code':'SUCCESS'
            'error_message':'错误信息'
        }
        '''
        url, data = self.gen_qrcode_request(subject, total_fee)
        resp = urllib2.urlopen(url, data, timeout=5).read()
        result = self.parse_xml_data(resp)
        if result['is_success'] != 'T':
            return 0, None
        if result['response']['alipay']['result_code'] == 'SUCCESS':
            return 1, result['response']['alipay']
        else:
            return 2, result['response']['alipay']

    def parse_xml_data(self, text):
        '''
        解析返回的XML结果
        '''
        if text.find('<?xml version="1.0" encoding="GBK"?>') >= 0:
            text = text.replace('<?xml version="1.0" encoding="GBK"?>',
                                '<?xml version="1.0" encoding="UTF-8"?>')
            text = text.decode('gbk').encode('utf-8')
        root = ElementTree.fromstring(text)
        return self._parse_xml(root)

    def _parse_xml(self, node):
        '''
        递归解析xml
        '''
        result = {}
        for i in node.getchildren():
            if i.getchildren():
                result[i.tag] = self._parse_xml(i)
            else:
                result[i.tag] = i.text
        return result

    def gen_qrcode_request(self, subject, total_fee):
        '''
        生成扫码支付交易请求URL 和 参数
        @total_fee: 商品价格, 单位: RMB－分
        return: 经过签名的移动扫码支付请求URL
        '''
        biz_data = {
            'trade_type': '1',  # 即时到帐
            'need_address': 'F',
            'goods_info':{
                'id':'10000',
                'name':'近邻宝充值',
                'price':'%s' % (float(total_fee)/100),
            },
            'return_url':self.conf['qrcode']['return_url'],
            'notify_url':self.conf['qrcode']['notify_url'],
        }
        param = {
            'service': 'alipay.mobile.qrcode.manage',
            '_input_charset': 'utf-8',
            'sign_type': 'MD5',
            'partner': self.conf['partner'],
            'timestamp':datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'method': 'add',
            'biz_type': '10',
            'biz_data': json.dumps(biz_data),
        }
        param['sign'] = self.build_signature(param)
        return self.conf['gateway'], urllib.urlencode(param)

    def verify_release(self, post_data):
        '''
        验证支付宝下单请求
        @post_data: 下单请求数据
        return: True or False
        '''
        data = dict(urlparse.parse_qsl(post_data))

        # TODO: 签名验证
        return True, data

    def verify_notify_data(self, post_data):
        '''
        验证支付宝扫码支付后的异步通知
        @post_data: 下单请求数据
        return: True or False
        '''
        # TODO: 签名验证
        post_data = dict(urlparse.parse_qsl(post_data))
        data = self.parse_xml_data(post_data['notify_data'])

        # 把元转化为分
        data['total_fee'] = int(float(data['total_fee']) * 100)

        return True, data

    def build_signature(self, param):
        '''
        构造签名
        '''
        param = self.filter_param(param)
        temp, param_keys = '', param.keys()
        for k in sorted(param_keys):
            temp += '%s=%s&' % (k, param[k])
        temp = '%s%s' % (temp[:-1], self.conf['ali_secret'])
        return hashlib.md5(temp).hexdigest()

    @staticmethod
    def filter_param(param):
        '''
        过滤参数
        '''
        result = {}
        for k in param:
            if param[k] and k not in ('sign', 'sign_type'):
                result[k] = param[k]
        return result

