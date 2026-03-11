#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
欧洲ESG新闻抓取脚本
定时运行抓取RSS源并推送到微信
"""
import sys
import io

# 解决Windows控制台编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import os
import re
import json
from pathlib import Path
from datetime import datetime
from dateutil import parser as date_parser
from concurrent.futures import ThreadPoolExecutor
import feedparser
from scrapling import Fetcher
import time
from threading import Lock

# AI 摘要功能
try:
    from ai_providers import get_ai_summary, get_model_name
    AI_ENABLED = True
except ImportError:
    AI_ENABLED = False
    print("⚠️ AI功能未启用 (ai_providers.py 未找到)")

# 速率限制器 - 每分钟最多15次请求
class RateLimiter:
    def __init__(self, max_requests_per_minute=15):
        self.max_requests = max_requests_per_minute
        self.requests = []
        self.lock = Lock()

    def wait_if_needed(self):
        """如果需要，等待直到可以发送下一个请求"""
        with self.lock:
            now = time.time()
            # 移除1分钟前的请求记录
            self.requests = [req_time for req_time in self.requests if now - req_time < 60]

            # 如果达到限制，等待
            if len(self.requests) >= self.max_requests:
                sleep_time = 60 - (now - self.requests[0]) + 1
                print(f"⏰ 已达到速率限制，等待 {sleep_time:.1f} 秒...")
                time.sleep(sleep_time)
                # 清空旧的请求记录
                now = time.time()
                self.requests = [req_time for req_time in self.requests if now - req_time < 60]

            # 记录当前请求
            self.requests.append(now)

# 全局速率限制器
rate_limiter = RateLimiter()


def parse_ai_translations(ai_content, news_list):
    """
    解析AI返回的JSON翻译数据

    Args:
        ai_content: AI返回的JSON字符串
        news_list: 原始新闻列表

    Returns:
        list: 更新后的新闻列表，包含中文标题和AI摘要
    """
    if not ai_content:
        return news_list

    try:
        # 尝试提取JSON部分
        json_match = re.search(r'\[.*\]', ai_content, re.DOTALL)
        if json_match:
            translations = json.loads(json_match.group())
        else:
            translations = json.loads(ai_content)

        # 更新新闻列表
        for i, trans in enumerate(translations):
            if i < len(news_list):
                news_list[i]['title_cn'] = trans.get('title', news_list[i].get('title', ''))
                news_list[i]['ai_summary'] = trans.get('summary', '')

        return news_list
    except json.JSONDecodeError as e:
        print(f"⚠️ AI返回数据解析失败: {e}")
        return news_list



# RSS新闻源
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

# 媒体源配置（直接抓取的源）
MEDIA_SOURCES = [
    {
        'name': 'Bloomberg ESG',
        'url': 'https://www.bloomberg.com/topics/esg',
        'type': 'scrape',
        'keywords': ['ESG', 'sustainability', 'climate', 'carbon', 'emissions'],
        'selectors': ['.article-body', '.content', 'article', 'main'],
        'scrape_pattern': 'data-testid="article-body"',
        'detail_url_pattern': 'https://www.bloomberg.com/.*',
        'max_articles': 5
    },
    {
        'name': 'Financial Times ESG',
        'url': 'https://www.ft.com/content/climate-environment',
        'type': 'scrape',
        'keywords': ['ESG', 'sustainability', 'climate', 'carbon', 'emissions'],
        'selectors': ['.article-body-content', 'article', 'main', '.content'],
        'scrape_pattern': 'data-content-type="article"',
        'detail_url_pattern': 'https://www.ft.com/content/.*',
        'max_articles': 5
    },
    {
        'name': 'ICIS ESG',
        'url': 'https://www.icis.com/energy-transition-esg/',
        'type': 'scrape',
        'keywords': ['carbon', 'emissions', 'trading', 'climate', 'ESG'],
        'selectors': ['.article-content', 'article', 'main', '.content'],
        'scrape_pattern': 'class="article"',
        'detail_url_pattern': 'https://www.icis.com/.*',
        'max_articles': 5
    },
    {
        'name': 'S&P Global ESG',
        'url': 'https://www.spglobal.com/esg/',
        'type': 'scrape',
        'keywords': ['ESG', 'sustainability', 'climate', 'carbon', 'emissions'],
        'selectors': ['.article-content', 'article', 'main', '.content'],
        'scrape_pattern': 'class="article"',
        'detail_url_pattern': 'https://www.spglobal.com/.*',
        'max_articles': 5
    },
    {
        'name': 'Global Platts ESG',
        'url': 'https://www.spglobal.com/commodityinsights/en/',
        'type': 'scrape',
        'keywords': ['energy', 'carbon', 'emissions', 'climate', 'ESG'],
        'selectors': ['.article-content', 'article', 'main', '.content'],
        'scrape_pattern': 'class="article"',
        'detail_url_pattern': 'https://www.spglobal.com/.*',
        'max_articles': 5
    }
]

# 合并所有源
ALL_SOURCES = RSS_SOURCES + MEDIA_SOURCES

# 关键词过滤（用于筛选ESG相关内容）
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
    'EUA futures', 'carbon futures', ' allowance futures', 'carbon contracts',
    'Phase 4', 'Phase 3', 'Trading Period', 'MRVA', 'FLEX', 'NER',

    # 政策和法规
    'Fit for 55', 'Green Deal', 'Climate Law', 'Carbon Border Adjustment',
    'CBAM', 'carbon border tax', 'energy transition', 'just transition',

    # 其他相关术语
    'circular economy', 'green deal', 'fit for 55',
    'decarbonization', 'decarbonize', 'low carbon', 'zero carbon',
    'climate target', 'carbon budget', 'climate action'
]

# 预编译正则表达式（性能优化）
ESG_PATTERN = re.compile('|'.join(re.escape(kw) for kw in ESG_KEYWORDS), re.IGNORECASE)

# ===== 函数 =====

def is_esg_related(text):
    """检查文本是否与ESG相关（使用预编译正则）"""
    if not text:
        return False
    return bool(ESG_PATTERN.search(text))

def fetch_rss_news(source):
    """抓取单个RSS源"""
    news_list = []
    try:
        print(f"抓取: {source['name']}")

        # 应用速率限制
        rate_limiter.wait_if_needed()

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

def fetch_page_content(url, selectors=None, max_retries=2):
    """使用scrapling抓取网页内容

    Args:
        url: 目标URL
        selectors: CSS选择器列表，默认为 ['article', 'main', '.content', '.article']
        max_retries: 最大重试次数

    Returns:
        提取的文本内容，如果失败返回None
    """
    if selectors is None:
        selectors = ['article', 'main', '.content', '.article', '.post-content']

    # User-Agent列表（避免被反爬）
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0'
    ]

    for attempt in range(max_retries):
        try:
            # 应用速率限制
            rate_limiter.wait_if_needed()

            # 轮换User-Agent
            ua = user_agents[attempt % len(user_agents)]
            session = Fetcher(default_headers={'User-Agent': ua})

            # 添加随机延迟，避免请求过快
            if attempt > 0:
                import time
                time.sleep(1 + attempt * 0.5)

            response = session.get(url)

            # 尝试多个选择器
            for selector in selectors:
                try:
                    element = response.css(selector).first()
                    if element:
                        text = element.text(separator=' ', trim=True)
                        # 清理多余空白和特殊字符
                        text = re.sub(r'\s+', ' ', text).strip()
                        text = re.sub(r'[\n\r\t]+', ' ', text)
                        # 提取正文内容（去除导航栏、广告等）
                        if len(text) > 100:  # 只返回足够长度的内容
                            return text[:800]  # 增加内容长度
                except Exception as e:
                    continue

            # 如果选择器都失败，尝试提取主要内容
            if response.text:
                # 尝试从页面中提取主要内容
                content = response.text
                # 移除script和style标签
                content = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', content, flags=re.DOTALL)
                # 提取纯文本
                text = re.sub(r'<[^>]+>', ' ', content)
                text = re.sub(r'\s+', ' ', text).strip()
                if len(text) > 200:
                    return text[:800]

            return None

        except Exception as e:
            if attempt == max_retries - 1:
                print(f"抓取页面失败 {url} (尝试 {attempt + 1}/{max_retries}): {e}")
            else:
                print(f"抓取页面失败，正在重试 {url} (尝试 {attempt + 1}/{max_retries}): {e}")

    return None


def scrape_media_source(source):
    """专门针对特定媒体源的抓取函数

    Args:
        source: 媒体源配置字典

    Returns:
        list: 新闻列表
    """
    news_list = []

    try:
        print(f"抓取媒体源: {source['name']} - {source['url']}")

        if source['type'] == 'rss':
            # RSS源使用原有逻辑
            return fetch_rss_news(source)

        elif source['type'] == 'scrape':
            # 直接抓取网页
            session = Fetcher(default_headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})

            # 抓取主页面
            response = session.get(source['url'])

            # 根据网站特性查找新闻链接
            if 'bloomberg.com' in source['url']:
                # Bloomberg - 查找带有ESG标签的文章
                links = response.css('a[data-testid="article-link"]').getall()
                links = [link for link in links if '/articles/' in link]

            elif 'ft.com' in source['url']:
                # Financial Times - 查找文章链接
                links = response.css('a[data-trackable="headline"]').getall()
                links = [link for link in links if '/content/' in link]

            elif 'icis.com' in source['url']:
                # ICIS - 查找文章链接
                links = response.css('a[href*="/energy-transition-esg/"]').getall()

            elif 'spglobal.com' in source['url']:
                # S&P Global - 查找文章链接
                links = response.css('a[href*="/esg/"]').getall()

            else:
                # 默认查找所有可能的链接
                links = response.css('a[href]').getall()

            # 提取并处理新闻链接
            for link in links[:10]:  # 最多处理10篇文章
                try:
                    # 提取URL
                    import re
                    match = re.search(r'href="([^"]+)"', link)
                    if match:
                        url = match.group(1)
                        if url.startswith('/'):
                            # 相对URL，补全为完整URL
                            domain = source['url'].split('//')[1].split('/')[0]
                            url = f"https://{domain}{url}"

                        # 检查是否符合URL模式
                        if 'detail_url_pattern' in source and not re.search(source['detail_url_pattern'], url):
                            continue

                        # 抓取文章内容
                        content = fetch_page_content(url, source['selectors'])
                        if content and is_esg_related(content):
                            # 提取标题（简单处理，实际可能需要更复杂的解析）
                            title = f"新闻标题 - {source['name']}"
                            summary = content[:200] + '...' if len(content) > 200 else content

                            # 获取当前时间
                            published = datetime.now().strftime('%Y-%m-%d %H:%M')

                            news_list.append({
                                'title': title,
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

def fetch_all_news():
    """抓取所有新闻源（RSS和直接抓取）"""
    # 并发抓取所有源
    def get_fetcher(source):
        # 兼容旧版本RSS源（没有type字段）
        if 'type' not in source or source['type'] == 'rss':
            return fetch_rss_news(source)
        else:
            return scrape_media_source(source)

    with ThreadPoolExecutor(max_workers=5) as executor:
        results = executor.map(get_fetcher, ALL_SOURCES)

    all_news = []
    for news_list in results:
        if news_list:  # 确保有结果
            all_news.extend(news_list)

    # 按发布时间排序
    all_news.sort(key=lambda x: x.get('published', ''), reverse=True)

    # 去重（基于URL和标题）
    seen_urls = set()
    seen_titles = set()
    unique_news = []

    for news in all_news:
        # 基于URL去重
        url_key = news.get('link', '')
        if url_key in seen_urls:
            continue
        seen_urls.add(url_key)

        # 基于标题去重
        title = news.get('title', '').lower().strip()
        title_key = title[:50]  # 取前50个字符
        if title_key in seen_titles:
            continue
        seen_titles.add(title_key)

        unique_news.append(news)

    return unique_news[:30]  # 最多返回30条新闻

def format_wechat_html(news_list, ai_model_name=None):
    """生成适合微信的HTML格式"""
    if not news_list:
        return ""

    # 来源映射（简称）
    source_map = {
        '欧盟委员会气候': '欧盟',
        '欧洲环境署 EEA': 'EEA',
        '德勤ESG': '德勤',
        'Reuters ESG': '路透',
        'Carbon Pulse': 'Carbon Pulse'
    }

    # 生成新闻项HTML
    news_items = []
    for news in news_list[:8]:
        source = source_map.get(news['source'], news['source'])
        title = news['title']
        title_cn = news.get('title_cn', '')
        ai_summary = news.get('ai_summary', '')
        summary = news.get('summary', '')[:120]
        link = news['link']
        published = news.get('published', '')[:16]

        if title_cn:
            item = f"""<div class="news-item">
            <div class="news-header">
                <span class="news-source">{source}</span>
                <span class="news-time">{published}</span>
            </div>
            <h3 class="news-title">{title_cn}</h3>
            <p class="news-original-title">原文: {title}</p>
            {'<p class="ai-summary-text">' + ai_summary + '</p>' if ai_summary else ''}
            <a class="news-link" href="{link}">阅读原文</a>
        </div>"""
        else:
            item = f"""<div class="news-item">
            <div class="news-header">
                <span class="news-source">{source}</span>
                <span class="news-time">{published}</span>
            </div>
            <h3 class="news-title">{title}</h3>
            <p class="news-summary">{summary}</p>
            <a class="news-link" href="{link}">阅读原文</a>
        </div>"""
        news_items.append(item)

    # AI区域
    ai_section = ""
    if ai_model_name:
        ai_section = f"""<div class="ai-summary">
            <span>AI翻译摘要</span>
            <span class="ai-model">{ai_model_name}</span>
        </div>"""

    # 读取模板并替换
    template_path = Path(__file__).parent / 'news' / 'template.html'
    template = template_path.read_text(encoding='utf-8')
    html = template.replace('{{date_str}}', datetime.now().strftime('%Y年%m月%d日'))
    html = html.replace('{{count}}', str(len(news_list[:8])))
    html = html.replace('{{ai_section}}', ai_section)
    html = html.replace('{{news_items}}', '\n'.join(news_items))

    return html

def save_to_github(html_content):
    """保存HTML到文件"""
    # 保存HTML版本
    html_path = Path(__file__).parent / 'news' / 'latest.html'
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print("\n✅ HTML已保存到 news/latest.html")

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

    # 获取AI翻译和摘要 (如果启用)
    ai_model_name = None
    if AI_ENABLED:
        print("🤖 正在生成AI翻译和摘要...")
        ai_content, _ = get_ai_summary(news_list)
        if ai_content:
            # 解析AI返回的翻译数据
            news_list = parse_ai_translations(ai_content, news_list)
            # 获取模型名称
            ai_model_name = get_model_name()
            print(f"✅ AI翻译生成成功 ({ai_model_name})")
        else:
            print("⚠️ AI翻译生成失败，将跳过")

    # 格式化HTML
    html_content = format_wechat_html(news_list, ai_model_name)

    # 保存到文件
    save_to_github(html_content)

    print("=== 完成 ===")

if __name__ == '__main__':
    main()
