#coding=gbk

import hashlib
from struct import *

digit62 = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
def int_to_str62(x):
    tmp = x
    try:
        x=int(x)
    except:
        x=0
    if x<0:
        x=-x
    if x==0:
        return "0"
    s=""
    while x>62:
        x1= x % 62
        s = digit62[x1]+s
        x = x // 62
    if x>0:
        if x > 62:
            print '62 -> 10 erre:' + str(tmp)
        s = digit62[x]+s
    return s

def base62_decode(string):
    """Decode a Base X encoded string into the number

    Arguments:
    - `string`: The encoded string
    - `alphabet`: The alphabet to use for encoding
    """
    base = len(digit62)
    strlen = len(string)
    num = 0

    idx = 0
    for char in string:
        power = (strlen - (idx + 1))
        num += digit62.index(char) * (base ** power)
        idx += 1

    return num    

def get_url_id(url):
    if not url:
        return None
    tmp_msg_id = hashlib.md5(url).hexdigest()[0:8]
    msg_id = long(unpack('Q',tmp_msg_id)[0])
    return msg_id

def my_encode_url(url):
    int_url = get_url_id(url)
    return int_to_str62(int_url)
    
if __name__ == '__main__':
    test_62 = int_to_str62(13811678953)
    print test_62
    print base62_decode('sdlkfjs')
    
    
    print my_encode_url('http://www.baidu.com/s?ie=utf-8&f=8&rsv_bp=1&rsv_idx=1&tn=baidu&wd=mysql%20%E6%9D%A1%E4%BB%B6%20%E6%89%93%E5%8D%B0&rsv_pq=d6f1a990000005bc&rsv_t=3c72yijFp6fbQM%2BdJtRFtLFrIO6cHcXdva7nzjmCG%2BcC0wUSUUcT9QNFBYg&rsv_enter=1&inputT=7106&rsv_sug3=24&rsv_sug1=23&rsv_sug2=0&rsv_sug4=8007')