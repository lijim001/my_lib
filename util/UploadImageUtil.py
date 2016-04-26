#coding=utf-8

import os,Image,stat

class ImageUploadUtil():
    def __init__(self, base_path, service_path):
        self.base_path = base_path
        self.service_path = service_path
        self.file_path_list = []
    
    def __del__(self):
        self.clear_upload_files()
    
    def get_file_path_list(self, request):
        for i in range(0, 10):
            if i == 0:
                key = 'file.path'
            else:
                key = 'file%s.path'%(str(i))
            file_path = request.REQUEST.get(key, '')
            if not file_path:
                continue
            self.file_path_list.append(file_path)
        print self.file_path_list
        return self.file_path_list
    
    def clear_upload_files(self):
        for file_path in self.file_path_list:
            os.system('rm -f %s'%(file_path))
        
    def handle(self, seq, sub_path, file_name):
        if seq < 0 or seq >= len(self.file_path_list):
            return ('', '')
        file_path = self.file_path_list[seq]
        check_path = os.path.join(self.base_path, sub_path)
        try:
            os.makedirs(check_path)
        except Exception,e:
            pass
        new_file = os.path.join(check_path, file_name)
        os.system('mv -f %s %s'%(file_path, new_file))
        os.chmod(new_file, stat.S_IREAD|stat.S_IWRITE|stat.S_IRGRP|stat.S_IROTH)
        #print self.service_path + sub_path + file_name
        result = self.service_path
        if sub_path:
            result += sub_path + '/'
        result += file_name
        return (result, new_file)
    
    def do_image_thumbnail(self, file_path, url, size):
        try:
            file_info = file_path.split('.')
            new_file_path = file_info[0] + '_' + str(size) + '.' + file_info[1]
            
            pos = new_file_path.rfind('/')
            if pos == -1:
                return ('','')
            pos_url = url.rfind('/')
            if pos_url == -1:
                return ('','')            
            new_file = new_file_path[pos+1:]
            new_url = url[:pos_url+1] + new_file
            # im = Image.open(file_path)
            # im = im.convert('RGB')
            # im = im.resize((size,size))
            # print 'save %s'%(str(new_file_path))
            # im.save(new_file_path)
            if not self.do_thumbnail(file_path, new_file_path, size):
                return ('', '')
            return (new_url, new_file_path)
        except Exception,e:
            print e
            return ('', '')

    def do_thumbnail(self, file_path, new_file_path, size):
        try:
            im = Image.open(file_path)
            im = im.convert('RGB')
            width, high = im.size
            min_size = min(width, high)
            if min_size == width:
                point_high = int((high - width) / 2)
                box = (0, point_high, min_size, min_size)
                im = im.crop(box) 
            else:
                point_width = int((width - high) / 2)
                box = (point_width, 0, min_size, min_size)
                im = im.crop(box)
            
            im = im.resize((size,size))
            im.save(new_file_path)
            return True
        except Exception,e:
            print e
            return False
            
if __name__ == '__main__':
    lines = last_lines('/opt/FeedService/log/service.log' , 500)
    print lines
    #line_list = lines.split('\n')
    #print type(line_list)
    #print line_list
    
    