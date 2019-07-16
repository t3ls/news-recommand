#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Sohu News Spider Module
# Author: t3ls (https://github/t3ls/)
# Designed for BUPT course: Practice of Large Program Design
# Create date: 2019/07/01

import asyncio
import codecs
import time
import os
import logging
import json
import requests
import spider_modules
import pyppeteer
from spider_modules import *
from pyppeteer import launch, errors


# 初始化日志输出
logging.basicConfig(level=logging.INFO, format='[+]: %(message)s')
logging.getLogger('pyppeteer').setLevel('ERROR')

timestamp = str()
refer_time = str()
result = {}


USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36'
TIMESTAMP_API = 'http://quan.suning.com/getSysTime.do'
TARGET_URL = 'https://news.sohu.com/'
WORLD_NEWS_URL = 'http://www.sohu.com/c/8/1461'
POLITICAL_NEWS_URL = 'http://www.sohu.com/c/8/1460'
MILITARY_NEWS_URL = 'http://mil.sohu.com/'

TIMEOUT = 3
PROXY_SERVER = ''
MAX_COROUTINE = 20
pyppeteer.DEBUG = True
TIMEOUT_RETRY_TIMES = 0


class sohu_spider(object):
    @classmethod
    def run(cls) -> None:
        # 入口点，调用协程异步爬取网页
        loop = asyncio.get_event_loop()
        futures = [
            launch(
                headless=False,
                # devtools=True,
                args=['--proxy-server='+PROXY_SERVER]
                ),
            cls.get_timestamp()
            ]
        browser = loop.run_until_complete(asyncio.gather(*futures))[0]
        futures = [
            cls().get_focus_news(browser),
            cls().get_world_news(browser),
            cls().get_mil_news(browser),
            cls().get_political_news(browser)
            ]
        loop.run_until_complete(asyncio.gather(*futures))
        # print(result)
        loop.run_until_complete(asyncio.gather(cls.build_json(), browser.close()))


    async def get_focus_news(self, browser: pyppeteer.browser.Browser) -> None:
    	# 要闻
        global result, refer_time
        category = '要闻'
        category_list = []
        focus_page = await browser.newPage()
        await focus_page.setRequestInterception(True)
        focus_page.on('request', self.request_check)
        await focus_page.setJavaScriptEnabled(enabled=True)
        await focus_page.setUserAgent(USER_AGENT)
        # for _ in range(TIMEOUT_RETRY_TIMES+1):
        try:
            await focus_page.goto(TARGET_URL, timeout=TIMEOUT*1000, waitUntil='networkidle2')
            # break
        except Exception as e:
            # logging.error('ERROR:' + str(e))
            pass

        logging.debug('-----------------------------------------------------------------')
        while not await focus_page.J('div.focus-news'):
            pass
        focus_news = await focus_page.J('div.focus-news')
        _focus_news = await focus_news.JJ('a')
        for iter_news in _focus_news:
            topic_list = []
            info_dict = {}
            title = (await focus_page.evaluate('node => node.title', iter_news)).replace('\n','').strip()
            if title == '' or title == None:
            	continue
            href = await focus_page.evaluate('node => node.href', iter_news)
            info_dict['title'] = title
            info_dict['url'] = href
            info_dict['category'] = category
            info_dict['refer_name'] = '搜狐新闻'
            info_dict['refer_time'] = refer_time
            logging.debug('title:{}'.format(title))
            topic_list.append(info_dict)
            category_list.append(topic_list)
        result[category] = category_list
        await focus_page.close()



    async def get_world_news(self, browser: pyppeteer.browser.Browser) -> None:
    	# 国际新闻
        global result
        category = '国际新闻'
        category_list = []
        world_page = await browser.newPage()
        await world_page.setRequestInterception(True)
        world_page.on('request', self.request_check)
        await world_page.setJavaScriptEnabled(enabled=True)
        await world_page.setUserAgent(USER_AGENT)
        # for _ in range(TIMEOUT_RETRY_TIMES+1):
        try:
            await world_page.goto(WORLD_NEWS_URL, timeout=TIMEOUT*1000, waitUntil='networkidle2')
            # break
        except Exception as e:
            # logging.error('ERROR:' + str(e))
            pass

        logging.debug('-----------------------------------------------------------------')
        while not await world_page.J('div.news-list > div > div.news-wrapper'):
            pass
        world_news = await world_page.J('div.news-list > div > div.news-wrapper')
        _world_news = await world_news.JJ('div[data-role=news-item]')
        for iter_news in _world_news:
            topic_list = []
            info_dict = {}
            title = (await iter_news.Jeval('h4 > a', 'node => node.textContent')).replace('\n','').strip()
            if title == '' or title == None:
            	continue
            href = await iter_news.Jeval('h4 > a', 'node => node.href')
            refer_timestamp = await iter_news.Jeval('div.other > span.time', 'node => node.outerHTML')
            refer_timestamp = refer_timestamp[refer_timestamp.find('data-val="')+len('data-val="'):]
            refer_timestamp = int(refer_timestamp[:refer_timestamp.find('"')-3])
            refer_time = time.strftime('%Y%m%dT%H%M%SZ', (time.localtime(refer_timestamp)))
            refer_name = await iter_news.Jeval('div.other > span.name > a', 'node => node.textContent')
            info_dict['title'] = title
            info_dict['url'] = href
            info_dict['category'] = category
            info_dict['refer_name'] = refer_name
            info_dict['refer_time'] = refer_time
            logging.debug('title:{}'.format(title))
            topic_list.append(info_dict)
            category_list.append(topic_list)
        result[category] = category_list
        # await asyncio.sleep(30)
        await world_page.close()


    async def get_mil_news(self, browser: pyppeteer.browser.Browser) -> None:
    	# 军事
        global result
        category = '军事'
        category_list = []
        mil_page = await browser.newPage()
        await mil_page.setRequestInterception(True)
        mil_page.on('request', self.request_check)
        await mil_page.setJavaScriptEnabled(enabled=True)
        await mil_page.setUserAgent(USER_AGENT)
        # for _ in range(TIMEOUT_RETRY_TIMES+1):
        try:
            await mil_page.goto(MILITARY_NEWS_URL, timeout=TIMEOUT*1000, waitUntil='networkidle2')
            # break
        except Exception as e:
            # logging.error('ERROR:' + str(e))
            pass

        logging.debug('-----------------------------------------------------------------')
        while not await mil_page.J('div.news-list > div > div.news-wrapper'):
            pass
        mil_news = await mil_page.J('div.news-list > div > div.news-wrapper')
        _mil_news = await mil_news.JJ('div[data-role=news-item]')
        for iter_news in _mil_news:
            topic_list = []
            info_dict = {}
            title = (await iter_news.Jeval('h4 > a', 'node => node.textContent')).replace('\n','').strip()
            if title == '' or title == None:
            	continue
            href = await iter_news.Jeval('h4 > a', 'node => node.href')
            refer_timestamp = await iter_news.Jeval('div.other > span.time', 'node => node.outerHTML')
            refer_timestamp = refer_timestamp[refer_timestamp.find('data-val="')+len('data-val="'):]
            refer_timestamp = int(refer_timestamp[:refer_timestamp.find('"')-3])
            refer_time = time.strftime('%Y%m%dT%H%M%SZ', (time.localtime(refer_timestamp)))
            refer_name = await iter_news.Jeval('div.other > span.name > a', 'node => node.textContent')
            info_dict['title'] = title
            info_dict['category'] = category
            info_dict['url'] = href
            info_dict['refer_name'] = refer_name
            info_dict['refer_time'] = refer_time
            logging.debug('title:{}'.format(title))
            topic_list.append(info_dict)
            category_list.append(topic_list)
        result[category] = category_list
        await mil_page.close()


    async def get_political_news(self, browser: pyppeteer.browser.Browser) -> None:
    	# 政治
        global result
        category = '政治'
        category_list = []
        political_page = await browser.newPage()
        await political_page.setRequestInterception(True)
        political_page.on('request', self.request_check)
        await political_page.setJavaScriptEnabled(enabled=True)
        await political_page.setUserAgent(USER_AGENT)
        # for _ in range(TIMEOUT_RETRY_TIMES+1):
        try:
            await political_page.goto(POLITICAL_NEWS_URL, timeout=TIMEOUT*1000, waitUntil='networkidle2')
            # break
        except Exception as e:
            # logging.error('ERROR:' + str(e))
            pass

        logging.debug('-----------------------------------------------------------------')
        # while not await political_page.J('div.news-list > div > div.news-wrapper'):
        #     pass
        political_news = await political_page.J('div.news-list > div > div.news-wrapper')
        _political_news = await political_news.JJ('div[data-role=news-item]')
        for iter_news in _political_news:
            topic_list = []
            info_dict = {}
            title = (await iter_news.Jeval('h4 > a', 'node => node.textContent')).replace('\n','').strip()
            if title == '' or title == None:
            	continue
            href = await iter_news.Jeval('h4 > a', 'node => node.href')
            refer_timestamp = await iter_news.Jeval('div.other > span.time', 'node => node.outerHTML')
            refer_timestamp = refer_timestamp[refer_timestamp.find('data-val="')+len('data-val="'):]
            refer_timestamp = int(refer_timestamp[:refer_timestamp.find('"')-3])
            refer_time = time.strftime('%Y%m%dT%H%M%SZ', (time.localtime(refer_timestamp)))
            refer_name = await iter_news.Jeval('div.other > span.name > a', 'node => node.textContent')
            info_dict['title'] = title
            info_dict['url'] = href
            info_dict['category'] = category
            info_dict['refer_name'] = refer_name
            info_dict['refer_time'] = refer_time
            logging.debug('title:{}'.format(title))
            topic_list.append(info_dict)
            category_list.append(topic_list)
        result[category] = category_list
        await political_page.close()

    @classmethod
    async def request_check(cls, req: pyppeteer.network_manager.Request) -> None:
        """ 请求过滤 """
        logging.debug('[*] Request :', req.url, ',Type :', req.resourceType)
        if req.resourceType in ['image', 'media', 'eventsource', 'websocket']:
            await req.abort()
        else:
            await req.continue_()

    @classmethod
    async def get_timestamp(cls) -> None:
        global timestamp, refer_time
        r = requests.get(TIMESTAMP_API)
        timestamp = r.json()['sysTime1']
        refer_time = timestamp[0:8]+'T'+timestamp[8:]+'Z'
        logging.debug('timestamp:', timestamp)


    @classmethod
    async def build_json(cls) -> None:
        global timestamp, result
        filename = 'spider_modules/Output/Spider-SohuNews-{}.json'.format(timestamp)
        if os.path.exists(filename):
            os.remove(filename)
        with codecs.open(filename, 'w', 'utf-8') as f:
            json.dump(result, f)
        logging.info('SohuNews Success')



if __name__ == '__main__':
    s = sohu_spider()
    s.run()