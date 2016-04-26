#coding=utf-8

import logging,os,ConfigParser,time

ITEM_SOLR_SERVICE = 'solr'
ITEM_SOLR_PATH = 'file_dir'
ITEM_SOLR_BACKUP_PATH = 'backup_dir'
ITEM_SOLR_FILE_PREFIX = 'file_prefix'
ITEM_SEGMENT_EXTEND_FILE = 'extend_file'

ITEM_DB_HOST = 'db_host'
ITEM_DB_USER = 'db_user'
ITEM_DB_PASSWD = 'db_passwd'
ITEM_DB_DB = 'db_database'

ITEM_REDIS_HOST = 'rd_host'
ITEM_REDIS_PORT = 'rd_port'
ITEM_REDIS_DB = 'rd_database'

ITEM_MONGO_HOST = 'mongo_host'
ITEM_MONGO_PORT = 'mongo_port'
ITEM_MONGO_DB = 'mongo_db'

ITEM_DOMAIN_IMAGE = 'image'
ITEM_DOMAIN_PAY_BACK = 'pay_call_back'
ITEM_DOMAIN_PAY_PHP = 'php_pay_call'

ITEM_WEIXIN_APP_KEY = 'app_key'
ITEM_WEIXIN_APP_SECRET = 'app_secret'
ITEM_WEIXIN_PARTNER_ID = 'partnerid'
ITEM_WEIXIN_PARTNERKEY = 'partnerkey'
ITEM_WEIXIN_PAY_SIGNKEY = 'paysignkey'
ITEM_WEIXIN_TRACE_ID = 'traceid'

ITEM_BAIDU_PUSH_APP_KEY = 'app_key'
ITEM_BAIDU_PUSH_APP_SECRET = 'app_secret'

ITEM_ENVIRONMENT = 'environment'
ITEM_CLIENT_DOWNLOAD_PAGE = 'client_download_page'
ITEM_BUSINESS_DOWNLOAD_PAGE = 'business_download_page'

ITME_INNER_ACCESS_CONTROLLER = 'domain_inner'

ITEM_NOTE_SENDER_PURCHASE_MANAGER = 'purchase_manager'
ITEM_NOTE_SENDER_FINANCE = 'finance'

ITEM_NOTE_RECEIVE_PROMOTE = 'promote'


def LoadSolrServiceAddr(config_file_name, config_section_name):
    try:
        cf = ConfigParser.ConfigParser()
        cf.read(config_file_name)
        addr = cf.get(config_section_name, ITEM_SOLR_SERVICE)
        return addr
    except Exception,e:
        return ''
        
def LoadFeedServicePort(file_name, section_name):
    try:
        cf = ConfigParser.ConfigParser()
        cf.read(file_name)
        port = cf.get(section_name, "port").strip()
        return port
    except Exception,e:
        return 0

def LoadPicAddr(file_name, section_name):
    try:
        cf = ConfigParser.ConfigParser()
        cf.read(file_name)
        port = cf.get(section_name, "pic_addr").strip()
        return port
    except Exception,e:
        return 0

def LoadAccessController(file_name, section_name):
    try:
        cf = ConfigParser.ConfigParser()
        cf.read(file_name)
        inner_domain_ips = cf.get(section_name, ITME_INNER_ACCESS_CONTROLLER).strip()
        return inner_domain_ips.split(',')
    except Exception,e:
        return []
        
def LoadStaticFileAddr(file_name, section_name):
    try:
        cf = ConfigParser.ConfigParser()
        cf.read(file_name)
        port = cf.get(section_name, "static_file_addr").strip()
        return port
    except Exception,e:
        return 0
        
def LoadGearman(file_name, section_name):
    try:
        cf = ConfigParser.ConfigParser()
        cf.read(file_name)
        host = cf.get(section_name, "host").strip()
        port = cf.get(section_name, "port").strip()
        return (host, port)
    except Exception,e:
        return (None, None)

def LoadEnvironment(file_name, section_name):
    try:
        cf = ConfigParser.ConfigParser()
        cf.read(file_name)
        environment = cf.get(section_name, ITEM_ENVIRONMENT).strip()
        return environment
    except Exception,e:
        return None

def LoadNoteSender(file_name, section_name):
    try:
        cf = ConfigParser.ConfigParser()
        cf.read(file_name)
        purchase_manager = cf.get(section_name, ITEM_NOTE_SENDER_PURCHASE_MANAGER).strip()
        finance = cf.get(section_name, ITEM_NOTE_SENDER_FINANCE).strip()
        return (purchase_manager, finance)
    except Exception,e:
        return (None, None)

def LoadNoteReceive(file_name, section_name):
    try:
        cf = ConfigParser.ConfigParser()
        cf.read(file_name)
        promote = cf.get(section_name, ITEM_NOTE_RECEIVE_PROMOTE).strip()
        return promote
    except Exception,e:
        return None
        
def LoadDownloadPage(config_file_name, config_section_name):
    try:
        cf = ConfigParser.ConfigParser()
        cf.read(config_file_name)
        client_download_page = cf.get(config_section_name, ITEM_CLIENT_DOWNLOAD_PAGE)
        business_download_page = cf.get(config_section_name, ITEM_BUSINESS_DOWNLOAD_PAGE)
        print client_download_page
        print business_download_page
        return (client_download_page, business_download_page)
    except Exception,e:
        print e
        return (None, None)    

def LoadRedis(config_file_name, config_section_name):
    try:
        cf = ConfigParser.ConfigParser()
        cf.read(config_file_name)
        host = cf.get(config_section_name, ITEM_REDIS_HOST)
        port = cf.getint(config_section_name, ITEM_REDIS_PORT)
        db = cf.getint(config_section_name, ITEM_REDIS_DB)
        return (host, port, db)
    except Exception,e:
        print e
        return (None, None, None)
 
def LoadDatabase(config_file_name, config_section_name):
    try:
        cf = ConfigParser.ConfigParser()
        cf.read(config_file_name)
        host = cf.get(config_section_name, ITEM_DB_HOST)
        user = cf.get(config_section_name, ITEM_DB_USER)
        passwd = cf.get(config_section_name, ITEM_DB_PASSWD)
        db = cf.get(config_section_name, ITEM_DB_DB)
        return (host, user, passwd, db)
    except Exception,e:
        return (None, None, None, None)
        
def LoadMongoDb(config_file_name, config_section_name):
    try:
        cf = ConfigParser.ConfigParser()
        cf.read(config_file_name)
        host = cf.get(config_section_name, ITEM_MONGO_HOST)
        port = cf.get(config_section_name, ITEM_MONGO_PORT)
        db = cf.get(config_section_name, ITEM_MONGO_DB)
        return (host, port, db)
    except Exception,e:
        print e
        return (None, None, None)  

def LoadSystemDomain(config_file_name, config_section_name):
    try:
        cf = ConfigParser.ConfigParser()
        cf.read(config_file_name)
        image_domain = cf.get(config_section_name, ITEM_DOMAIN_IMAGE)
        pay_back_domain = cf.get(config_section_name, ITEM_DOMAIN_PAY_BACK)
        php_pay_domain = cf.get(config_section_name, ITEM_DOMAIN_PAY_PHP)
        return (image_domain, pay_back_domain, php_pay_domain)
    except Exception,e:
        print e
        return (None, None, None)  
        
        
def LoadWeixinPay(config_file_name, config_section_name):
    try:
        cf = ConfigParser.ConfigParser()
        cf.read(config_file_name)
        app_key = cf.get(config_section_name, ITEM_WEIXIN_APP_KEY)
        app_secret = cf.get(config_section_name, ITEM_WEIXIN_APP_SECRET)
        partnerid = cf.get(config_section_name, ITEM_WEIXIN_PARTNER_ID)
        partnerkey = cf.get(config_section_name, ITEM_WEIXIN_PARTNERKEY)
        trace_id = cf.get(config_section_name, ITEM_WEIXIN_TRACE_ID)
        paysignkey = cf.get(config_section_name, ITEM_WEIXIN_PAY_SIGNKEY)
        return (app_key, app_secret, partnerid, partnerkey, trace_id,paysignkey)
    except Exception,e:
        print e
        return (None, None, None, None, None)  
        
def LoadPushBaiduPay(config_file_name, config_section_name):
    try:
        cf = ConfigParser.ConfigParser()
        cf.read(config_file_name)
        app_key = cf.get(config_section_name, ITEM_BAIDU_PUSH_APP_KEY)
        app_secret = cf.get(config_section_name, ITEM_BAIDU_PUSH_APP_SECRET)
        return (app_key, app_secret)
    except Exception,e:
        print e
        return (None, None)

def LoadPushJpushPay(config_file_name, config_section_name):
    try:
        cf = ConfigParser.ConfigParser()
        cf.read(config_file_name)
        app_key = cf.get(config_section_name, ITEM_BAIDU_PUSH_APP_KEY)
        app_secret = cf.get(config_section_name, ITEM_BAIDU_PUSH_APP_SECRET)
        return (app_key, app_secret)
    except Exception,e:
        print e
        return (None, None)
