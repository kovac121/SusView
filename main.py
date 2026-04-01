#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ESG新闻爬虫主入口
使用多进程提高抓取性能
"""
import sys
import io

# 解决Windows控制台编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import os
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import cpu_count

# 导入配置
from config import (
    MAX_WORKERS, MAX_NEWS, SOURCE_SHORT_NAMES,
    TEMPLATE_FILE, OUTPUT_FILE, is_esg_related
)

# 导入抓取模块
import rss_fetcher
import web_scraper

# AI 摘要功能
try:
    from ai_providers import get_ai_summary, get_model_name
    AI_ENABLED = True
except ImportError:
    AI_ENABLED = False
    print("⚠️ AI功能未启用 (ai_providers.py 未找到)")

# 邮件发送功能
try:
    from email_sender import send_html_file
    EMAIL_ENABLED = True
except ImportError:
    EMAIL_ENABLED = False
    print("⚠️ 邮件功能未启用 (email_sender.py 未找到)")


def fetch_source(source):
    """多进程抓取单个源

    Args:
        source: 源配置字典

    Returns:
        list: 新闻列表
    """
    if source['type'] == 'rss':
        return rss_fetcher.fetch_single_rss(source)
    else:
        return web_scraper.scrape_single_media(source)


def fetch_all_news():
    """使用多进程抓取所有新闻源

    Returns:
        list: 所有新闻列表
    """
    from config import ALL_SOURCES

    all_news = []

    # 使用多进程并行抓取
    # 注意：ProcessPoolExecutor不能直接传递方法，需要使用模块级函数
    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # 提交所有任务
        future_to_source = {
            executor.submit(fetch_source, source): source
            for source in ALL_SOURCES
        }

        # 收集结果
        for future in as_completed(future_to_source):
            source = future_to_source[future]
            try:
                news_list = future.result()
                if news_list:
                    all_news.extend(news_list)
                    print(f"✓ {source['name']}: 抓取到 {len(news_list)} 条新闻")
            except Exception as e:
                print(f"✗ {source['name']}: 抓取失败 - {e}")

    return all_news


def deduplicate_and_sort(news_list):
    """去重和排序

    Args:
        news_list: 新闻列表

    Returns:
        list: 去重排序后的新闻列表
    """
    # 按发布时间排序
    news_list.sort(key=lambda x: x.get('published', ''), reverse=True)

    # 去重（基于URL和标题）
    seen_urls = set()
    seen_titles = set()
    unique_news = []

    for news in news_list:
        url_key = news.get('link', '')
        if url_key and url_key in seen_urls:
            continue
        seen_urls.add(url_key)

        title = news.get('title', '').lower().strip()
        title_key = title[:50]
        if title_key in seen_titles:
            continue
        seen_titles.add(title_key)

        unique_news.append(news)

    return unique_news[:MAX_NEWS]


def parse_ai_translations(ai_content, news_list):
    """解析AI返回的JSON翻译数据"""
    import json
    import re

    if not ai_content:
        return news_list

    try:
        json_match = re.search(r'\[.*\]', ai_content, re.DOTALL)
        if json_match:
            translations = json.loads(json_match.group())
        else:
            translations = json.loads(ai_content)

        for i, trans in enumerate(translations):
            if i < len(news_list):
                news_list[i]['title_cn'] = trans.get('title', news_list[i].get('title', ''))
                news_list[i]['ai_summary'] = trans.get('summary', '')

        return news_list
    except Exception as e:
        print(f"⚠️ AI返回数据解析失败: {e}")
        return news_list


def format_wechat_html(news_list, ai_model_name=None):
    """生成适合微信的HTML格式（微信兼容的内联样式）"""
    if not news_list:
        return ""

    # 生成新闻项HTML（微信兼容的内联样式）
    news_items = []
    for news in news_list[:10]:
        source = SOURCE_SHORT_NAMES.get(news['source'], news['source'])
        title = news['title']
        title_cn = news.get('title_cn', '')
        ai_summary = news.get('ai_summary', '')
        summary = news.get('summary', '')[:120]
        link = news['link']
        published = news.get('published', '')[:16]

        # 微信兼容HTML：无border-radius/box-shadow/rgba，用border做分割
        if title_cn:
            ai_summary_html = f'<div style="background:#e8f5e9;padding:10px 12px;border-left:3px solid #22c55e;font-size:14px;color:#333333;">{ai_summary}</div>' if ai_summary else ''

            item = f'''
        <div style="background:#ffffff;padding:16px;border-bottom:1px solid #e9ecef;">
            <div style="margin-bottom:8px;">
                <span style="background:#e8f5e9;color:#2e7d32;padding:3px 8px;font-size:11px;font-weight:600;">{source}</span>
                <span style="font-size:12px;color:#666666;">{published}</span>
            </div>
            <h3 style="margin:0;font-size:16px;font-weight:600;color:#1a1a1a;line-height:1.4;">{title_cn}</h3>
            <div style="font-size:12px;color:#666666;">原文: {title}</div>
            {ai_summary_html}
            <a href="{link}" style="color:#15803d;font-size:13px;font-weight:500;">阅读原文 →</a>
        </div>'''
        else:
            item = f'''
        <div style="background:#ffffff;padding:16px;border-bottom:1px solid #e9ecef;">
            <div style="margin-bottom:8px;">
                <span style="background:#e8f5e9;color:#2e7d32;padding:3px 8px;font-size:11px;font-weight:600;">{source}</span>
                <span style="font-size:12px;color:#666666;">{published}</span>
            </div>
            <h3 style="margin:0;font-size:16px;font-weight:600;color:#1a1a1a;line-height:1.4;">{title}</h3>
            <div style="font-size:14px;color:#666666;">{summary}</div>
            <a href="{link}" style="color:#15803d;font-size:13px;font-weight:500;">阅读原文 →</a>
        </div>'''
        news_items.append(item)

    # AI区域 - 微信兼容
    ai_summary_section = ""
    if ai_model_name:
        ai_summary_section = f'''
    <div style="background:#e8f5e9;padding:12px 16px;border-bottom:1px solid #c8e6c9;font-size:13px;color:#2e7d32;">
        <span>AI翻译摘要</span>
        <span style="font-size:12px;color:#666666;">{ai_model_name}</span>
    </div>'''

    # 读取模板并替换
    template = TEMPLATE_FILE.read_text(encoding='utf-8')
    html = template.replace('{{date_str}}', datetime.now().strftime('%Y年%m月%d日'))
    html = html.replace('{{count}}', str(len(news_list[:10])))
    html = html.replace('{{ai_summary}}', ai_summary_section)
    html = html.replace('{{news_items}}', '\n'.join(news_items))

    return html


def save_html(html_content):
    """保存HTML到文件"""
    OUTPUT_FILE.write_text(html_content, encoding='utf-8')
    print("\n✅ HTML已保存到 news/latest.html")
    return True


def main():
    print(f"=== 开始抓取ESG新闻 {datetime.now().strftime('%Y-%m-%d %H:%M')} ===")
    print(f"使用 {MAX_WORKERS} 个进程并行抓取...")

    # 确保news目录存在
    os.makedirs('news', exist_ok=True)

    # 抓取新闻
    news_list = fetch_all_news()
    print(f"\n共抓取到 {len(news_list)} 条原始新闻")

    # 去重和排序
    news_list = deduplicate_and_sort(news_list)
    print(f"去重后剩余 {len(news_list)} 条新闻")

    # 获取AI翻译和摘要
    ai_model_name = None
    if AI_ENABLED and news_list:
        print("🤖 正在生成AI翻译和摘要...")
        ai_content, _ = get_ai_summary(news_list)
        if ai_content:
            news_list = parse_ai_translations(ai_content, news_list)
            ai_model_name = get_model_name()
            print(f"✅ AI翻译生成成功 ({ai_model_name})")
        else:
            print("⚠️ AI翻译生成失败，将跳过")

    # 格式化HTML
    html_content = format_wechat_html(news_list, ai_model_name)

    # 保存到文件
    save_html(html_content)

    # 发送邮件
    if EMAIL_ENABLED:
        print("\n📧 正在发送邮件...")
        if send_html_file(str(OUTPUT_FILE)):
            print("✅ 邮件发送成功!")
        else:
            print("⚠️ 邮件发送失败")

    print("=== 完成 ===")


if __name__ == '__main__':
    main()
