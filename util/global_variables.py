#coding=utf-8

########################################
# global variables
########################################

import os, sys, simplejson as json, datetime, re, uuid, redis, hashlib, urllib, random, math

from django.conf import settings

SESSION_COOKIE_NAME = settings.SESSION_COOKIE_NAME
MY_HOST_PIC_URL = settings.MY_HOST_PIC_URL
MY_HOST_PIC_START_NUM = settings.KAKER_PIC_SERVER_START_NUM
MY_HOST_PIC_NUM = settings.KAKER_PIC_SERVER_NUM
LOG_PATH = settings.KAKER_LOG_PATH
TIME_ZONE = settings.TIME_ZONE
GEARMAN_HOSTS_LIST = settings.GEARMAN_HOSTS.split()
ENCODE_SERVICE_ID = settings.ENCODE_SERVICE_ID
UPLOAD_FILE_PATH = settings.UPLOAD_FILE_PATH

KAKER_MONGODB_HOST = settings.KAKER_MONGODB_HOST
KAKER_MONGODB_PORT = settings.KAKER_MONGODB_PORT
MONGODB_REPLICA_SET = settings.MONGODB_REPLICA_SET

ENCODE_TYPE = settings.ENCODE_TYPE
KAKER_MONGODB_DATABASE = settings.KAKER_MONGODB_DATABASE
KAKER_SNS_SERVICE_ADDR = 'http://' + settings.SNS_SERVICE_HOST + ':' + settings.SNS_SERVICE_PORT + '/sns_api_1.0'

SINA_WEIBO_NAME = 'sina_weibo'
QQ_WEIBO_NAME = 'qq_weibo'
RENREN_SNS_NAME = 'RenRen'
MSN_NAME = 'msn'
QQ_NAME = 'qq'
DOUBAN_NAME = 'douban'
KAIXIN_NAME = 'kaixin'

# SNS settiongs
SNS_login_redirect_page = {
    'kaker': 'http://api.kaker.me/sns/api_1.0/sns_login_redirect/?sns_name=' + SINA_WEIBO_NAME,
    '': 'http://api.51banbao.com/api_2.0/SNS_login_redirect/'
}

SNS_validation_bitmap = {
    '': 0x0,
    SINA_WEIBO_NAME: 0x2,
    QQ_WEIBO_NAME: 0x4,
    RENREN_SNS_NAME: 0x8,
    MSN_NAME: 0x10,
    QQ_NAME: 0x20,
    DOUBAN_NAME: 0x40,
    KAIXIN_NAME: 0x80,
}

source_map = {
    SINA_WEIBO_NAME: '新浪微博',
	QQ_WEIBO_NAME: '腾讯微博',
	RENREN_SNS_NAME: '人人',
	MSN_NAME: 'MSN',
	QQ_NAME: 'QQ',
	DOUBAN_NAME: 'douban',
    KAIXIN_NAME: 'kaixin',
}

SINA_BANBAO_ID = '2468036445'
QQ_BANBAO_NAME = 'banbaowang'

WEIBO_ARTICLE_LEN = 140
EDITABLE_LEN = 40

API_ACCESS_LOGGER_NAME = 'kaker_api_log'
ERROR_LOGGER_NAME = 'kaker_error_log'
api_access_logger = None
api_access_hdlr = None
error_logger = None
current_time_stamp = None
redis_cache = None