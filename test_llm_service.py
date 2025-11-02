#!/usr/bin/env python3
"""
LLM服务测试脚本

使用示例：
python test_llm_service.py
"""

import asyncio
import os
from app.services.llm_service import get_llm_service, invoke_llm


async def test_basic_functionality():
    """测试基本功能"""
    print("=== LLM服务基础功能测试 ===\n")
    
    try:
        # 测试服务初始化
        print("1. 初始化LLM服务...")
        service = get_llm_service()
        print("✓ LLM服务初始化成功")
        
        # 测试配置读取
        print(f"✓ 配置读取成功 - Temperature: {service.config.temperature}")
        
        # 测试简单对话（需要有效的API密钥）
        if service.config.deepseek_api_key and service.config.deepseek_api_key != "your-deepseek-api-key":
            print("\n2. 测试聊天功能...")
            response = await invoke_llm("你好，请简单介绍一下你自己")
            print(f"✓ 聊天测试成功")
            print(f"回复: {response[:100]}...")
        else:
            print("\n2. 跳过聊天测试（需要配置有效的API密钥）")
        
        # 测试嵌入功能（需要有效的API密钥）
        if service.config.qwen_api_key and service.config.qwen_api_key != "your-qwen-api-key":
            print("\n3. 测试嵌入功能...")
            embedding = await service.generate_embedding("测试文本")
            print(f"✓ 嵌入测试成功 - 向量维度: {len(embedding)}")
        else:
            print("\n3. 跳过嵌入测试（需要配置有效的API密钥）")
            
        print("\n=== 所有测试完成 ===")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


def test_configuration():
    """测试配置功能"""
    print("=== 配置测试 ===\n")
    
    # 显示当前环境变量配置
    env_vars = [
        'DEEPSEEK_API_KEY',
        'QWEN_API_KEY', 
        'LLM_TEMPERATURE',
        'LLM_MAX_TOKENS',
        'LLM_TIMEOUT'
    ]
    
    print("当前环境变量配置:")
    for var in env_vars:
        value = os.getenv(var, "未设置")
        if 'API_KEY' in var and value != "未设置":
            # 隐藏API密钥的大部分内容
            value = value[:8] + "..." + value[-4:] if len(value) > 12 else "***"
        print(f"  {var}: {value}")
    
    print("\n配置说明:")
    print("- DEEPSEEK_API_KEY: DeepSeek API密钥（必需）")
    print("- QWEN_API_KEY: 通义千问API密钥（可选，默认使用DeepSeek密钥）")
    print("- LLM_TEMPERATURE: 模型温度参数（默认: 0.0）")
    print("- LLM_MAX_TOKENS: 最大输出token数（可选）")
    print("- LLM_TIMEOUT: 请求超时时间（默认: 30秒）")


if __name__ == "__main__":
    print("LLM服务测试工具\n")
    
    # 测试配置
    test_configuration()
    print("\n" + "="*50 + "\n")
    
    # 测试基础功能
    asyncio.run(test_basic_functionality())