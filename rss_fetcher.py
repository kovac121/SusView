#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RSS新闻抓取模块
"""
import re
import ssl
import urllib3
from dateutil import parser as date_parser
import feedparser
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context

from config import RSS_SOURCES, MAX_ARTICLES_PER_SOURCE, USER_AGENTS, is_esg_related

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class _TLSAdapter(HTTPAdapter):
    """兼容部分站点（如 Carbon Pulse）在 Windows 上的 TLS 握手失败。"""

    def init_poolmanager(self, *args, **kwargs):
        ctx = create_urllib3_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        ctx.options |= getattr(ssl, 'OP_LEGACY_SERVER_CONNECT', 0x4)
        kwargs['ssl_context'] = ctx
        return super().init_poolmanager(*args, **kwargs)


def _build_session(verify_ssl=True):
    session = requests.Session()
    session.headers.update({
        'User-Agent': USER_AGENTS[0],
        'Accept': 'application/rss+xml, application/xml, text/xml, */*',
    })
    if not verify_ssl:
        session.mount('https://', _TLSAdapter())
        session.verify = False
    return session


def _download_feed(url, verify_ssl=True):
    session = _build_session(verify_ssl=verify_ssl)
    response = session.get(url, timeout=20, allow_redirects=True)
    response.raise_for_status()
    return feedparser.parse(response.content)


def fetch_single_rss(source):
    """抓取单个RSS源"""
    news_list = []
    url = source['url']
    verify_ssl = source.get('verify_ssl', True)

    try:
        try:
            feed = _download_feed(url, verify_ssl=verify_ssl)
        except requests.exceptions.SSLError:
            print(f"⚠️ {source['name']}: SSL 失败，改用宽松握手重试")
            feed = _download_feed(url, verify_ssl=False)

        if getattr(feed, 'bozo', False) and not feed.entries:
            print(f"⚠️ {source['name']}: RSS 解析失败")
            return news_list

        limit = source.get('max_articles', MAX_ARTICLES_PER_SOURCE)
        for entry in feed.entries[:limit]:
            title = entry.get('title', '')
            link = entry.get('link', '')
            summary = entry.get('summary', '') or entry.get('description', '')
            summary = re.sub(r'<[^>]+>', '', summary)
            summary = summary[:200] + '...' if len(summary) > 200 else summary

            published = entry.get('published') or entry.get('updated', '')
            if published:
                try:
                    dt = date_parser.parse(published)
                    published = dt.strftime('%Y-%m-%d %H:%M')
                except Exception:
                    pass

            if is_esg_related(title + ' ' + summary):
                news_list.append({
                    'title': title,
                    'link': link,
                    'summary': summary,
                    'published': published,
                    'source': source['name'],
                })

    except Exception as e:
        print(f"抓取 {source['name']} 失败: {e}")

    return news_list


def fetch_all_rss():
    """抓取所有RSS源"""
    all_news = []
    for source in RSS_SOURCES:
        news_list = fetch_single_rss(source)
        all_news.extend(news_list)
    return all_news


if __name__ == '__main__':
    print('测试RSS抓取...')
    news = fetch_all_rss()
    print(f'共抓取到 {len(news)} 条新闻')
