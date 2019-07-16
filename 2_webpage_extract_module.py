#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Web Page Content Extraction Module
# Author: t3ls (https://github/t3ls/)
# Designed for BUPT course: Practice of Large Program Design
# Create date: 2019/07/01

import asyncio
import os
import re
import json
import chardet
import requests
import hashlib
from tqdm import tqdm
import pymysql
from config import *


if DEBUG:
    # 初始化网页正文提取字数阈值
    THRESHOLD = 86


# 初始化进度条及数据库连接
pbar = tqdm
conn = pymysql.connect(host=DB_HOST,
            port=int(DB_PORT),
            user=DB_USER,
            password=DB_PASS,
            db=DB_NAME,
            charset=DB_CHARSET
            )



class CxExtractor(object):
    # 基于行块分布函数的通用网页正文抽取算法

    __text = [] # 直接提供处理后的text
    __indexDistribution = [] # 自定义


    def __init__(self, threshold=86, blocksWidth=3) -> None:
        # 设置行块宽度与正文骤升点阈值
        self.__blocksWidth = blocksWidth
        self.__threshold = threshold


    async def getText(self, content: str) -> str:
        # 基于HTML文件的方块分布正文提取算法主逻辑
        if self.__text:
            self.__text = []

        # 行切分，去除空白字符
        lines = content.split('\n')
        for i in range(len(lines)):
            lines[i] = re.sub("\r|\n|\\s{2,}", "",lines[i])

        # 获取行块及行块包含的字符数
        self.__indexDistribution.clear()
        for i in range(0, len(lines) - self.__blocksWidth):
            wordsNum = 0
            for j in range(i, i + self.__blocksWidth):
                lines[j] = lines[j].replace("\\s", "")
                wordsNum += len(lines[j])
            self.__indexDistribution.append(wordsNum)

        start = -1
        end = -1
        boolstart = False
        boolend = False

        # 判断行块个数，小于3时直接返回
        if len(self.__indexDistribution) < 3:
            return 'This page has no content to extract'

        # 循环行块，提取正文
        for i in range(len(self.__indexDistribution) - 3):
            if(self.__indexDistribution[i] > self.__threshold and (not boolstart)):
                # 判断行块字数是否小于阈值
                if (self.__indexDistribution[i + 1] != 0 or self.__indexDistribution[i + 2] != 0 or self.__indexDistribution[i + 3] != 0):
                    # 判断骤升点附近是否存在空块，若否则设置正文起点索引
                    boolstart = True
                    start = i
                    continue
            if (boolstart):
                # 判断是否存在骤降点，若是则设置正文终点索引
                if (self.__indexDistribution[i] == 0 or self.__indexDistribution[i + 1] == 0):
                    end = i
                    boolend = True
            tmp = []
            if(boolend):
                # 添加正文内容
                for ii in range(start, end + 1):
                    if(len(lines[ii]) < 5):
                        # 字数太少
                        continue
                    tmp.append(lines[ii] + "\n")
                str = "".join(list(tmp))
                if ("Copyright" in str or "版权所有" in str):
                    # 版权信息
                    continue
                self.__text.append(str)
                boolstart = boolend = False

        # 返回正文
        result = "".join(list(self.__text))
        if result == '':
            return 'This page has no content to extract'
        else:
            return result


    async def replaceCharEntity(self, htmlstr: str) -> str:
        # 替换转义后的字符
        CHAR_ENTITIES = {'nbsp': ' ', '160': ' ',
                         'lt': '<', '60': '<',
                         'gt': '>', '62': '>',
                         'amp': '&', '38': '&',
                         'quot': '"', '34': '"', }
        re_charEntity = re.compile(r'&#?(?P<name>\w+);')
        sz = re_charEntity.search(htmlstr)
        while sz:
            entity = sz.group()
            key = sz.group('name')
            try:
                htmlstr = re_charEntity.sub(CHAR_ENTITIES[key], htmlstr, 1)
                sz = re_charEntity.search(htmlstr)
            except KeyError:
                htmlstr = re_charEntity.sub('', htmlstr, 1)
                sz = re_charEntity.search(htmlstr)
        return htmlstr


    async def getHtml(self, url: str) -> str:
        # 获取网页并识别编码
        if not url.startswith('http'):
            return None
        try:
            response = requests.get(url)
        except ConnectionResetError as e:
            return None
        except requests.exceptions.ConnectionError as e:
            return None
        encode_info = chardet.detect(response.content)
        response.encoding = encode_info['encoding'] if encode_info['confidence'] > 0.5 else 'utf-8'
        return response.text


    async def readHtml(self, path: str, coding: str) -> str:
        # 循环分析HTML行
        page = open(path, encoding=coding)
        lines = page.readlines()
        s = ''
        for line in lines:
            s += line
        page.close()
        return s


    async def filter_tags(self, htmlstr: str) -> str:
        # 预处理，识别HTML无关标签并进行过滤
        re_doctype = re.compile('<![DOCTYPE|doctype].*>')
        re_nav = re.compile('<nav.+</nav>')
        re_cdata = re.compile('//<!\[CDATA\[.*//\]\]>', re.DOTALL)
        re_script = re.compile(
            '<\s*script[^>]*>.*?<\s*/\s*script\s*>', re.DOTALL | re.I)
        re_style = re.compile(
            '<\s*style[^>]*>.*?<\s*/\s*style\s*>', re.DOTALL | re.I)
        re_textarea = re.compile(
            '<\s*textarea[^>]*>.*?<\s*/\s*textarea\s*>', re.DOTALL | re.I)
        re_br = re.compile('<br\s*?/?>')
        re_h = re.compile('</?\w+.*?>', re.DOTALL)
        re_comment = re.compile('<!--.*?-->', re.DOTALL)
        re_space = re.compile(' +')
        s = re_cdata.sub('', htmlstr)
        s = re_doctype.sub('',s)
        s = re_nav.sub('', s)
        s = re_script.sub('', s)
        s = re_style.sub('', s)
        s = re_textarea.sub('', s)
        s = re_br.sub('', s)
        s = re_h.sub('', s)
        s = re_comment.sub('', s)
        s = re.sub('\\t', '', s)
        s = re_space.sub(' ', s)
        return await self.replaceCharEntity(s)


async def _get_url_from_dict(result: list, dict_file: list) -> list:
    # 遍历JSON文件，返回文章信息
    for i in dict_file:
        if type(i) == list:
            await _get_url_from_dict(result, i)
        else:
            for key,value in i.items():
                if key == 'url' and value not in result:
                    try:
                        result.append(i)
                    except:
                        pass
                elif type(value) == dict:
                    tmp = []
                    tmp.append(value)
                    await _get_url_from_dict(result, tmp)
                elif type(value) == list:
                    await _get_url_from_dict(result, value)
    return result


async def get_url_from_db() -> (list, list):
    # 从数据库中获取文章url及相关信息
    global conn
    url_list, result, hash_list = [], [], []
    cursor = conn.cursor()
    cursor.execute(
        'SELECT `original_news`.`news_dict`, `original_news`.`hash` '+
        'FROM `original_news`'+
        'WHERE `original_news`.`flag` = 0'
        )
    
    for json_file in cursor.fetchall():
        result.append(json.loads(json_file[0]))
        cursor.execute(
            'UPDATE `original_news` SET flag=1 WHERE hash="%s"' % json_file[1]
            )
        conn.commit()

    """ No json file get from db """
    if len(result) == 0:
        return

    return await _get_url_from_dict(url_list, result), hash_list


async def get_page_text(cx: CxExtractor, page: dict) -> str:
    # 获取正文并写入数据库
    global pbar
    pbar.update(1)
    row = {}
    # print('[*] Getting page text')
    html = await cx.getHtml(page['url'])
    if html == None:
        return
    content = await cx.filter_tags(html)
    text = await cx.getText(content)
    cursor = conn.cursor()
    # print('[*] building row:',page)
    try:
        row['url'] = page['url']
        row['page_text'] = text
        row['category'] = page['category']
        row['title'] = page['title']
        row['time'] = page['refer_time']
        row['refer_from'] = page['refer_name']
        row['hash'] = hashlib.md5(text.encode('utf-8')).hexdigest()
    except Exception as e:
        # print(page)
        return
    cursor.execute('SELECT `id` FROM `webpage_text` WHERE hash="%s"' % row['hash'])
    result = cursor.fetchone()
    if result != None:
        # print('[-] same hash detected')
        return
    cursor.execute('SELECT `id` FROM `webpage_text` WHERE url="%s"' % row['url'])
    result = cursor.fetchone()
    if result == None:
        cursor.execute(
            'INSERT INTO `webpage_text` (`url`, `page_text`, `hash`, `page_title`, `category`, `time`, `refer_from`)'+
            'VALUES (%(url)s, %(page_text)s, %(hash)s, %(title)s, %(category)s, %(time)s, %(refer_from)s)', row
            )
        # print('[+] Insert Success')
    else:
        cursor.execute(
            'UPDATE `webpage_text` SET cnn_predict=NULL,'+
            'page_text="%(page_text)s", hash="%(hash)s", page_title="%(title)s", category="%(category)s", time="%(time)s",  refer_from="%(refer_from)s" WHERE url="%(url)s"', row
            )
        # print('[+] Update Success')
    conn.commit()



def run() -> None:
    # 入口点
    global pbar
    loop = asyncio.get_event_loop()
    cx = CxExtractor(threshold=THRESHOLD)
    url_info = loop.run_until_complete(get_url_from_db())
    if url_info == None:
        print('[+] Success')
        return
    page_list = url_info[0]
    hash_list = url_info[1]
    pbar = tqdm(total=len(page_list))
    futures = []
    for page in page_list:
        futures.append(get_page_text(cx, page))
    loop.run_until_complete(asyncio.gather(*futures))
    pbar.close()
    print('[+] Success')


if __name__ == '__main__':
    run()
    