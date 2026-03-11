#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网页爬取模块
"""
import re
import time
from datetime import datetime
from scrapling import Fetcher

from config import (
    MEDIA_SOURCES, USER_AGENTS, MAX_ARTICLES_PER_SOURCE, is_esg_related
)


class RateLimiter:
    """简单的速率限制器"""
    def __init__(self, max_per_minute=15):
        self.max_per_minute = max_per_minute
        self.requests = []

    def wait_if_needed(self):
        """等待直到可以发送请求"""
        now = time.time()
        # 移除1分钟前的请求
        self.requests = [t for t in self.requests if now - t < 60]

        if len(self.requests) >= self.max_per_minute:
            sleep_time = 60 - (now - self.requests[0]) + 0.5
            time.sleep(sleep_time)
            self.requests = [t for t in self.requests if time.time() - t < 60]

        self.requests.append(time.time())


# 全局速率限制器
rate_limiter = RateLimiter()


def fetch_page_content(url, selectors=None, max_retries=2):
    """使用scrapling抓取网页内容

    Args:
        url: 目标URL
        selectors: CSS选择器列表
        max_retries: 最大重试次数

    Returns:
        str: 提取的文本内容，如果失败返回None
    """
    if selectors is None:
        selectors = ['article', 'main', '.content', '.article', '.post-content']

    for attempt in range(max_retries):
        try:
            # 应用速率限制
            rate_limiter.wait_if_needed()

            # 轮换User-Agent
            ua = USER_AGENTS[attempt % len(USER_AGENTS)]
            session = Fetcher(default_headers={'User-Agent': ua})

            response = session.get(url)

            # 尝试多个选择器
            for selector in selectors:
                try:
                    element = response.css(selector).first()
                    if element:
                        text = element.text(separator=' ', trim=True)
                        text = re.sub(r'\s+', ' ', text).strip()
                        text = re.sub(r'[\n\r\t]+', ' ', text)
                        if len(text) > 100:
                            return text[:800]
                except:
                    continue

            # 备用方案：提取纯文本
            if response.text:
                content = response.text
                content = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', content, flags=re.DOTALL)
                text = re.sub(r'<[^>]+>', ' ', content)
                text = re.sub(r'\s+', ' ', text).strip()
                if len(text) > 200:
                    return text[:800]

            return None

        except Exception as e:
            if attempt == max_retries - 1:
                print(f"抓取页面失败 {url}: {e}")
            else:
                time.sleep(1 + attempt * 0.5)

    return None


def scrape_single_media(source):
    """抓取单个媒体源

    Args:
        source: 媒体源配置字典

    Returns:
        list: 新闻列表
    """
    news_list = []

    try:
        print(f"抓取媒体源: {source['name']}")

        # 创建session
        session = Fetcher(default_headers={'User-Agent': USER_AGENTS[0]})

        # 应用速率限制
        rate_limiter.wait_if_needed()

        # 抓取主页面
        response = session.get(source['url'])

        # 根据网站特性查找新闻链接
        links = []
        if 'bloomberg.com' in source['url']:
            links = response.css('a[data-testid="article-link"]').getall()
            links = [l for l in links if '/articles/' in l]
        elif 'ft.com' in source['url']:
            links = response.css('a[data-trackable="headline"]').getall()
            links = [l for l in links if '/content/' in l]
        elif 'icis.com' in source['url']:
            links = response.css('a[href*="/energy-transition-esg/"]').getall()
        elif 'spglobal.com' in source['url']:
            links = response.css('a[href*="/esg/"]').getall()
        else:
            links = response.css('a[href]').getall()

        # 处理链接
        max_articles = source.get('max_articles', 5)
        for link in links[:max_articles]:
            try:
                match = re.search(r'href="([^"]+)"', link)
                if match:
                    url = match.group(1)
                    if url.startswith('/'):
                        domain = source['url'].split('//')[1].split('/')[0]
                        url = f"https://{domain}{url}"

                    # 检查URL模式
                    pattern = source.get('detail_url_pattern', '')
                    if pattern and not re.search(pattern, url):
                        continue

                    # 抓取内容
                    content = fetch_page_content(url, source['selectors'])
                    if content and is_esg_related(content):
                        summary = content[:200] + '...' if len(content) > 200 else content
                        published = datetime.now().strftime('%Y-%m-%d %H:%M')

                        news_list.append({
                            'title': f"新闻 - {source['name']}",
                            'link': url,
                            'summary': summary,
                            'published': published,
                            'source': source['name']
                        })

            except Exception as e:
                print(f"处理链接失败: {e}")
                continue

    except Exception as e:
        print(f"抓取媒体源 {source['name']} 失败: {e}")

    return news_list


def scrape_all_media():
    """抓取所有媒体源

    Returns:
        list: 所有媒体源抓取的新闻列表
    """
    all_news = []

    for source in MEDIA_SOURCES:
        news_list = scrape_single_media(source)
        all_news.extend(news_list)

    return all_news


if __name__ == '__main__':
    # 测试
    print("测试网页爬取...")
    news = scrape_all_media()
    print(f"共抓取到 {len(news)} 条新闻")
