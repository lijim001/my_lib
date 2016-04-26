#coding=utf-8

import urllib,os,time
import simplejson as json

if __name__ == '__main__':
    import os,sys
    G_PATH = os.path.split(os.path.realpath(__file__))[0]
    sys.path.append(G_PATH + '/../../')
    os.environ['DJANGO_SETTINGS_MODULE'] = 'MobileService.settings'
    from django.conf import settings
    
from MobileService.util.HttpUtil import *

GEO_CODER_ADDER = 'http://api.map.baidu.com/geocoder/v2/'

class BaiduLocationUtil():
    def __init__(self, ak='912ed94181a2ff2a86dc9416e53d9d6e'):
        self.ak = ak
        
    def get_postion_by_addr(self, addr):
        service_addr = GEO_CODER_ADDER + '?output=json&ak=' + str(self.ak) + '&address=' + addr.encode('utf8', 'ignore')
        print service_addr
        ret_data = OpenUrl(service_addr)
        print ret_data
        if not ret_data:
            return (None, '')
        json_data = json.loads(ret_data)
        status = json_data.get('status')
        if status != 0:
            return (None, json_data.get('msg', ''))
        ret = json_data.get('result')
        location = ret.get('location', None)
        confidence = ret.get('confidence', 0)
        return (location, confidence)
        
if __name__ == '__main__':
    handler = BaiduLocationUtil()
    print handler.get_postion_by_addr(u'北京市朝阳区十里河龙凤之家三层 地康展厅')
    
    