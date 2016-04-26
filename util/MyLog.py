#coding=utf-8

import logging,os,ConfigParser
import traceback, sys, datetime,time

from logging.handlers import TimedRotatingFileHandler

ITEM_LEVEL = "level"

MyLogLevel = {"NOTSET" : logging.NOTSET, "DEBUG" : logging.DEBUG, "INFO" : logging.INFO, "WARNING": logging.WARNING, "ERROR" : logging.ERROR, "CRITICAL" : logging.CRITICAL}

_filefmt=os.path.join("logs","%Y-%m-%d","%H.log")

class MyLoggerHandler(logging.Handler):
    def __init__(self,filefmt=None):
        self.filefmt=filefmt
        if filefmt is None:
            self.filefmt=_filefmt
        logging.Handler.__init__(self)
        self._dir = os.path.dirname(self.filefmt)
        self._fileName = os.path.basename(self.filefmt)
        self.current_time = None
        self._fobj = None
        self._filePath = None

    def check_date(self):
        current_time = datetime.datetime.now().strftime("%Y%m%d")
        if current_time == self.current_time:
            return
        self.current_time = current_time
        self._filePath = os.path.join(self._dir, self._fileName + '.' + self.current_time)
        if self._fobj:
            self._fobj.flush()
            self._fobj.close()
        try:
            self._fobj = open(self._filePath, 'a')
        except Exception:
            print "can not open file"
            
    def emit(self,record):
        msg = self.format(record)
        self.check_date()
        try:
            self._fobj.write(msg)
            self._fobj.write("\n")
            self._fobj.flush()
        except Exception:
            print "write to file failed "
            
def CreateLoggerScreen(loggerName, fileName, level="INFO"):
    logger = logging.getLogger(loggerName) 
    logger.setLevel(MyLogLevel[level]) 
    fh = logging.FileHandler(fileName) 
    fh.setLevel(MyLogLevel[level]) 
    ch = logging.StreamHandler() 
    ch.setLevel(MyLogLevel[level]) 
    formatter = logging.Formatter('%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s%(message)s') 
    fh.setFormatter(formatter) 
    ch.setFormatter(formatter) 
    logger.addHandler(fh) 
    logger.addHandler(ch)
    
def CreateLoggerScreenByMyHandlerConfig(loggerName, fileName, config_file_name, config_section_name):
    cf = ConfigParser.ConfigParser()
    cf.read(config_file_name)
    level = cf.get(config_section_name, ITEM_LEVEL)
    logger = logging.getLogger(loggerName) 
    logger.setLevel(MyLogLevel[level]) 
    ch = logging.StreamHandler() 
    ch.setLevel(MyLogLevel[level]) 
    fileTimeHandler = TimedRotatingFileHandler(fileName, when="midnight")
    fileTimeHandler.suffix = "%Y%m%d.log"
    formatter = logging.Formatter('%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s%(message)s') 
    ch.setFormatter(formatter)
    fileTimeHandler.setFormatter(formatter)
    logger.addHandler(ch)
    logger.addHandler(fileTimeHandler)

def CreateLoggerScreenByConfig(loggerName, fileName, config_file_name, config_section_name):
    cf = ConfigParser.ConfigParser()
    cf.read(config_file_name)
    level = cf.get(config_section_name, ITEM_LEVEL)
    
    logger = logging.getLogger(loggerName) 
    logger.setLevel(MyLogLevel[level]) 
    fh = MyLoggerHandler(fileName) 
    fh.setLevel(MyLogLevel[level]) 
    ch = logging.StreamHandler() 
    ch.setLevel(MyLogLevel[level]) 

    formatter = logging.Formatter('%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s%(message)s') 
    fh.setFormatter(formatter) 
    ch.setFormatter(formatter) 
    logger.addHandler(fh) 
    logger.addHandler(ch)
    
def MyLogExcept(logger):
    if not logger:
        return
    info = sys.exc_info()
    for file, lineno, function, text in traceback.extract_tb(info[2]):
        logger.error('%s line:%s in %s'%(file,str(lineno), function))
        logger.error('%s'%(text))
    logger.error("** %s: %s"%info[:2])
    
if __name__ == '__main__':
    MY_PAY_LOGGERFILE = './test.log'
    MY_MOBILE_SERVICE_CONFIG = '../conf/service.ini'
    CreateLoggerScreenByMyHandlerConfig('pay_service', MY_PAY_LOGGERFILE, MY_MOBILE_SERVICE_CONFIG, 'pay_log')
    pay_logger = logging.getLogger("pay_service")
    while 1:
        pay_logger.info('jalkdfsdf1233')
        time.sleep(1)
    