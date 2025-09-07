#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DeepSeek 函数调用配置示例

使用说明：
1. 复制此文件为 config.py
2. 填入你的 DeepSeek API Key
3. 根据需要调整其他配置
"""

# DeepSeek API 配置
DEEPSEEK_CONFIG = {
    # 你的 DeepSeek API Key
    # 获取地址: https://platform.deepseek.com/api_keys
    "api_key": "your_deepseek_api_key_here",
    
    # API 基础URL（通常不需要修改）
    "api_base": "https://api.deepseek.com/v1",
    
    # 使用的模型
    "model": "deepseek-chat",
    
    # 请求超时时间（秒）
    "timeout": 30,
    
    # 温度参数（0-1，越低越确定）
    "temperature": 0.1,
    
    # 最大token数
    "max_tokens": 1000
}

# 环境变量设置说明
"""
你也可以通过环境变量设置 API Key：

在 macOS/Linux 中：
export DEEPSEEK_API_KEY="your_api_key_here"

在 Windows 中：
set DEEPSEEK_API_KEY=your_api_key_here

或者在 .env 文件中：
DEEPSEEK_API_KEY=your_api_key_here
"""

# 日志配置
LOGGING_CONFIG = {
    "level": "INFO",  # DEBUG, INFO, WARNING, ERROR
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": "deepseek_function_calling.log"  # 设置为 None 则不写入文件
}

# 函数执行配置
FUNCTION_CONFIG = {
    # 是否启用函数执行（False时只进行分析不执行）
    "enable_execution": True,
    
    # 是否显示详细日志
    "verbose": True,
    
    # 是否保存执行历史
    "save_history": True,
    
    # 历史文件路径
    "history_file": "function_call_history.json"
}