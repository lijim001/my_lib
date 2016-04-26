#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
图像操作
'''

import Image
import logging
import StringIO

class ImageOper(object):
    '''
    图像操作类
    '''
    def __init__(self, data):
        '''
        @data: 图书原始数据
        '''
        if isinstance(data, Image.Image):
            self.image = data
        else:
            self.image = Image.open(StringIO.StringIO(data))

    def get_image_size(self):
        '''
        @return: 图片的尺寸
        '''
        return self.image.size

    def get_image_format(self):
        '''
        @return: 图片的格式
        '''
        return self.image.format

    def get_image_data(self):
        '''
        取得图像的数据
        '''
        f = StringIO.StringIO()
        self.image.save(f, self.get_image_format())
        data = f.getvalue()
        f.close()
        return data

    def resize(self, width, height, mode=Image.ANTIALIAS):
        '''
        对图像进行缩放
        @width: 缩放的宽
        @height: 缩放的高
        @mode: 缩放的模式
        @return: 缩放后的图像数据
        '''
        try:
            result = self.image.resize((width, height), mode)
        except IOError as e:
            logging.warn('error when resize by %s, %s', mode, str(e), exc_info=True)
            result = self.image.resize((width, height), Image.BILINEAR)
        f = StringIO.StringIO()
        result.save(f, self.get_image_format())
        data = f.getvalue()
        f.close()
        return data

    def save_file(self, file_name, quality=100):
        '''
        保存到文件
        @file_name: 文件名
        @quality: 质量
        '''
        with open(file_name, 'wb') as f:
            self.image.save(f, self.get_image_format(), quality=quality)

