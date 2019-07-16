#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Tencent News Spider Module
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
import pyppeteer
import spider_modules
from spider_modules import *
from pyppeteer import launch, errors



logging.basicConfig(level=logging.INFO, format='[+]: %(message)s')
logging.getLogger('pyppeteer').setLevel('ERROR')

timestamp = str()
refer_time = str()
result = {}


USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36'
TIMESTAMP_API = 'http://quan.suning.com/getSysTime.do'
TARGET_URL = 'https://news.qq.com/'
WORLD_NEWS_URL = 'https://new.qq.com/ch/world/'
MILITARY_NEWS_URL = 'https://new.qq.com/ch/milite/'
TECH_NEWS_URL = 'https://new.qq.com/ch/tech/'
FINANCE_NEWS_URL = 'https://new.qq.com/ch/finance/'
TIMEOUT = 5
PROXY_SERVER = 'socks5://127.0.0.1:1080'
MAX_COROUTINE = 20
pyppeteer.DEBUG = DEBUG
TIMEOUT_RETRY_TIMES = 0 


class tencent_spider(object):
    @classmethod
    def run(cls) -> None:
        # 入口点，调用协程异步爬取网页
        loop = asyncio.get_event_loop()
        futures = [
            launch(
                headless=True,
                # devtools=True,
                args=['--proxy-server='+PROXY_SERVER]
                ),
            cls.get_timestamp()
            ]
        browser = loop.run_until_complete(asyncio.gather(*futures))[0]
        futures = [
            cls().get_focus_news(browser),
            cls().get_mil_news(browser),
            cls().get_world_news(browser),
            cls().get_tech_news(browser),
            cls().get_finance_news(browser)
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
        focus_news = await focus_page.J('ul.top-list')
        _focus_news = await focus_news.JJ('h3 > a')
        for iter_news in _focus_news:
            topic_list = []
            info_dict = {}
            title = (await focus_page.evaluate('node => node.textContent', iter_news)).replace('\n','').strip()
            if title == '' or title == None:
            	continue
            href = await focus_page.evaluate('node => node.href', iter_news)
            info_dict['title'] = title
            info_dict['url'] = href
            info_dict['category'] = category
            info_dict['refer_name'] = '腾讯新闻'
            info_dict['refer_time'] = refer_time
            logging.debug('title:{}'.format(title))
            topic_list.append(info_dict)
            category_list.append(topic_list)
        result[category] = category_list
        await focus_page.close()


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
        mil_news = await mil_page.J('div.hotnews > ul.list')
        _mil_news = await mil_news.JJ('li.cf')

        for iter_news in _mil_news:
            topic_list = []
            info_dict = {}
            title = (await iter_news.Jeval('h3 > a', 'node => node.textContent')).replace('\n','').strip()
            if title == '' or title == None:
            	continue
            href = await iter_news.Jeval('h3 > a', 'node => node.href')
            try:
                refer_name = await iter_news.Jeval('div.binfo > div[class=fl] > a', 'node => node.textContent')
            except pyppeteer.errors.ElementHandleError as e:
                refer_name = '腾讯新闻'
            refer_time = (await mil_page.evaluate('node => node.id', iter_news))[:8]+'T000000Z'
            info_dict['title'] = title
            info_dict['url'] = href
            info_dict['category'] = category
            info_dict['refer_name'] = refer_name
            info_dict['refer_time'] = refer_time
            logging.debug('title:{}'.format(title))
            topic_list.append(info_dict)
            category_list.append(topic_list)
        result[category] = category_list
        await mil_page.close()


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
        world_news = await world_page.J('div.hotnews > ul.list')
        _world_news = await world_news.JJ('li.cf')
        for iter_news in _world_news:
            topic_list = []
            info_dict = {}
            title = (await iter_news.Jeval('h3 > a', 'node => node.textContent')).replace('\n','').strip()
            if title == '' or title == None:
            	continue
            href = await iter_news.Jeval('h3 > a', 'node => node.href')
            try:
                refer_name = await iter_news.Jeval('div.binfo > div[class=fl] > a', 'node => node.textContent')
            except pyppeteer.errors.ElementHandleError as e:
                refer_name = '腾讯新闻'
            refer_time = (await world_page.evaluate('node => node.id', iter_news))[:8]+'T000000Z'
            info_dict['title'] = title
            info_dict['url'] = href
            info_dict['refer_name'] = refer_name
            info_dict['category'] = category
            info_dict['refer_time'] = refer_time
            logging.debug('title:{}'.format(title))
            topic_list.append(info_dict)
            category_list.append(topic_list)
        result[category] = category_list
        await world_page.close()


    async def get_tech_news(self, browser: pyppeteer.browser.Browser) -> None:
    	# 科技
        global result
        category = '科技'
        category_list = []
        tech_page = await browser.newPage()
        await tech_page.setRequestInterception(True)
        tech_page.on('request', self.request_check)
        await tech_page.setJavaScriptEnabled(enabled=True)
        await tech_page.setUserAgent(USER_AGENT)
        # for _ in range(TIMEOUT_RETRY_TIMES+1):
        try:
            await tech_page.goto(TECH_NEWS_URL, timeout=TIMEOUT*1000, waitUntil='networkidle2')
            # break
        except Exception as e:
            # logging.error('ERROR:' + str(e))
            pass

        logging.debug('-----------------------------------------------------------------')
        tech_news = await tech_page.J('div.hotnews > ul.list')
        _tech_news = await tech_news.JJ('li.cf')

        for iter_news in _tech_news:
            topic_list = []
            info_dict = {}
            title = (await iter_news.Jeval('h3 > a', 'node => node.textContent')).replace('\n','').strip()
            if title == '' or title == None:
            	continue
            href = await iter_news.Jeval('h3 > a', 'node => node.href')
            try:
                refer_name = await iter_news.Jeval('div.binfo > div[class=fl] > a', 'node => node.textContent')
            except pyppeteer.errors.ElementHandleError as e:
                refer_name = '腾讯新闻'
            refer_time = (await tech_page.evaluate('node => node.id', iter_news))[:8]+'T000000Z'
            info_dict['title'] = title
            info_dict['url'] = href
            info_dict['category'] = category
            info_dict['refer_name'] = refer_name
            info_dict['refer_time'] = refer_time
            logging.debug('title:{}'.format(title))
            topic_list.append(info_dict)
            category_list.append(topic_list)
        result[category] = category_list
        await tech_page.close()


    async def get_finance_news(self, browser: pyppeteer.browser.Browser) -> None:
    	# 财经
        global result
        category = '财经'
        category_list = []
        finance_page = await browser.newPage()
        await finance_page.setRequestInterception(True)
        finance_page.on('request', self.request_check)
        await finance_page.setJavaScriptEnabled(enabled=True)
        await finance_page.setUserAgent(USER_AGENT)
        # for _ in range(TIMEOUT_RETRY_TIMES+1):
        try:
            await finance_page.goto(FINANCE_NEWS_URL, timeout=TIMEOUT*1000, waitUntil='networkidle2')
            # break
        except Exception as e:
            # logging.error('ERROR:' + str(e))
            pass

        logging.debug('-----------------------------------------------------------------')
        finance_news = await finance_page.J('div.hotnews > ul.list')
        _finance_news = await finance_news.JJ('li.cf')
        for iter_news in _finance_news:
            topic_list = []
            info_dict = {}
            title = (await iter_news.Jeval('h3 > a', 'node => node.textContent')).replace('\n','').strip()
            if title == '' or title == None:
            	continue
            href = await iter_news.Jeval('h3 > a', 'node => node.href')
            try:
                refer_name = await iter_news.Jeval('div.binfo > div[class=fl] > a', 'node => node.textContent')
            except pyppeteer.errors.ElementHandleError as e:
                refer_name = '腾讯新闻'
            refer_time = (await finance_page.evaluate('node => node.id', iter_news))[:8]+'T000000Z'
            info_dict['title'] = title
            info_dict['url'] = href
            info_dict['category'] = category
            info_dict['refer_name'] = refer_name
            info_dict['refer_time'] = refer_time
            logging.debug('title:{}'.format(title))
            topic_list.append(info_dict)
            category_list.append(topic_list)
        result[category] = category_list
        await finance_page.close()

    @classmethod
    async def request_check(cls, req: pyppeteer.network_manager.Request) -> None:
        """ 请求过滤 """
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
        filename = 'spider_modules/Output/Spider-TencentNews-{}.json'.format(timestamp)
        if os.path.exists(filename):
            os.remove(filename)
        with codecs.open(filename, 'w', 'utf-8') as f:
            json.dump(result, f)
        logging.info('TencentNews Success')



if __name__ == '__main__':
    t = tencent_news()
    t.run()