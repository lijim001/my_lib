#coding=utf-8

import time,re
from MobileService.util.mobile_errors import *
from MobileService.util.log_manager import *
from MobileService.util.session_manage import *
from MobileService.util.BanUserUtil import *
#from MobileService.util.OpenWeixin import OpenWeixinUtil
from MobileService.business_user.db_business_user import DbBusinessUser

from django.conf import settings

xinwo_token = 'cab9fea6486f34fe65137eb16d4f2bd6'

def logger_init(fn):
    def logger_init_before(*args):
        request = args[0]
        path = request.META.get('PATH_INFO')
        result = fn(*args)
        if len(str(result)) >= 512:
            user_info = 'too long'
        else:
            user_info = str(result)[32:]
        environment = settings.COMMON_DATA['environment']
        request_response_access_log(request, user_info, environment)
        return result
    return logger_init_before
    
# set cookie for request
def set_cookie_for_request(fn):
    def set_cookie_routine(*args):
        result = fn(*args)
        #print result
        return result

    return set_cookie_routine

DO_NOT_CHECK_USER_ID_LIST = [
    '/user/login/',
    '/user/register/',
    '/user/login_register/',
    '/user/promote_register/',
    '/business_user/register/',
    '/business_user/register_v2/',
    '/business_user/login/',
    '/shop/category/',
    '/shop/get_brands/',
    '/shop/get_shops/',
    '/promote/login/',
    '/message/customer_create_session_v2/',
]

BUSINESS_NOT_ALLOW_URL_PREFIX = [
    '/user/',
    '/wallet/',
    '/order/',
]

XINWO_ADMIN_DICT = {
    xinwo_token : ['/message/customer_get_mail/', '/message/business_get_mail/', '/message/business_get_mail_v2/','/message/customer_get_mail_v2/', 'upload_image/upload_goods/'],
}

BUSINESS_ALLOW_PATH_LIST = [
    '/business_user/login/',
    '/business_user/register/',
    '/business_user/register_v2/',
    '/business_user/login_register/'
]

def check_ban_user(request):
    if session_is_business_user(request):
        app = 'wallet_business'
    elif session_is_promote_user(request):
        app = 'promote'
    else:
        app = 'wallet_client'
    
    phone = session_get_user_name(request)
    handler = BanUserUtil(settings.COMMON_DATA)
    return handler.check_banner_user(app, phone)
    

def get_server_name(request):
    http_host = request.META.get('HTTP_HOST', '')
    return http_host.split(':')[0]

def check_promote(request):
    server_name = get_server_name(request)
    path_info = request.META.get('PATH_INFO', '')
    if not path_info.startswith('/promote/'):
        return True
    if server_name not in ['test.promote.mobile.xinwo.com', 'test.promote.mobiles.xinwo.com', 'promote.mobile.xinwo.com', 'promote.mobiles.xinwo.com']:
        return True
    return True

def check_open_weixin(request):
    server_name = get_server_name(request)
    path_info = request.META.get('PATH_INFO', '')
    if not path_info.startswith('/open_weixin/'):
        return False
    if server_name not in ['test.owx.mobile.xinwo.com', 'owx.mobile.xinwo.com']:
        return (True, ERROR_USER_NO_PRIVILEGE)
    user_name = session_get_user_name(request)
    if user_name:
        return (True, ERROR_NO_ERROR)
    code = request.REQUEST.get('code', '')
    state = request.REQUEST.get('state', '')
    handler = OpenWeixinUtil(settings.COMMON_DATA)
    open_id = handler.get_access_token(code)
    if not open_id:
        return (True, ERROR_USER_NO_PRIVILEGE)
    
    
    return True
    
def forbid_url_business(request):
    if check_domain_inner(request):
        return True
    path_info = request.META.get('PATH_INFO', '')
    if session_is_root(request):
        return True
    if not session_is_business_user(request):
        if path_info in BUSINESS_ALLOW_PATH_LIST:
            return True
        if path_info.startswith('/business'):
            return False
        return True
    for item in BUSINESS_NOT_ALLOW_URL_PREFIX:
        if path_info.startswith(item):
            return False
    return True
    
def need_check_user(request):
    path_info = request.META.get('PATH_INFO', '')
    if path_info in DO_NOT_CHECK_USER_ID_LIST:
        return False
    else:
        return True

def check_xinwo_admin(request):
    if check_domain_inner(request):
        session_set_root(request)
        return True
    xinwo_admin = request.REQUEST.get('xinwo_admin', '')
    path_info = request.META.get('PATH_INFO', '')
    path_list = XINWO_ADMIN_DICT.get(xinwo_admin, '')
    if not path_list:
        return False
    if not path_info in path_list:
        return False
    session_set_root(request)
    return True
    
def check_business_session(request):
    if session_check_business_user(request):
        return False
    handler = DbBusinessUser(settings.COMMON_DATA['mobile_db'])
    user_id = request.session.get('user_id', '')
    basic_info = handler.get_business_user(user_id)
    if not basic_info:
        return False
    user_id = basic_info.get('user_id', 0)
    user_name = basic_info.get('telephone', '')
    brand_id = basic_info.get('brand_id', 0)
    channel_id = basic_info.get('channel_id', 0)
    role = basic_info.get('role', 'sales')
    shop_id = basic_info.get('shop_id', 0)
    sales_name = basic_info.get('name', '')
    session_set_business_user(request, user_id, user_name, brand_id, channel_id, shop_id, role, sales_name)
    return True
        
def check_user_id(request):
    param_user_id = str(request.REQUEST.get('user_id', ''))
    session_user_id = str(request.session.get('user_id', ''))

    if not session_user_id or not param_user_id:
        return False
    if param_user_id and session_user_id:
        return param_user_id == session_user_id
    return True

def check_use_time(request):
    last_use_time = session_get_last_use_time(request)
    now = int(time.time())
    if now - last_use_time < 6:
    #if now - last_use_time < 60 * 60 * 6:
        return
    session_update_last_use_time(request, now)
    if session_is_customer_user(request):
        handler = DbBusinessUser(settings.COMMON_DATA['mobile_db'])
        user_id = session_get_user_id(request)
        handler.update_customer_usage_time(user_id, login_time=now)

def check_domain_inner(request):
    remote_ip = request.META.get('REMOTE_ADDR', '')
    environment = settings.COMMON_DATA['environment']

    server_name = get_server_name(request)
    if server_name not in ['test.inner.mobile.xinwo.com', 'test.inner.mobiles.xinwo.com', 'inner.mobile.xinwo.com', 'inner.mobiles.xinwo.com', 'test.mobiles.xinwo.com']:
        return False
    if environment == 'test':
        return True
    inner_ip_list = settings.COMMON_DATA['inner_ip_list']
    if remote_ip in inner_ip_list:
        return True
    return False

def check_inner_domain_access(fn):
    def check_access(*args):
        request = args[0]
        if check_domain_inner(request):
            role = session_get_business_role(request)
            session_set_root(request)
            ret = fn(*args)
            session_set_business_role(request, role)
            return ret
        else:
            return response_error_json(ERROR_USER_NO_PRIVILEGE)
    return check_access

def do_inner_domain_access(request):
    if check_domain_inner(request):
        role = session_get_business_role(request)
        session_set_root(request)
        session_set_business_role(request, role)
    return request
    
def user_checking_routine_dec(fn):
    def user_generator(*args):
        request = args[0]
        phone = session_get_user_name(request)
        
        request = do_inner_domain_access(request)
        
        if not check_ban_user(request):
            phone = session_get_user_name(request)
            print 'baned user %s'%(str(phone))
            return response_error_json(ERROR_USER_NO_PRIVILEGE)
        if not check_promote(request):
            return response_error_json(ERROR_USER_NO_PRIVILEGE)
        if not forbid_url_business(request):
            print 'url forbid'
            return response_error_json(ERROR_USER_NO_PRIVILEGE)
            
        if not check_xinwo_admin(request) and need_check_user(request) and not check_user_id(request):
            return response_error_json(ERROR_USER_NEED_LOGIN)
        check_business_session(request)
        check_use_time(request)
        return fn(*args)

    return user_generator

def log_slow_func(func_name, threshold = 100):
    def outer(func):
        import time
        def inner(*args, **kwargs):
            start = time.time() * 1000
            ret_func = func(*args, **kwargs)
            end = time.time() * 1000
            duration = int(end - start)
            
            if duration > threshold:
                print duration
                request = args[0]
                import logging
                #from kaker.util import global_variables
                logger_name = global_variables.ERROR_LOGGER_NAME
                my_logger = logging.getLogger(logger_name)
                if my_logger:
                    my_logger.error('slow log %s %dms'%(func_name, duration))
            return ret_func
        return inner
    return outer
