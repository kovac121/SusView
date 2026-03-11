#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ESG新闻爬虫配置
"""

import re
from pathlib import Path
from threading import Lock
import time

# ===== 路径配置 =====
NEWS_DIR = Path(__file__).parent / 'news'
TEMPLATE_FILE = NEWS_DIR / 'template.html'
OUTPUT_FILE = NEWS_DIR / 'latest.html'

# ===== RSS新闻源 =====
RSS_SOURCES = [
    {
        'name': '欧盟委员会气候',
        'url': 'https://climate.ec.europa.eu/rss_en',
        'type': 'rss',
        'keywords': ['environment', 'climate', 'energy', 'sustainability', 'green', 'carbon', 'emissions', 'ESG'],
        'selectors': ['article', 'main', '.content', '.article']
    },
    {
        'name': '欧洲环境署 EEA',
        'url': 'https://www.eea.europa.eu/en/rss',
        'type': 'rss',
        'keywords': ['environment', 'climate', 'sustainability', 'carbon', 'emissions', 'ESG'],
        'selectors': ['article', 'main', '.content', '.article']
    },
    {
        'name': '德勤ESG',
        'url': 'https://www2.deloitte.com/content/Domains/rss/sustainability.rss',
        'type': 'rss',
        'keywords': ['ESG', 'sustainability', 'climate', 'green', 'carbon', 'net zero'],
        'selectors': ['article', 'main', '.content', '.article']
    },
    {
        'name': 'Reuters ESG',
        'url': 'https://www.reutersagency.com/feed/?best-topics=esg&post_type=best',
        'type': 'rss',
        'keywords': ['ESG', 'sustainability', 'climate', 'carbon', 'emissions', 'green'],
        'selectors': ['article', 'main', '.content', '.article']
    },
    {
        'name': 'Carbon Pulse',
        'url': 'https://carbon-pulse.com/feed/',
        'type': 'rss',
        'keywords': ['carbon', 'ETS', 'emissions', 'trading', 'allowance'],
        'selectors': ['.post', '.article', '.content', '.entry-content']
    }
]

# ===== 媒体源配置（直接抓取的源）=====
MEDIA_SOURCES = [
    {
        'name': 'Bloomberg ESG',
        'url': 'https://www.bloomberg.com/topics/esg',
        'type': 'scrape',
        'keywords': ['ESG', 'sustainability', 'climate', 'carbon', 'emissions'],
        'selectors': ['.article-body', '.content', 'article', 'main'],
        'detail_url_pattern': 'https://www.bloomberg.com/.*',
        'max_articles': 5
    },
    {
        'name': 'Financial Times ESG',
        'url': 'https://www.ft.com/content/climate-environment',
        'type': 'scrape',
        'keywords': ['ESG', 'sustainability', 'climate', 'carbon', 'emissions'],
        'selectors': ['.article-body-content', 'article', 'main', '.content'],
        'detail_url_pattern': 'https://www.ft.com/content/.*',
        'max_articles': 5
    },
    {
        'name': 'ICIS ESG',
        'url': 'https://www.icis.com/energy-transition-esg/',
        'type': 'scrape',
        'keywords': ['carbon', 'emissions', 'trading', 'climate', 'ESG'],
        'selectors': ['.article-content', 'article', 'main', '.content'],
        'detail_url_pattern': 'https://www.icis.com/.*',
        'max_articles': 5
    },
    {
        'name': 'S&P Global ESG',
        'url': 'https://www.spglobal.com/esg/',
        'type': 'scrape',
        'keywords': ['ESG', 'sustainability', 'climate', 'carbon', 'emissions'],
        'selectors': ['.article-content', 'article', 'main', '.content'],
        'detail_url_pattern': 'https://www.spglobal.com/.*',
        'max_articles': 5
    },
    {
        'name': 'Global Platts ESG',
        'url': 'https://www.spglobal.com/commodityinsights/en/',
        'type': 'scrape',
        'keywords': ['energy', 'carbon', 'emissions', 'climate', 'ESG'],
        'selectors': ['.article-content', 'article', 'main', '.content'],
        'detail_url_pattern': 'https://www.spglobal.com/.*',
        'max_articles': 5
    }
]

# ===== 合并所有源 =====
ALL_SOURCES = RSS_SOURCES + MEDIA_SOURCES

# ===== 关键词过滤 =====
ESG_KEYWORDS = [
    # ESG基础关键词
    'ESG', 'sustainability', 'sustainable', 'climate', 'carbon', 'emissions',
    'green', 'renewable', 'net zero', 'carbon neutral', 'environmental',

    # 欧洲碳市场核心关键词
    'EU ETS', 'EU Emissions Trading System', 'European Union Emissions Trading',
    'carbon market', 'carbon price', 'EUA', 'allowance', 'allowance price',
    'carbon credit', 'carbon offset', 'carbon allowance', 'emission allowance',
    'emissions trading', 'greenhouse gas emissions', 'GHG emissions',
    'cap and trade', 'carbon cap', 'emission cap', 'carbon auction',
    'carbon market reform', 'ETS reform', 'EU climate policy',

    # 具体产品和代码
    'EUA futures', 'carbon futures', 'allowance futures', 'carbon contracts',
    'Phase 4', 'Phase 3', 'Trading Period', 'MRVA', 'FLEX', 'NER',

    # 政策和法规
    'Fit for 55', 'Green Deal', 'Climate Law', 'Carbon Border Adjustment',
    'CBAM', 'carbon border tax', 'energy transition', 'just transition',

    # 其他相关术语
    'circular economy', 'decarbonization', 'decarbonize', 'low carbon', 'zero carbon',
    'climate target', 'carbon budget', 'climate action'
]

# 预编译正则表达式（性能优化）
ESG_PATTERN = re.compile('|'.join(re.escape(kw) for kw in ESG_KEYWORDS), re.IGNORECASE)

# ===== 速率限制配置 =====
MAX_REQUESTS_PER_MINUTE = 15
MAX_WORKERS = 8  # 多进程并发数
MAX_NEWS = 30  # 最多返回新闻数
MAX_ARTICLES_PER_SOURCE = 10  # 每个源最多文章数

# ===== User-Agent列表 =====
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
]

# ===== 来源简称映射 =====
SOURCE_SHORT_NAMES = {
    '欧盟委员会气候': '欧盟',
    '欧洲环境署 EEA': 'EEA',
    '德勤ESG': '德勤',
    'Reuters ESG': '路透',
    'Carbon Pulse': 'Carbon Pulse',
    'Bloomberg ESG': '彭博',
    'Financial Times ESG': 'FT',
    'ICIS ESG': 'ICIS',
    'S&P Global ESG': 'S&P',
    'Global Platts': 'Platts'
}


def is_esg_related(text):
    """检查文本是否与ESG相关（使用预编译正则）"""
    if not text:
        return False
    return bool(ESG_PATTERN.search(text))
