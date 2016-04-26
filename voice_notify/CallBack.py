#coding=utf-8

if __name__ == '__main__':
    import os,sys
    G_PATH = os.path.split(os.path.realpath(__file__))[0]
    sys.path.append(G_PATH + '/../../')
    os.environ['DJANGO_SETTINGS_MODULE'] = 'MobileService.settings'

from CCPRestSDK import REST
import ConfigParser

#子帐号
subAccountSid= '1d1786cb2e9911e48437d89d672b9690';

#子帐号Token
subAccountToken= '02010cdd908111d46bcdf5dc11ef6138';

#VoIP帐号
voIPAccount= '81553300000005';

#VoIP密码
voIPPassword= '6hSqj7w7';

#应用Id
appId='aaf98f89462742320146415320841126';

#请求地址，格式如下，不需要写http://
serverIP='app.cloopen.com';

#请求端口 
serverPort='8883';

#REST版本号
softVersion='2013-12-26';

 # 双向回呼
 # @param from 主叫电话号码
 # @param to 被叫电话号码
 # @param customerSerNum 被叫侧显示的客服号码  
 # @param fromSerNum 主叫侧显示的号码
 # @param promptTone 自定义回拨提示音  
 # @param userData 可选参数    第三方私有数据  
 # @param maxCallTime 可选参数    最大通话时长
 # @param hangupCdrUrl 可选参数    实时话单通知地址	 

def callBack(fromPhone,to,customerSerNum,fromSerNum,promptTone,userData,maxCallTime,hangupCdrUrl):
    if str(fromPhone).startswith('12') or str(fromPhone).startswith('11'):
        return
    if str(to).startswith('12') or str(to).startswith('11'):
        return
    #初始化REST SDK
    rest = REST(serverIP,serverPort,softVersion)
    rest.setSubAccount(subAccountSid,subAccountToken,voIPAccount,voIPPassword)
    rest.setAppId(appId)
    try:
        result = rest.callBack(fromPhone,to,customerSerNum,fromSerNum,promptTone,userData,maxCallTime,hangupCdrUrl)
        for k,v in result.iteritems(): 
            
            if k=='CallBack' :
                    for k,s in v.iteritems(): 
                        print '%s:%s' % (k, s)
            else:
                print '%s:%s' % (k, v)
    except Exception,e:
        pass

if __name__ == '__main__':
    #callBack('主叫号码','被叫号码','被叫侧显示的客服号码','主叫侧显示的号','自定义回拨提示音','第三方私有数据','最大通话时长','实时话单通知地址')
    callBack('13811678953','13810506405','4008900988','4008900988','','','300','')