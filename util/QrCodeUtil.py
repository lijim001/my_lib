#coding=utf-8


import qrcode

def create_qr(input, file_name):
    try:
        img = qrcode.make(input)
        img.save(file_name)
        return True
    except Exception,e:
        return False
