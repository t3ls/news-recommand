#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Json2Db Module
# Author: t3ls (https://github/t3ls/)
# Designed for BUPT course: Practice of Large Program Design
# Create date: 2019/07/01

import pymysql
import os
import json
import logging
import codecs
import spider_modules
import hashlib
import asyncio
from spider_modules import *

# 将Output目录中的JSON文件写入数据库
def Json2Db(json_dir: str = 'spider_modules/Output/') -> None:
	for filename in os.listdir(json_dir):
		if filename.find('Spider-') < 0 or filename.find('.json') < 0:
			continue
		_news_dict = str()
		with codecs.open(json_dir+filename, 'r', 'utf-8') as f:
			_news_dict = f.read()
		_draw_from = filename.split('-')[1]
		_time = filename.split('-')[2].split('.')[0]
		row = {
			'draw_from': _draw_from,
			'news_dict': _news_dict,
			'time': _time,
			'flag': 0,
			'hash': hashlib.md5(_news_dict.encode('utf-8')).hexdigest()
			}
		conn = pymysql.connect(host=DB_HOST,
                        port=int(DB_PORT),
                        user=DB_USER,
                        password=DB_PASS,
                        db=DB_NAME,
                        charset='utf8'
                        )
		cursor = conn.cursor()
		cursor.execute(
			'SELECT `id`, `flag` FROM `original_news`' +
			'WHERE hash="%s"' % row['hash']
			)
		result = cursor.fetchone()
		if result != None:
			if str(result[1]) == '0':
				print('[-] same hash detected')
				continue
		effect_row = cursor.execute(
    		'INSERT INTO `original_news` (`draw_from`, `news_dict`, `time`, `flag`, `hash`) ' +
    		'VALUES (%(draw_from)s, %(news_dict)s, %(time)s, %(flag)s, %(hash)s)', row
    		)
		conn.commit()
	print('[+] Successfully write2DB')


if __name__ == '__main__':
	Json2Db.Json2Db()

		
