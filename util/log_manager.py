#coding=utf-8

import simplejson as json
from django.conf import settings
from MobileService.util.session_manage import *

def get_client_ip_addr(request):
    try:
        forward_addr = request.META.get('HTTP_X_FORWARDED_FOR', None)
        if forward_addr:
            return forward_addr.split(',')[0]

        remote_addr = request.META['REMOTE_ADDR']
        return remote_addr.split(',')[0]
    except Exception,e:
        return ''

def format_log_header(request=None, usr_msg='', is_quest = True):
    if not request:
        return ''
    ip_addr = get_client_ip_addr(request)
    app = request.REQUEST.get('app', '')
    device_id = request.REQUEST.get('device_id', '')
    platform = request.REQUEST.get('platform', '')
    user_id = str(request.session.get('user_id', ''))
    version = request.REQUEST.get('version', '')
    user_name = session_get_user_name(request)
    channel_id = session_get_channel_id(request)
    shop_id = session_get_shop_id(request)
    brand_id = session_get_brand_id(request)
    msg = '|user_id: ' + user_id + '|ip: ' + ip_addr + '|version: ' + version + '|app: ' + app + '|device_id: ' + device_id \
    + '|platform: ' + platform + '|user_name: ' + str(user_name) + '|brand_id: ' + str(brand_id) + '|channel_id: ' + str(channel_id) + '|shop_id: ' + str(shop_id)
    if is_quest is None:
        return usr_msg + msg
    if is_quest:
        return 'request ' + usr_msg + msg
    else:
        return 'response ' + usr_msg + msg

def unicode_encode(str):
    return isinstance(str, unicode) and str.encode('utf-8') or str

def sort_params(params = None):
    return "&".join(["%s=%s" % (unicode_encode(x), unicode_encode(params[x])) for x in sorted(params.keys())])

def format_request(request, environment='normal'):
    params = {}
    for key, value in request.REQUEST.items():
        if len(value) >= 256:
            continue
        if key.find('pass') >= 0 and environment == 'normal':
            value = '*****'
            #pass
        params[key] = value
    return params
    
def access_log(request, usr_msg, info_dict = {}):
    my_logger = settings.COMMON_DATA['access_logger']
    msg = format_log_header(request, usr_msg)
    finally_msg = msg + '|params:' + json.dumps(format_request(request))
    my_logger.info(finally_msg)

def response_access_log(request, path, usr_msg):
    my_logger = settings.COMMON_DATA['access_logger']
    msg = format_log_header(request, path, False)
    finally_msg = msg + usr_msg
    my_logger.info(finally_msg)
    
def request_response_access_log(request, usr_msg, environment='normal'):
    my_logger = settings.COMMON_DATA['access_logger']
    path = request.META.get('PATH_INFO')
    msg = format_log_header(request, path, None)
    msg = msg + '|params:' + json.dumps(format_request(request,environment)) + ' >> ret :' + usr_msg
    my_logger.info(msg)
    
def info_log(request, usr_msg, info_dict = {}):
    my_logger = settings.COMMON_DATA['mobile_logger']
    msg = format_log_header(request, usr_msg)
    finally_msg = msg + json.dumps(format_request(request))
    my_logger.info(finally_msg)
    
def pay_log(request, usr_msg, info_dict = {}):
    my_logger = settings.COMMON_DATA['pay_logger']
    msg = format_log_header(request, usr_msg)
    finally_msg = msg + '|params:' + json.dumps(format_request(request))
    my_logger.info(finally_msg)    
    
