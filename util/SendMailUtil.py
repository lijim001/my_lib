#coding=utf-8

import smtplib,codecs,base64
from email.mime.text import MIMEText

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

def send_mail(to_list, sub, content, subtype='plain'):  
    me= u"新窝自动统计"+"<postmaster@xinwo.com>"  
    msg = MIMEText(content,_subtype=subtype,_charset='gbk')  
    #msg = MIMEText(content,_subtype='plain',_charset='utf8')
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
        
def send_mail_utf(to_list, sub, content, subtype='plain'):  
    me = u"新窝自动统计"+"<postmaster@xinwo.com>"  
    msg = MIMEText(content,_subtype=subtype,_charset='utf8')  
    #msg = MIMEText(content,_subtype='plain',_charset='utf8')
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

if __name__ == '__main__':
    pass