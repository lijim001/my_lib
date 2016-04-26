#coding=utf-8

import urllib,os,sys,time
from datetime import date, timedelta

class PerDayActionUtil():
    def __init__(self, save_history_file):
        self.date_action_dict = {}
        self.save_file = open(save_history_file, 'a+')
        self.load_history()
        
    def load_history(self):
        for line in self.save_file:
            items = line.split('\t')
            if len(items) != 2:
                continue
            action_date = items[0]
            condition = items[1]
            self.date_action_dict[action_date] = condition
            
    def sync_history(self):
        date_list = self.date_action_dict.keys()
        date_list.sort(reverse=True)
        save_date_list = date_list[:5]
        un_save_date_list = date_list[5:]
        try:
            for date in save_date_list:
                self.save_file.write('%s\t1\n'%(date))
            for date in un_save_date_list:
                del self.date_action_dict[date]
        except Exception,e:
            print e
            
    def check_yestody(self):
        now = date.today()
        yestoday = str(now - timedelta(days=1))
        if self.date_action_dict.has_key(yestoday):
            return False
        else:
            return True
        
    def do_yestody(self):
        now = date.today()
        yestoday = str(now - timedelta(days=1))
        self.date_action_dict[yestoday] = 1
        self.sync_history()
        
        
if __name__ == '__main__':
    day_action = PerDayActionUtil('.sync_log')
    print day_action.check_yestody()
    day_action.do_yestody()
    print day_action.check_yestody()
    