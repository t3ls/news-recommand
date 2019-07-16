#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from config import *
from .spider_module_google_news import google_spider
from .spider_module_sina_news import sina_spider
from .spider_module_sohu_news import sohu_spider
from .spider_module_tencent_news import tencent_spider
from .Json2Db import Json2Db

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36'
TIMESTAMP_API = 'http://quan.suning.com/getSysTime.do'

__all__ = [
	'google_spider',
	'sina_spider',
	'sohu_spider',
	'tencent_spider',
	'Json2Db'
]