#!/usr/bin/env python3
"""
AI Provider 适配器
支持多种AI服务的统一调用接口
"""

import os
import json
import requests
from ai_config import AI_CONFIG


def get_ai_summary(news_list, max_news=5):
    """
    获取AI生成的新闻摘要
    根据配置自动调用对应的AI服务

    Args:
        news_list: 新闻列表
        max_news: 最多处理的新闻数量

    Returns:
        str: AI生成的摘要，失败时返回None
    """
    provider = AI_CONFIG.get('provider', 'custom')

    # 构建新闻内容
    news_content = build_news_content(news_list, max_news)

    # 根据provider调用对应的AI服务
    if provider == 'openai':
        return call_openai(news_content)
    elif provider == 'anthropic':
        return call_anthropic(news_content)
    elif provider == 'minimax':
        return call_minimax(news_content)
    elif provider == 'deepseek':
        return call_deepseek(news_content)
    elif provider == 'longcat':
        return call_longcat(news_content)
    elif provider == 'custom':
        return call_custom_api(news_content)
    else:
        print(f"⚠️ 未知的AI provider: {provider}")
        return None


def build_news_content(news_list, max_news=5):
    """构建发送给AI的新闻内容"""
    content = "请为以下ESG新闻生成详细的中文摘要，包含背景、影响和意义：\n\n"
    for i, news in enumerate(news_list[:max_news], 1):
        content += f"【新闻{i}】\n"
        content += f"标题: {news.get('title', '')}\n"
        content += f"来源: {news.get('source', '')}\n"
        content += f"摘要: {news.get('summary', '')}\n"
        content += f"链接: {news.get('link', '')}\n\n"
    return content


# ===== OpenAI =====

def call_openai(content):
    """调用 OpenAI API"""
    import openai

    config = AI_CONFIG.get('openai', {})
    api_key = config.get('api_key') or os.environ.get('OPENAI_API_KEY')
    model = config.get('model', 'gpt-3.5-turbo')

    if not api_key:
        print("⚠️ 未配置 OpenAI API Key")
        return None

    openai.api_key = api_key

    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是一个专业的ESG新闻分析师，请用中文生成详细、有洞察力的新闻摘要。"},
                {"role": "user", "content": content}
            ],
            max_tokens=1500,
            temperature=0.7,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"❌ OpenAI API 调用失败: {e}")
        return None


# ===== Anthropic Claude =====

def call_anthropic(content):
    """调用 Anthropic Claude API"""
    try:
        import anthropic
    except ImportError:
        print("⚠️ 请安装 anthropic 库: pip install anthropic")
        return None

    config = AI_CONFIG.get('anthropic', {})
    api_key = config.get('api_key') or os.environ.get('ANTHROPIC_API_KEY')
    model = config.get('model', 'claude-3-haiku-20240307')

    if not api_key:
        print("⚠️ 未配置 Anthropic API Key")
        return None

    try:
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model=model,
            max_tokens=1500,
            system="你是一个专业的ESG新闻分析师，请用中文生成详细、有洞察力的新闻摘要。",
            messages=[{"role": "user", "content": content}]
        )
        return message.content[0].text
    except Exception as e:
        print(f"❌ Anthropic API 调用失败: {e}")
        return None


# ===== MiniMax =====

def call_minimax(content):
    """调用 MiniMax API"""
    config = AI_CONFIG.get('minimax', {})
    api_key = config.get('api_key') or os.environ.get('MINIMAX_API_KEY')
    model = config.get('model', 'abab6.5s-chat')
    api_base = config.get('api_base', 'https://api.minimax.chat/v1')

    if not api_key:
        print("⚠️ 未配置 MiniMax API Key")
        return None

    url = f"{api_base}/text/chatcompletion_v2"

    try:
        response = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": "你是一个专业的ESG新闻分析师，请用中文生成详细、有洞察力的新闻摘要。"},
                    {"role": "user", "content": content}
                ],
                "max_tokens": 1500,
                "temperature": 0.7
            },
            timeout=60
        )
        result = response.json()

        if 'choices' in result and len(result['choices']) > 0:
            return result['choices'][0]['message']['content']
        else:
            print(f"❌ MiniMax API 返回异常: {result}")
            return None
    except Exception as e:
        print(f"❌ MiniMax API 调用失败: {e}")
        return None


# ===== DeepSeek =====

def call_deepseek(content):
    """调用 DeepSeek API"""
    config = AI_CONFIG.get('deepseek', {})
    api_key = config.get('api_key') or os.environ.get('DEEPSEEK_API_KEY')
    model = config.get('model', 'deepseek-chat')

    if not api_key:
        print("⚠️ 未配置 DeepSeek API Key")
        return None

    url = "https://api.deepseek.com/chat/completions"

    try:
        response = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": "你是一个专业的ESG新闻分析师，请用中文生成详细、有洞察力的新闻摘要。"},
                    {"role": "user", "content": content}
                ],
                "max_tokens": 1500,
                "temperature": 0.7
            },
            timeout=60
        )
        result = response.json()

        if 'choices' in result and len(result['choices']) > 0:
            return result['choices'][0]['message']['content']
        else:
            print(f"❌ DeepSeek API 返回异常: {result}")
            return None
    except Exception as e:
        print(f"❌ DeepSeek API 调用失败: {e}")
        return None


# ===== LongCat =====

def call_longcat(content):
    """调用 LongCat API"""
    config = AI_CONFIG.get('longcat', {})
    api_key = config.get('api_key') or os.environ.get('LONGCAT_API_KEY')
    model = config.get('model', 'longchat-lion-7b')
    api_base = config.get('api_base', 'https://api.longcat.cn/v1')

    if not api_key:
        print("⚠️ 未配置 LongCat API Key")
        return None

    url = f"{api_base}/chat/completions"

    try:
        response = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": "你是一个专业的ESG新闻分析师，请用中文生成详细、有洞察力的新闻摘要。"},
                    {"role": "user", "content": content}
                ],
                "max_tokens": 1500,
                "temperature": 0.7
            },
            timeout=60
        )
        result = response.json()

        if 'choices' in result and len(result['choices']) > 0:
            return result['choices'][0]['message']['content']
        else:
            print(f"❌ LongCat API 返回异常: {result}")
            return None
    except Exception as e:
        print(f"❌ LongCat API 调用失败: {e}")
        return None


# ===== 自定义 API =====

def call_custom_api(content):
    """
    调用自定义API
    适用于其他第三方API服务，只需配置好api_base和model即可
    """
    config = AI_CONFIG.get('custom', {})
    api_key = config.get('api_key') or os.environ.get('CUSTOM_API_KEY')
    api_base = config.get('api_base') or os.environ.get('CUSTOM_API_BASE')
    model = config.get('model') or os.environ.get('CUSTOM_MODEL')
    system_prompt = config.get('system_prompt', '你是一个专业的ESG新闻分析师，请用中文生成详细、有洞察力的新闻摘要。')

    if not api_key or not api_base:
        print("⚠️ 未配置自定义API (需要 api_key 和 api_base)")
        print("   请在 ai_config.py 中配置或设置环境变量 CUSTOM_API_KEY 和 CUSTOM_API_BASE")
        return None

    # 兼容 OpenAI 格式的API
    url = f"{api_base.rstrip('/')}/chat/completions"

    try:
        response = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": content}
                ],
                "max_tokens": 1500,
                "temperature": 0.7
            },
            timeout=60
        )
        result = response.json()

        if 'choices' in result and len(result['choices']) > 0:
            return result['choices'][0]['message']['content']
        else:
            print(f"❌ 自定义API 返回异常: {result}")
            return None
    except Exception as e:
        print(f"❌ 自定义API 调用失败: {e}")
        return None


# ===== 添加新的AI服务商 =====
# 参考上面的示例，添加新的函数并注册到 get_ai_summary 中
#
# 示例：添加新的API服务商 "newapi"
# 1. 在 ai_config.py 中添加配置:
#    'newapi': {
#        'api_key': '',
#        'model': 'xxx',
#        'api_base': 'https://api.newapi.com/v1',
#    }
#
# 2. 在 ai_providers.py 中添加调用函数:
#    def call_newapi(content):
#        config = AI_CONFIG.get('newapi', {})
#        # 实现调用逻辑...
#
# 3. 在 get_ai_summary 中添加:
#    elif provider == 'newapi':
#        return call_newapi(content)
#
# 4. 修改 ai_config.py 中的 'provider' 为 'newapi'
