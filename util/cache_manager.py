#coding=utf-8

if __name__ == '__main__':
    import os,sys
    G_PATH = os.path.split(os.path.realpath(__file__))[0]
    sys.path.append(G_PATH + '/../../')
    os.environ['DJANGO_SETTINGS_MODULE'] = 'kaker.settings'
from django.core.cache import get_cache

class CacheManager():
    def __init__(self):
        self.cache = get_cache('default')
    
    def save_list(self, key, input_list, timeout):
        self.cache.set(key, input_list, timeout)
        
    def get_list(self, key, start, num):
        output_list = self.cache.get(key)
        if not output_list:
            return None
        return output_list[start: start + num]
        
    def delete_key(self, key):
        return self.cache.delete(key)
        
    def get_key(self, key):
        return self.cache.get(key)
        
    def save_key(self, key, value, timeout=None):
        if timeout:
            self.cache.set(key, value, timeout)
        else:
            self.cache.set(key, value)

if __name__ == '__main__':
    cache = CacheManager()
    cache.save_key('test_ssosun','woqu,niqusi')
    print cache.get_key('test_ssosun')
    print cache.delete_key('test_ssosun')