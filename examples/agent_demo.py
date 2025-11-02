"""
Agent使用示例脚本

这个脚本展示了如何使用不同类型的Agent：
1. SimpleAgent - 简单的工具调用Agent
2. ReactAgent - 推理和行动Agent

运行方式：
python examples/agent_demo.py
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agents import SimpleAgent, ReactAgent
from app.tools import AVAILABLE_TOOLS


async def demo_simple_agent():
    """演示SimpleAgent的使用"""
    print("=" * 50)
    print("SimpleAgent 演示")
    print("=" * 50)
    
    # 创建SimpleAgent
    agent = SimpleAgent(
        name="数学助手",
        description="专门处理数学计算和日期时间查询的助手"
    )
    
    # 添加工具
    agent.add_tools(AVAILABLE_TOOLS)
    
    # 显示Agent信息
    info = agent.get_info()
    print(f"Agent名称: {info['name']}")
    print(f"Agent描述: {info['description']}")
    print(f"可用工具: {', '.join(info['tools'])}")
    print()
    
    # 测试查询
    test_queries = [
        "计算 15 + 27 * 3",
        "现在是几点？",
        "今天是什么日期？",
        "计算 (10 + 5) / 3 的结果"
    ]
    
    for query in test_queries:
        print(f"用户查询: {query}")
        result = await agent.run(query)
        
        if result["success"]:
            print(f"Agent回答: {result['result']}")
            if result.get("tool_calls"):
                print(f"使用的工具: {[tc['name'] for tc in result['tool_calls']]}")
        else:
            print(f"错误: {result['error']}")
        print("-" * 30)


async def demo_react_agent():
    """演示ReactAgent的使用"""
    print("=" * 50)
    print("ReactAgent 演示")
    print("=" * 50)
    
    # 创建ReactAgent
    agent = ReactAgent(
        name="推理助手",
        description="能够进行复杂推理和多步骤问题解决的助手"
    )
    
    # 添加工具
    agent.add_tools(AVAILABLE_TOOLS)
    
    # 设置参数
    agent.set_max_iterations(3)
    agent.set_verbose(True)
    
    # 显示Agent信息
    info = agent.get_info()
    print(f"Agent名称: {info['name']}")
    print(f"Agent描述: {info['description']}")
    print(f"可用工具: {', '.join(info['tools'])}")
    print()
    
    # 测试复杂查询
    test_queries = [
        "先计算 20 + 15，然后告诉我现在的时间",
        "计算 (8 * 7) - 10，然后告诉我今天是星期几",
        "如果现在是下午，计算 100 / 4，否则计算 50 * 2"
    ]
    
    for query in test_queries:
        print(f"用户查询: {query}")
        result = await agent.run(query, verbose=True)
        
        if result["success"]:
            print(f"最终答案: {result['result']}")
            print(f"推理步骤数: {result['iterations']}")
            
            # 显示中间步骤
            if result.get("intermediate_steps"):
                print("推理过程:")
                for i, step in enumerate(result["intermediate_steps"], 1):
                    action, observation = step
                    print(f"  步骤{i}: {action.tool} -> {observation}")
        else:
            print(f"错误: {result['error']}")
        print("-" * 50)


async def interactive_demo():
    """交互式演示"""
    print("=" * 50)
    print("交互式Agent演示")
    print("=" * 50)
    print("选择Agent类型:")
    print("1. SimpleAgent (简单工具调用)")
    print("2. ReactAgent (推理和行动)")
    print("输入 'quit' 退出")
    print()
    
    while True:
        choice = input("请选择Agent类型 (1/2) 或输入 'quit': ").strip()
        
        if choice.lower() == 'quit':
            break
        
        if choice == '1':
            agent = SimpleAgent("交互助手", "交互式简单助手")
            agent_type = "SimpleAgent"
        elif choice == '2':
            agent = ReactAgent("交互推理助手", "交互式推理助手")
            agent_type = "ReactAgent"
        else:
            print("无效选择，请重新输入")
            continue
        
        # 添加工具
        agent.add_tools(AVAILABLE_TOOLS)
        
        print(f"\n已选择 {agent_type}")
        print("可用工具:", ", ".join([tool.name for tool in AVAILABLE_TOOLS]))
        print("输入 'back' 返回选择菜单\n")
        
        while True:
            query = input("请输入您的问题: ").strip()
            
            if query.lower() == 'back':
                break
            
            if not query:
                continue
            
            print("处理中...")
            result = await agent.run(query)
            
            if result["success"]:
                print(f"回答: {result['result']}")
                
                if agent_type == "ReactAgent" and result.get("intermediate_steps"):
                    print(f"推理步骤: {result['iterations']}步")
            else:
                print(f"错误: {result['error']}")
            print()


async def main():
    """主函数"""
    print("Agent演示程序")
    print("这个程序展示了不同类型Agent的使用方法")
    print()
    
    try:
        # 运行SimpleAgent演示
        await demo_simple_agent()
        
        # 等待用户确认
        input("\n按Enter键继续ReactAgent演示...")
        
        # 运行ReactAgent演示
        await demo_react_agent()
        
        # 等待用户确认
        choice = input("\n是否进入交互式演示？(y/n): ").strip().lower()
        if choice == 'y':
            await interactive_demo()
        
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"程序运行出错: {e}")
    
    print("演示结束")


if __name__ == "__main__":
    asyncio.run(main())