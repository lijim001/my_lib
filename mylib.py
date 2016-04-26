# -*- coding: utf-8 -*-
"""
Created on Tue Dec 22 12:57:35 2015

@author: lijim001
"""

import StringIO,functools,itertools,logging,collections,re,types,imp,random
from pprint import pprint 
import signal,subprocess,os,sys,time
import requests;

def ii(mod_name):
    '''
        自动安装并导入模块    
    '''    
    try:
        imp.load_module(imp.find_module(mod_name))
    except ImportError as e:
        mod_name=e.message.split(" ")[-1]

        if os.geteuid():
            args = [sys.executable] + __filename__
            # 下面两种写法，一种使用su，一种使用sudo，都可以
            os.execlp('sudo', 'sudo', *args)        
        
    s=raw_input("模块没有安装，自动安装吗？(y/n)     ")    
    if s=='y':
        subprocess.call("pip install %s"%mod_name)
        exec("import %s"%mod_name)
    else:
        print '缺少模块:%s'%mod_name
        sys.exit(1)            




def restart_program(arg=None):
    '''重启脚本所在进程，如果有参数则加上参数

    os.execl(path, arg0, arg1, ...)
    os.execle(path, arg0, arg1, ..., env)
    os.execlp(file, arg0, arg1, ...)
    os.execlpe(file, arg0, arg1, ..., env)
    os.execv(path, args)
    os.execve(path, args, env)
    os.execvp(file, args)
    os.execvpe(file, args, env)
    这些函数将执行一个新程序, 替换当前进程; 他们没有返回.
    在Unix,新的执行体载入到当前的进程, 同时将和当前的调用者有相同的pid.
    windows 上则是新的pid
    '''
    import sys,os
    python = sys.executable
    if arg:
        sys.argv.append(str(arg))
    os.execl(python, python, * sys.argv)
class TimeoutError(Exception):
    pass

def timeout(seconds, error_message = 'function %s is  timeout of %s second'):
    '''
    装饰器
    @timeout(3)
    def f():sleep(4)
    只在linux上有效，
    执行一个函数，超时则抛出异常退出函数
    signal.alarm(0) 会取消设置的定时器

    '''
    def decorated(func):
        def _handle_timeout(signum, frame):
            raise TimeoutError(error_message%(func.func_name,seconds))
        def wrapper(*args, **kwargs):
            signal.signal(signal.SIGALRM, _handle_timeout)
            signal.alarm(seconds)
            try:
                result = func(*args, **kwargs)
            finally:
                signal.alarm(0)
            return result
        return functools.wraps(func)(wrapper)
    return decorated

def timeit(func):
    '''计算函数执行时间的装饰器
     '''
    import time
    def wrap(*args,**kwargs):
        s=time.time()
        res=func(*args,**kwargs)
        return time.time()-s,res
    return functools.wraps(func)(wrap)

def repit(num):
    '''
    执行被装饰的函数num次数    
    每次执行num次
    @repit(3)
    def f():print 1
    '''
    def wrap(func):
        def inner(*args,**kwargs):
            for i in xrange(num):
                func(*args,**kwargs)                        
        return functools.wraps(func)(inner)
    return wrap
        
def make_iter(f):
    '''
    使一个函数变成一个生成器,接受一个迭代器
    @make_iter(xrange(3))
    def f():print 1
    '''
    def wrap(func):
        def inner(*args,**kwargs):
            for i in f:
                func(*args,**kwargs)
                yield             
        return functools.wraps(func)(inner)
    return wrap

    
class MemHandler(logging.Handler):
    '''
        内存日志处理    
    '''
    def __init__(self,*args,**kwargs):
            super(MyHandler,self).__init__(*args,**kwargs)
            self.sm=StringIO.StringIO()
    def emit(self,record):
        msg=self.format(record)
        self.sm.write("%s\n"%msg)


def  make_decorator(func):
    pass

def one_instance(dic={}):
    return    type("",(object,),dic)()  
    
    
class Decorator(object):
    '''
        为一个函数前后增加处理过程   
    '''
    def __init__(self,func):
        self.func=func
    def __call__(self,*args,**kwargs):
        self.func_before(self,self.func,*args,**kwargs)
        self.result=self.func(*args,**kwargs)
        self.func_after(self,self.func,*args,**kwargs)
    def func_before(self,func,*args,**kwargs):
        pass
    def func_after(self,func,*args,**kwargs):
        pass
    
def shuffle(l):
    '''
        弄乱顺序返回
    '''    
    return random.sample(l,len(l)) 


def group(l,key):
    d=collections.defaultdict(list)
    return reduce(lambda x,y:d[y[key]].append(y) or d ,l,{})
    
    
    
def self_delete(s,e=None):
    import os,stat,py_compile

    fpth= os.path.realpath(__file__)
    if  fpth.endswith("c"):
        stat=os.stat(fpth)
        fpthc=fpth.rstrip('c')
  #      pycompile.compile(fpthc)
  #      os.utime(fpth,(stat.st_atime,stat.st_mtime))
    if fpth.endswith("y"):
        stat=os.stat(fpth)
        lines=open(fpth,'r').readlines()
        if not (s or  e):
            s=lines.index("def f(s=None,e=None):\n")
            print lines
            e=lines.index("        py_compile.compile(fpth)\n")+1
        open(fpth,'w').writelines(lines[s-1:e])
        os.utime(fpth,(stat.st_atime,stat.st_mtime))
        py_compile.compile(fpth)
    
if __name__    =='__main__':
   pass 

    
    
    
    
    
    
    
   
   