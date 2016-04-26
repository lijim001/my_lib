#coding=utf-8

if __name__ == '__main__':
    import os,sys
    G_PATH = os.path.split(os.path.realpath(__file__))[0]
    sys.path.append(G_PATH + '/../../')
    os.environ['DJANGO_SETTINGS_MODULE'] = 'MobileService.settings'

from CCPRestSDK import REST
import ConfigParser

#���ʺ�
subAccountSid= '1d1786cb2e9911e48437d89d672b9690';

#���ʺ�Token
subAccountToken= '02010cdd908111d46bcdf5dc11ef6138';

#VoIP�ʺ�
voIPAccount= '81553300000005';

#VoIP����
voIPPassword= '6hSqj7w7';

#Ӧ��Id
appId='aaf98f89462742320146415320841126';

#�����ַ����ʽ���£�����Ҫдhttp://
serverIP='app.cloopen.com';

#����˿� 
serverPort='8883';

#REST�汾��
softVersion='2013-12-26';

 # ˫��غ�
 # @param from ���е绰����
 # @param to ���е绰����
 # @param customerSerNum ���в���ʾ�Ŀͷ�����  
 # @param fromSerNum ���в���ʾ�ĺ���
 # @param promptTone �Զ���ز���ʾ��  
 # @param userData ��ѡ����    ������˽������  
 # @param maxCallTime ��ѡ����    ���ͨ��ʱ��
 # @param hangupCdrUrl ��ѡ����    ʵʱ����֪ͨ��ַ	 

def callBack(fromPhone,to,customerSerNum,fromSerNum,promptTone,userData,maxCallTime,hangupCdrUrl):
    if str(fromPhone).startswith('12') or str(fromPhone).startswith('11'):
        return
    if str(to).startswith('12') or str(to).startswith('11'):
        return
    #��ʼ��REST SDK
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
    #callBack('���к���','���к���','���в���ʾ�Ŀͷ�����','���в���ʾ�ĺ�','�Զ���ز���ʾ��','������˽������','���ͨ��ʱ��','ʵʱ����֪ͨ��ַ')
    callBack('13811678953','13810506405','4008900988','4008900988','','','300','')