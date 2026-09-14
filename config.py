#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ESG新闻爬虫配置
"""

import re
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / '.env')
except ImportError:
    pass

# ===== 路径配置 =====
NEWS_DIR = Path(__file__).parent / 'news'
TEMPLATE_FILE = NEWS_DIR / 'template.html'
OUTPUT_FILE = NEWS_DIR / 'latest.html'

# ===== RSS新闻源（2026-09-14 实测可用）=====
RSS_SOURCES = [
    {
        'name': 'Carbon Pulse',
        'url': 'https://carbon-pulse.com/feed/',
        'type': 'rss',
        'verify_ssl': False,
        'max_articles': 4,
        'keywords': ['carbon', 'ETS', 'emissions', 'trading', 'allowance', 'EU ETS'],
    },
    {
        'name': 'EU Commission',
        'url': 'https://ec.europa.eu/commission/presscorner/api/rss',
        'type': 'rss',
        'keywords': ['EU ETS', 'climate', 'energy', 'carbon', 'emissions', 'Green Deal', 'CBAM'],
    },
    {
        'name': 'Carbon Brief',
        'url': 'https://www.carbonbrief.org/feed',
        'type': 'rss',
        'keywords': ['carbon', 'climate', 'emissions', 'EU ETS', 'carbon market', 'energy'],
    },
    {
        'name': 'Sandbag',
        'url': 'https://sandbag.be/feed/',
        'type': 'rss',
        'keywords': ['EU ETS', 'carbon', 'emissions', 'allowance', 'EUA', 'climate'],
    },
    {
        'name': 'Windpower Monthly',
        'url': 'https://www.windpowermonthly.com/rss',
        'type': 'rss',
        'keywords': ['wind', 'renewable', 'energy', 'carbon', 'climate', 'ESG'],
    },
    {
        'name': 'Climate Home',
        'url': 'https://www.climatechangenews.com/feed/',
        'type': 'rss',
        'keywords': ['climate', 'carbon', 'ETS', 'CBAM', 'energy', 'emissions'],
    },
    {
        'name': 'Carbon Market Watch',
        'url': 'https://carbonmarketwatch.org/feed/',
        'type': 'rss',
        'keywords': ['EU ETS', 'carbon', 'CBAM', 'allowance', 'ETS2', 'emissions'],
    },
    {
        'name': 'Clean Energy Wire',
        'url': 'https://www.cleanenergywire.org/rss.xml',
        'type': 'rss',
        'keywords': ['energy', 'climate', 'ETS', 'carbon', 'Germany', 'EU'],
    },
    {
        'name': 'EEA',
        'url': 'https://www.eea.europa.eu/en/newsroom/news/rss.xml',
        'type': 'rss',
        'keywords': ['climate', 'emissions', 'carbon', 'energy', 'environment', 'EU'],
    },
    {
        'name': 'Carbon Credits',
        'url': 'https://carboncredits.com/feed/',
        'type': 'rss',
        'keywords': ['carbon', 'credit', 'offset', 'ETS', 'allowance', 'market'],
    },
    {
        'name': 'Responsible Investor',
        'url': 'https://www.responsible-investor.com/feed/',
        'type': 'rss',
        'keywords': ['ESG', 'climate', 'carbon', 'sustainable', 'disclosure'],
    },
    {
        'name': 'ESG Today',
        'url': 'https://www.esgtoday.com/feed/',
        'type': 'rss',
        'keywords': ['ESG', 'sustainability', 'climate', 'carbon', 'net zero'],
    },
    {
        'name': 'FT Climate',
        'url': 'https://www.ft.com/climate-capital?format=rss',
        'type': 'rss',
        'keywords': ['climate', 'carbon', 'energy', 'ESG', 'emissions'],
    },
    {
        'name': 'Google News ETS',
        'url': (
            'https://news.google.com/rss/search'
            '?q=EU+ETS+OR+CBAM+OR+%22carbon+market%22+OR+%22ETS2%22'
            '&hl=en&gl=US&ceid=US:en'
        ),
        'type': 'rss',
        'max_articles': 8,
        'keywords': ['EU ETS', 'CBAM', 'carbon market', 'allowance'],
    },
]

# 网页抓取源：Bloomberg / Reuters 反爬或 404，暂不启用
MEDIA_SOURCES = []

ALL_SOURCES = RSS_SOURCES + MEDIA_SOURCES

# ===== 关键词过滤 =====
ESG_KEYWORDS = [
    'ESG', 'sustainability', 'sustainable', 'climate', 'carbon', 'emissions',
    'green', 'renewable', 'net zero', 'carbon neutral', 'environmental',
    'EU ETS', 'EU Emissions Trading System', 'European Union Emissions Trading',
    'carbon market', 'carbon price', 'EUA', 'allowance', 'allowance price',
    'carbon credit', 'carbon offset', 'carbon allowance', 'emission allowance',
    'emissions trading', 'greenhouse gas emissions', 'GHG emissions',
    'cap and trade', 'carbon cap', 'emission cap', 'carbon auction',
    'carbon market reform', 'ETS reform', 'EU climate policy',
    'ETS2', 'ETS II', 'Market Stability Reserve', 'MSR',
    'EUA futures', 'carbon futures', 'allowance futures', 'carbon contracts',
    'Phase 4', 'Phase 3', 'Trading Period', 'MRVA', 'FLEX', 'NER',
    'Fit for 55', 'Green Deal', 'Climate Law', 'Carbon Border Adjustment',
    'CBAM', 'carbon border tax', 'energy transition', 'just transition',
    'circular economy', 'decarbonization', 'decarbonise', 'decarbonize',
    'low carbon', 'zero carbon', 'climate target', 'carbon budget', 'climate action',
    'carbon removals', 'industrial decarbonisation', 'industrial decarbonization',
]

ESG_PATTERN = re.compile('|'.join(re.escape(kw) for kw in ESG_KEYWORDS), re.IGNORECASE)

# ===== 运行参数 =====
MAX_REQUESTS_PER_MINUTE = 15
MAX_WORKERS = 8
MAX_NEWS = 10
MAX_ARTICLES_PER_SOURCE = 10

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
]

SOURCE_SHORT_NAMES = {
    'Carbon Pulse': 'Carbon Pulse',
    'EU Commission': '欧盟委员会',
    'Carbon Brief': 'Carbon Brief',
    'Sandbag': 'Sandbag',
    'Windpower Monthly': 'Windpower',
    'Climate Home': 'Climate Home',
    'Carbon Market Watch': 'CMW',
    'Clean Energy Wire': 'CLEW',
    'EEA': '欧盟环境署',
    'Carbon Credits': 'Carbon Credits',
    'Responsible Investor': 'RI',
    'ESG Today': 'ESG Today',
    'FT Climate': 'FT',
    'Google News ETS': 'Google News',
}


def is_esg_related(text):
    """检查文本是否与ESG相关（使用预编译正则）"""
    if not text:
        return False
    return bool(ESG_PATTERN.search(text))
