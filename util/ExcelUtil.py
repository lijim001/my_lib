#coding=utf-8

import xlrd,xlwt
import os,time,re,sys

if __name__ == '__main__':
    G_PATH = os.path.split(os.path.realpath(__file__))[0]
    sys.path.append(G_PATH + '/../../')
    os.environ['DJANGO_SETTINGS_MODULE'] = 'MobileService.settings'
    
    from django.conf import settings
from MobileService.util.DbUtil import DbUtil    
    
class ExcelUtil(DbUtil):
    def __init__(self, database):
        self.info_logger = database['mobile_logger']
        self.db = database['mobile_db']    
        DbUtil.__init__(self, self.db, self.info_logger)
        self.database = database
        
    def collect_data(self, sql, file_name, sheet_name):
        data_infos = sql.split('from')
        if len(data_infos) != 2:
            return
        search_data = data_infos[0]
        regx = re.compile(r'as\s+([^,\s]*?)[,\s]')
        column_list = regx.findall(search_data)
        print column_list
        ret_datas = self.do_query(sql)
        self.do_excel_write(file_name, sheet_name, column_list, ret_datas)
    
    def do_excel_write(self, file_name, sheet_name, header_list, data_list):
        book = xlwt.Workbook(encoding = 'utf-8')
        sheet = book.add_sheet(sheet_name)
        for i in range(0, len(header_list)):
            sheet.write(0, i, header_list[i])
        row_len = len(data_list)
        for i in range(1, row_len+1):
            row_data = data_list[i-1]
            for j in range(0, len(row_data)):
                sheet.write(i, j, row_data[j])
        book.save(file_name)
        
    def do_query(self, sql):
        self.get_db_connect()
        try:
            count = self.cursor.execute(sql)
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
                self.logger.error('do_query except %s'%(e))
            self.release_db_connect()    
            return []

if __name__ == '__main__':
    handler = ExcelUtil(settings.COMMON_DATA)
    sql = 'select us.name as 名字,ll.user_phone as 手机号,if(ll.type=10,6,12) as 类型,ll.lottery_name as 奖品,us.province as 省份,DATE_FORMAT(ll.create_time,"%Y-%m-%d") as 时间 from lottery_list ll inner join user_shop us on us.telephone=ll.user_phone where ll.create_time > "2015-1-29 0:0:0" and ll.create_time < "2015-1-30 0:0:0"'
    handler.collect_data(sql, 'test.xls', '1.30')
            