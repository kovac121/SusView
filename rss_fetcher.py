#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RSS新闻抓取模块
"""
import re
from datetime import datetime
from dateutil import parser as date_parser
import feedparser

from config import RSS_SOURCES, MAX_ARTICLES_PER_SOURCE, is_esg_related


def fetch_single_rss(source):
    """抓取单个RSS源

    Args:
        source: RSS源配置字典

    Returns:
        list: 新闻列表
    """
    news_list = []

    try:
        feed = feedparser.parse(source['url'])

        # Carbon Pulse限制为4条，其他源10条
        limit = 4 if source['name'] == 'Carbon Pulse' else 10
        for entry in feed.entries[:limit]:
            title = entry.get('title', '')
            link = entry.get('link', '')
            summary = entry.get('summary', '') or entry.get('description', '')

            # 清理HTML标签
            summary = re.sub(r'<[^>]+>', '', summary)
            summary = summary[:200] + '...' if len(summary) > 200 else summary

            # 获取发布时间
            published = entry.get('published', '')
            if published:
                try:
                    dt = date_parser.parse(published)
                    published = dt.strftime('%Y-%m-%d %H:%M')
                except:
                    pass

            # 检查是否ESG相关
            if is_esg_related(title + ' ' + summary):
                news_list.append({
                    'title': title,
                    'link': link,
                    'summary': summary,
                    'published': published,
                    'source': source['name']
                })

    except Exception as e:
        print(f"抓取 {source['name']} 失败: {e}")

    return news_list


def fetch_all_rss():
    """抓取所有RSS源

    Returns:
        list: 所有RSS源抓取的新闻列表
    """
    all_news = []

    for source in RSS_SOURCES:
        news_list = fetch_single_rss(source)
        all_news.extend(news_list)

    return all_news


if __name__ == '__main__':
    # 测试
    print("测试RSS抓取...")
    news = fetch_all_rss()
    print(f"共抓取到 {len(news)} 条新闻")
