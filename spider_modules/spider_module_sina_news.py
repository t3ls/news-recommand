#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Sina News Spider Module
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
TARGET_URL = 'https://news.sina.com.cn/'
TIMEOUT = 3
PROXY_SERVER = ''
MAX_COROUTINE = 20
TIMEOUT_RETRY_TIMES = 0
pyppeteer.DEBUG = DEBUG


class sina_spider(object):

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
            cls().get_other_news(browser),
            cls().get_finance_news(browser),
            cls().get_tech_news(browser),
            cls().get_sports_news(browser)
            ]
        loop.run_until_complete(asyncio.gather(*futures))
        # print(result)
        loop.run_until_complete(asyncio.gather(cls.build_json(), browser.close()))



    async def get_other_news(self, browser: pyppeteer.browser.Browser) -> None:
        global result, refer_time
        category_list = []
        category = str()
        page = await browser.newPage()
        await page.setRequestInterception(True)
        page.on('request', self.request_check)
        await page.setJavaScriptEnabled(enabled=True)
        await page.setUserAgent(USER_AGENT)
        # for _ in range(TIMEOUT_RETRY_TIMES+1):
        try:
            await page.goto(TARGET_URL, timeout=TIMEOUT*1000, waitUntil='networkidle2')
            # break
        except Exception as e:
            # logging.error('ERROR:' + str(e))
            pass

        wrap = await page.J('div.wrap')
        news = await wrap.JJ('div.part_01')

        logging.debug('-----------------------------------------------------------------')
        # 抓取要闻
        category = '要闻'
        important_news = await news[0].J('div.p_middle > div[data-client=important]')
        yaowen = await important_news.J('div[data-sudaclick=yaowen]')
        yaowen_h1 = await yaowen.JJ('h1')
        yaowen_p = await yaowen.JJ('p[data-client=throw]')
        for i in range(len(yaowen_h1)):
            topic_list = []
            info_dict = {}
            title = (await (await yaowen_h1[i].getProperty('textContent')).jsonValue()).replace('\n','')
            href = await yaowen_h1[i].Jeval('a', 'node => node.href')
            info_dict['title'] = title
            info_dict['url'] = href
            info_dict['category'] = category
            info_dict['refer_name'] = '新浪新闻'
            info_dict['refer_time'] = refer_time
            logging.debug('title:{}'.format(title))
            topic_list.append(info_dict)
            try:
                other_same_yaowen = await yaowen_p[i].JJ('a')
            except:
                continue
            for yaowen in other_same_yaowen:
                info_dict = {}
                title = (await (await yaowen.getProperty('textContent')).jsonValue()).replace('\n','')
                href = await (await yaowen.getProperty('href')).jsonValue()
                info_dict['title'] = title
                info_dict['url'] = href
                info_dict['category'] = category
                info_dict['refer_name'] = '新浪新闻'
                info_dict['refer_time'] = refer_time
                logging.debug('title:{}'.format(title))
                topic_list.append(info_dict)
            category_list.append(topic_list)
        result[category] = category_list
        # print(result)

        logging.debug('-----------------------------------------------------------------')
        # 军事
        category = '军事'
        military_news = await news[2].J('div.p_left_2 > div.p_left > div.blk_08[data-sudaclick=mil_1]')
        first_mil = await military_news.J('div.ct_pt_02 > h4.link_c000')
        topic_list = []
        info_dict = {}
        title = (await first_mil.Jeval('a', 'node => node.textContent')).replace('\n','')
        href = await first_mil.Jeval('a', 'node => node.href')
        info_dict['title'] = title
        info_dict['url'] = href
        info_dict['category'] = category
        info_dict['refer_name'] = '新浪新闻'
        info_dict['refer_time'] = refer_time
        logging.debug('title:{}'.format(title))
        topic_list.append(info_dict)
        category_list.append(topic_list)
        other_mil = await military_news.JJ('ul.list_12 > li')
        for mil_news in other_mil:
            topic_list = []
            info_dict = {}
            title = (await mil_news.Jeval('a', 'node => node.textContent')).replace('\n','')
            href = await mil_news.Jeval('a', 'node => node.href')
            info_dict['title'] = title
            info_dict['url'] = href
            info_dict['category'] = category
            info_dict['refer_name'] = '新浪新闻'
            info_dict['refer_time'] = refer_time
            logging.debug('title:{}'.format(title))
            topic_list.append(info_dict)
            category_list.append(topic_list)
        result[category] = category_list
        # print(result)

        logging.debug('-----------------------------------------------------------------')
        # 国内新闻
        category = '国内新闻'
        china_news = await news[2].J('div.p_left_2 > div.p_middle > div#blk_new_gnxw > div.blk_09 > ul[data-client=p_china]')
        ch_news = await china_news.JJ('li')
        for iter_news in ch_news:
            topic_list = []
            info_dict = {}
            title = (await iter_news.Jeval('a', 'node => node.textContent')).replace('\n','')
            href = await iter_news.Jeval('a', 'node => node.href')
            info_dict['title'] = title
            info_dict['url'] = href
            info_dict['category'] = category
            info_dict['refer_name'] = '新浪新闻'
            info_dict['refer_time'] = refer_time
            logging.debug('title:{}'.format(title))
            topic_list.append(info_dict)
            category_list.append(topic_list)
        result[category] = category_list
        # print(result)

        logging.debug('-----------------------------------------------------------------')
        # 国际新闻
        category = '国际新闻'
        world_news = await news[2].J('div.p_left_2 > div.p_middle:nth-last-child(1) > div#blk_gjxw_01 > ul[data-client=p_world]')
        wor_news = await world_news.JJ('li')
        for iter_news in wor_news:
            topic_list = []
            info_dict = {}
            title = (await iter_news.Jeval('a', 'node => node.textContent')).replace('\n','')
            href = await iter_news.Jeval('a', 'node => node.href')
            info_dict['title'] = title
            info_dict['url'] = href
            info_dict['category'] = category
            info_dict['refer_name'] = '新浪新闻'
            info_dict['refer_time'] = refer_time
            logging.debug('title:{}'.format(title))
            topic_list.append(info_dict)
            category_list.append(topic_list)
        result[category] = category_list
        await page.close()


    async def get_finance_news(self, browser: pyppeteer.browser.Browser) -> None:
        # 财经
        global result, refer_time
        category = '财经'
        category_list = []
        finance_page = await browser.newPage()
        await finance_page.setRequestInterception(True)
        finance_page.on('request', self.request_check)
        await finance_page.setJavaScriptEnabled(enabled=True)
        await finance_page.setUserAgent(USER_AGENT)
        # for _ in range(TIMEOUT_RETRY_TIMES+1):
        try:
            await finance_page.goto('https://finance.sina.com.cn/', timeout=TIMEOUT*1000, waitUntil='networkidle2')
            # break
        except Exception as e:
            # logging.error('ERROR:' + str(e))
            pass

        logging.debug('-----------------------------------------------------------------')
        wrap = await finance_page.J('div.main')
        finance_news = await wrap.J('div.m-part > div.m-p-middle > div.m-p1-m-blk1 > div.fin_tabs0_c0 > div.m-hdline')
        # live_tabs = await finance_news.JJ('a.liveNewsLeft')
        fina_news = await finance_news.JJ('a')

        for i in range(len(fina_news)):
            element = await (await fina_news[i].getProperty('outerHTML')).jsonValue()
            if 'liveNewsLeft' in element:
                fina_news.remove(fina_news[i])
                break
            
        for iter_news in fina_news:
            topic_list = []
            info_dict = {}
            title = (await finance_page.evaluate('node => node.textContent', iter_news)).replace('\n','')
            href = await finance_page.evaluate('node => node.href', iter_news)
            info_dict['title'] = title
            info_dict['url'] = href
            info_dict['category'] = category
            info_dict['refer_name'] = '新浪新闻'
            info_dict['refer_time'] = refer_time
            logging.debug('title:{}'.format(title))
            topic_list.append(info_dict)
            category_list.append(topic_list)
        result[category] = category_list
        await finance_page.close()


    async def get_tech_news(self, browser: pyppeteer.browser.Browser) -> None:
        # 科技
        global result, timestamp
        category = '科技'
        category_list = []
        tech_page = await browser.newPage()
        await tech_page.setRequestInterception(True)
        tech_page.on('request', self.request_check)
        await tech_page.setJavaScriptEnabled(enabled=True)
        await tech_page.setUserAgent(USER_AGENT)
        # for _ in range(TIMEOUT_RETRY_TIMES+1):
        try:
            await tech_page.goto('https://tech.sina.com.cn/', timeout=TIMEOUT*1000, waitUntil='networkidle2')
            # break
        except Exception as e:
            # logging.error('ERROR:' + str(e))
            pass

        logging.debug('-----------------------------------------------------------------')
        tech_news = await tech_page.J('div#tech_body > div.tech-main > div.tech-mid > div.feed_card > div.ty-cardlist-w > div#j_cardlist > div.cardlist-a__list')
        _tech_news = await tech_news.JJ('div.ty-card')
        for iter_news in _tech_news:
            topic_list = []
            info_dict = {}
            info_tab = await iter_news.J('div.ty-card-r')
            title = (await info_tab.Jeval('h3 > a', 'node => node.textContent')).replace('\n','')
            href = await info_tab.Jeval('h3 > a', 'node => node.href')
            try:
                refer_time = await info_tab.Jeval('p:nth-last-child(1) > span.ty-card-time', 'node => node.textContent')
                if '今天' in refer_time:
                    refer_time_T = timestamp[0:8]+'T'
                else:
                    refer_time_T = '2019'+refer_time.split('月')[0].rjust(2,'0')+refer_time.split('月')[1].split('日')[0].rjust(2,'0')+'T'
                refer_time_Z = refer_time.split(' ')[1].replace(':','')+'00Z'
                refer_time = refer_time_T + refer_time_Z
            except Exception as e:
                refer_time = timestamp[0:8]+'T'+timestamp[8:]+'Z'
            info_dict['title'] = title
            info_dict['category'] = category
            info_dict['url'] = href
            info_dict['refer_name'] = '新浪新闻'
            info_dict['refer_time'] = refer_time
            logging.debug('title:{}'.format(title))
            topic_list.append(info_dict)
            category_list.append(topic_list)
        result[category] = category_list
        await tech_page.close()


    async def get_sports_news(self, browser: pyppeteer.browser.Browser) -> None:
        # 体育
        global result, refer_time
        category = '体育'
        category_list = []
        sports_page = await browser.newPage()
        await sports_page.setRequestInterception(True)
        sports_page.on('request', self.request_check)
        await sports_page.setJavaScriptEnabled(enabled=True)
        await sports_page.setUserAgent(USER_AGENT)
        # for _ in range(TIMEOUT_RETRY_TIMES+1):
        try:
            await sports_page.goto('http://sports.sina.com.cn/', timeout=TIMEOUT*1000, waitUntil='networkidle2')
            # break
        except Exception as e:
            # logging.error('ERROR:' + str(e))
            pass

        logging.debug('-----------------------------------------------------------------')
        sports_news = await sports_page.J('div#ty-top-ent0')
        _sports_news = await sports_news.JJ('div.ty-card > h3.ty-card-tt > a[node-type=tytop]')
        for iter_news in _sports_news:
            topic_list = []
            info_dict = {}
            title = (await sports_page.evaluate('node => node.textContent', iter_news)).replace('\n','')
            href = await sports_page.evaluate('node => node.href', iter_news)
            info_dict['title'] = title
            info_dict['url'] = href
            info_dict['category'] = category
            info_dict['refer_name'] = '新浪新闻'
            info_dict['refer_time'] = refer_time
            logging.debug('title:{}'.format(title))
            topic_list.append(info_dict)
            category_list.append(topic_list)
        result[category] = category_list
        await sports_page.close()


    @classmethod
    async def request_check(cls, req: pyppeteer.network_manager.Request) -> None:
        """ 请求过滤 """
        if req.resourceType in ['image', 'media', 'eventsource', 'websocket']:
            if 'img-replaced-w.png' in req.url:
                await req.continue_()
            else:
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
        # 构建JSON
        global timestamp, result
        filename = 'spider_modules/Output/Spider-SinaNews-{}.json'.format(timestamp)
        if os.path.exists(filename):
            os.remove(filename)
        with codecs.open(filename, 'w', 'utf-8') as f:
            json.dump(result, f)
        logging.info('SinaNews Success')


if __name__ == '__main__':
    s = sina_spider()
    s.run()