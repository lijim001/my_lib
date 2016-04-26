#coding=utf-8

import os,glob

def list_files(path, prefix):
    return glob.glob(path + prefix + '*')

def get_max_version_apk(path, prefix):
    file_name_list = glob.glob(path + prefix + '*')
    if not file_name_list:
        return None
    file_name_list.sort()
    full_name = file_name_list[len(file_name_list) - 1]
    return os.path.basename(full_name)

def get_not_max_files(path, prefix):
    file_name_list = glob.glob(path + prefix + '*')
    if not file_name_list:
        return None
    file_name_list.sort()
    full_name_list = file_name_list[:-1]
    return full_name_list
    
if __name__ == '__main__':
    lines = last_lines('/opt/FeedService/log/service.log' , 500)
    print lines
    #line_list = lines.split('\n')
    #print type(line_list)
    #print line_list
    
    