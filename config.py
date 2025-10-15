#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
配置文件
"""

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# LLM 提供商配置 (qianfan 或 deepseek)
LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'qianfan')

# 千帆API配置
QIANFAN_ACCESS_KEY = os.getenv('QIANFAN_ACCESS_KEY', '')
QIANFAN_SECRET_KEY = os.getenv('QIANFAN_SECRET_KEY', '')

# DeepSeek API配置
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', '')
DEEPSEEK_BASE_URL = os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')
DEEPSEEK_MODEL = os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')

# 服务配置
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 8000))

# 模型配置
DEFAULT_MODEL = os.getenv('DEFAULT_MODEL', 'ERNIE-4.0-8K')

# 日志配置
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

