#coding=utf-8

from kaker.util import global_variables

def random_number_generator_hash(possible_values, pic_url, start_num):    
    a = 63689
    b = 378551
    c = 97
    hash = 0
    if len(pic_url) >= 9:
        for char in pic_url[-9:-4]:
            hash = a * hash + ord(char)
            a = a * b % c
    else:
        for char in pic_url[:-4]:
            hash = a * hash + ord(char)
            a = a * b % c

    return hash % int(possible_values) + start_num
    
def format_pic_url(inner_path):
    if not inner_path or len(inner_path) == 0:
        return ''
    return 'http://' + str(random_number_generator_hash(global_variables.MY_HOST_PIC_NUM, inner_path, global_variables.MY_HOST_PIC_START_NUM)) + '.' + global_variables.MY_HOST_PIC_URL + 'azure/' + inner_path

def format_pic_url_no_azure(inner_path):
    if not inner_path or len(inner_path) == 0:
        return ''
    return 'http://' + str(random_number_generator_hash(global_variables.MY_HOST_PIC_NUM, inner_path, global_variables.MY_HOST_PIC_START_NUM)) + '.' + global_variables.MY_HOST_PIC_URL + inner_path
