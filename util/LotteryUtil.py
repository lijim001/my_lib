#coding=utf-8

import urllib,os,time,random, uuid
import urllib2,cookielib,httplib
from datetime import datetime,date,timedelta
import smtplib,codecs,base64
from email.mime.text import MIMEText

if __name__ == '__main__':
    import os,sys
    G_PATH = os.path.split(os.path.realpath(__file__))[0]
    sys.path.append(G_PATH + '/../../')
    os.environ['DJANGO_SETTINGS_MODULE'] = 'MobileService.settings'
    from django.conf import settings
    
from MobileService.util.DbUtil import DbUtil
#from MobileService.util.PushBaiduUtil import *

REWARD_TYPE_ONE = 10
LOTTERY_TYPE_ONE = 20

mail_host = "smtp.xinwo.com"
mail_user = "postmaster@xinwo.com"
mail_pass = "Xwpost@0116"
from_addr = "postmaster@xinwo.com"

to_list = []
# to_list.append('yangyi@xinwo.com')
# to_list.append('lidaming@xinwo.com')
# to_list.append('xinxin@xinwo.com')
to_list.append('wuzhenyu@xinwo.com')
# to_list.append('liqingwei@xinwo.com')
        
def send_mail(to_list, sub, content):  
    me="hello"+"<postmaster@xinwo.com>"  
    msg = MIMEText(content,_subtype='plain',_charset='gbk')  
    msg['Subject'] = sub  
    msg['From'] = me
    msg['To'] = ";".join(to_list)
    try:  
        server = smtplib.SMTP()  
        server.connect(mail_host)  
        server.login(mail_user,mail_pass)  
        server.sendmail(me, to_list, msg.as_string())  
        server.close()  
        return True  
    except Exception, e:  
        print str(e)  
        return False
        
class DbLottery(DbUtil):
    def __init__(self, database, logger=None):
        DbUtil.__init__(self, database, logger)
        
    def format_lottery_list(self, results):
        ret_dict = {}
        ret_pro_dict = {}
        total_probability = 0
        for result in results:
            id = int(result[0])
            lottery_name = result[1]
            probability = int(result[2])
            ret_dict[id] = lottery_name
            ret_pro_dict[[total_probability, total_probability + probability ]] = id
            total_probability += probability
        return (ret_dict, ret_pro_dict, total_probability)
            
    def get_lottery_list(self, type):
        self.get_db_connect()
        sql = 'select id,lottery_name,probability from lottery_info where type="%s" order by id'%(str(type))
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                ret_list = []
                self.cursor.scroll(0, mode='absolute')
                results = self.cursor.fetchall()
                self.release_db_connect()
                return self.format_lottery_list(results)
            else:
                self.release_db_connect()
                return ({}, {}, 0)
        except Exception,e:
            if self.logger:
                self.logger.error('get_lottery_list except %s'%(e))
            self.release_db_connect()
            return ({}, {}, 0)           

    def add_lottery(self, user_phone, lottery_name, lottery_identifying, app, type):
        self.get_db_connect()
        sql = 'insert into lottery_list (user_phone, lottery_name, lottery_identifying,app, type) values ("%s","%s","%s","%s",%s)'%(str(user_phone), lottery_name, str(lottery_identifying), str(app), str(type))
        try:
            count = self.cursor.execute(sql)
            self.conn.commit()
            self.release_db_connect()
            return True
        except Exception,e:
            if self.logger:
                self.logger.error('add_lottery except %s'%(e))
            self.release_db_connect()    
            return False

    def add_multi_lottery(self, user_phone, lottery_name, lottery_identifying, app, type, order_number=None):
        self.get_db_connect()
        sql = 'insert into lottery_multi_list (user_phone, lottery_name, order_number,lottery_identifying,app, type) values ("%s","%s","%s", "%s","%s",%s)'%(str(user_phone), lottery_name, order_number, str(lottery_identifying), str(app), str(type))
        try:
            count = self.cursor.execute(sql)
            self.conn.commit()
            self.release_db_connect()
            return True
        except Exception,e:
            if self.logger:
                self.logger.error('add_multi_lottery except %s'%(e))
            self.release_db_connect()    
            return False
    
    def report_lottery_choose(self, lottery_identifying):
        self.get_db_connect()
        try:
            sql = 'update lottery_multi_list set state=1 where lottery_identifying="%s"'%(str(lottery_identifying))
            count = self.cursor.execute(sql)
            self.conn.commit()
            self.release_db_connect()
            if count > 0:
                return True
            else:
                return False
        except Exception,e:
            self.conn.rollback()
            if self.logger:
                self.logger.error('report_lottery_choose except %s'%(e))
            self.release_db_connect()    
            return False
            
    def draw_lottery(self, lottery_identifying, lottery_name= ''):
        self.get_db_connect()
        try:
            sql = 'update lottery_list set state=1 where lottery_identifying="%s"'%(str(lottery_identifying))
            count = self.cursor.execute(sql)
            if lottery_name:
                sql = 'update lottery_list set lottery_name="%s" where lottery_identifying="%s"'%(lottery_name, str(lottery_identifying))
                count = self.cursor.execute(sql)
            self.conn.commit()
            self.release_db_connect()
            if count > 0:
                return True
            else:
                return False
        except Exception,e:
            self.conn.rollback()
            if self.logger:
                self.logger.error('draw_lottery except %s'%(e))
            self.release_db_connect()    
            return False
            
    def get_lottery_by_identifying(self, lottery_identifying):
        self.get_db_connect()
        sql = 'select id,lottery_name,state,type from lottery_list where lottery_identifying="%s"'%(str(lottery_identifying))
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                ret_list = []
                result = self.cursor.fetchone()
                self.release_db_connect()
                ret_dict = {}
                ret_dict['id'] = result[0]
                ret_dict['lottery_name'] = result[1]
                ret_dict['state'] = result[2]
                ret_dict['type'] = result[3]
                return ret_dict
            else:
                self.release_db_connect()
                return {}
        except Exception,e:
            if self.logger:
                self.logger.error('get_lottery_by_identifying except %s'%(e))
            self.release_db_connect()
            return {}

    def get_multi_lottery_by_identifying(self, lottery_identifying):
        self.get_db_connect()
        sql = 'select id,lottery_name,state,type,order_number,user_phone from lottery_multi_list where lottery_identifying="%s"'%(str(lottery_identifying))
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                ret_list = []
                result = self.cursor.fetchone()
                self.release_db_connect()
                ret_dict = {}
                ret_dict['id'] = result[0]
                ret_dict['lottery_name'] = result[1]
                ret_dict['state'] = result[2]
                ret_dict['type'] = result[3]
                ret_dict['order_number'] = result[4]
                ret_dict['user_phone'] = result[5]
                return ret_dict
            else:
                self.release_db_connect()
                return {}
        except Exception,e:
            if self.logger:
                self.logger.error('get_multi_lottery_by_identifying except %s'%(e))
            self.release_db_connect()
            return {}

    def get_multi_lottery_by_phone(self, phone, activity_type):
        self.get_db_connect()
        sql = 'select  create_time, order_number, lottery_identifying from lottery_multi_list where user_phone="%s" and state = 0 and type="%s"'%(str(phone), str(activity_type))
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                ret_list = []
                self.cursor.scroll(0, mode='absolute')
                results = self.cursor.fetchall()
                self.release_db_connect()
                for result in results:
                    ret_dict = {}
                    ret_dict['create_time'] = result[0].strftime("%Y/%m/%d %H:%M")
                    ret_dict['order_number'] = result[1]
                    ret_dict['lottery_identifying'] = result[2]
                    ret_list.append(ret_dict)

                return ret_list
            else:
                self.release_db_connect()
                return []
        except Exception,e:
            if self.logger:
                self.logger.error('get_multi_lottery_by_phone except %s'%(e))
            self.release_db_connect()
            return []
            
    def get_multi_lottery_by_order_number(self, order_number):
        self.get_db_connect()
        sql = 'select create_time, order_number, lottery_identifying, user_phone from lottery_multi_list where order_number="%s" and type=13'%(str(order_number))
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                ret_list = []
                self.cursor.scroll(0, mode='absolute')
                results = self.cursor.fetchall()
                self.release_db_connect()
                for result in results:
                    ret_dict = {}
                    ret_dict['create_time'] = result[0].strftime("%Y/%m/%d %H:%M")
                    ret_dict['order_number'] = result[1]
                    ret_dict['lottery_identifying'] = result[2]
                    ret_dict['user_phone'] = result[3]
                    ret_list.append(ret_dict)

                return ret_list
            else:
                self.release_db_connect()
                return []
        except Exception,e:
            if self.logger:
                self.logger.error('get_multi_lottery_by_order_number except %s'%(e))
            self.release_db_connect()
            return []
    
    def get_pay_flag_by_order(self, order_number):
        self.get_db_connect()
        sql = 'select flag from orders where order_number=%s'%(str(order_number))
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                result = self.cursor.fetchone()
                self.release_db_connect()
                return result[0]
            else:
                self.release_db_connect()
                return 0
        except Exception,e:
            if self.logger:
                self.logger.error('get_pay_flag_by_order except %s'%(e))
            self.release_db_connect()
            return 0

    def format_invite_business_list(self, results):
        ret_list = []
        for result in results:
            ret_dict = {}
            ret_dict['user_phone'] = result[0]
            ret_dict['shop_name'] = result[1]
            ret_dict['name'] = result[2]
            ret_dict['business_card'] = result[3]
            ret_list.append(ret_dict)
        return ret_list
        
    def get_user_invite_business_phone_list(self, user_phone):
        self.get_db_connect()
        sql = 'select user_phone from commision_info where sales_phone="%s"'%(str(user_phone))
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                ret_list = []
                self.cursor.scroll(0, mode='absolute')
                results = self.cursor.fetchall()
                self.release_db_connect()
                for result in results:
                    ret_list.append(result[0])
                return ret_list
            else:
                self.release_db_connect()
                return []
        except Exception,e:
            if self.logger:
                self.logger.error('get_user_invite_business_phone_list except %s'%(e))
            self.release_db_connect()
            return []
            
    def get_user_invited_business_info(self, user_phone):
        self.get_db_connect()
        sql = 'select ci.state,ci.settle_state,ci.callback_state,ci.custom_state,ci.purchase_name,us.name,us.shop_name,us.brand_name,us.user_state from commision_info ci inner join user_shop us on ci.user_phone=us.telephone where ci.user_phone="%s"'%(str(user_phone))
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                ret_dict = {}
                result = self.cursor.fetchone()
                self.release_db_connect()
                ret_dict['state'] = result[0]
                ret_dict['settle_state'] = result[1]
                ret_dict['callback_state'] = result[2]
                ret_dict['custom_state'] = result[3]
                ret_dict['purchase_name'] = result[4]
                ret_dict['name'] = result[5]
                ret_dict['shop_name'] = result[6]
                ret_dict['brand_name'] = result[7]
                ret_dict['user_state'] = result[8]
                return ret_dict
            else:
                self.release_db_connect()
                return {}
        except Exception,e:
            if self.logger:
                self.logger.error('get_user_invite_business_info except %s'%(e))
            self.release_db_connect()
            return {}

    def get_user_invited_business_content_list(self, user_phone):
        self.get_db_connect()
        sql = 'select content from commision_content where phone="%s" and content!=""'%(str(user_phone))
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                ret_list = []
                self.cursor.scroll(0, mode='absolute')
                results = self.cursor.fetchall()
                self.release_db_connect()
                for result in results:
                    ret_list.append(result[0])
                return ret_list
            else:
                self.release_db_connect()
                return []
        except Exception,e:
            if self.logger:
                self.logger.error('get_user_invite_business_content_list except %s'%(e))
            self.release_db_connect()
            return []
            
    def format_lottery_info_list(self, results):
        ret_list = []
        for result in results:
            ret_dict = {}
            ret_dict['user_phone'] = result[0]
            ret_dict['lottery_name'] = result[1]
            ret_dict['name'] = result[2]
            ret_dict['shop_name'] = result[3]
            ret_dict['brand_name'] = result[4]
            ret_list.append(ret_dict)
        return ret_list
    
    def get_user_lottery(self, user_phone, type):
        self.get_db_connect()
        sql = 'select lottery_name from lottery_list where user_phone="%s" and type=%s and state=1'%(str(user_phone), str(type))
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                ret_list = []
                result = self.cursor.fetchone()
                self.release_db_connect()
                return result[0]
            else:
                self.release_db_connect()
                return ''
        except Exception,e:
            if self.logger:
                self.logger.error('get_user_lottery except %s'%(e))
            self.release_db_connect()
            return ''
            
    def get_lottery_info_list(self, type):
        self.get_db_connect()
        sql = 'select ll.user_phone,ll.lottery_name,us.name,us.shop_name,brand_name from lottery_list ll inner join user_shop us on ll.user_phone=us.telephone where type=%s and state=1'%(str(type))
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                ret_list = []
                self.cursor.scroll(0, mode='absolute')
                results = self.cursor.fetchall()
                self.release_db_connect()
                return self.format_lottery_info_list(results)
            else:
                self.release_db_connect()
                return []
        except Exception,e:
            if self.logger:
                self.logger.error('get_lottery_info_list except %s'%(e))
            self.release_db_connect()
            return []

    def get_lottery_info_list_by_send_message(self, type):
        self.get_db_connect()
        sql = 'select id,user_phone from lottery_list where type=%s and state=1 and send_message=0'%(str(type))
        print sql
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                ret_list = []
                self.cursor.scroll(0, mode='absolute')
                results = self.cursor.fetchall()
                self.release_db_connect()
                for result in results:
                    ret_dict = {}
                    ret_dict['id'] = result[0]
                    ret_dict['phone'] = result[1]
                    ret_list.append(ret_dict)
                return ret_list
            else:
                self.release_db_connect()
                return []
        except Exception,e:
            if self.logger:
                self.logger.error('get_lottery_info_list_by_send_message except %s'%(e))
            self.release_db_connect()
            return []
            
    def update_lottery_send_message(self, id):
        self.get_db_connect()
        try:
            sql = 'update lottery_list set send_message=1 where id=%s'%(str(id))
            count = self.cursor.execute(sql)
            self.conn.commit()
            self.release_db_connect()
            if count > 0:
                return True
            else:
                return False
        except Exception,e:
            self.conn.rollback()
            if self.logger:
                self.logger.error('update_lottery_send_message except %s'%(e))
            self.release_db_connect()    
            return False

    def get_lottery_info_list_by_state(self, state = 0):
        self.get_db_connect()
        sql = 'select id,user_phone,lottery_identifying,type from lottery_list where state=%s'%(str(state))
        print sql
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                ret_list = []
                self.cursor.scroll(0, mode='absolute')
                results = self.cursor.fetchall()
                self.release_db_connect()
                for result in results:
                    ret_dict = {}
                    ret_dict['id'] = result[2]
                    ret_dict['phone'] = result[1]
                    ret_dict['type'] = result[3]
                    ret_list.append(ret_dict)
                return ret_list
            else:
                self.release_db_connect()
                return []
        except Exception,e:
            if self.logger:
                self.logger.error('get_lottery_info_list_by_state except %s'%(e))
            self.release_db_connect()
            return []
            
    def get_lottery_list_by_day(self, type, day):
        today = day.strftime('%Y-%m-%d %H:%M:%S')
        tomorrow = (day + timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
        self.get_db_connect()
        sql = 'select user_phone from lottery_list where type=%s and create_time > "%s" and create_time < "%s"'%(str(type), str(today),str(tomorrow))
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                ret_list = []
                self.cursor.scroll(0, mode='absolute')
                results = self.cursor.fetchall()
                self.release_db_connect()
                for result in results:
                    ret_list.append(result[0])
                return ret_list
            else:
                self.release_db_connect()
                return []
        except Exception,e:
            if self.logger:
                self.logger.error('get_lottery_list_by_day except %s'%(e))
            self.release_db_connect()
            return []

    def get_real_money_by_order_number(self, order_number):
        self.get_db_connect()
        sql = 'select price_total from orders where order_number = "%s"'%(str(order_number))
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                result = self.cursor.fetchone()
                self.release_db_connect()
                return result[0]
            else:
                self.release_db_connect()
                return 0
        except Exception,e:
            if self.logger:
                self.logger.error('get_real_money_by_order_number except %s'%(e))
            self.release_db_connect()
            return 0


    def get_customer_num_from_some_time(self, date):
        self.get_db_connect()
        #date = date.strftime('%Y-%m-%d %H:%M:%S')
        sql = 'select count(*) from customer_user where create_time > "%s"'%(str(date))
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                result = self.cursor.fetchone()
                self.release_db_connect()
                return result[0]
            else:
                self.release_db_connect()
                return 0
        except Exception,e:
            if self.logger:
                self.logger.error('get_customer_num_from_some_time except %s'%(e))
            self.release_db_connect()
            return 0
            
    def get_lottery_list_all(self, type):
        self.get_db_connect()
        sql = 'select user_phone from lottery_list where type=%s'%(str(type))
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                ret_list = []
                self.cursor.scroll(0, mode='absolute')
                results = self.cursor.fetchall()
                self.release_db_connect()
                for result in results:
                    ret_list.append(result[0])
                return ret_list
            else:
                self.release_db_connect()
                return []
        except Exception,e:
            if self.logger:
                self.logger.error('get_lottery_list_all except %s'%(e))
            self.release_db_connect()
            return []

    def get_lottery_id_by_order_number(self, user_phone, order_number):
        self.get_db_connect()
        sql = 'select lottery_identifying from lottery_multi_list where user_phone="%s" and order_number="%s" and type=13 ' %(str(user_phone), str(order_number))
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                result = self.cursor.fetchone()
                self.release_db_connect()
                return result[0]
            else:
                self.release_db_connect()
                return ''
        except Exception,e:
            if self.logger:
                self.logger.error('get_lottery_id_by_order_number except %s'%(e))
            self.release_db_connect()
            return ''
            
    def get_user_invite_business_num(self, user_phone):
        self.get_db_connect()
        sql = 'select count(*) from commision_info where sales_phone="%s" and type=3'%(str(user_phone))
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                ret_list = []
                result = self.cursor.fetchone()
                self.release_db_connect()
                return result[0]
            else:
                self.release_db_connect()
                return 0
        except Exception,e:
            if self.logger:
                self.logger.error('get_user_invite_business_num except %s'%(e))
            self.release_db_connect()
            return 0 
    
    def get_lottery_multi_num(self, type):
        self.get_db_connect()
        sql = 'select count(*) from lottery_multi_list where type=%s and lottery_name!=0'%(str(type))
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                result = self.cursor.fetchone()
                self.release_db_connect()
                return result[0]
            else:
                self.release_db_connect()
                return 0
        except Exception,e:
            if self.logger:
                self.logger.error('get_lottery_num except %s'%(e))
            self.release_db_connect()
            return 0

    def get_user_lottery_multi_num(self, user_phone, type, state = None):
        self.get_db_connect()
        if state is None:
            sql = 'select count(*) from lottery_multi_list where user_phone="%s" and type=%s and lottery_name!=0'%(str(user_phone), str(type))
        else:
            sql = 'select count(*) from lottery_multi_list where user_phone="%s" and type=%s and state=%s and lottery_name!=0'%(str(user_phone), str(type), str(state))
            
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                result = self.cursor.fetchone()
                self.release_db_connect()
                return result[0]
            else:
                self.release_db_connect()
                return 0
        except Exception,e:
            if self.logger:
                self.logger.error('get_lottery_num except %s'%(e))
            self.release_db_connect()
            return 0
            
    def get_business_user_by_phone(self, phone):
        self.get_db_connect()
        sql = 'select name,shop_name,brand_name from user_shop where telephone=%s'%(str(phone))
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                result = self.cursor.fetchone()
                self.release_db_connect()
                ret_dict = {}
                ret_dict['name'] = result[0]
                ret_dict['shop_name'] = result[1]
                ret_dict['brand_name'] = result[2]
                return ret_dict
            else:
                self.release_db_connect()
                return {}
        except Exception,e:
            if self.logger:
                self.logger.error('get_business_user_by_phone except %s'%(e))
            self.release_db_connect()    
            return {}
            
    def draw_order_pay_reward(self, lottery_identifying, type, settle_mode, settle_account):
        self.get_db_connect()
        sql = 'select id,lottery_name,state,type,order_number,user_phone from lottery_multi_list where lottery_identifying="%s" and type=%s and state=0'%(str(lottery_identifying), str(type))
        try:
            count = self.cursor.execute(sql)
            if count == 0:
                if self.logger:
                    self.logger.error('draw_order_pay_reward no data for %s'%(str(lottery_identifying)))
                return False
            result = self.cursor.fetchone()
            lottery_name = result[1]
            state = result[2]
            type = result[3]
            order_number = result[4]
            sales_phone = result[5]
            if not order_number or not lottery_name or not sales_phone:
                if self.logger:
                    self.logger.error('draw_order_pay_reward no order for %s'%(str(lottery_identifying)))            
                return False
            money_list = lottery_name.split('|')
            if len(money_list) != 3:
                if self.logger:
                    self.logger.error('draw_order_pay_reward no money for %s'%(str(lottery_identifying))) 
                return False
            money = float(money_list[0])
            sql = 'select user_phone from orders where order_number="%s"'%(str(order_number))
            count = self.cursor.execute(sql)
            if count == 0:
                if self.logger:
                    self.logger.error('draw_order_pay_reward no user_phone for %s'%(str(lottery_identifying)))             
                return False            
            result = self.cursor.fetchone()
            user_phone= result[0]
            if not user_phone:
                if self.logger:
                    self.logger.error('draw_order_pay_reward empty user_phone for %s'%(str(lottery_identifying)))            
                return False
            reward_type = '5' + datetime.now().strftime('%H%M%S')

            sql = 'select flag,verify_state from orders where order_number="%s"'%(str(order_number))
            count = self.cursor.execute(sql)
            if count == 0:
                if self.logger:
                    self.logger.error('draw_order_pay_reward no pay flag %s'%(str(lottery_identifying)))
                return False

            result = self.cursor.fetchone()
            flag, verify_state = result[0], result[1]
            
            if verify_state == 3:
                sql = 'insert into commision_info (money, user_phone, sales_phone, type, order_number, callback_state, settle_state, update_time,settle_mode, settle_account) values (%s, "%s", "%s", %s, "%s",%s, %s, %s, %s, "%s")' \
                %(str(money), user_phone, sales_phone, str(reward_type), str(order_number),'1', '2', str(int(time.time())), str(settle_mode), str(settle_account))
            elif verify_state in [0,1]:
                sql = 'insert into commision_info (money, user_phone, sales_phone, type, order_number, callback_state, settle_state, update_time, settle_mode, settle_account) values (%s, "%s", "%s", %s, "%s", %s, %s, %s, %s, "%s")' \
                %(str(money), user_phone, sales_phone, str(reward_type), str(order_number),'1', '0', str(int(time.time())), str(settle_mode), str(settle_account))   
            elif verify_state in [2,4,5]:    
                sql = 'insert into commision_info (money, user_phone, sales_phone, type, order_number, callback_state, settle_state, update_time, settle_mode, settle_account) values (%s, "%s", "%s", %s, "%s", %s, %s, %s, %s, "%s")' \
                %(str(money), user_phone, sales_phone, str(reward_type), str(order_number),'1', '1', str(int(time.time())), str(settle_mode), str(settle_account))  
            else:
                return False
            count = self.cursor.execute(sql)
            sql = 'update lottery_multi_list set state=1 where lottery_identifying="%s"'%(str(lottery_identifying))
            count = self.cursor.execute(sql)
            self.conn.commit()
            self.release_db_connect()
            return True
        except Exception,e:
            self.conn.rollback()
            if self.logger:
                self.logger.error('draw_order_pay_reward except %s'%(e))
            self.release_db_connect()
            return False        
    
    def get_business_user_list_by_invited_num(self, start, end):
        self.get_db_connect()
        sql = 'select ci.sales_phone,count(*) from commision_info ci inner join user_shop us on ci.user_phone=us.telephone where us.user_state>=1 and ci.type=3 group by ci.sales_phone having count(*)>=%s and count(*)<=%s order by count(*) desc'%(str(start),str(end))
        try:
            count = self.cursor.execute(sql)
            if count > 0:
                ret_dict = {}
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
                self.logger.error('get_business_user_list_by_invited_num except %s'%(e))
            self.release_db_connect()
            return {}
                
    def format_lottery_stat(self, now, phone_list, type):
        ret_dict = {}
        origin = sys.stdout
        file_name = str(now) + '.txt'
        f = open(file_name, 'a+')
        #sys.stdout = f
        for phone in phone_list:
            num = self.get_user_invite_business_num(phone)
            ret_dict[phone] = num
        for user_phone, invite_num in ret_dict.items():
            user_basic_info = self.get_business_user_by_phone(user_phone)
            if not user_basic_info:
                continue
            user_name = user_basic_info['name']
            lottery_name = self.get_user_lottery(user_phone, type)
            print '邀请人：%s 姓名：%s 邀请数：%s 奖品：%s'%(str(user_phone), user_name.encode('utf8', 'ignore'),str(invite_num), lottery_name.encode('utf8', 'ignore'))
            f.write('邀请人：%s 姓名：%s 邀请数：%s 奖品：%s\n'%(str(user_phone), user_name.encode('utf8', 'ignore'), str(invite_num), lottery_name.encode('utf8', 'ignore')))

            invited_user_phone_list = self.get_user_invite_business_phone_list(user_phone)
            invited_user_phone_list = list(set(invited_user_phone_list))
            for invited_user in invited_user_phone_list:
                invited_user_dict = {}
                invited_user_dict = self.get_user_invited_business_info(invited_user)
                content_list = self.get_user_invited_business_content_list(invited_user)
                
                invited_user_dict['content'] = content_list
                state = invited_user_dict.get('state', 0)
                if int(state) == 1:
                    str_state = '申请提现'
                else:
                    str_state = '未申请提现'
                callback_state = int(invited_user_dict.get('callback_state', 0))
                if callback_state == 0:
                    str_callback_state = '未回访'
                else:
                    str_callback_state = '已回访'
                
                settle_state = int(invited_user_dict.get('settle_state', 0))
                if settle_state == 0:
                    str_settle_state = '未审核'
                elif settle_state == 1:
                    str_settle_state = '被驳回'
                elif settle_state == 2:
                    str_settle_state = '审核通过'
                elif settle_state == 4:
                    str_settle_state = '已结算'
                else:
                    str_settle_state = '未知'
                
                custom_state = int(invited_user_dict.get('custom_state', 0))
                if custom_state == 0:
                    str_custom_state = '线上返现'
                else:
                    str_custom_state = '线下返现'
                purchase_name = invited_user_dict.get('purchase_name', '')
                purchase_name = u'无' if not purchase_name else purchase_name
                name = invited_user_dict.get('name', u'未设置')
                name = u'未设置' if not name else name
                shop_name = invited_user_dict.get('shop_name', u'未设置')
                shop_name = u'未设置' if not shop_name else shop_name
                brand_name = invited_user_dict.get('brand_name', u'未设置')
                brand_name = u'未设置' if not brand_name else brand_name
                user_state = invited_user_dict.get('user_state', '')
                print '被邀请人：%s 名字：%s 品牌：%s 店铺：%s 采购：%s %s %s %s %s'%(str(invited_user),name.encode('utf8', 'ignore'),brand_name.encode('utf8', 'ignore'),shop_name.encode('utf8', 'ignore'),purchase_name.encode('utf8', 'ignore'),str_state,str_callback_state,str_settle_state,str_custom_state)
                f.write('被邀请人：%s 名字：%s 品牌：%s 店铺：%s 采购：%s %s %s %s %s\n'%(str(invited_user),name.encode('utf8', 'ignore'),brand_name.encode('utf8', 'ignore'),shop_name.encode('utf8', 'ignore'),purchase_name.encode('utf8', 'ignore'),str_state,str_callback_state,str_settle_state,str_custom_state))
        f.close()    
    def get_lottery_stat_v2(self, type):
        now = datetime.now().date()
        phone_list = self.get_lottery_list_by_day(type, now)
        self.format_lottery_stat(now, phone_list,type)

    def get_lottery_stat_v2_total(self, type):
        now = datetime.now().date()
        phone_list = self.get_lottery_list_all(type)
        self.format_lottery_stat(now, phone_list,type)
        
    def get_lottery_num(self, sales_phone, start_time, end_time):
        self.get_db_connect()
        sql = 'select user_phone,sales from orders where sales=%s and state in (1,2) and pay_time > UNIX_TIMESTAMP(%s) and pay_time < UNIX_TIMESTAMP(%s) and verify_state!=4 and price_total >= 100 and user_phone not in (select telephone from company_user) group by user_phone, sales'
        try:
            print sql,start_time,end_time
            count = self.cursor.execute(sql, [sales_phone, start_time, end_time])
            if count > 0:
                self.cursor.scroll(0, mode='absolute')
                results = self.cursor.fetchall()
                self.release_db_connect()
                return len(results)
            else:
                self.release_db_connect()
                return 0
        except Exception,e:
            if self.logger:
                self.logger.error('get_lottery_num except %s'%(e))
            self.release_db_connect()
            return 0
            
    def get_lottery_infos(self, sales_phone, start_time, end_time):
        self.get_db_connect()
        sql = 'select ci.id, SUBSTRING_INDEX(lml.lottery_name, "|", 1) from orders os inner join lottery_multi_list lml on os.order_number=lml.order_number \
        inner join commision_info ci on ci.order_number=os.order_number \
        where os.sales=%s and os.state in (1,2) and os.pay_time > UNIX_TIMESTAMP(%s) and os.pay_time < UNIX_TIMESTAMP(%s) and \
        os.price_total >= 100 and lml.type=13 and lml.state=1 and ci.state=0'
        try:
            count = self.cursor.execute(sql, [sales_phone, start_time, end_time])
            if count > 0:
                self.cursor.scroll(0, mode='absolute')
                results = self.cursor.fetchall()
                self.release_db_connect()
                return results
            else:
                self.release_db_connect()
                return []
        except Exception,e:
            if self.logger:
                self.logger.error('get_lottery_infos except %s'%(e))
            self.release_db_connect()
            return []

    def update_lottery_money(self, lottery_money_list):
        self.get_db_connect()
        try:
            sql = 'update commision_info set money=%s,rate=%s where id=%s'
            count = self.cursor.executemany(sql, lottery_money_list)
            self.conn.commit()
            self.release_db_connect()
            return True
        except Exception,e:
            self.conn.rollback()
            if self.logger:
                self.logger.error('update_lottery_money except %s'%(e))
            self.release_db_connect()    
            return False            

    def get_first_lottery_info(self, sales_phone):
        self.get_db_connect()
        sales_phone = str(sales_phone)
        sql = 'select ci.id, ci.create_time, ci.order_number from orders os inner join commision_info ci on os.order_number=ci.order_number where os.sales=%s and os.state in (1,2) and os.price_total >= 100 and os.user_phone not in (select telephone from company_user) and ci.type like "5%%" order by os.id limit 1'
        try:
            count = self.cursor.execute(sql, [sales_phone])
            if count > 0:
                result = self.cursor.fetchone()
                self.release_db_connect()
                return result 
            else:
                self.release_db_connect()
                return None
        except Exception,e:
            if self.logger:
                self.logger.error('get_first_lottery_info except %s'%(e))
            self.release_db_connect()
            return None

    def get_user_draw_lottery_num(self, sales_phone):
        self.get_db_connect()
        sales_phone = str(sales_phone)
        sql = 'select count(*) from commision_info where sales_phone=%s and user_phone not in (select telephone from company_user) and type like "5%%"'
        try:
            count = self.cursor.execute(sql, [sales_phone])
            if count > 0:
                result = self.cursor.fetchone()
                self.release_db_connect()
                return result[0]
            else:
                self.release_db_connect()
                return 0
        except Exception,e:
            if self.logger:
                self.logger.error('get_user_draw_lottery_num except %s'%(e))
            self.release_db_connect()
            return 0
            
    def get_lottery_time_by_order(self, order_number):
        if not order_number:
            return None
        self.get_db_connect()
        sql = 'select create_time from commision_info where order_number=%s'
        try:
            count = self.cursor.execute(sql, [order_number])
            if count > 0:
                result = self.cursor.fetchone()
                self.release_db_connect()
                return result[0]
            else:
                self.release_db_connect()
                return None
        except Exception,e:
            if self.logger:
                self.logger.error('get_lottery_time_by_order except %s'%(e))
            self.release_db_connect()
            return None
            
class LotteryUtil():
    def __init__(self,databases):
        self.database = databases
        self.mobile_db = databases['mobile_db']
        self.info_logger = databases['mobile_logger']
        self.pay_back_domain = databases['pay_back_domain']
        
    def create_lottery_user(self, user_phone, app, type):
        handler = DbLottery(self.mobile_db, self.info_logger)
        lottery_dict, pro_dict, total_probability = handler.get_lottery_list(type)
        token = random.randint(0, total_probability)
        lottery_id = -1
        for lot_range, id in pro_dict.items():
            if token in lot_range:
                lottery_id = id
                break
        lottery_name = lottery_dict.get(lottery_id, '')
        lottery_identifying = str(uuid.uuid1())
        if handler.add_lottery(user_phone, lottery_name, lottery_identifying, app, type):
            return lottery_identifying
        else:
            return ''

    def draw_order_pay_reward(self, lottery_identifying, type, user_phone):
        handler = DbLottery(self.mobile_db, self.info_logger)
        settle_mode, settle_account = handler.get_settle_mode_account(user_phone)
        ret = handler.draw_order_pay_reward(lottery_identifying, type, settle_mode, settle_account)
        self.handle_week_lottery_by_order(user_phone, '')
        
        notify_content = self.get_activity_notify(user_phone)
        if notify_content and user_phone:
            from MobileService.util.PushBaiduUtil import *
            push_handler = PushBaiduUtil(self.database, APP_BUSINESS)
            push_handler.send_new_award_notify(10, user_phone, notify_content)
        return ret
    
    def create_lottery_url(self, user_phone, app, type):
        lottery_identifying = self.create_lottery_user(user_phone, app, type)
        return self.pay_back_domain + 'activity/get_lottery_page/?id=' + str(lottery_identifying)
        
    def create_reward_user(self, user_phone, app, type):
        handler = DbLottery(self.mobile_db, self.info_logger)
        lottery_dict, pro_dict, total_probability = handler.get_lottery_list(type)
        lottery_name = ''
        lottery_identifying = str(uuid.uuid1())
        if handler.add_lottery(user_phone, lottery_name, lottery_identifying, app, type):
            return lottery_identifying
        else:
            return ''

    def create_payed_related_lottery_url(self, customer_user, user_phone, money, order_number, app, type=13):
        handler = DbLottery(self.mobile_db, self.info_logger)
        order_info = handler.get_order_detail(order_number)
        lottery_identifying, first_order = self.create_customer_create_order_lottery(customer_user, user_phone, money, order_number, app, type)
        print lottery_identifying, first_order
        return self.pay_back_domain + '/static/html/redmoney.html?id=' + str(lottery_identifying)
        #return self.pay_back_domain + 'activity/get_lottery_page/?id=' + str(lottery_identifying)
        
    def create_payed_lottery_url(self, customer_user, user_phone, money, order_number, app, type=13, is_random_cutoff = 0):
        handler = DbLottery(self.mobile_db, self.info_logger)
        order_info = handler.get_order_detail(order_number)
        creator = order_info.get('creator', 0)
        
        lottery_identifying, first_order = self.create_payed_lottery(customer_user, user_phone, money, order_number, app, type, is_random_cutoff)
        return self.pay_back_domain + 'activity/get_lottery_page/?id=' + str(lottery_identifying)

    def create_customer_create_order_lottery(self, customer_user, user_phone, money, order_number, app, type):
        self.info_logger.info('create_customer_create_order_lottery for %s %s'%(str(user_phone), str(order_number)))
        handler = DbLottery(self.mobile_db, self.info_logger)
        
        payed_info = handler.get_user_pay_times_by_sales(customer_user, [user_phone])
        payed_num = len(payed_info)
        choice = random.randint(1, 100000)
        if choice <= 15000:
            real_money, second_money, third_money = random.sample(range(100, 120), 3)
        else:
            real_money, second_money, third_money = random.sample(range(30, 100), 3)

            
        lottery_name = '%s|%s|%s' % (real_money, second_money, third_money)
        
        lottery_identifying = str(uuid.uuid1())
        if handler.add_multi_lottery(user_phone, lottery_name, lottery_identifying, app, type, order_number):
            return (lottery_identifying, 0)
        else:
            return ('', 0)
        
    def get_random_scope(self):
        choice = random.randint(1, 100000)
        ###20% high 80% low
        if choice <= 15000:
            return (350, 500)
        else:
            return (180, 350)
            
    def create_payed_lottery_inner(self, price_total, money):
        print 'total %s curent %s'%(str(price_total), str(money))
        handler = DbLottery(self.mobile_db, self.info_logger)
        before_money = price_total - money
        if before_money >= 6000 or before_money < 0:
            percent = range(100, 300)
            real_money, second_money, third_money = [ float('%0.1f'%( l / float(10))) for l in random.sample(percent, 3)]
        else:
            (start, end) = self.get_random_scope()
            #percent = range(180, 500)
            percent = range(start, end)
            percent_choice = random.sample(percent, 3)
            left_money = 6000 - before_money
            money = min(money, left_money)

            real_money, second_money, third_money = [float('%0.1f'%(money * l / float(10000))) for l in percent_choice]

        lottery_name = '%s|%s|%s' % (real_money, second_money, third_money)
        return lottery_name

    def create_activity_lottery(self, lottery_name, payed_num, rate = 2):
        try:
            if payed_num > 1 and rate == 2:
                return lottery_name
            elif payed_num > 0 and rate < 1:
                return lottery_name
            from_date = date(2015, 9, 19)
            to_date = date(2015, 10, 7)
            if date.today() < from_date or date.today() > to_date:
                return lottery_name
            self.info_logger.info('create_activity_lottery 1 %s %s'%(str(lottery_name), str(payed_num)))
            new_lottery_name = [ str(float('%0.1f'%(float(i))) * rate) for i in lottery_name.split('|') ]
            
            new_lottery_name = '|'.join(new_lottery_name)
            self.info_logger.info('create_activity_lottery 2 %s %s'%(str(new_lottery_name), str(payed_num)))
            
            return new_lottery_name
        except Exception,e:
            self.info_logger.error('create_activity_lottery except %s %s'%(e, str(payed_num)))
            return lottery_name
        
    def create_payed_lottery(self, customer_user, user_phone, money, order_number, app, type=13, is_random_cutoff = 0):
        money = float(money)
        if money < 0:
            return ('', 0)
        
        handler = DbLottery(self.mobile_db, self.info_logger)
        payed_info = handler.get_user_pay_times_by_sales(customer_user, [user_phone])
        payed_num = len(payed_info)
        price_total = 0
        for money_info in payed_info:
            price_total += float(money_info[0])
        ###如果是随机立减的订单特殊处理
        if is_random_cutoff:
            price_total = money
        lottery_name = self.create_payed_lottery_inner(price_total, money)
        self.info_logger.info('create_payed_lottery for %s %s %s %s %s'%(str(user_phone), str(order_number), str(price_total),str(money), str(lottery_name)))
        sales_payed_num = handler.get_sales_payed_order_num(user_phone)
        from_date = date(2015, 9, 19)
        to_date = date(2015, 10, 7)
        if date.today() < from_date or date.today() > to_date:
            sales_payed_num = 20
        lottery_name = self.create_activity_lottery(lottery_name, sales_payed_num)
        lottery_identifying = str(uuid.uuid1())
        if handler.add_multi_lottery(user_phone, lottery_name, lottery_identifying, app, type, order_number):
            return (lottery_identifying, 0)
        else:
            return ('', 0)

    def get_week_start(self, input_date = None):
        if not input_date:
            now = date.today()
        else:
            now = date(input_date.year, input_date.month, input_date.day)
        delta_days = now.weekday()
        return now - timedelta(days=delta_days)
        
    def get_week_end(self, input_date = None):
        if not input_date:
            now = date.today()
        else:
            now = date(input_date.year, input_date.month, input_date.day)
        delta_days = now.weekday()
        delta_days = 7 - delta_days - 1
        return now + timedelta(days=delta_days)
    
    def get_week_lottery_rate(self, order_count):
        if order_count < 5:
            return (1, 1)
        elif order_count < 10:
            return (1.5, 1.25)
        else:
            return (2, 1.5)
            
    def get_activity_time_scope(self, lottery_time = None):
        print lottery_time
        week_start = self.get_week_start(lottery_time)
        week_end = self.get_week_end(lottery_time)
        from_date = date(2015, 9, 21)
        to_date = date(2015, 10, 7)

        if week_start > to_date or week_end < from_date:
            print 're non'
            return (None, None)
        
        do_start_time = max(week_start, from_date)
        do_end_time = min(week_end, to_date) + timedelta(days=1)
        if do_start_time > do_end_time:
            return (None, None)
        return (do_start_time, do_end_time)
        
    def get_activity_notify(self, sales_phone):
        handler = DbLottery(self.mobile_db, self.info_logger)
        do_start_time, do_end_time = self.get_activity_time_scope()
        if not do_start_time:
            return None
        do_start_time = str(do_start_time)
        do_end_time = str(do_end_time)
        order_count = handler.get_lottery_num(sales_phone, do_start_time, do_end_time)
        if order_count == 5:
            return u'恭喜,您已成功与5名顾客交易,当周享受1.5倍交易红包奖励,请您再接再厉。'
        elif order_count == 10:
            return u'恭喜,您已成功与10名顾客交易,当周享受2倍交易红包奖励,请您再接再厉。'
        return None
        
    def handle_week_lottery(self, sales_phone):
        handler = DbLottery(self.mobile_db, self.info_logger)
        week_start = self.get_week_start()
        from_date = date(2015, 9, 21)
        to_date = date(2015, 10, 7)
        if week_start < from_date or week_start > to_date:
            return False
            
        end_time = date.today() + timedelta(days=1)
        if end_time > to_date:
            end_time = to_date + timedelta(days=1)
        week_start = str(week_start)
        end_time = str(end_time)
        order_count = handler.get_lottery_num(sales_phone, week_start, end_time)
        lottery_rate, first_order_rate = self.get_week_lottery_rate(order_count)
        print 'handle_week_lottery order_count %s lottery_rate %s'%(str(order_count), str(lottery_rate))
        lottery_infos = handler.get_lottery_infos(sales_phone, week_start, end_time)
        if not lottery_infos:
            return False
        lottery_modify_list = []
        for lottery in lottery_infos:
            id = lottery[0]
            money = float(lottery[1]) * lottery_rate
            lottery_modify_list.append((money, lottery_rate, id))
        handler.update_lottery_money(lottery_modify_list)
        return True

    def handle_week_lottery_by_order(self, sales_phone, order_number='', lottery_time = None):
        handler = DbLottery(self.mobile_db, self.info_logger)
        if not lottery_time:
            lottery_time = handler.get_lottery_time_by_order(order_number)
        do_start_time, do_end_time = self.get_activity_time_scope(lottery_time)
        if not do_start_time:
            return False
        do_start_time = datetime.strptime(str(do_start_time),'%Y-%m-%d')
        do_end_time = datetime.strptime(str(do_end_time),'%Y-%m-%d')
        ####首次红包时间是否在活动范围内
        first_lottery_info = handler.get_first_lottery_info(sales_phone)
        first_lottery_id = 0
        if first_lottery_info:
            first_lottery_id = first_lottery_info[0]
            first_lottery_time = first_lottery_info[1]
            self.info_logger.info('first_lottery_time %s'%(str(first_lottery_time)))
            if first_lottery_time < do_start_time or first_lottery_time > do_end_time:
                first_lottery_id = 0
        self.info_logger.info('first_lottery_id %s %s %s'%(str(first_lottery_id), str(do_start_time), str(do_end_time)))
        do_start_time = str(do_start_time)
        do_end_time = str(do_end_time)
        print do_start_time, do_end_time, first_lottery_id
        order_count = handler.get_lottery_num(sales_phone, do_start_time, do_end_time)
        lottery_rate, first_order_rate = self.get_week_lottery_rate(order_count)

        print 'handle_week_lottery order_count %s lottery_rate %s %s'%(str(order_count), str(lottery_rate) , str(first_order_rate))
        lottery_infos = handler.get_lottery_infos(sales_phone, do_start_time, do_end_time)
        if not lottery_infos:
            return False
        lottery_modify_list = []
        for lottery in lottery_infos:
            id = lottery[0]
            if str(id) == str(first_lottery_id):
                money = float(lottery[1]) * first_order_rate
            else:
                money = float(lottery[1]) * lottery_rate
            lottery_modify_list.append((money, lottery_rate, id))
        handler.update_lottery_money(lottery_modify_list)
        return True
        
    def create_huochepiao_url(self, user_phone, date, app, type=12):
        lottery_identifying = self.create_huochepiao_lottery(user_phone, date, app, type)
        return self.pay_back_domain + 'activity/get_lottery_page/?id=' + str(lottery_identifying)
        
    def create_huochepiao_lottery(self, user_phone, date, app, type=12):
        handler = DbLottery(self.mobile_db, self.info_logger)
        register_num = handler.get_customer_num_from_some_time(date)
        has_drawed_num = handler.get_lottery_multi_num(type)
        lottery_name = ''
        if register_num / 100 >= has_drawed_num:
            token = random.randint(0, 10000)
            if token in [1000, 1100]:
                lottery_name = u'火车票'
                if handler.get_user_lottery_multi_num(user_phone, type) > 0:
                    return ''
        lottery_identifying = str(uuid.uuid1())
        if handler.add_multi_lottery(user_phone, lottery_name, lottery_identifying, app, type):
            return lottery_identifying
        else:
            return ''        
    def create_reward_url(self, user_phone, app, type):
        lottery_identifying = self.create_lottery_user(user_phone, app, type)
        if not lottery_identifying:
            return ''
        return self.pay_back_domain + 'activity/get_reward_page/?id=' + str(lottery_identifying)

    def get_lottery_by_identifying(self, lottery_identifying):
        handler = DbLottery(self.mobile_db, self.info_logger)
        return handler.get_lottery_by_identifying(lottery_identifying)
        
    def get_multi_lottery_by_identifying(self, lottery_identifying):
        handler = DbLottery(self.mobile_db, self.info_logger)
        ret_dict = handler.get_multi_lottery_by_identifying(lottery_identifying)
        user_phone = ret_dict.get('user_phone', '')
        lottery_name = ret_dict.get('lottery_name', '')
        
        sales_payed_num = handler.get_user_draw_lottery_num(user_phone)
        from_date = date(2015, 9, 19)
        to_date = date(2015, 10, 7)
        if date.today() < from_date or date.today() > to_date:      
            return ret_dict
        else:
            lottery_name = self.create_activity_lottery(lottery_name, sales_payed_num, 0.5)
            ret_dict['lottery_name'] = lottery_name
            return ret_dict

    def get_pay_flag_by_order_number(self, order_number):
        handler = DbLottery(self.mobile_db, self.info_logger)
        return handler.get_pay_flag_by_order(order_number)

    def get_multi_lottery_by_phone(self, phone, activity_type):
        handler = DbLottery(self.mobile_db, self.info_logger)
        return handler.get_multi_lottery_by_phone(phone, activity_type)

    def get_multi_lottery_by_order_number(self, order_number):
        handler = DbLottery(self.mobile_db, self.info_logger)
        return handler.get_multi_lottery_by_order_number(order_number)
        
    def draw_lottery(self, lottery_identifying, lottery_name = ''):
        handler = DbLottery(self.mobile_db, self.info_logger)
        return handler.draw_lottery(lottery_identifying, lottery_name)
    
    def report_lottery_choose(self, lottery_identifying):
        handler = DbLottery(self.mobile_db, self.info_logger)
        return handler.report_lottery_choose(lottery_identifying)
        
    def get_lottery_info_list(self, type, start, end):
        handler = DbLottery(self.mobile_db, self.info_logger)
        handler.get_lottery_stat(type, start, end)

    def get_real_money_by_order_number(self, order_number):
        handler = DbLottery(self.mobile_db, self.info_logger)
        return handler.get_real_money_by_order_number(order_number)
    
    def get_lottery_stat_v2(self, type, all= False):
        handler = DbLottery(self.mobile_db, self.info_logger)
        if all:
            handler.get_lottery_stat_v2_total(type)
        else:
            handler.get_lottery_stat_v2(type)

    def save_two_poit(self, number):
        return round(number, 2)
        
if __name__ == '__main__':
    handler = LotteryUtil(settings.COMMON_DATA)
    print handler.create_payed_lottery('11100000956', '11100000913', 1, '145440670906144', 'wallet_business', 13, 1)
    #print handler.create_reward_url('13811678953', '', 10)
    #if len(sys.argv) == 2 and sys.argv[1] == 'all':
    #    handler.get_lottery_stat_v2(10, True)
    #    handler.get_lottery_stat_v2(11, True)
    #else:
    #    handler.get_lottery_stat_v2(10)
    #    handler.get_lottery_stat_v2(11)
    #now = datetime.now().date()
    #file_name = str(now) + '.txt'
    #f = codecs.open(file_name, 'r', 'utf-8')
    #stri = f.read()
    #send_mail(to_list, u'每日报告', stri)
    #print handler.create_payed_lottery_url('13911807448', '18701506591', 59219, '144349319208937', 'wallet_business')
    #print handler.get_activity_time_scope()
    #print handler.handle_week_lottery_by_order('11122233315', '1444205104750732264')
    
    