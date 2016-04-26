#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
银联移动支付
'''
import urllib
import urllib2
import urlparse
import hashlib
import datetime


RESP_CODE_SUCC = '00'  # 成功应答码


class UnionpayClient(object):
    '''
    银联支付
    '''
    def __init__(self, conf):
        '''
        初始化配置
        @conf:{
            'mer_id':'商户号',
            'secret_key':'商户秘钥',
            'back_notify_url':'商户后台通知URL',
            'front_notify_url':'商户前台通知URL',
            'upmp_trade_url':'交易URL',
            'upmp_query_url':'查询URL',
            'upop_base_url':'支付网址'
        }
        '''
        self.conf = conf

    def create_mob_trade(self, out_trade_no, total_fee, body):
        '''
        创建移动支付交易请求数据
        @out_trade_no: 交易号(在商户系统中唯一)
        @total_fee: 商品价格, 单位: RMB－分
        @body: 商品描述
        return: 是否验证通过, {
            'tn':交易流水号,
            'respCode':响应码,
            'respMsg':响应信息,
        }
        '''
        now_str = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        param = {
            'version': '1.0.0',
            'charset': 'UTF-8',
            'transType': '01',                           # 交易类型
            'merId':self.conf['mer_id'],                 # 商户代码
            'backEndUrl': self.conf['back_notify_url'],  # 通知URL
            'orderDescription': body,                    # 订单描述(可选)
            'orderTime': now_str,                        # 交易开始时间
            'orderTimeout': "",                          # 订单超时时间(可选)
            'orderNumber': out_trade_no,                 # 商户订单号
            'orderAmount': int(total_fee),               # 订单金额, 整数，单位分
            'orderCurrency': '156',                      # 交易币种(可选)
            'reqReserved': '',                           # 请求方保留域(可选, 用于透传商户信息)
            'merReserved': ''                            # 商户保留
        }
        param['signature'] = self.build_signature(param)
        param['signMethod'] = 'MD5'
        data = urllib.urlencode(param)
        response = self.send_post(self.conf['upmp_trade_url'], data)
        is_ok, result = self.verify_response(response)
        if is_ok and result['respCode'] == RESP_CODE_SUCC:
            return True, result
        else:
            return False, result

    def verify_notify_data(self, post_data):
        '''
        验证银联后台交易通知
        return: 是否验证通过, {
            'transStatus':交易状态,
            'respCode':响应码,
            'respMsg':响应信息,
            'qn':查询流水号,
            'orderNumber':商户订单号,
            'settleAmount':清算金额,
        }
        '''
        is_ok, result = self.verify_response(post_data)
        if is_ok and result['respCode'] == RESP_CODE_SUCC:
            return True, result
        else:
            return False, result

    def build_signature(self, param):
        '''
        构造签名
        '''
        param = self.filter_param(param)
        temp, param_keys = '', param.keys()
        for k in sorted(param_keys):
            temp += '%s=%s&' % (k, param[k])
        temp = '%s%s' % (temp, hashlib.md5(self.conf['secret_key']).hexdigest())
        return hashlib.md5(temp).hexdigest()

    @staticmethod
    def filter_param(param):
        '''
        过滤参数
        '''
        result = {}
        for k in param:
            if param[k] and k not in ('signature', 'signMethod'):
                result[k] = param[k]
        return result

    @staticmethod
    def send_post(url, data):
        '''
        发送POST请求
        '''
        resp = urllib2.urlopen(url, data, timeout=10).read()
        return resp.decode('UTF-8')

    def verify_response(self, post_data):
        '''
        校验响应内容
        @post_data: 银联返回数据
        return: 是否验证通过
        '''
        param = dict(urlparse.parse_qsl(post_data))
        signature = self.build_signature(param)
        return param['signature'] == signature, param

    def web_verify_notify_data(self, post_data):
        '''
        验证银联后台交易通知
        return: 是否验证通过, {
            'respCode':响应码,
            'respMsg':响应信息,
            'qn':查询流水号,
            'orderNumber':商户订单号,
            'settleAmount':清算金额,
        }
        '''
        is_ok, result = self.web_verify_response(post_data)
        if is_ok and result['respCode'] == RESP_CODE_SUCC:
            return True, result
        else:
            return False, result

    def web_verify_response(self, post_data):
        '''
        校验响应内容
        @post_data: 银联返回数据
        return: 是否验证通过
        '''
        signature = self.web_build_signature(post_data)
        return signature == post_data['signature'], post_data

    @staticmethod
    def web_filter_param(param):
        '''
        过滤参数
        '''
        result = {}
        for k in param:
            if k not in ('signature', 'signMethod'):
                result[k] = param[k]
        return result

    def web_build_signature(self, param):
        '''
        构造签名
        '''
        param = self.web_filter_param(param)
        temp, param_keys = '', param.keys()
        for k in sorted(param_keys):
            temp += '%s=%s&' % (k, param[k])
        temp = '%s%s' % (temp, hashlib.md5(self.conf['secret_key']).hexdigest())
        return hashlib.md5(temp).hexdigest()

    def create_pay_html(self, out_trade_no, total_fee, commodity_name,
                        commodity_unitprice, commodity_quantity,
                        commodity_discount, transfer_fee, uid):
        '''
        生成发送银联报文页面
        @out_trade_no: 交易号(在商户系统中唯一)
        @total_fee: 商品价格, 单位: RMB－分
        @commodity_name: 商品名称
        @commodity_unitprice: 商品单价
        @commodity_quantity: 商品数量
        @commodity_discount: 商品折扣
        @transfer_fee: 商品运费
        @body: 商品描述
        @uid: 交费人ID
        return: data
        '''
        now_str = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        param = {
            'version': '1.0.0',                                                  # 协议版本
            'charset': 'UTF-8',                                                  # 字符编码
            'transType': '01',                                                   # 交易类型
            'origQid': '',                                                       # 原始交易流水号
            'merId': self.conf['mer_id'],                                        # 商户代码
            'merAbbr': self.conf['mer_abbr'],                                    # 商户简称
            'acqCode': '',                                                       # 收单机构代码
            'merCode': '',                                                       # 商户类别
            'commodityUrl': '',                                                  # 商品URL
            'commodityName': commodity_name,                                     # 商品名称
            'commodityUnitPrice': int(commodity_unitprice),                      # 商品单价(分)
            'commodityQuantity': int(commodity_quantity),                        # 商品数量
            'commodityDiscount': int(commodity_discount),                        # 商品折扣(分)
            'transferFee': int(transfer_fee),                                    # 运费(分)
            'orderNumber': out_trade_no,                                         # 商户订单号
            'orderAmount': int(total_fee),                                       # 订单金额, 整数，单位分
            'orderCurrency': '156',                                              # 交易币种(可选)
            'orderTime': now_str,                                                # 交易开始时间
            'customerIp': '127.0.0.1',                                           # 用户IP
            'customerName': '',                                                  # 用户真实姓名
            'defaultPayType': '',                                                # 默认支付方式
            'defaultBankNumber': '',                                             # 默认银行编号
            'transTimeout': '300000',                                            # 订单超时时间(可选)
            'frontEndUrl': '%s?merUserId=%s' % (self.conf['front_end_url'], uid),# 前台回调商户URL
            'backEndUrl': '%s?merUserId=%s' % (self.conf['back_end_url'], uid),  # 后台回调商户URL
            'merReserved': '{merUserId=%s}' % uid                                # 商户保留
        }
        param['signature'] = self.web_build_signature(param)
        param['signMethod'] = 'MD5'
        return param

    def generateAutoSubmitForm(self, out_trade_no, total_fee, uid):
        '''
        生成表单
        '''
        html_text = '<script language="javascript">window.onload=function(){document.pay_form.submit();}</script>\n'
        html_text += '<form id="pay_form" name="pay_form" action="%s" method="post">\n' % self.conf['upop_base_url']
        data = self.create_pay_html(out_trade_no, total_fee, '近邻宝充值', 0, 1, 0, 0, uid)
        for k, v in data.items():
            html_text += '<input type="hidden" name="%s" id="%s" value="%s">\n' % (k, k, v)
        html_text += '</form>\n'
        return html_text

