#coding=utf-8

import time

BUSINESS_USER_ROLE = 'bussiness'
CUSTOMER_USER_ROLE = 'customer'
PROMOTE_USER_ROLE = 'promote'

def session_is_loggin(request):
    return request.session.get('is_login', False)
    
def session_get_id(request):
    return request.session.get_session_key()

def session_set_expire(request, expire):
    return request.session.set_session_expire(expire)

def session_get_last_use_time(request):
    return request.session.get('use_time', 0)

def session_update_last_use_time(request, update_time):
    request.session['use_time'] = update_time
    
def session_set_user_business(request):
    request.session['user_role'] = BUSINESS_USER_ROLE

def session_is_business_user(request):
    return request.session.get('user_role', '') == BUSINESS_USER_ROLE

def session_set_user_promote(request):
    request.session['user_role'] = PROMOTE_USER_ROLE

def session_is_promote_user(request):
    return request.session.get('user_role', '') == PROMOTE_USER_ROLE
    
def session_set_user_customer(request):
    request.session['user_role'] = CUSTOMER_USER_ROLE

def session_is_customer_user(request):
    return request.session.get('user_role', '') == CUSTOMER_USER_ROLE
    
def session_set_business_role(request, role):
    request.session['business_role'] = role

def session_get_business_role(request):
    return request.session.get('business_role', 'sales')

def session_is_root(request):
    return request.session.get('business_role', 'sales') == 'root'
    
def session_set_root(request):
    request.session['business_role'] = 'root'
    
def session_get_user_id(request):
    return request.session.get('user_id', '')
    
def session_set_user_id(request, user_id):
    request.session['user_id'] = user_id
    
def session_get_user_name(request):
    return request.session.get('user_name', '')

def session_set_user_name(request, user_name):
    request.session['user_name'] = user_name

def session_get_brand_id(request):
    return request.session.get('brand_id', '')

def session_set_brand_id(request, brand_id):
    request.session['brand_id'] = brand_id

def session_get_channel_id(request):
    return request.session.get('channel_id', '')

def session_set_shop_id(request, shop_id):
    request.session['shop_id'] = shop_id

def session_get_shop_id(request):
    return request.session.get('shop_id', '')

def session_set_sales_name(request, sales_name):
    request.session['sales_name'] = sales_name

def session_get_sales_name(request):
    return request.session.get('sales_name', '')
    
def session_logout(request):
    return request.session.delete()

def session_set_channel_id(request, channel_id):
    request.session['channel_id'] = channel_id

def session_check_business_user(request):
    if not session_is_business_user(request):
        return True
    user_id = session_get_user_id(request)
    if not user_id:
        return True
    channel_id = session_get_channel_id(request)
    if channel_id == '':
        return False
    brand_id = session_get_brand_id(request)
    if brand_id == '':
        return False
    shop_id = session_get_shop_id(request)
    if shop_id == '':
        return False
    user_name = session_get_user_name(request)
    if user_name == '':
        return False
    sales_name = session_get_sales_name(request)
    if sales_name == '':
        return False    
    return True
    
def session_set_business_user(request, user_id, user_name, brand_id, channel_id, shop_id, role = 'sales', sales_name = ''):
    session_set_user_id(request, user_id)
    session_set_user_name(request, user_name)
    session_set_brand_id(request, brand_id)
    session_set_channel_id(request, channel_id)
    session_set_shop_id(request, shop_id)
    session_set_business_role(request, role)
    session_set_sales_name(request, sales_name)
    session_set_user_business(request)
    #session_print_business(request)

def session_print_business(request):
    print session_get_user_id(request)
    print session_get_user_name(request)
    print session_get_brand_id(request)
    print session_get_shop_id(request)
    print session_get_business_role(request)
    print session_get_channel_id(request)
    
def session_get_int_param(request, param_name, default_value = 0):
    value = request.REQUEST.get(param_name, '')
    try:
        value = int(value)
    except:
        value = default_value
    finally:
        return value

def session_set_mail_time(request):
    request.session['mail_time'] = time.time()
    
def session_get_mail_time(request):
    return request.session.get('mail_time', 0)
    
def session_set_create_inquire_time(request):
    request.session['create_inquire'] = time.time()
    
def session_get_create_inquire_time(request):
    return request.session.get('create_inquire', 0)
    
def session_get_float_param(request, param_name, default_value = 0):
    value = request.REQUEST.get(param_name, '')
    try:
        value = float(value)
    except:
        value = default_value
    finally:
        return value

def session_init(request, user_id):
    request.session['user_id'] = user_id
