#coding=utf-8

import urllib,os,time
import urllib2,cookielib,httplib
import simplejson as json

def OpenUrl(url):
    try:
        req = urllib2.Request(url)
        req.add_header('Accept-Encoding', 'gzip, deflate')
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

TEST_HOST_ADDR = 'https://mobiles.xinwo.com/'
TEST_HOST_ADDR = 'https://test.mobiles.xinwo.com/'
class ServiceTester():
    def __init__(self):
        self.cookies = None
        self.user_id = None
        
    def do_request(self, url, params):
        params['user_id'] = self.user_id
        data = urllib.urlencode(params)
        if not url.startswith('http'):
            url = TEST_HOST_ADDR + url
        oRequest = urllib2.Request(url, data)
        try:
            oRequest.add_header('Cookie', self.cookies)
            retval = urllib2.urlopen(oRequest)
            response = retval.read()
            print 'orig data:'
            print response
            ret_dict = json.loads(response)
            return json.dumps(ret_dict, ensure_ascii=False)
            return ret_dict
        except urllib2.URLError,e:
            if hasattr(e, 'reason'):
                print e.reason
            elif hasattr(e, 'code'):
                print e.code
            if hasattr(e, 'read'):
                print e.read()
        except urllib2.HTTPError,e:
            print e
        return None
        
    def check_result(self, ret_data):
        try:
            print 'ret data:'
            print ret_data
            json.loads(ret_data)
            return True
        except Exception,e:
            print e
            return False
        
class ServiceCustomTester(ServiceTester):
    def __init__(self):
        ServiceTester.__init__(self)
    
    def login(self, user_name, password):
        url = TEST_HOST_ADDR + 'user/login/'
        params = {}
        params["password"] = password
        params["user_name"] = user_name
        data = urllib.urlencode(params)
        oRequest = urllib2.Request(url, data)
        try:
            retval = urllib2.urlopen(oRequest)
            self.cookies = retval.headers["Set-cookie"]
            response = retval.read()
            ret_dict = json.loads(response)
            self.user_id = ret_dict['data']['user_id']
            print 'login cumstom sucess'
        except urllib2.URLError,e:
            if hasattr(e, 'reason'):
                print e.reason
            elif hasattr(e, 'code'):
                print e.code
            if hasattr(e, 'read'):
                print e.read()
        except urllib2.HTTPError,e:
            print e
    
    def test_check_user_exist(self, user_name):
        print '#############'
        url = 'user/check_user_exist/'
        params = {}
        params['user_name'] = user_name
        if self.check_result(self.do_request(url, params)):
            print 'test %s sucess'%(url)
        else:
            print 'test %s failed'%(url)
        print '#############'

    def test_pay_discount(self):
        url = 'user/pay_discount/'
        if self.check_result(self.do_request(url, {})):
            print 'test %s sucess'%(url)        
        else:
            print 'test %s failed'%(url)
    
    def test_pull_order_score(self, order_number):
        url = 'user/pull_order_score/'
        params = {}
        params['order_number'] = order_number
        if self.check_result(self.do_request(url, params)):
            print 'test %s sucess'%(url)
        else:
            print 'test %s failed'%(url)
        print '#############'
        
class ServiceBusinessTester(ServiceTester):
    def __init__(self):
        ServiceTester.__init__(self)
        
    def login(self, user_name, password):
        url = TEST_HOST_ADDR + 'business_user/login/'
        params = {}
        params["password"] = password
        params["user_name"] = user_name
        data = urllib.urlencode(params)
        oRequest = urllib2.Request(url, data)
        try:
            retval = urllib2.urlopen(oRequest)
            self.cookies = retval.headers["Set-cookie"]
            response = retval.read()
            ret_dict = json.loads(response)
            self.user_id = ret_dict['data']['user_id']
        except urllib2.URLError,e:
            if hasattr(e, 'reason'):
                print e.reason
            elif hasattr(e, 'code'):
                print e.code
            if hasattr(e, 'read'):
                print e.read()
        except urllib2.HTTPError,e:
            print e    


if __name__ == '__main__':
    tester = ServiceCustomTester()
    tester.login('13811678953', '123456')
    for i in range(3):
        tester.test_pull_order_score('1418779347648977565')
    #tester.test_pay_discount()
        
        
