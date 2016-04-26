#coding=utf-8

import urllib,os,time,sys
import urllib2,cookielib,httplib
import simplejson as json

if __name__ == '__main__':
    G_PATH = os.path.split(os.path.realpath(__file__))[0]
    sys.path.append(G_PATH + '/../../')
    os.environ['DJANGO_SETTINGS_MODULE'] = 'MobileService.settings'
    from django.conf import settings
from django.conf import settings

common_logger = settings.COMMON_DATA['mobile_logger']


def OpenUrl(url):
    try:
        req = urllib2.Request(url)
        #req.add_header('Accept-Encoding', 'gzip, deflate')
        response = urllib2.urlopen(req)
        the_page = response.read()
    except Exception,e :
        print e
        return None
    else:
        return the_page
        
def PostUrl(url, data):
    try:
        params = urllib.urlencode(data)
        req = urllib2.Request(url,params)
        response = urllib2.urlopen(req)
        the_page = response.read()
    except Exception,e :
        print e
        common_logger.error('PostUrl %s'%(e))
        return None
    else:
        return the_page

def PostUrlStringData(url, data):
    try:
        req = urllib2.Request(url,data)
        response = urllib2.urlopen(req)
        the_page = response.read()
    except Exception,e :
        print e
        return None
    else:
        return the_page
        
def OpenHttpUrl(url, conn):
    try:
        conn.connect()
        header = {'Connection': 'Keep-Alive', 'Accept-Encoding' : 'gzip, deflate'}
        conn.request('GET', url, headers=header)
        resp = conn.getresponse()
        ret_data = resp.read()
    except Exception,e :
        print e
        return None
    else:
        return ret_data

def get_short_url(url):
    input_url = 'http://qqurl.com/create/?url=' + url
    print input_url
    ret_data = OpenUrl(input_url)
    try:
        print ret_data
        if ret_data:
            ret_dict = json.loads(ret_data)
            return ret_dict.get('short_url', '')
        return ''
    except Exception,e:
        print e
        return ''
    return ''
    
if __name__ == '__main__':
    print get_short_url('https://test.mobiles.xinwo.com/activity/get_lottery_page/?id=8282ed1e-c713-11e5-aa17-0019b9e05348')
        