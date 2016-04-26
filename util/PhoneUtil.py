#coding=utf-8

from xml.etree import ElementTree
import re

if __name__ == '__main__':
    import os,sys
    G_PATH = os.path.split(os.path.realpath(__file__))[0]
    sys.path.append(G_PATH + '/../../')
    os.environ['DJANGO_SETTINGS_MODULE'] = 'MobileService.settings'
    from django.conf import settings
    
from MobileService.util.HttpUtil import *

def check_phone_number(phone):
    try:
        int_phone = int(phone)
    except Exception,e:
        pass
        return False
    else:
        if len(str(int_phone)) == 11:
            return True
        else:
            return False

def get_phone_locate(phone):
    ret_data = OpenUrl('http://life.tenpay.com/cgi-bin/mobile/MobileQueryAttribution.cgi?chgmobile=' + str(phone))
    if not ret_data:
        return {}
    ret_dict = {}
    province=''
    city=''
    try:
        rep_data = ret_data.decode('gbk','ignore')
        regx = re.compile(r'<province>(.*?)</province>')
        m = regx.search(rep_data)
        if m:
            province = m.group(1)
        regx = re.compile(r'<city>(.*?)</city>')
        m = regx.search(rep_data)
        if m:
            city = m.group(1)
        if province:
            #print type(province)
            #print province
            ret_dict['province'] = province.strip()
            ret_dict['city'] = city.strip()

        return ret_dict
    except Exception,e:
        print e
        return {}
        
if __name__ == '__main__':
    print get_phone_locate(13810806543)