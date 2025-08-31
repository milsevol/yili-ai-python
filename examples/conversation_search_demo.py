import sys
import os
import json
import asyncio
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.es_service import get_es_client, create_conversation_index, index_conversation
from app.services.langchain_service import get_langchain_client, process_conversation, convert_nl_to_es_query


# 示例会话数据
def create_sample_conversation(conversation_id, customer_id, advisor_id, days_ago=0):
    """创建示例会话数据"""
    conversation_time = datetime.now() - timedelta(days=days_ago)
    
    return {
        "conversation_id": conversation_id,
        "customer_id": customer_id,
        "customer_name": f"客户{customer_id}",
        "advisor_id": advisor_id,
        "advisor_name": f"顾问{advisor_id}",
        "conversation_time": conversation_time.isoformat(),
        "full_content": f"顾问{advisor_id}: 您好，有什么可以帮助您的吗？\n客户{customer_id}: 我想了解一下最近的基金产品，特别是科技类的。\n顾问{advisor_id}: 我们有几款科技主题基金，包括科技创新混合型基金和科技龙头指数基金，您对哪种更感兴趣？\n客户{customer_id}: 科技创新混合型基金听起来不错，能详细介绍一下吗？\n顾问{advisor_id}: 这款基金主要投资于科技创新领域的上市公司，包括人工智能、半导体、新能源等赛道，过去一年收益率约15%，但风险等级为R4，属于中高风险产品。\n客户{customer_id}: 风险有点高，有没有风险低一点的产品？\n顾问{advisor_id}: 您可以考虑我们的稳健理财产品，风险等级R2，预期年化收益3.5%左右。\n客户{customer_id}: 这个收益太低了，有没有风险适中但收益稍高的产品？\n顾问{advisor_id}: 那您可以考虑我们的固收+产品，风险等级R3，预期年化收益5%左右，投资于债券为主，少量股票提升收益。\n客户{customer_id}: 这个听起来不错，我考虑一下，谢谢。",
        "messages": [
            {
                "sender_type": "advisor",
                "sender_id": advisor_id,
                "sender_name": f"顾问{advisor_id}",
                "content": "您好，有什么可以帮助您的吗？",
                "send_time": (conversation_time - timedelta(minutes=30)).isoformat(),
                "message_type": "text"
            },
            {
                "sender_type": "customer",
                "sender_id": customer_id,
                "sender_name": f"客户{customer_id}",
                "content": "我想了解一下最近的基金产品，特别是科技类的。",
                "send_time": (conversation_time - timedelta(minutes=29)).isoformat(),
                "message_type": "text"
            },
            {
                "sender_type": "advisor",
                "sender_id": advisor_id,
                "sender_name": f"顾问{advisor_id}",
                "content": "我们有几款科技主题基金，包括科技创新混合型基金和科技龙头指数基金，您对哪种更感兴趣？",
                "send_time": (conversation_time - timedelta(minutes=28)).isoformat(),
                "message_type": "text"
            },
            {
                "sender_type": "customer",
                "sender_id": customer_id,
                "sender_name": f"客户{customer_id}",
                "content": "科技创新混合型基金听起来不错，能详细介绍一下吗？",
                "send_time": (conversation_time - timedelta(minutes=27)).isoformat(),
                "message_type": "text"
            },
            {
                "sender_type": "advisor",
                "sender_id": advisor_id,
                "sender_name": f"顾问{advisor_id}",
                "content": "这款基金主要投资于科技创新领域的上市公司，包括人工智能、半导体、新能源等赛道，过去一年收益率约15%，但风险等级为R4，属于中高风险产品。",
                "send_time": (conversation_time - timedelta(minutes=26)).isoformat(),
                "message_type": "text"
            },
            {
                "sender_type": "customer",
                "sender_id": customer_id,
                "sender_name": f"客户{customer_id}",
                "content": "风险有点高，有没有风险低一点的产品？",
                "send_time": (conversation_time - timedelta(minutes=25)).isoformat(),
                "message_type": "text"
            },
            {
                "sender_type": "advisor",
                "sender_id": advisor_id,
                "sender_name": f"顾问{advisor_id}",
                "content": "您可以考虑我们的稳健理财产品，风险等级R2，预期年化收益3.5%左右。",
                "send_time": (conversation_time - timedelta(minutes=24)).isoformat(),
                "message_type": "text"
            },
            {
                "sender_type": "customer",
                "sender_id": customer_id,
                "sender_name": f"客户{customer_id}",
                "content": "这个收益太低了，有没有风险适中但收益稍高的产品？",
                "send_time": (conversation_time - timedelta(minutes=23)).isoformat(),
                "message_type": "text"
            },
            {
                "sender_type": "advisor",
                "sender_id": advisor_id,
                "sender_name": f"顾问{advisor_id}",
                "content": "那您可以考虑我们的固收+产品，风险等级R3，预期年化收益5%左右，投资于债券为主，少量股票提升收益。",
                "send_time": (conversation_time - timedelta(minutes=22)).isoformat(),
                "message_type": "text"
            },
            {
                "sender_type": "customer",
                "sender_id": customer_id,
                "sender_name": f"客户{customer_id}",
                "content": "这个听起来不错，我考虑一下，谢谢。",
                "send_time": (conversation_time - timedelta(minutes=21)).isoformat(),
                "message_type": "text"
            }
        ]
    }


async def main():
    # 获取ES客户端
    es_client = get_es_client()
    
    # 获取LangChain客户端
    langchain_client = get_langchain_client()
    
    # 创建会话索引
    create_conversation_index(es_client)
    
    # 创建示例会话数据
    conversations = [
        create_sample_conversation("conv001", "cust001", "adv001", 5),
        create_sample_conversation("conv002", "cust002", "adv001", 3),
        create_sample_conversation("conv003", "cust003", "adv002", 2),
        create_sample_conversation("conv004", "cust004", "adv002", 1),
        create_sample_conversation("conv005", "cust005", "adv003", 0)
    ]
    
    # 处理会话数据并索引
    for conversation in conversations:
        # 使用LangChain处理会话数据
        processed_conversation = await process_conversation(langchain_client, conversation)
        
        # 索引处理后的会话数据
        index_conversation(es_client, processed_conversation)
        print(f"已索引会话: {conversation['conversation_id']}")
    
    # 等待索引刷新
    es_client.indices.refresh(index="conversation_contents")
    
    # 示例：自然语言搜索
    nl_query = "客户对哪些产品感兴趣？"
    print(f"\n执行自然语言搜索: '{nl_query}'")
    
    # 构建查询
    query_body = await convert_nl_to_es_query(langchain_client, nl_query)
    
    # 执行搜索
    search_result = es_client.search(
        index="conversation_contents",
        body=query_body
    )
    
    # 打印搜索结果
    print(f"找到 {search_result['hits']['total']['value']} 条匹配的会话")
    for hit in search_result["hits"]["hits"]:
        print(f"会话ID: {hit['_source']['conversation_id']}, 得分: {hit['_score']}")
        print(f"摘要: {hit['_source'].get('summary', '无摘要')}")
        if "highlight" in hit:
            print("高亮片段:")
            for field, fragments in hit["highlight"].items():
                for fragment in fragments:
                    print(f"  - {fragment}")
        print("---")
    
    # 示例：获取会话洞察
    print("\n获取会话洞察数据")
    
    # 构建聚合查询
    agg_query = {
        "size": 0,
        "aggs": {
            "top_products": {
                "terms": {
                    "field": "mentioned_products",
                    "size": 5
                }
            },
            "top_topics": {
                "terms": {
                    "field": "mentioned_topics",
                    "size": 5
                }
            }
        }
    }
    
    # 执行聚合查询
    agg_result = es_client.search(
        index="conversation_contents",
        body=agg_query
    )
    
    # 打印聚合结果
    print("热门产品:")
    for bucket in agg_result["aggregations"]["top_products"]["buckets"]:
        print(f"  - {bucket['key']}: {bucket['doc_count']}次提及")
    
    print("热门话题:")
    for bucket in agg_result["aggregations"]["top_topics"]["buckets"]:
        print(f"  - {bucket['key']}: {bucket['doc_count']}次提及")


# 此函数已移至langchain_service.py
# 在这里不需要重复实现


if __name__ == "__main__":
    asyncio.run(main())