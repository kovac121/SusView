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


def format_wechat_html(news_list):
    """生成适合微信的HTML格式"""
    if not news_list:
        return ""

    date_str = datetime.now().strftime('%Y年%m月%d日')

    # 来源映射（简称）
    source_map = {
        '欧盟委员会气候': '欧盟',
        '欧洲环境署 EEA': 'EEA',
        '德勤ESG': '德勤',
        'Reuters ESG': '路透',
        'Carbon Pulse': 'Carbon Pulse'
    }

    html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 100%; }}
    .header {{ background: linear-gradient(135deg, #1a5f2a 0%, #2d8a4e 100%); color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
    .header h1 {{ margin: 0; font-size: 20px; }}
    .header .date {{ opacity: 0.9; font-size: 14px; margin-top: 5px; }}
    .news-list {{ background: #f9f9f9; padding: 15px; }}
    .news-item {{ background: white; border-radius: 8px; padding: 15px; margin-bottom: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.08); }}
    .news-item:last-child {{ margin-bottom: 0; }}
    .news-source {{ display: inline-block; background: #e8f5e9; color: #2e7d32; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: 500; margin-bottom: 8px; }}
    .news-title {{ font-size: 15px; font-weight: 600; color: #1a1a1a; margin: 0 0 8px 0; line-height: 1.4; }}
    .news-summary {{ font-size: 13px; color: #666; margin: 0 0 10px 0; line-height: 1.5; }}
    .news-link {{ display: inline-block; color: #1976d2; text-decoration: none; font-size: 13px; }}
    .news-link:after {{ content: ' →'; }}
    .footer {{ background: #f5f5f5; padding: 15px; text-align: center; font-size: 12px; color: #999; border-radius: 0 0 8px 8px; }}
    .count {{ background: #fff3e0; color: #e65100; padding: 3px 10px; border-radius: 12px; font-size: 12px; }}
</style>
</head>
<body>
    <div class="header">
        <h1>🌍 欧洲ESG新闻</h1>
        <div class="date">{date_str} · 今日{len(news_list[:8])}条</div>
    </div>
    <div class="news-list">
"""

    for news in news_list[:8]:
        source = source_map.get(news['source'], news['source'])
        title = news['title']
        summary = news.get('summary', '')[:100]
        link = news['link']

        html += f"""
        <div class="news-item">
            <span class="news-source">{source}</span>
            <h3 class="news-title">{title}</h3>
            <p class="news-summary">{summary}</p>
            <a class="news-link" href="{link}">阅读原文</a>
        </div>
"""

    html += """
    </div>
    <div class="footer">
        来源：欧盟委员会、欧洲环境署、德勤、路透、Carbon Pulse<br>
        SusView · 自动抓取整理
    </div>
</body>
</html>
"""
    return html

def save_to_github(message, html_content):
    """保存新闻到GitHub兼容格式 (供GitHub Actions自动提交)"""
    # 输出为Markdown格式，方便查看
    print("\n" + "="*50)
    print("📰 今日ESG新闻摘要")
    print("="*50)
    print(message)
    print("="*50)

    # 保存Markdown版本
    with open('news/latest.md', 'w', encoding='utf-8') as f:
        f.write(f"# 欧洲ESG新闻\n\n")
        f.write(f"更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(message)
        f.write("\n\n---\n自动抓取自 SusView\n")

    # 保存HTML版本（可直接复制到微信）
    with open('news/latest.html', 'w', encoding='utf-8') as f:
        f.write(html_content)

    print("\n✅ 新闻已保存到 news/latest.md 和 news/latest.html")

    return True

def main():
    import os
    print(f"=== 开始抓取ESG新闻 {datetime.now().strftime('%Y-%m-%d %H:%M')} ===")

    # 确保news目录存在
    os.makedirs('news', exist_ok=True)
    print("✅ news目录已准备")

    # 抓取新闻
    news_list = fetch_all_news()
    print(f"共抓取到 {len(news_list)} 条ESG相关新闻")

    # 格式化消息
    message = format_news_message(news_list)
    html_content = format_wechat_html(news_list)

    # 保存到文件（GitHub会自动提交）
    save_to_github(message, html_content)

    print("=== 完成 ===")

if __name__ == '__main__':
    main()
