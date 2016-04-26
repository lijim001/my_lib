#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Copyright(c) 2010 poweredsites.org

Licensed under the Apache License, Version 2.0 (the 'License'); you may
not use this file except in compliance with the License. You may obtain
a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an 'AS IS' BASIS, WITHOUT
WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
License for the specific language governing permissions and limitations
under the License.
'''

import time
import hashlib

# 全局缓存字典
_G_CACHE = {}

def mem_cache(expire=7200, key='', maxlen=100000, start=0):
    '''
    内存缓存装饰器
    @expire: 失效时间, 秒
    @key: 指定键值
    @maxlen: 缓存数据的最大长度
    @start: 从开始计算的参数下标
    return: 装饰器
    '''
    def wrapper(func):
        '''
        缓存装饰器
        '''
        def mem_wrapped_func(*args, **kwargs):
            '''
            装饰后的函数
            '''
            now = time.time()
            cache_key = _gen_mem_key(key or repr(func), *(args[start:]), **kwargs)
            value = _G_CACHE.get(cache_key, None)
            if _is_valid_cache(value, now):
                return value['value']
            else:
                val = func(*args, **kwargs)
                assert len(str(val)) <= maxlen
                _G_CACHE[cache_key] = {'value':val, 'expire':now + expire}
                return val
        return mem_wrapped_func
    return wrapper

def _gen_mem_key(key, *args, **kwargs):
    '''
    生成内存缓存Cache的Key
    @key: 函数的Key, 默认为函数名
    @args: 位置参数列表
    @kwargs: 关键字参数
    return: 内存缓存Key
    '''
    code = hashlib.md5()
    code.update(str(key))
    code.update(''.join(sorted([str(i) for i in args])))
    code.update(''.join(sorted([str(i) for i in kwargs.iteritems()])))
    return code.hexdigest()

def _is_valid_cache(value, now):
    '''
    缓存是否有效
    @value: 缓存的数据, 包括原始数据、失效时间
    @now: 当前时间戳
    return: 是否有效
    '''
    if value and value['expire'] > now:
        return True
    return False

def purge_cache():
    '''
    清除内存cache
    return: None
    '''
    _G_CACHE.clear()

