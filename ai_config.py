#!/usr/bin/env python3
"""
AI API 配置
只需在这里添加您的API配置即可使用不同的AI服务
"""

# ===== 选择您要使用的AI服务 =====
# 将下面的 provider 改为您想使用的服务商即可
# 可选: 'anthropic', 'custom'

AI_CONFIG = {
    'provider': 'anthropic',  # 修改这里来切换AI服务商

    # Anthropic Claude 配置 (使用LongCat兼容API)
    'anthropic': {
        'api_key': 'ak_2yX14a1eC3Ib9Ye4Qr3aK9Gz39m8e',  # LongCat API Key
        'model': 'LongCat-Flash-Chat',
        'api_base': 'https://api.longcat.chat/anthropic',  # LongCat兼容端点
    },

    # 自定义 API 配置 (用于其他第三方API)
    'custom': {
        'api_key': '',  # 从环境变量 CUSTOM_API_KEY 读取
        'api_base': '',  # API地址，如 https://api.example.com/v1
        'model': '',    # 使用的模型名称
        'system_prompt': '你是一个专业的ESG新闻分析师，请用中文生成详细、有洞察力的新闻摘要。',
    },
}


# ===== 添加新的AI服务商 =====
# 只需在 AI_CONFIG 中添加新的配置项，然后在 ai_providers.py 中添加对应的调用函数
# 详细说明请参考 ai_providers.py
