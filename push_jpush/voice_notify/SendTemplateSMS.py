#coding=utf-8

from MobileService.voice_notify.CCPRestSDK import REST
import ConfigParser

####���ʺ�
accountSid= 'aaf98f8946274232014640d3e0d210cd';

####���ʺ�Token
accountToken= 'fa5203faecbc4ab1ba2b9674707b9974';

####Ӧ��Id
appId='aaf98f89462742320146415320841126';

#�����ַ����ʽ���£�����Ҫдhttp://
serverIP='app.cloopen.com';

#����˿� 
serverPort='8883';

#REST�汾��
softVersion='2013-12-26';

  # ����ģ�����
  # @param to �ֻ�����
  # @param datas �������� ��ʽΪ���� ���磺{'12','34'}���粻���滻���� ''
  # @param $tempId ģ��Id

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

            
#sendTemplateSMS(�ֻ�����,��������,ģ��Id)