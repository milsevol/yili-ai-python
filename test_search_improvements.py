#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试向量搜索改进效果的脚本
用于验证查询预处理、同义词扩展和搜索参数优化的效果
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.services.langchain_service import (
    get_langchain_client,
    preprocess_query_text,
    llm_preprocess_query,
    generate_query_vector_with_preprocessing
)

async def test_query_preprocessing():
    """
    测试查询预处理功能
    """
    print("=== 测试查询预处理功能 ===")
    
    # 测试查询
    test_queries = [
        "想投资美股的有自己公司的客户",
        "高净值客户咨询理财产品",
        "企业主想要资产配置",
        "公司老板询问基金投资",
        "创业者需要风险管理"
    ]
    
    for query in test_queries:
        print(f"\n原始查询: {query}")
        
        # 基础预处理
        basic_processed = preprocess_query_text(query)
        print(f"基础预处理: {basic_processed}")
        
        # 大模型预处理
        try:
            langchain_client = get_langchain_client()
            chat_model = langchain_client["chat_model"]
            
            llm_processed = await llm_preprocess_query(chat_model, query)
            print(f"大模型预处理: {llm_processed}")
            
        except Exception as e:
            print(f"大模型预处理失败: {str(e)}")
        
        print("-" * 80)

async def test_vector_generation():
    """
    测试向量生成功能
    """
    print("\n=== 测试向量生成功能 ===")
    
    test_query = "想投资美股的有自己公司的客户"
    print(f"测试查询: {test_query}")
    
    try:
        langchain_client = get_langchain_client()
        
        # 生成查询向量（包含预处理）
        vector_result = await generate_query_vector_with_preprocessing(
            langchain_client, test_query
        )
        
        if vector_result and len(vector_result) == 2:
            query_vector, processed_query = vector_result
            
            print(f"处理后的查询: {processed_query}")
            print(f"向量维度: {len(query_vector) if query_vector else 0}")
            print(f"向量前5个值: {query_vector[:5] if query_vector else 'None'}")
        else:
            print("向量生成失败")
            
    except Exception as e:
        print(f"向量生成测试失败: {str(e)}")

def test_synonym_expansion():
    """
    测试同义词扩展功能
    """
    print("\n=== 测试同义词扩展功能 ===")
    
    test_cases = [
        ("公司", ["企业", "机构", "公司老板", "企业主", "创业者"]),
        ("投资", ["理财", "资产配置", "财富管理", "投资理财"]),
        ("美股", ["美国股票", "海外投资", "境外投资", "国际投资"]),
        ("高净值", ["富裕", "资金充裕", "有钱", "财富", "资产丰厚"])
    ]
    
    for keyword, expected_synonyms in test_cases:
        processed = preprocess_query_text(keyword)
        print(f"关键词: {keyword}")
        print(f"扩展结果: {processed}")
        
        # 检查是否包含预期的同义词
        found_synonyms = []
        for synonym in expected_synonyms:
            if synonym in processed:
                found_synonyms.append(synonym)
        
        print(f"找到的同义词: {found_synonyms}")
        print(f"覆盖率: {len(found_synonyms)}/{len(expected_synonyms)} ({len(found_synonyms)/len(expected_synonyms)*100:.1f}%)")
        print("-" * 60)

async def main():
    """
    主测试函数
    """
    print("开始测试向量搜索改进效果...\n")
    
    # 测试同义词扩展
    test_synonym_expansion()
    
    # 测试查询预处理
    await test_query_preprocessing()
    
    # 测试向量生成
    await test_vector_generation()
    
    print("\n=== 测试完成 ===")
    print("\n改进总结:")
    print("1. ✅ 扩展了同义词映射表，增加了客户特征、投资类型等领域词汇")
    print("2. ✅ 优化了大模型预处理提示词，增强了实体识别能力")
    print("3. ✅ 调整了向量搜索参数，提高了召回率")
    print("4. ✅ 降低了相似度阈值，使用动态阈值策略")
    print("5. ✅ 增强了实体提取功能，支持多维度匹配")
    
    print("\n建议:")
    print("- 在生产环境中测试这些改进")
    print("- 收集用户反馈，进一步调优参数")
    print("- 考虑添加更多领域特定的同义词")
    print("- 监控搜索性能和准确性指标")

if __name__ == "__main__":
    asyncio.run(main())