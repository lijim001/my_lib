#coding=utf-8

from kaker.util.session_manage import session_get_user_id,session_is_loggin
from kaker.util.db_api.user_interface import get_userinfo_by_id
            
def is_system_manager(request):
    if not session_is_loggin(request):
        return False
    user_id = session_get_user_id(request)
    user = get_userinfo_by_id(user_id)
    if user.role == 'low_manager' or user.role == 'high_manager':
        return True
    return False
    
def is_system_high_manager(request):
    if not session_is_loggin(request):
        return False
    user_id = session_get_user_id(request)
    user = get_userinfo_by_id(user_id)
    if user.role == 'high_manager':
        return True
    return False

def is_system_manager_from_user(user_id):
    user = get_userinfo_by_id(user_id)
    if user.role == 'low_manager' or user.role == 'high_manager':
        return True
    return False

def is_system_high_manager_from_user(user_id):
    user = get_userinfo_by_id(user_id)
    if user.role == 'high_manager':
        return True
    return False    