#!/usr/bin/env python3
"""
AI API 配置（密钥只从环境变量读取，不要写进仓库）
"""

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / '.env')
except ImportError:
    pass

AI_CONFIG = {
    'provider': os.getenv('AI_PROVIDER', 'anthropic'),

    # LongCat 兼容 Anthropic Messages API
    'anthropic': {
        'api_key': os.getenv('LONGCAT_API_KEY') or os.getenv('ANTHROPIC_API_KEY') or '',
        'model': os.getenv('AI_MODEL', 'LongCat-Flash-Chat'),
        'api_base': os.getenv('AI_API_BASE', 'https://api.longcat.chat/anthropic'),
    },

    'custom': {
        'api_key': os.getenv('CUSTOM_API_KEY', ''),
        'api_base': os.getenv('CUSTOM_API_BASE', ''),
        'model': os.getenv('CUSTOM_MODEL', ''),
        'system_prompt': '你是一个专业的ESG新闻分析师，请用中文生成详细、有洞察力的新闻摘要。',
    },
}
