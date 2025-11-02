"""
天气Agent使用示例
演示如何使用WeatherAgent进行各种天气查询
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agents.weather_agent import WeatherAgent, create_weather_agent


async def demo_basic_weather_query():
    """演示基本天气查询"""
    print("🌤️ === 基本天气查询演示 ===")
    
    # 创建天气Agent
    weather_agent = create_weather_agent()
    
    # 查询北京天气
    print("\n📍 查询北京当前天气:")
    result = await weather_agent.get_weather("北京")
    print(f"✅ 查询结果: {result['result']}")
    print(f"🔄 执行步骤数: {result.get('iterations', 0)}")
    
    print("\n" + "="*50)


async def demo_weather_forecast():
    """演示天气预报查询"""
    print("🌦️ === 天气预报查询演示 ===")
    
    weather_agent = create_weather_agent()
    
    # 查询上海天气预报
    print("\n📍 查询上海未来3天天气预报:")
    result = await weather_agent.get_weather_with_forecast("上海", 3)
    print(f"✅ 预报结果: {result['result']}")
    
    print("\n" + "="*50)


async def demo_weather_advice():
    """演示天气建议查询"""
    print("💡 === 天气建议查询演示 ===")
    
    weather_agent = create_weather_agent()
    
    # 查询广州天气和建议
    print("\n📍 查询广州天气和生活建议:")
    result = await weather_agent.get_weather_advice("广州")
    print(f"✅ 建议结果: {result['result']}")
    
    print("\n" + "="*50)


async def demo_custom_queries():
    """演示自定义天气查询"""
    print("🎯 === 自定义天气查询演示 ===")
    
    weather_agent = create_weather_agent()
    
    # 自定义查询示例
    queries = [
        "深圳明天会下雨吗？",
        "杭州这周的天气适合户外运动吗？",
        "成都今天的空气质量怎么样？",
        "比较一下北京和上海今天的天气"
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n🔍 查询 {i}: {query}")
        result = await weather_agent.run(query)
        print(f"✅ 回答: {result['result']}")
        print(f"🔄 执行步骤: {result.get('iterations', 0)}")
        
        if i < len(queries):
            print("-" * 30)
    
    print("\n" + "="*50)


async def demo_agent_info():
    """演示Agent信息查询"""
    print("ℹ️ === Agent信息演示 ===")
    
    weather_agent = create_weather_agent()
    
    # 获取Agent信息
    info = weather_agent.get_info()
    print(f"\n📋 Agent名称: {info['name']}")
    print(f"📝 Agent描述: {info['description']}")
    print(f"🛠️ 可用工具数量: {len(info['tools'])}")
    print(f"🏙️ 支持城市: {', '.join(info['supported_cities'])}")
    print(f"⚡ 核心能力:")
    for capability in info['capabilities']:
        print(f"   • {capability}")
    
    print(f"\n💬 使用示例:")
    for example in info['usage_examples']:
        print(f"   • {example}")
    
    print("\n" + "="*50)


async def interactive_weather_demo():
    """交互式天气查询演示"""
    print("🎮 === 交互式天气查询 ===")
    print("输入天气相关问题，输入 'quit' 退出")
    
    weather_agent = create_weather_agent()
    
    while True:
        try:
            query = input("\n🤔 请输入您的天气问题: ").strip()
            
            if query.lower() in ['quit', 'exit', '退出', 'q']:
                print("👋 再见！")
                break
            
            if not query:
                print("❌ 请输入有效的问题")
                continue
            
            print("🔄 正在查询天气信息...")
            result = await weather_agent.run(query)
            
            if result['success']:
                print(f"✅ {result['result']}")
                print(f"📊 执行了 {result.get('iterations', 0)} 个步骤")
            else:
                print(f"❌ 查询失败: {result.get('error', '未知错误')}")
                
        except KeyboardInterrupt:
            print("\n👋 程序被中断，再见！")
            break
        except Exception as e:
            print(f"❌ 发生错误: {str(e)}")


async def main():
    """主函数 - 运行所有演示"""
    print("🌈 欢迎使用天气Agent演示程序！")
    print("=" * 60)
    
    try:
        # 运行各种演示
        await demo_basic_weather_query()
        await demo_weather_forecast()
        await demo_weather_advice()
        await demo_custom_queries()
        await demo_agent_info()
        
        # 询问是否进入交互模式
        print("\n🎮 是否要进入交互式查询模式？(y/n): ", end="")
        choice = input().strip().lower()
        
        if choice in ['y', 'yes', '是', 'Y']:
            await interactive_weather_demo()
        
    except Exception as e:
        print(f"❌ 演示过程中发生错误: {str(e)}")
    
    print("\n🎉 天气Agent演示完成！")


if __name__ == "__main__":
    # 运行演示
    asyncio.run(main())