#coding=utf-8

from MobileService.voice_notify.CCPRestSDK import REST
import ConfigParser

####主帐号
accountSid= 'aaf98f8946274232014640d3e0d210cd';

####主帐号Token
accountToken= 'fa5203faecbc4ab1ba2b9674707b9974';

####应用Id
appId='aaf98f89462742320146415320841126';

#请求地址，格式如下，不需要写http://
serverIP='app.cloopen.com';

#请求端口 
serverPort='8883';

#REST版本号
softVersion='2013-12-26';

  # 发送模板短信
  # @param to 手机号码
  # @param datas 内容数据 格式为数组 例如：{'12','34'}，如不需替换请填 ''
  # @param $tempId 模板Id

def sendTemplateSMS(to,datas,tempId):
    try:
        rest = REST(serverIP,serverPort,softVersion)
        rest.setAccount(accountSid,accountToken)
        rest.setAppId(appId)
        
        result = rest.sendTemplateSMS(to,datas,tempId)
        for k,v in result.iteritems(): 
            
            if k=='templateSMS' :
                    for k,s in v.iteritems(): 
                        print '%s:%s' % (k, s)
            else:
                print '%s:%s' % (k, v)
    except Exception,e:
        print e

            
#sendTemplateSMS(手机号码,内容数据,模板Id)