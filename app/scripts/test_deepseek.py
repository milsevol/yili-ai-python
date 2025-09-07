#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DeepSeek 函数调用测试脚本

使用方法：
1. 设置环境变量 DEEPSEEK_API_KEY
2. 运行: python test_deepseek.py
"""

import os
import sys
from deepseek_function_calling import DeepSeekFunctionCallHandler


def test_basic_functionality():
    """测试基本功能"""
    print("=" * 60)
    print("DeepSeek 函数调用基本功能测试")
    print("=" * 60)
    
    # 检查API Key
    api_key = os.getenv('DEEPSEEK_API_KEY')
    if not api_key:
        print("⚠️  警告: 未设置 DEEPSEEK_API_KEY 环境变量")
        print("将使用备用的关键词匹配模式进行测试")
        print("\n要使用完整功能，请设置环境变量:")
        print("export DEEPSEEK_API_KEY='your_api_key_here'")
        print()
    else:
        print(f"✅ 已检测到 API Key: {api_key[:10]}...")
    
    # 初始化处理器
    handler = DeepSeekFunctionCallHandler()
    
    # 测试用例
    test_cases = [
        {
            "input": "北京今天天气怎么样？",
            "expected_function": "get_weather",
            "description": "天气查询测试"
        },
        {
            "input": "计算 100 + 200 * 3",
            "expected_function": "calculate_math",
            "description": "数学计算测试"
        },
        {
            "input": "搜索Python教程",
            "expected_function": "search_information",
            "description": "信息搜索测试"
        },
        {
            "input": "把Hello翻译成中文",
            "expected_function": "translate_text",
            "description": "文本翻译测试"
        },
        {
            "input": "提醒我明天9点开会",
            "expected_function": "set_reminder",
            "description": "设置提醒测试"
        }
    ]
    
    success_count = 0
    total_count = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n[测试 {i}/{total_count}] {test_case['description']}")
        print(f"输入: {test_case['input']}")
        
        try:
            result = handler.process_user_input(test_case['input'])
            
            if result["success"]:
                selected_function = result["selected_function"]
                expected_function = test_case["expected_function"]
                
                if selected_function == expected_function:
                    print(f"✅ 测试通过 - 正确识别为: {selected_function}")
                    success_count += 1
                else:
                    print(f"⚠️  函数识别不准确 - 期望: {expected_function}, 实际: {selected_function}")
                
                # 显示执行结果
                if result["execution_result"]["success"]:
                    print(f"📋 执行结果: {result['execution_result']['result']}")
                else:
                    print(f"❌ 执行失败: {result['execution_result']['error']}")
            else:
                print(f"❌ 测试失败: {result['error']}")
                
        except Exception as e:
            print(f"❌ 测试异常: {str(e)}")
        
        print("-" * 50)
    
    # 测试总结
    print(f"\n测试总结: {success_count}/{total_count} 通过")
    success_rate = (success_count / total_count) * 100
    print(f"成功率: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print("🎉 测试结果良好！")
    elif success_rate >= 60:
        print("⚠️  测试结果一般，建议检查配置")
    else:
        print("❌ 测试结果较差，请检查API配置")


def test_interactive_mode():
    """测试交互模式"""
    print("\n" + "=" * 60)
    print("交互模式测试 (输入 'quit' 退出)")
    print("=" * 60)
    
    handler = DeepSeekFunctionCallHandler()
    
    while True:
        try:
            user_input = input("\n请输入测试内容: ").strip()
            if user_input.lower() in ['quit', 'exit', '退出', 'q']:
                print("测试结束！")
                break
            
            if not user_input:
                continue
            
            result = handler.process_user_input(user_input)
            
            if result["success"]:
                if result["execution_result"]["success"]:
                    print(f"\n✅ {result['execution_result']['result']}")
                else:
                    print(f"\n❌ {result['execution_result']['error']}")
            else:
                print(f"\n❌ {result['error']}")
                
        except KeyboardInterrupt:
            print("\n\n测试中断！")
            break
        except Exception as e:
            print(f"\n发生错误: {e}")


def main():
    """主函数"""
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        test_interactive_mode()
    else:
        test_basic_functionality()
        
        # 询问是否进入交互模式
        try:
            choice = input("\n是否进入交互模式测试？(y/n): ").strip().lower()
            if choice in ['y', 'yes', '是', '好']:
                test_interactive_mode()
        except KeyboardInterrupt:
            print("\n再见！")


if __name__ == "__main__":
    main()