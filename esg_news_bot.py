#!/usr/bin/env python3
"""
欧洲ESG新闻抓取脚本
定时运行抓取RSS源并推送到微信
"""

import os
import re
import json
import requests
from datetime import datetime
from dateutil import parser as date_parser
import feedparser

# ===== 配置 =====
# Server酱 SCKEY (免费注册: https://sc.ftqq.com/)
SENDKEY = os.environ.get('SENDKEY', '')

# RSS新闻源
RSS_SOURCES = [
    {
        'name': '欧盟委员会气候',
        'url': 'https://climate.ec.europa.eu/rss_en',
        'keywords': ['environment', 'climate', 'energy', 'sustainability', 'green', 'carbon', 'emissions', 'ESG']
    },
    {
        'name': '欧洲环境署 EEA',
        'url': 'https://www.eea.europa.eu/en/rss',
        'keywords': ['environment', 'climate', 'sustainability', 'carbon', 'emissions', 'ESG']
    },
    {
        'name': '德勤ESG',
        'url': 'https://www2.deloitte.com/content/Domains/rss/sustainability.rss',
        'keywords': ['ESG', 'sustainability', 'climate', 'green', 'carbon', 'net zero']
    },
    {
        'name': 'Reuters ESG',
        'url': 'https://www.reutersagency.com/feed/?best-topics=esg&post_type=best',
        'keywords': ['ESG', 'sustainability', 'climate', 'carbon', 'emissions', 'green']
    },
    {
        'name': 'Carbon Pulse',
        'url': 'https://carbon-pulse.com/feed/',
        'keywords': ['carbon', 'ETS', 'emissions', 'trading', 'allowance']
    },
]

# 关键词过滤（用于筛选ESG相关内容）
ESG_KEYWORDS = [
    'ESG', 'sustainability', 'sustainable', 'climate', 'carbon', 'emissions',
    'green', 'renewable', 'net zero', 'carbon neutral', 'environmental',
    'EU ETS', 'emissions trading', 'carbon market', 'carbon credit',
    'circular economy', 'green deal', 'fit for 55'
]

# ===== 函数 =====

def is_esg_related(text):
    """检查文本是否与ESG相关"""
    if not text:
        return False
    text_lower = text.lower()
    for keyword in ESG_KEYWORDS:
        if keyword.lower() in text_lower:
            return True
    return False

def fetch_rss_news(source):
    """抓取单个RSS源"""
    news_list = []
    try:
        print(f"抓取: {source['name']}")
        feed = feedparser.parse(source['url'])

        for entry in feed.entries[:10]:  # 每个源取最新10条
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

def fetch_all_news():
    """抓取所有RSS源"""
    all_news = []
    for source in RSS_SOURCES:
        news = fetch_rss_news(source)
        all_news.extend(news)

    # 按发布时间排序
    all_news.sort(key=lambda x: x.get('published', ''), reverse=True)

    # 去重（根据标题相似度）
    seen = set()
    unique_news = []
    for news in all_news:
        title_key = news['title'][:30].lower()
        if title_key not in seen:
            seen.add(title_key)
            unique_news.append(news)

    return unique_news[:20]  # 最多返回20条

def format_news_message(news_list):
    """格式化新闻为微信消息"""
    if not news_list:
        return "今日暂无新的ESG新闻"

    date_str = datetime.now().strftime('%Y-%m-%d')
    message = f"📰 欧洲ESG新闻 ({date_str})\n\n"

    for i, news in enumerate(news_list[:8], 1):  # 最多8条
        message += f"{i}. {news['title']}\n"
        message += f"   来源: {news['source']}\n"
        message += f"   链接: {news['link']}\n\n"

    message += "---来自SusView自动推送"
    return message

def save_to_github(message):
    """保存新闻到GitHub兼容格式 (供GitHub Actions自动提交)"""
    # 输出为Markdown格式，方便查看
    print("\n" + "="*50)
    print("📰 今日ESG新闻摘要")
    print("="*50)
    print(message)
    print("="*50)

    # 保存到文件 (GitHub Actions会自动提交这个文件)
    with open('news/latest.md', 'w', encoding='utf-8') as f:
        f.write(f"# 欧洲ESG新闻\n\n")
        f.write(f"更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(message)
        f.write("\n\n---\n自动抓取自 SusView\n")

    print("\n✅ 新闻已保存到 news/latest.md")

    return True

def main():
    print(f"=== 开始抓取ESG新闻 {datetime.now().strftime('%Y-%m-%d %H:%M')} ===")

    # 抓取新闻
    news_list = fetch_all_news()
    print(f"共抓取到 {len(news_list)} 条ESG相关新闻")

    # 格式化消息
    message = format_news_message(news_list)

    # 保存到文件（GitHub会自动提交）
    save_to_github(message)

    print("=== 完成 ===")

if __name__ == '__main__':
    main()
