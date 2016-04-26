#coding=utf-8

if __name__ == '__main__':
    import os,sys
    G_PATH = os.path.split(os.path.realpath(__file__))[0]
    sys.path.append(G_PATH + '/../../')
    os.environ['DJANGO_SETTINGS_MODULE'] = 'MobileService.settings'
    
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

  # 语音验证码
  # @param verifyCode 验证码内容，为数字和英文字母，不区分大小写，长度4-8位
  # @param playTimes 播放次数，1－3次
  # @param to 接收号码
  # @param displayNum 显示的主叫号码
  # @param respUrl 语音验证码状态通知回调地址，云通讯平台将向该Url地址发送呼叫结果通知

def voiceVerify(verifyCode,playTimes,to,displayNum,respUrl):
    #初始化REST SDK
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