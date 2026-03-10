#!/usr/bin/env python3
"""
AI API 配置
只需在这里添加您的API配置即可使用不同的AI服务
"""

# ===== 选择您要使用的AI服务 =====
# 将下面的 provider 改为您想使用的服务商即可
# 可选: 'openai', 'anthropic', 'minimax', 'deepseek', 'longcat', 'custom'

AI_CONFIG = {
    'provider': 'longcat',  # 修改这里来切换AI服务商

    # OpenAI 配置 (如果您使用 OpenAI)
    'openai': {
        'api_key': '',  # 从环境变量 OPENAI_API_KEY 读取
        'model': 'gpt-3.5-turbo',
    },

    # Anthropic Claude 配置
    'anthropic': {
        'api_key': '',  # 从环境变量 ANTHROPIC_API_KEY 读取
        'model': 'claude-3-haiku-20240307',
    },

    # MiniMax 配置 (https://platform.minimaxi.com)
    'minimax': {
        'api_key': '',  # 从环境变量 MINIMAX_API_KEY 读取
        'model': 'abab6.5s-chat',
        'api_base': 'https://api.minimax.chat/v1',  # API地址
    },

    # DeepSeek 配置 (https://platform.deepseek.com)
    'deepseek': {
        'api_key': '',  # 从环境变量 DEEPSEEK_API_KEY 读取
        'model': 'deepseek-chat',
    },

    # LongCat 配置 (https://longcat.cn)
    'longcat': {
        'api_key': '',  # 从环境变量 LONGCAT_API_KEY 读取
        'model': 'longchat-lion-7b',  # 使用的模型
        'api_base': 'https://api.longcat.cn/v1',  # API地址
    },

    # 自定义 API 配置 (用于其他第三方API)
    # 您可以在这里添加任意API服务商
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
