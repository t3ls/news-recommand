#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Web Build Module
# Author: t3ls (https://github/t3ls/)
# Designed for BUPT course: Practice of Large Program Design
# Create date: 2019/07/01

import codecs
import pymysql
import asyncio
import os
import requests
from config import *
from datetime import datetime

MAX_HOTKEY = 20 # 热词显示数
DISPLAY_ARTICALS = 1500 # 网站新闻数
timestamp = ''
CATEGORIES = ['时政','科技','军事','财经','体育','娱乐','教育'] # 新闻分类

TIMESTAMP_API = 'http://quan.suning.com/getSysTime.do' # 时间API

# 初始化数据库
conn = pymysql.connect(host=DB_HOST,	
    port=int(DB_PORT),
    user=DB_USER,
    password=DB_PASS,
    db=DB_NAME,
    charset=DB_CHARSET
    )
cursor = conn.cursor()


def get_articles() -> None:
	# 获取文章并以markdown格式生成
	global timestamp
	cursor.execute(
		'SELECT * FROM `webpage_text` ORDER BY `time` desc'
		)
	result = cursor.fetchmany(DISPLAY_ARTICALS)
	for i in os.listdir('web/source/_posts/'):
		os.remove('web/source/_posts/'+i)
	for article in result:
		category = '军事' if article[1] == '军事' else article[8] # cnn_predict
		date = article[6][:4]+'-'+article[6][4:6]+'-'+article[6][6:8]
		if category not in CATEGORIES:
			category = '其它'
		if (datetime.strptime(timestamp, '%Y%m%dT%H%M%SZ') - datetime.strptime(article[6], '%Y%m%dT%H%M%SZ')).days <= 1:
			if article[1] == '要闻':
				category = '[要闻,'+category+']'
		md = '---\ntitle: {0}\ndate: {1}\ncategories: {2}\n---\n'.format(article[3].replace('@',''), date, category)
		md += '## 阅读原文：{0}\n\n## 引自：{1}\n\n{2}\n'.format(article[2],article[7],article[4])
		with codecs.open('web/source/_posts/%s.md'%article[5], 'w', 'utf-8') as f:
			f.write(md)



def get_hot_key() -> (list, list):
	# 获取热词及词频
	global cursor, conn
	key_name, total = [], []
	cursor.execute(
		'SELECT `key_name`,`total` FROM `hot_key`' +
		'ORDER BY `id` asc'
		)
	result = cursor.fetchmany(MAX_HOTKEY)
	for i in result:
		key_name.append(i[0])
		total.append(i[1])
	return key_name, total


def gen_config_yml(key_name: list, amount: list) -> None:
	# 根据热词构建网页config文件
	template = ''
	with codecs.open('web/yml_part1.yml', 'r', 'utf-8') as f1:
		with codecs.open('web/yml_part2.yml', 'r', 'utf-8') as f2:
			for i in range(len(key_name)):
				template += ' ' * 10
				template += '<a class="category-list-link" href="#">'
				template += '{0}</a>\n          <span class="category-list-count">{1}</span>\n          &nbsp;&nbsp;\n'.format(key_name[i],amount[i])
			new_yml = f1.read() + template + f2.read()
			with codecs.open('web/themes/polarbear/_config.yml', 'w', 'utf-8') as f3:
				f3.write(new_yml)


def get_timestamp() -> None:
	# 获取当前时间
    global timestamp
    r = requests.get(TIMESTAMP_API)
    timestamp = r.json()['sysTime1']
    timestamp = timestamp[0:8]+'T'+timestamp[8:]+'Z'

if __name__ == '__main__':
	# 入口点
	get_timestamp()
	key_name,total = get_hot_key()
	gen_config_yml(key_name, total)
	get_articles()
	print('[+] Success')
	os.chdir('web')
	# 网页生成
	os.system('hexo g')
	# 部署
	os.system('hexo s')
