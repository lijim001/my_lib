#coding=utf-8
import redis

RETRY_TIMES = 3

class MyBaseRedis():
    def __init__(self, host, port, db):
        self.host = host
        self.port = int(port)
        self.db = int(db)
        self.r = redis.Redis(host=self.host, port=self.port, db=self.db)
            
    def re_connect(self):
        try:
            self.r = redis.Redis(host=self.host, port=self.port, db=self.db)
        except Exception,e:
            return False
        else:
            return True

class StringRedis(MyBaseRedis):
    def __init__(self, host, port, db):
        MyBaseRedis.__init__(self,  host, port, db)
        
    def save(self, key, value, timeout = 0):
        for i in range(RETRY_TIMES):
            try:
                pipe = self.r.pipeline()
                pipe.set(key, value)
                if timeout != 0:
                    pipe.expire(str(key), timeout)
                pipe.execute()
                return True
            except Exception,e:
                self.re_connect()
        return False
                
    def get(self, key):
        for i in range(RETRY_TIMES):
            try:
                return self.r.get(key)
            except Exception,e:
                self.re_connect()
              