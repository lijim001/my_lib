#coding=utf-8

if __name__ == '__main__':
    import os,sys
    G_PATH = os.path.split(os.path.realpath(__file__))[0]
    sys.path.append(G_PATH + '/../../')
    os.environ['DJANGO_SETTINGS_MODULE'] = 'MobileService.settings'
    
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

  # ������֤��
  # @param verifyCode ��֤�����ݣ�Ϊ���ֺ�Ӣ����ĸ�������ִ�Сд������4-8λ
  # @param playTimes ���Ŵ�����1��3��
  # @param to ���պ���
  # @param displayNum ��ʾ�����к���
  # @param respUrl ������֤��״̬֪ͨ�ص���ַ����ͨѶƽ̨�����Url��ַ���ͺ��н��֪ͨ

def voiceVerify(verifyCode,playTimes,to,displayNum,respUrl):
    #��ʼ��REST SDK
    try:
        rest = REST(serverIP,serverPort,softVersion)
        rest.setAccount(accountSid,accountToken)
        rest.setAppId(appId)
        
        result = rest.voiceVerify(verifyCode,playTimes,to,displayNum,respUrl)
        for k,v in result.iteritems(): 
            
            if k=='VoiceVerify' :
                    for k,s in v.iteritems(): 
                        print '%s:%s' % (k, s)
            else:
                print '%s:%s' % (k, v)
    except Exception,e:
        print e
   
if __name__ == '__main__':
    voiceVerify('123456','3','13811678953', '4008900988','')