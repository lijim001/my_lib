#coding=utf-8

import socket, struct

def encode_ip_to_int(ip):
    return socket.ntohl(struct.unpack("I",socket.inet_aton(str(ip)))[0])

def encode_int_to_ip(int_ip):
    return socket.inet_ntoa(struct.pack('I',socket.htonl(int_ip))) 