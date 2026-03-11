#!/usr/bin/env python3
"""
AI Provider 适配器
支持多种AI服务的统一调用接口 (基于Anthropic兼容API)
"""

import os
import json
import requests
import urllib3
from urllib3.util.ssl_ import create_urllib3_context
from ai_config import AI_CONFIG

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 创建宽松的SSL上下文
try:
    CREATE_URLLIB3_CONTEXT = create_urllib3_context()
except:
    CREATE_URLLIB3_CONTEXT = None

# 获取代理配置
PROXY = os.environ.get('HTTP_PROXY') or os.environ.get('HTTPS_PROXY') or os.environ.get('http_proxy') or os.environ.get('https_proxy')
SESSION = requests.Session()

# 配置更宽松的SSL
try:
    import ssl
    SSL_CONTEXT = ssl.create_default_context()
    SSL_CONTEXT.check_hostname = False
    SSL_CONTEXT.verify_mode = ssl.CERT_NONE
    SESSION.mount('https://', requests.adapters.HTTPAdapter(ssl_context=SSL_CONTEXT))
except:
    pass

if PROXY:
    SESSION.proxies = {'http': PROXY, 'https': PROXY}


def get_ai_summary(news_list, max_news=5):
    """
    获取AI生成的新闻摘要
    根据配置自动调用对应的AI服务

    Args:
        news_list: 新闻列表
        max_news: 最多处理的新闻数量

    Returns:
        tuple: (AI返回的内容, 使用的模型名称)，失败时返回(None, None)
    """
    provider = AI_CONFIG.get('provider', 'custom')

    # 构建新闻内容
    news_content = build_news_content(news_list, max_news)

    # 根据provider调用对应的AI服务
    result = None
    if provider == 'anthropic':
        result = call_anthropic(news_content)
    elif provider == 'custom':
        result = call_custom_api(news_content)
    else:
        print(f"⚠️ 未知的AI provider: {provider}")

    # 返回结果和模型名称
    model_name = get_model_name() if result else None
    return result, model_name


def get_model_name():
    """获取当前配置的模型名称"""
    provider = AI_CONFIG.get('provider', 'custom')
    config = AI_CONFIG.get(provider, {})

    model_names = {
        'anthropic': 'Claude',
        'custom': 'Custom'
    }

    model = config.get('model', '')
    prefix = model_names.get(provider, 'AI')

    if model:
        return f"{prefix} ({model})"
    return prefix


def build_news_content(news_list, max_news=5):
    """构建发送给AI的新闻内容，要求返回JSON格式"""
    content = """请为每条ESG新闻翻译标题为中文，要求：

【标题风格 - 章回体】
- 不超过15字
- 突出冲击/影响
- 使用比喻修辞
- 如：野火焚林碳汇梦断加州

【摘要】50-100字，精准提炼核心影响

返回JSON：[{"title":"标题","summary":"摘要"}]

新闻：
"""
    for i, news in enumerate(news_list[:max_news], 1):
        summary = news.get('summary', '')[:100]  # 截断摘要到100字
        content += f"{i}. {news.get('title', '')}\n"
        content += f"   {summary}\n\n"
    return content


# ===== Anthropic Claude =====

def call_anthropic(content):
    """调用 Anthropic Claude API (使用requests直接调用，支持自定义端点如LongCat)"""
    config = AI_CONFIG.get('anthropic', {})
    api_key = config.get('api_key') or os.environ.get('ANTHROPIC_API_KEY')
    model = config.get('model', 'claude-3-haiku-20240307')
    api_base = config.get('api_base')  # 支持自定义端点

    if not api_key:
        print("⚠️ 未配置 Anthropic API Key")
        return None

    if not api_base:
        print("⚠️ 未配置 API 端点")
        return None

    # 使用 requests 直接调用 (LongCat 需要 Authorization: Bearer)
    url = f"{api_base.rstrip('/')}/v1/messages"

    try:
        response = SESSION.post(
            url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "max_tokens": 800,
                "system": "你是一个专业的ESG新闻分析师，请用中文生成详细、有洞察力的新闻摘要。",
                "messages": [{"role": "user", "content": content}]
            },
            timeout=60,
            verify=False
        )
        # 检查响应状态
        if response.status_code != 200:
            print(f"❌ Anthropic API 返回错误 ({response.status_code}): {response.text}")
            return None

        result = response.json()

        if 'content' in result and len(result['content']) > 0:
            return result['content'][0].get('text', '')
        else:
            print(f"❌ Anthropic API 返回异常: {result}")
            return None
    except Exception as e:
        print(f"❌ Anthropic API 调用失败: {e}")
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
        response = SESSION.post(
            url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Connection": "close"
            },
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": content}
                ],
                "max_tokens": 800,
                "temperature": 0.7
            },
            timeout=60,
            verify=False
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
