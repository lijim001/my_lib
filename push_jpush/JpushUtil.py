#coding=utf-8

import jpush as jpush
import sys, os
import simplejson as json

G_PATH = os.path.split(os.path.realpath(__file__))[0]
sys.path.append(G_PATH + '/../../')
os.environ['DJANGO_SETTINGS_MODULE'] = 'MobileService.settings'

from django.conf import settings

from MobileService.push_jpush.JpushException import JpushException

class JpushUtil(object):

    #Jpush错误
    JPUSH_AUDIENCE_EMPTY = 1
    MESSAGE_DICT_EMPTY = 2
    MESSAGE_CONTENT_EMPTY = 3

    def __init__(self, app_key, master_secret):
        self.app_key = app_key
        self.master_secret = master_secret
        self._jpush = jpush.JPush(app_key, master_secret)

    def pushMessage(self, audience, message_dict):
        try:
            push = self._jpush.create_push()
            if not audience:
                raise JpushException('audience is empty', self.JPUSH_AUDIENCE_EMPTY)
            if audience == 'all':
                push.audience = jpush.all_
            else:
                push.audience = jpush.audience(
                    jpush.alias(*audience)
                )
            #android_msg = jpush.android(alert="Hello, android msg")
            if not message_dict:
                raise JpushException('message_dict is empty', self.MESSAGE_DICT_EMPTY)

            alert_message = message_dict.get('content', '')
            if not alert_message:
                raise JpushException('message_content is empty', self.MESSAGE_CONTENT_EMPTY)
            msg_content = json.dumps(message_dict)

            push.message = jpush.message(msg_content=msg_content)
            push.platform = jpush.all_
            return push.send()
        except jpush.common.JPushFailure, e:
            print e
            return False
        ###catch all
        except JpushException, e:
            print str(e)
            return False

        except Exception,e:
            print e
            return False


if __name__ == '__main__':
    #jpush = JpushUtil(app_key='d6a4d59fef6b7fe813743f3b', master_secret='06b9c8fbb96a26509fb10fcd')
    jpush_test = JpushUtil(app_key='80be2efe18c976963966ad7a', master_secret='bde4caa3b01ab6426347bd40')
    #jpush_test.pushMessage(('18618281170_wallet_client',), message_dict={'title': 'hello'})
    #jpush_test.pushMessage(('18618281170_wallet_client',), message_dict={'hello': 'ehfuck'})
    #jpush_test.pushMessage(('18618281170_wallet_client',), message_dict={'content': 'hello', 'title': 'hello'})
    #jpush_test.pushMessage((), message_dict={'content': 'hello', 'title': 'hello'})
