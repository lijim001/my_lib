#coding=utf-8

import MySQLdb,random,hashlib,time
from datetime import datetime,date,timedelta
import simplejson as json
import os,sys


if __name__ == '__main__':
    G_PATH = os.path.split(os.path.realpath(__file__))[0]
    sys.path.append(G_PATH + '/../../')
    os.environ['DJANGO_SETTINGS_MODULE'] = 'MobileService.settings'
    from django.conf import settings
    
from MobileService.util.HttpUtil import *
from MobileService.util.DbUtil import *
from MobileService.business_user.db_business_user import DbBusinessUser
from MobileService.util.LotteryUtil import DbLottery
from MobileService.voice_notify.SendTemplateSMS import *

RONGLIAN_KEY_DICT = {
    25656 : u'店员认证通过',
    43781 : u'店员奖励已发放',
    48526 : u'顾客预约成功',
    48527 : u'顾客预约失败',
}

class YiMeiUtil(object):
    def __init__(self,cdkey, password, host = 'http://sdk999ws.eucp.b2m.cn:8080/sdkproxy/', logger = None):
        self.cdkey = cdkey
        self.password = password
        self.logger = logger
        self.host = host
        
    def register(self):
        url = self.host + 'regist.action'
        param = {}
        param['cdkey'] = self.cdkey
        param['password'] = self.password
        print PostUrl(url, param)
    
    def register_ent(self):
        url = self.host + 'registdetailinfo.action'
        param = {}
        param['cdkey'] = self.cdkey
        param['password'] = self.password
        param['ename'] = "北京新窝在线科技有限公司"
        param['linkman'] = "吴振宇"
        param['phonenum'] = "4008900988"
        param['mobile'] = "13811678953"
        param['email'] = "wuzhenyu@xinwo.com"
        param['fax'] = "65307533"
        param['address'] = "北京市朝阳区建国路89号华贸中心商务楼15号楼1502室"
        param['postcode'] = "100025"
        print PostUrl(url, param)
        
    def send_message(self, phone, message):
        url = self.host + 'sendsms.action'    
        param = {}
        param['cdkey'] = self.cdkey
        param['password'] = self.password
        param['phone'] = phone
        param['message'] = '【新窝消息】' + message
        if self.logger:
            self.logger.info('YiMeiUtil send message to %s %s'%(str(phone), param['message']))
        print PostUrl(url, param)
    
    def get_remainder(self):
        url = self.host + 'querybalance.action'
        param = {}
        param['cdkey'] = self.cdkey
        param['password'] = self.password
        return PostUrl(url, param)
    
    def get_report(self):
        url = self.host + 'getreport.action'
        param = {}
        param['cdkey'] = self.cdkey
        param['password'] = self.password
        return PostUrl(url, param)
        
    def get_mo(self):
        url = self.host + 'getmo.action'
        param = {}
        param['cdkey'] = self.cdkey
        param['password'] = self.password
        return PostUrl(url, param)        

REWARD_USER_LIST = [
    '13001937382',
    ]

class DbNoteSend(DbUtil):
    def __init__(self, database, logger=None):
        DbUtil.__init__(self, database, logger)

    def get_real_business_user_phone(self, last_user_id=0, num=100):
        self.get_db_connect()
        sql = 'select user_id,telephone,category from user_shop where user_state=2 and user_id > %s order by id limit %s'%(str(last_user_id), str(num))
        try:
            ret_list = []
            max_id = 0
            count = self.cursor.execute(sql)
            if count > 0:
                self.cursor.scroll(0, mode='absolute')
                results = self.cursor.fetchall()
                self.release_db_connect()
                for result in results:
                    if max_id < int(result[0]):
                        max_id = int(result[0])
                    ret_list.append((result[1],result[2]))
                return (ret_list, max_id)
            else:
                self.release_db_connect()
                return ([], None)
        except Exception,e:
            if self.logger:
                self.logger.error('get_real_business_user_phone except %s'%(e))
            self.release_db_connect()
            return ([], None)

    def get_inquire_category_dict(self, start_num, end_num):
        self.get_db_connect()
        sql = 'select category,count(*) from user_inquire_record where action="create_session" and create_time > "%s" and create_time < "%s" group by category' \
        %(str(start_num), str(end_num))
        try:
            ret_dict = {}
            count = self.cursor.execute(sql)
            if count > 0:
                self.cursor.scroll(0, mode='absolute')
                results = self.cursor.fetchall()
                self.release_db_connect()
                for result in results:
                    ret_dict[result[0]] = result[1]
                return ret_dict
            else:
                self.release_db_connect()
                return {}
        except Exception,e:
            if self.logger:
                self.logger.error('get_inquire_category_dict except %s'%(e))
            self.release_db_connect()
            return {}

class NoteSendUtil():
    def __init__(self, database):
        self.mobile_db = database['mobile_db']
        self.info_logger = database['mobile_logger']
        self.purchase_manager, self.finance = database['note_sender']
        self.promote = database['note_receive']

    def send_welcome_business(self, phone):
        message = '恭喜您，已成功注册新窝店员。您专属新窝客服人员会在24小时内与您联系，为您提供使用帮助，请保持通话畅通。'
        #self.send_note_phone(phone, message)
        self.send_message_with_ronglian(phone, 25654, [])

    def send_invite_business(self, from_phone, phone):
        return
        handler = DbBusinessUser(self.mobile_db, self.info_logger)
        user_info = handler.get_business_user_by_phone(from_phone)
        name = user_info.get('name', '')
        message = '您已成功邀请了%s注册新窝店员，新窝为您发放50元奖励。'%(name.encode('utf8','ignore'))
        self.send_note_phone(phone, message)

    def send_task_business(self, phone, from_phone, state = 1):
        return
        if state == 1:
            handler = DbBusinessUser(self.mobile_db, self.info_logger)
            user_info = handler.get_business_user_by_phone(from_phone)
            name = user_info.get('name', '')
            message = '您已成功邀请了%s注册完成并领取红包，再送出一个红包就能完成任务了'%(name.encode('utf8','ignore'))
        elif state == 2:
            message = '任务完成，100元奖励已可以领取，此后您每邀请一位同事完成注册新窝钱包，就可以直接获得50元奖励。'
        self.send_note_phone(phone, message)

    def send_commision_settle_business(self, phone, is_first = True):
        handler = DbBusinessUser(self.mobile_db, self.info_logger)
        user_info = handler.get_business_user_by_phone(phone)
        name = user_info.get('name', '')
        message = '%s您好，新窝工作人员已经开始为您处理奖励提现，预计在3个工作日内到账，如有问题请拨打客服电话：4008900988'%(name.encode('utf8','ignore'))
        #self.send_note_phone(phone, message)
        self.send_message_with_ronglian(phone, 25655, [name])

    def send_invite_custom(self, phone, from_phone):
        return
        from_phone = str(from_phone)
        from_phone = '%s****%s'%(from_phone[:3], from_phone[-3:])
        message = '您已成功邀请了顾客（%s）注册新窝钱包，新窝为您发放50元奖励。'%(from_phone)
        self.send_note_phone(phone, message)

    def send_order_payed(self, phone, from_phone):
        return
        from_phone = str(from_phone)
        from_phone = '%s****%s'%(from_phone[:3], from_phone[-3:])
        message = '您邀请的顾客（%s）通过新窝钱包交易成功，新窝为您发放150元奖励。'%(from_phone)
        self.send_note_phone(phone, message)

    def send_business_verify(self, phone):
        phone = str(phone)
        message = '恭喜您被认证为新窝店员，新窝各种奖励活动等您拿到手软。'
        #self.send_note_phone(phone, message)
        self.send_message_with_ronglian(phone, 25656, [])
    
    def send_message_with_ronglian(self, phone, template_id, data_list):
        if phone.startswith('11') or phone.startswith('12'):
            return False
        sendTemplateSMS(phone, data_list, template_id)
        self.info_logger.info('send note with ronglian %s %s'%(str(phone), str(template_id)))
        return True
    def send_pre_invite_business(self, phone, upper_phone, url):
        handler = DbBusinessUser(self.mobile_db, self.info_logger)
        user_info = handler.get_business_user_by_phone(upper_phone)
        name = user_info.get('name', '')
        url = 'http://t.cn/RZABjJ2'
        message = '您的同事%s为您推荐一款店员必备app，促进成单，顾客送上门，还有各种红包，下载地址：%s'%(name.encode('utf8','ignore'), str(url))
        #self.send_note_phone(phone, message)
        sendTemplateSMS(phone, [name], 24316)
        self.info_logger.info('send note %s'%(message))

    def send_pre_invite_customer(self, phone, upper_phone, url='', current_price=0):
        handler = DbBusinessUser(self.mobile_db, self.info_logger)
        user_info = handler.get_business_user_by_phone(upper_phone)
        name = user_info.get('name', '')
        url = 'http://t.cn/RZAB70C'
        if current_price:
            message = '您好，店员%s为您发送了一笔%s元的订单，请下载安装新窝钱包，并在客户端内完成支付，客户端下载：%s'%(name.encode('utf8','ignore'), str(current_price),str(url))
            #self.send_note_phone(phone, message)
            sendTemplateSMS(phone, [name,str(current_price)], 24314)
        else:
            message = '您好，店员%s为您发送了一笔订单，请下载安装新窝钱包，并在客户端内完成支付，客户端下载：%s'%(name.encode('utf8','ignore'), str(url))
            #self.send_note_phone(phone, message)
            sendTemplateSMS(phone, [name], 25326)
        self.info_logger.info('send note %s'%(message))

    def send_invited_customer(self, phone, upper_phone, url='', current_price=0):
        handler = DbBusinessUser(self.mobile_db, self.info_logger)
        user_info = handler.get_business_user_by_phone(upper_phone)
        name = user_info.get('name', '')
        url = 'http://t.cn/RZAB70C'
        if current_price:
            message = '您好，店员%s为您创建一笔总价为%s元的订单，请您在新窝钱包客户端完成支付, 客户端下载: %s'%(name.encode('utf8', 'ignore'), str(current_price), str(url))
            sendTemplateSMS(phone, [name,str(current_price)], 25327)
        else:
            message = '您好，店员%s为您创建一笔订单，请您在新窝钱包客户端完成支付, 客户端下载: %s'%(name.encode('utf8', 'ignore'), str(url))
            sendTemplateSMS(phone, [name], 25328)
        #self.send_note_phone(phone, message)
        self.info_logger.info('send note %s'%(message))

    def send_customer_order(self, phone, upper_phone, current_price=0, invited=False, pay_type=None):
        handler = DbBusinessUser(self.mobile_db, self.info_logger)
        user_info = handler.get_business_user_by_phone(upper_phone)
        name = user_info.get('name', '')
        url = 'http://t.cn/RZAB70C'
        code = 0
        if pay_type is None:
            if invited:
                code = 25327
            else:
                code = 24314
        elif pay_type == 0:
            code = 43785
        elif pay_type == 1:
            code = 43784
        if code:
            sendTemplateSMS(phone, [name, str(current_price)], code)
            
        self.info_logger.info('send send_customer_order code: %s'%(str(code)))

    def send_sales_reward_sent(self, phone):
        code = 43781
        sendTemplateSMS(phone, [], code)
        self.info_logger.info('send send_sales_reward_sent code: %s'%(str(code)))
        
    def send_pre_invite_business_no_materal(self, phone, upper_phone):
        phone = str(phone)
        phone = '%s****%s'%(phone[:3], phone[-3:])
        message = '您邀请的%s没有完成注册新窝钱包，请帮助他完成注册后才能获得相应奖励。'%(str(phone))
        self.send_note_phone(upper_phone, message)

    def send_note_phone_old(self, phone_number, message):
        url = 'http://shop.xinwo.com/index.php?module=api&action=ytx&fn=send&fr=mxinwo&mobile=%s&message='%(str(phone_number))
        url = url + message
        self.info_logger.info('send note to phone %s %s'%(str(phone_number), str(message)))
        OpenUrl(url)

    def send_note_phone(self, phone_number, message):
        if len(str(phone_number)) < 11:
            self.info_logger.info('send note to phone(no) %s %s'%(str(phone_number), str(message)))
            return 
        self.send_note_phone_second_tunel(phone_number, message)

    def send_note_phone_first_tunel(self, phone_number, message):
        if str(phone_number).startswith('11'):
            return    
        self.info_logger.info('send note to phone %s %s'%(str(phone_number), str(message)))
        handler = YiMeiUtil('9SDK-EMY-0999-JBXMR', 'b4bb2d221a2d9cf55fa7e2904cd648ee')
        handler.send_message(str(phone_number), message)
        
    def send_note_phone_second_tunel(self, phone_number, message):
        if str(phone_number).startswith('11'):
            return
        self.info_logger.info('send note to phone %s %s'%(str(phone_number), str(message)))
        handler = YiMeiUtil('6SDK-EMY-6688-KHXUO', '487574', 'http://sdk4report.eucp.b2m.cn:8080/sdkproxy/')
        handler.send_message(str(phone_number), message)

    def send_payed_message(self, sales, customer_phone, total_money, have_lottery, settle_flag, orig_order_number):
        if have_lottery:
            user_phone = '%s*****%s'%(customer_phone[:3], customer_phone[-3:])
            message = '恭喜您完成一笔收款，顾客%s已成功支付%s元。您获得一次抽取交易红包的机会，立即登录客户端抽取吧！'%(str(user_phone), str(total_money))
            self.send_note_phone_first_tunel(sales, message)
            #self.send_message_with_ronglian(sales, 25677, [str(user_phone), str(total_money)])
        if settle_flag:
            message = '恭喜您完成一笔收款，新窝财务人员将在1个工作日将款项打至贵公司银行帐号中，请知悉。'
            finance_message = '有一笔总价为%s元的交易已完成，顾客手机号：%s，请在1个工作日内完成打款。'%(str(total_money),str(customer_phone))
            #self.send_note_phone(sales, message)
            #self.send_message_to_finance(finance_message)
            # self.send_message_with_ronglian(sales, 25678, [])
            # self.send_message_to_finance_with_ronglian(25679, [str(total_money),str(customer_phone)])
        else:
            message = '恭喜您完成一笔收款，新窝财务人员将按合作账期规定，将交易款项打至贵公司银行账户内，请知悉。'
            purchase_message = '您所负责的供应商店员与顾客%s完成一笔%s元交易。请在后台及时审核交易。'%(str(customer_phone),str(total_money))
            #self.send_note_phone(sales, message)
            #self.send_message_to_purchase_manager(purchase_message)
            
            # self.send_message_with_ronglian(sales, 25680, [])
            # self.send_message_to_finance_with_ronglian(25681, [str(customer_phone),str(total_money)])
    
    def send_promote_invite_message(self, phone_number, from_phone):
        message = '新窝工作人员为您提供的下载地址：http://t.cn/RZABjJ2'
        #self.send_note_phone(phone_number, message)
        self.send_message_with_ronglian(phone_number, 25664, [])
    
    def send_promote_customer_order_shop(self, order_id):
        from MobileService.shop.db_shop import DbShop
        handler = DbShop(self.mobile_db, self.info_logger)
        order_detail = handler.get_shop_order_detail(order_id)
        user_phone = order_detail.get('user_phone', '')
        order_time = order_detail.get('order_time', '')
        shop_address = order_detail.get('shop_address', '')
        service_phone = order_detail.get('service_phone', '')
        if not service_phone:
            return False
        phone = '%s****%s'%(user_phone[:3], user_phone[-4:])
        data_list = [shop_address, order_time, phone]
        
        self.send_message_with_ronglian(service_phone, 56172, data_list)
        return True
    
    def send_message_to_purchase_manager(self, message):
        self.send_note_phone(self.purchase_manager, message)
        
    def send_message_to_purchase_manager_with_ronglian(self, template_id, data_list):
        for phone in self.purchase_manager.split(','):
            self.send_message_with_ronglian(phone, template_id, data_list)
        
    def send_message_to_finance(self, message):
        self.send_note_phone(self.finance, message)

    def send_message_to_finance_with_ronglian(self, template_id, data_list):
        for phone in self.finance.split(','):
            self.send_message_with_ronglian(phone, template_id, data_list)
            
    def send_message_to_promote(self, message):
        phone_list = self.promote.split(',')
        for user_phone in phone_list:
            self.send_note_phone(user_phone,  message)
    
    def send_message_to_pre_h5_inquire(self, user_phone, password):
        pass
        
    def send_subscribe_message_business_user(self, send_phone, user_phone, order_time):
        data_list = []
        phone = '%s*****%s'%(user_phone[:3], user_phone[-3:])
        data_list = [phone, order_time]
        self.send_message_with_ronglian(send_phone, 48486, data_list)

    def send_subscribe_message_customer_user(self, send_phone, brand_name, shop_name, order_time, fail = 0):
        data_list = []
        if not fail:
            month = order_time.month
            day = order_time.day
            data_list = [str(month), str(day), brand_name, shop_name]
            self.send_message_with_ronglian(send_phone, 48526, data_list)
        else:
            data_list = [brand_name, shop_name]
            self.send_message_with_ronglian(send_phone, 48527, data_list)
    
    def send_subscribe_failed_message_purchase(self, send_phone, brand_name, shop_name, reason=''):
        shop_info = brand_name + u'（' + shop_name + u'）'
        data_list = [shop_info, reason]
        
        self.send_message_with_ronglian(send_phone, 48608, data_list)
    
    def send_random_cutoff_cooperation_sales(self, send_phone, money):
        data_list = [str(money), 'http://t.cn/RZcP6Xn']
        self.send_message_with_ronglian(send_phone, 65260, data_list)

    def send_random_cutoff_non_cooperation_sales(self, send_phone, money):
        data_list = [str(money), 'http://t.cn/RZcP6Xn']
        self.send_message_with_ronglian(send_phone, 65262, data_list)

    def send_customer_create_order_sales(self, send_phone, money):
        data_list = [str(money), 'http://t.cn/RZcP6Xn']
        self.send_message_with_ronglian(send_phone, 65263, data_list)

    def send_sales_draw_reward(self, send_phone, user_phone, url):
        data_list = [str(user_phone), url]
        self.send_message_with_ronglian(send_phone, 65267, data_list)
        
    def send_all_business_user(self, message):
        handler = DbUtil(settings.COMMON_DATA['mobile_db'])
        last_user_id = 0
        PER_FETCH_NUM = 20
        for i in range(1000):
            (phone_list, max_id) = handler.get_business_phones(0, last_user_id, PER_FETCH_NUM)
            if not phone_list:
                break
            for phone_number in phone_list:
                self.info_logger.info('send all note to phone %s'%(str(phone_number)))
                self.send_note_phone(phone_number, message)
                time.sleep(0.1)
            last_user_id = max_id

    def handle_inquire_one_user(self, category_info_dict, phone_number, category):
        if not category:
            return False
        user_category_list = category.split(',')
        try:
            user_category_list.remove('')
        except:
            pass
        category_count = 0
        for user_category in user_category_list:
            category_count += category_info_dict.get(user_category, 0)
        if not category_count:
            return False

        if len(user_category_list) > 1:
            message = '你好，今天有%s位北京装修顾客求购了你家的产品，查看：http://t.cn/RZcP6Xn'%(str(category_count))
        else:
            message = '你好，今天有%s位北京装修顾客求购你家的%s，查看：http://t.cn/RZcP6Xn'%(str(category_count), user_category_list[0].encode('utf8', 'ignore'))
        self.info_logger.info('send inquire to phone %s'%(str(phone_number)))
        self.send_note_phone(phone_number, message)
        return True

    def send_inquire_business_user(self):
        log_handler = DbNoteSend(settings.COMMON_DATA['log_db'])
        category_info_dict = log_handler.get_inquire_category_dict(str(date.today()), str(date.today() + timedelta(days=1)))
        handler = DbNoteSend(settings.COMMON_DATA['mobile_db'])
        last_user_id = 0
        PER_FETCH_NUM = 20
        for i in range(1000):
            (phone_list, max_id) = handler.get_real_business_user_phone(last_user_id, PER_FETCH_NUM)
            if not phone_list:
                break
            for phone_number, category in phone_list:
                if str(phone_number) in ['13910784806','15311853797']:
                    continue
                self.handle_inquire_one_user(category_info_dict, phone_number, category)
                time.sleep(0.1)
            last_user_id = max_id

    def send_all_customer_user(self, message):
        handler = DbUtil(settings.COMMON_DATA['mobile_db'])
        last_user_id = 0
        PER_FETCH_NUM = 20
        for i in range(1000):
            (phone_list, max_id) = handler.get_customer_phones(last_user_id, PER_FETCH_NUM)
            if not phone_list:
                break
            for phone_number in phone_list:
                self.info_logger.info('send all note to phone %s'%(str(phone_number)))
                self.send_note_phone(phone_number, message)
                #print phone_number
                time.sleep(0.1)
            last_user_id = max_id

    def send_have_invite_business_user(self, message):
        handler = DbUtil(settings.COMMON_DATA['mobile_db'])
        last_user_id = 0
        PER_FETCH_NUM = 20
        for i in range(1000):
            (phone_list, max_id) = handler.get_business_phones(0, last_user_id, PER_FETCH_NUM)
            if not phone_list:
                break
            for phone_number in phone_list:
                invite_num = handler.get_invite_num(phone_number)
                if invite_num == 0:
                    print 'no invite action %s'%(str(phone_number))
                    continue
                self.info_logger.info('send_have_invite_business_user %s'%(str(phone_number)))
                self.send_note_phone(phone_number, message)
                time.sleep(0.1)
            last_user_id = max_id

    def send_ios_business_user(self, message):
        handler = DbUtil(settings.COMMON_DATA['mobile_db'])
        last_user_id = 0
        PER_FETCH_NUM = 20
        for i in range(1000):
            (phone_list, max_id) = handler.get_business_phones(0, last_user_id, PER_FETCH_NUM)
            if not phone_list:
                break
            for phone_number in phone_list:
                platform = handler.get_business_user_platform(phone_number)
                if platform == 'android':
                    print 'android platform user %s'%(str(phone_number))
                    continue
                self.info_logger.info('send_ios_business_user %s'%(str(phone_number)))
                self.send_note_phone(phone_number, message)
                time.sleep(0.1)
            last_user_id = max_id

    def send_no_material_business_user(self, message):
        handler = DbUtil(settings.COMMON_DATA['mobile_db'])
        last_user_id = 0
        PER_FETCH_NUM = 20
        for i in range(1000):
            (phone_list, max_id) = handler.get_business_phones(0, last_user_id, PER_FETCH_NUM)
            if not phone_list:
                break
            for phone_number in phone_list:
                user_info = handler.get_business_user_by_phone(phone_number)
                if not user_info or user_info.get('shop_name', ''):
                    print 'has material user %s'%(str(phone_number))
                    continue
                self.info_logger.info('send_no_material_business_user %s'%(str(phone_number)))
                self.send_note_phone(phone_number, message)
                time.sleep(0.1)
            last_user_id = max_id

    def send_have_no_invite_business_user(self, message):
        handler = DbUtil(settings.COMMON_DATA['mobile_db'])
        last_user_id = 0
        PER_FETCH_NUM = 20
        for i in range(1000):
            (phone_list, max_id) = handler.get_business_phones(0, last_user_id, PER_FETCH_NUM)
            if not phone_list:
                break
            for phone_number in phone_list:
                invite_num = handler.get_invite_num(phone_number)
                if invite_num > 0:
                    print 'have invite action %s'%(str(phone_number))
                    continue
                self.info_logger.info('send_have_no_invite_business_user %s'%(str(phone_number)))
                self.send_note_phone(phone_number, message)
                time.sleep(0.1)
            last_user_id = max_id

    def send_lottery_message(self, type):
        handler = DbLottery(settings.COMMON_DATA['mobile_db'])
        info_list = handler.get_lottery_info_list_by_send_message(type)
        for user in info_list:
            user_phone = user.get('phone', '')
            id = user.get('id', '')
            if type == 10:
                self.send_note_phone(user_phone, '领取奖品申请已收到，只要邀请对象为北京家居店员，数量达到6个，奖品在5个工作日后派发，还请耐心等待，有任何问题可拨打400-890-0988。')
            elif type == 11:
                self.send_note_phone(user_phone, '领取奖品申请已收到，只要邀请对象为北京家居店员，数量达到12个，奖品在5个工作日后派发，还请耐心等待，有任何问题可拨打400-890-0988。')
            if id:
                handler.update_lottery_send_message(id)

    def send_message_to_list(self, user_list, message):
        for user in user_list:
            self.send_note_phone(user, message)
            time.sleep(0.1)

    def send_message_files(self, file_name, message):
        fp = open(file_name, 'r')
        for line in fp:
            phone = line.strip()
            print 'handle %s|'%(str(phone))
            self.send_note_phone(phone, message)
            time.sleep(0.1)

def test_inquire():
    log_handler = DbNoteSend(settings.COMMON_DATA['log_db'])
    category_info_dict = log_handler.get_inquire_category_dict(str(date.today()), str(date.today() + timedelta(days=1)))
    handler = NoteSendUtil(settings.COMMON_DATA)
    print category_info_dict
    handler.handle_inquire_one_user(category_info_dict, '13811678953', u'浴缸,窗,油漆涂料,家居用品,壁纸,家居环保')
    #handler.handle_inquire_one_user(category_info_dict, '13811678953', u'浴缸')

def send_message_users(user_list, message):
    handler = YiMeiUtil('6SDK-EMY-6688-KHXUO', '487574', 'http://sdk4report.eucp.b2m.cn:8080/sdkproxy/')
    phone = ','.join(user_list)
    #print handler.get_remainder()
    print 'send message users'
    handler.send_message(phone, message)
    #print handler.get_remainder()

def send_tt_message(message):
    todo_phone = []
    for phone in REWARD_USER_LIST:
        todo_phone.append(phone)
        if len(todo_phone) >= 50:
            send_message_users(todo_phone, message)
            time.sleep(2)
            todo_phone = []
    if len(todo_phone) > 0:
        send_message_users(todo_phone, message)


if __name__ == '__main__':
    from_phone = '13811678953'
    phone = '18611408491'
    phone = '18612111315'
    test_send_list = [13811678953]

    handler = NoteSendUtil(settings.COMMON_DATA)
    #handler.send_promote_customer_order_shop(1188)
    #handler.send_payed_message('18618281170', '18618281170', 1000, 1, 0, '12312312')

    
