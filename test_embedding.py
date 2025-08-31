#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试通义千问嵌入模型的脚本
用于排查向量生成失败的问题
"""

import os
import asyncio
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from pydantic import SecretStr

# 加载.env文件
load_dotenv()

def test_embedding():
    """测试嵌入模型"""
    # 从环境变量获取API密钥
    qwen_key = os.getenv('DASHSCOPE_API_KEY')
    if not qwen_key:
        print("错误: 请设置DASHSCOPE_API_KEY环境变量")
        return
    
    print(f"使用API密钥: {qwen_key[:10]}...")
    
    # 创建嵌入模型
    embedding_model = OpenAIEmbeddings(
        model="text-embedding-v4",
        api_key=SecretStr(qwen_key),
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
    )
    
    # 测试文本
    test_text = "这是一个测试文本，用于生成向量嵌入。"
    
    try:
        print("开始生成向量...")
        print(f"测试文本: {test_text}")
        
        # 尝试生成向量
        vector = embedding_model.embed_query(test_text)
        
        print(f"向量生成成功!")
        print(f"向量维度: {len(vector)}")
        print(f"向量前5个值: {vector[:5]}")
        
    except Exception as e:
        print(f"向量生成失败: {str(e)}")
        print(f"错误类型: {type(e).__name__}")
        
        # 打印详细的错误信息
        import traceback
        print("\n详细错误信息:")
        traceback.print_exc()

async def test_async_embedding():
    """测试异步嵌入模型"""
    # 从环境变量获取API密钥
    qwen_key = os.getenv('DASHSCOPE_API_KEY')
    if not qwen_key:
        print("错误: 请设置DASHSCOPE_API_KEY环境变量")
        return
    
    print(f"\n=== 异步测试 ===")
    print(f"使用API密钥: {qwen_key[:10]}...")
    
    # 创建嵌入模型
    embedding_model = OpenAIEmbeddings(
        model="text-embedding-v4",
        api_key=SecretStr(qwen_key),
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
    )
    
    # 测试文本
    test_text = "这是一个异步测试文本，用于生成向量嵌入。"
    
    try:
        print("开始异步生成向量...")
        print(f"测试文本: {test_text}")
        
        # 尝试异步生成向量
        vector = await embedding_model.aembed_query(test_text)
        
        print(f"异步向量生成成功!")
        print(f"向量维度: {len(vector)}")
        print(f"向量前5个值: {vector[:5]}")
        
    except Exception as e:
        print(f"异步向量生成失败: {str(e)}")
        print(f"错误类型: {type(e).__name__}")
        
        # 打印详细的错误信息
        import traceback
        print("\n详细错误信息:")
        traceback.print_exc()

if __name__ == "__main__":
    print("=== 通义千问嵌入模型测试 ===")
    
    # 同步测试
    test_embedding()
    
    # 异步测试
    asyncio.run(test_async_embedding())