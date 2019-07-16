#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Spider Modules Controller
# Author: t3ls (https://github/t3ls/)
# Designed for BUPT course: Practice of Large Program Design
# Create date: 2019/07/01

import os
import multiprocessing
import argparse
from spider_modules import *
from multiprocessing import Pool
from config import *

multiprocessing.freeze_support()

def run(args) -> None:
    # 创建进程池并异步添加爬虫模块
    pool = Pool()
    if args.google:
        pool.apply_async(google_spider.run())
    if args.sohu:
        pool.apply_async(sohu_spider.run())
    if args.sina:
        pool.apply_async(sina_spider.run())
    if args.tencent:
        pool.apply_async(tencent_spider.run())
    pool.close()
    pool.join()
    # 将爬虫输出的JSON文件写入数据库
    Json2Db()
    print('[+] Success')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    # 爬虫模块及调试模式，默认全开
    parser.add_argument('-g', '--google', default=True, help='google_spider', )
    parser.add_argument('-so', '--sohu', default=True, help='sohu_spider')
    parser.add_argument('-si', '--sina', default=True, help='sina_spider')
    parser.add_argument('-t', '--tencent', default=True, help='tencent_spider')
    parser.add_argument('-d', '--debug', default=True, help='debug')
    args = parser.parse_args()
    run(args)

