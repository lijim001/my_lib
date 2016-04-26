#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
微信
"""
import copy
import json
import uuid
import time
import urllib
import hashlib
import logging
import urlparse
import StringIO
from lib.httpclient import HttpClient
from xml.etree import ElementTree


# 交易类型
TRADE_TYPE_JSAPI = "JSAPI"
TRADE_TYPE_NATIVE = "NATIVE"
TRADE_TYPE_APP = "APP"


def parse_xml_data(text):
    """
    解析XML数据
    :param string text: 待解析的XML文本
    """
    root = ElementTree.fromstring(text)
    data = {}
    for i in root.getchildren():
        data[i.tag] = i.text
    return data


def generate_xml(data):
    """
    生成XML数据
    :param string text: 待解析的XML文本
    """
    root = ElementTree.Element('xml')
    tree = ElementTree.ElementTree(root)
    for i in data:
        child = ElementTree.Element(i)
        if isinstance(data[i], str):
            text = data[i].decode("UTF-8")
        elif isinstance(data[i], unicode):
            text = data[i]
        else:
            text = '%s' % data[i]
        child.text = text
        root.append(child)
    fobj = StringIO.StringIO()
    tree.write(fobj, 'UTF-8')
    return fobj.getvalue()


class WeixinClient(object):
    """
    微信支付
    """
    def __init__(self, conf):
        """
        初始化配置
        :param dict conf:{
            "appid":"应用ID",
            "appsecret":"长度为32的字符串, 用于获取access_token",
            "appkey":"长度为128的字符串, 用户支付过程中生成app_signature",
            "partnerkey":"微信公众平台商户模块生成的商户密钥",
            "notify_url":"服务器异步通知URL",
        }
        """
        self.conf = conf
        self.http = HttpClient(timeout=5)
        self.token_url = "https://api.weixin.qq.com/cgi-bin/token"
        self.prepay_url = "https://api.weixin.qq.com/pay/genprepay"

    def get_access_token(self):
        """
        获取APP的全局唯一票据
        return: {
            "access_token":APP的访问令牌,
            "expires_in":实效时间,
        }
        """
        param = {
            "grant_type": "client_credential",
            "appid":self.conf["appid"],
            "secret":self.conf["appsecret"],
        }
        url = "%s?%s" % (self.token_url, urllib.urlencode(param))
        return self.http.http_get(url)

    def generate_prepay(self, access_token, out_trade_no, total_fee,
                        body, traceid):
        """
        创建移动支付交易请求数据
        :param string access_token: APP的全局访问票据
        :param string out_trade_no: 交易号(在商户系统中唯一)
        :param int total_fee: 商品价格, 单位: RMB－分
        :param string body: 商品描述
        :param string traceid: 商家对用户的唯一标识,如果用微信 SSO,
                  此处建议填写 授权用户的 openid
        :return:{
            "prepayid":"PREPAY_ID",
            "errcode":0,
            "errmsg":"Success"
        }
        """
        # 生成package字段
        param = {
            "bank_type": "WX",
            "fee_type": "1",
            "input_charset": "UTF-8",
            "partner": self.conf["partnerid"],
            "notify_url": self.conf["notify_url"],
            "out_trade_no": out_trade_no,
            "total_fee":"%s" % total_fee,
            "body":body,
            "spbill_create_ip":"127.0.0.1",
        }
        string1 = "&".join(["%s=%s" % (k, v) for k, v in sorted(param.items())])
        string1 += "&key=%s" % self.conf["partnerkey"]
        sign = hashlib.md5(string1).hexdigest().upper()
        string2 = "&".join(["%s=%s" % (k, urllib.quote(v)) \
                                       for k, v in sorted(param.items())])
        package = "%s&sign=%s" % (string2, sign)

        # 生成预支付POST数据
        request_data = {
            "appid": self.conf["appid"],
            "noncestr": hashlib.md5(str(uuid.uuid4())).hexdigest(),
            "package": package,
            "timestamp": int(time.time()),
            "traceid": traceid
        }
        request_data["app_signature"] = self.build_signature(request_data)
        request_data["sign_method"] = "sha1"

        # 请求预支付API
        qstr = urllib.urlencode({"access_token": access_token})
        url = "%s?%s" % (self.prepay_url, qstr)
        res = self.http.http_post(url, body=json.dumps(request_data))
        if res["errcode"] != 0:
            logging.error("#fail to generate prepayid: %s, res: %s",
                          json.dumps(request_data), res)
            return res
        info = {
            "appid":self.conf["appid"],
            "noncestr":request_data["noncestr"],
            "timestamp":request_data["timestamp"],
            "package":"Sign=WXPay",
            "partnerid":self.conf["partnerid"],
            "prepayid":res["prepayid"],
        }
        info["sign"] = self.build_signature(info)
        return info

    def build_signature(self, param):
        """
        构造签名
        """
        data = copy.deepcopy(param)
        data["appkey"] = self.conf["appkey"]
        temp = "&".join(["%s=%s" % (k, v) for k, v in sorted(data.items())])
        return hashlib.sha1(temp).hexdigest()

    def verify_notify_data(self, query_data, post_data):
        """
        校验异步通知数据
        :param string query_data: 微信的查询字符串数据, 订单信息, 微信服务端太2b了!
        :param string post_data: 微信的POST数据, 携带的是本次支付的用户相关信息
        :return: 是否验证通过, 通知数据(DICT){
            "out_trade_no":"商户订单系统中的订单号",
            "trade_no":"该交易在支付宝系统中的交易流水号",
            "trade_status":"交易状态",
            "trade_id":"通知校验ID",
            "total_fee":"交易金额",
            "buyer_id":"买家支付宝用户号",
            "buyer_email":"买家支付宝账号",
            ...
        }
        """
        # 校验订单数据
        raw, data = dict(urlparse.parse_qsl(query_data)), {}
        for k in raw:
            if k == "sign" or raw[k] == "":
                continue
            data[k] = raw[k]
        temp = "&".join(["%s=%s" % (k, v) for k, v in sorted(data.items())])
        temp += "&key=%s" % self.conf["partnerkey"]
        sign = hashlib.md5(temp).hexdigest().upper()

        # TODO 校验用户数据
        user_data = parse_xml_data(post_data)
        data["userdata"] = user_data

        return sign == raw["sign"], data


class WeixinPayClient(object):
    """
    微信支付
    """
    def __init__(self, conf):
        """
        初始化配置
        :param dict conf:{
            "appid":"应用ID",
            "appsecret":"长度为32的字符串, 用于获取access_token",
            "appkey":"长度为128的字符串, 用户支付过程中生成app_signature",
            "partnerid":"商户ID",
            "partnerkey":"微信公众平台商户模块生成的商户密钥",
            "notify_url":"服务器异步通知URL",
        }
        """
        self.conf = conf
        self.http = HttpClient(timeout=5)
        self.unifiedorder_url = "https://api.mch.weixin.qq.com/pay/unifiedorder"

    def create_prepay(self, out_trade_no, total_fee, body, trade_type):
        """
        创建预支付交易
        :param string out_trade_no: 交易号(在商户系统中唯一)
        :param int total_fee: 商品价格, 单位: RMB－分
        :param string body: 商品描述
        :param trade_type: 交易类型
        :return:{
            "prepayid":"PREPAY_ID",
            "code_url":"二维码链接",
            "return_code":"Success or FAIL",
            "return_msg":"错误原因"
        }
        """
        # 请求参数
        param = {
            "appid": self.conf["appid"],
            "mch_id": self.conf["partnerid"],
            "noncestr": hashlib.md5(str(uuid.uuid4())).hexdigest(),
            "body":body,
            "out_trade_no": out_trade_no,
            "fee_type": "CNY",
            "total_fee":total_fee,
            "spbill_create_ip":"127.0.0.1",         # Native支付填调用微信支付API的机器IP
            "notify_url": self.conf["notify_url"],
            "trade_type": trade_type,
            "product_id": out_trade_no,
        }
        param["sign"] = self.build_signature(param)

        # 生成XML数据
        xml_text = generate_xml(param)

        # POST请求, 解析XML
        response = self.http.http_post(self.unifiedorder_url, "text",
                                       body=xml_text)
        res = parse_xml_data(response)
        if res["return_code"] != "SUCCESS" or res["result_code"] != "SUCCESS":
            logging.error("fail to create prepay: %s", param)
            return None

        # 验证签名
        if not self.verify_signature(res):
            logging.error("fail to verify signature: %s", res)
            return None

        info = {
            "prepayid":res["prepay_id"],
            "code_url":res.get("code_url", ""),
        }
        return info

    def build_signature(self, param):
        """
        构造签名
        """
        temp_str = "&".join(["%s=%s" % (k, v) for k, v in \
                             sorted(param.items()) if str(v) and k != 'sign'])
        temp_str += "&key=%s" % self.conf["appkey"]
        return hashlib.md5(temp_str).hexdigest().upper()

    def verify_signature(self, param):
        """
        验证签名
        """
        return param['sign'] == self.build_signature(param)

    def verify_notify_data(self, post_data):
        """
        校验异步通知数据
        :param string post_data: 通知数据
        :return: 是否验证通过, 通知数据(DICT){
            "out_trade_no":"商户订单系统中的订单号",
            "trade_no":"该交易在支付宝系统中的交易流水号",
            "trade_status":"交易状态",
            "trade_id":"通知校验ID",
            "total_fee":"交易金额",
            "buyer_id":"买家支付宝用户号",
            "buyer_email":"买家支付宝账号",
            ...
        }
        """
        data = parse_xml_data(post_data)
        if not self.verify_signature(data):
            logging.error("fail to verify signature: %s", data)
            return False, None

        return True, data

