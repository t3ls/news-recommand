#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Google News Spider Module
# Author: t3ls (https://github/t3ls/)
# Designed for BUPT course: Practice of Large Program Design
# Create date: 2019/07/01

import asyncio
import codecs
import time
import os
import logging
import json
import sys
import requests
import pyppeteer
import spider_modules
from spider_modules import *
from pyppeteer import launch, errors

# 初始化日志输出
logging.basicConfig(level=logging.INFO, format='[+]: %(message)s')
logging.getLogger('pyppeteer').setLevel('ERROR')

timestamp = str()


USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36'
TIMESTAMP_API = 'http://quan.suning.com/getSysTime.do'
TARGET_URL = 'https://news.google.com/?hl=zh-CN&gl=CN&ceid=CN%3Azh-Hans'
TIMEOUT = 3
PROXY_SERVER = ''
TIMEOUT_RETRY_TIMES = 0
MAX_COROUTINE = 20
pyppeteer.DEBUG = DEBUG


class google_spider(object):

    @classmethod
    def run(cls) -> None:
        # 入口点
        loop = asyncio.get_event_loop()
        loop.run_until_complete(asyncio.gather(cls().main(), cls.get_timestamp()))


    async def main(self) -> None:
        # 启动chromium浏览器并初始化
        browser = await launch(
            headless=True,
            # devtools=True,
            args=['--proxy-server='+PROXY_SERVER]
            )
        page = await browser.newPage()
        await page.setRequestInterception(True)
        page.on('request', self.request_check)
        await page.setJavaScriptEnabled(enabled=True)
        await page.setUserAgent(USER_AGENT)

        # 访问网页
        # for _ in range(TIMEOUT_RETRY_TIMES+1):
        try:
            await page.goto(TARGET_URL, timeout=TIMEOUT*1000, waitUntil='networkidle2')
            # break
        except Exception as e:
            # logging.error('ERROR:' + str(e))
            pass

        # 选中文章所处元素
        main_selector = await page.J('c-wiz > div > div > div > div > main > c-wiz > div')
        article_div = await main_selector.JJ('c-wiz > div > div')
        logging.debug('article_div length: ' + str(len(article_div)))
        articles_jshandle_list = []    # Articles JSHandle Pool
        category_list = []
        result = {}
        category = str()

        for div in article_div:
            # 遍历文章，获取标题，url，发布时间，新闻来源
            topic_list = []
            articles_jshandle_list = await div.JJ('div > article')
            # Judge the handle is article or category?
            if len(articles_jshandle_list) > 0:
                # Get info from pool
                for article_iterator in articles_jshandle_list:
                    info_dict = {}
                    a_div = await article_iterator.J('a')
                    href = await (await a_div.getProperty('href')).jsonValue()
                    title = await (await (await article_iterator.J('h3 > a, h4 > a')).getProperty('textContent')).jsonValue()
                    refer_selector = await article_iterator.J('div.QmrVtf.RD0gLb') # Get refer selector
                    refer_name = await (await (await refer_selector.J('div > a')).getProperty('textContent')).jsonValue()
                    try:
                        # TODO:
                        # Maybe pyppeteer bug: can't get attributes of JSHandle(time)
                        # So get the refer_time manually instead
                        refer_time = await (await (await refer_selector.J('div > time')).getProperty('outerHTML')).jsonValue()
                        refer_time = refer_time[refer_time.find('datetime')+len('datetime="'):refer_time.find('">')].replace(':','').replace('-','')
                    except Exception as e:
                        continue
                    info_dict['title'] = title
                    info_dict['url'] = href
                    info_dict['category'] = category
                    info_dict['refer_name'] = refer_name
                    info_dict['refer_time'] = refer_time

                    # logging.debug('title:{0}\nhref:{1}\nrefer_name:{2}\ntime:{3}'.format(title, href, refer_name, refer_time))
                    topic_list.append(info_dict)
                category_list.append(topic_list)
                result[category] = category_list
            else:
                # print category name
                logging.debug('----------------------------------------------------------------')
                topic = await div.J('h2 > span > a')
                category = await (await topic.getProperty('textContent')).jsonValue()
                if category == '中华人民共和国':
                    category = '国内新闻'
                elif category == '全球':
                    category = '国际新闻'
                elif category == '商业':
                    category = '财经'
                elif category == '科学技术':
                    category = '科技'
                logging.debug(category)
                category_list = []
                result[category] = []

        # Get Hot word
        category = '热词'
        hot_word = []
        hot_keyword = await page.Jx('//*[@id="yDmH0d"]/c-wiz/div/div[2]/div[2]/div/aside/c-wiz/div[1]/div[2]/div[2]')
        _hot_keyword = await hot_keyword[0].JJ('a')
        for iter_handle in _hot_keyword:
            word_info = {}
            name = await page.evaluate('node => node.outerHTML', iter_handle)
            name = name[name.find('aria-label="')+len('aria-label="'):]
            name = name[:name.find('"')]
            word_info['name'] = name
            word_info['url'] = await page.evaluate('node => node.href', iter_handle)
            hot_word.append(word_info)
        result[category] = hot_word

        global timestamp
        # 构建JSON
        filename = 'spider_modules/Output/Spider-GoogleNews-{}.json'.format(timestamp)
        if os.path.exists(filename):
            os.remove(filename)
        with codecs.open(filename, 'w', 'utf-8') as f:
            json.dump(result, f)
        logging.info('GoogleNews Success')

    @classmethod
    async def request_check(cls, req: pyppeteer.network_manager.Request) -> None:
        """ 请求过滤 """
        if req.resourceType in ['image', 'media', 'eventsource', 'websocket']:
            await req.abort()
        else:
            await req.continue_()

    @staticmethod
    async def get_timestamp() -> None:
        global timestamp
        r = requests.get(TIMESTAMP_API)
        timestamp = r.json()['sysTime1']
        logging.debug('timestamp:', timestamp)


if __name__ == '__main__':
    g = google_spider()
    g.run()