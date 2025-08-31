from elasticsearch import Elasticsearch
import json
import os
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()

# 读取配置文件
def read_config():
    es_host = os.getenv("ES_HOST", "localhost")
    es_port = int(os.getenv("ES_PORT", "9200"))
    
    return es_host, es_port

# 创建ES客户端
def get_es_client():
    es_host, es_port = read_config()
    # 使用兼容Elasticsearch 7.17.0的连接方式
    es = Elasticsearch([f"http://{es_host}:{es_port}"])
    return es

# 创建会话索引
def create_conversation_index(es_client: Elasticsearch):
    # 检查索引是否存在
    if es_client.indices.exists(index="conversation_contents"):
        print("会话索引已存在")
        return
    
    # 创建索引映射
    mapping = {
        "mappings": {
            "properties": {
                # 基础信息字段
                "conversation_id": {"type": "keyword"},
                "customer_id": {"type": "keyword"},
                "customer_name": {"type": "keyword"},
                "advisor_id": {"type": "keyword"},
                "advisor_name": {"type": "keyword"},
                "conversation_time": {"type": "date"},
                
                # 会话内容字段
                "full_content": {
                    "type": "text",
                    "analyzer": "standard",
                    "search_analyzer": "standard",
                    "fields": {
                        "keyword": {"type": "keyword", "ignore_above": 256}
                    }
                },
                
                # 会话消息数组
                "messages": {
                    "type": "nested",
                    "properties": {
                        "sender_type": {"type": "keyword"},
                        "sender_id": {"type": "keyword"},
                        "sender_name": {"type": "keyword"},
                        "content": {
                            "type": "text",
                            "analyzer": "standard",
                            "search_analyzer": "standard",
                            "fields": {
                                "keyword": {"type": "keyword", "ignore_above": 256}
                            }
                        },
                        "send_time": {"type": "date"},
                        "message_type": {"type": "keyword"}
                    }
                },
                
                # 会话摘要
                "summary": {
                    "type": "text",
                    "analyzer": "standard",
                    "search_analyzer": "standard"
                },
                
                # 会话内容向量（用于语义搜索）
                "content_vector": {
                    "type": "dense_vector",
                    "dims": 1024
                },
                
                # 自动提取的实体和关键词
                "extracted_entities": {
                    "type": "nested",
                    "properties": {
                        "entity_type": {"type": "keyword"},
                        "entity_value": {"type": "keyword"},
                        "confidence": {"type": "float"},
                        "positions": {
                            "type": "nested",
                            "properties": {
                                "message_index": {"type": "integer"},
                                "start_pos": {"type": "integer"},
                                "end_pos": {"type": "integer"}
                            }
                        }
                    }
                },
                
                # 情感分析结果
                "sentiment": {
                    "type": "nested",
                    "properties": {
                        "message_index": {"type": "integer"},
                        "sentiment_type": {"type": "keyword"},
                        "sentiment_score": {"type": "float"}
                    }
                },
                
                # 提及的产品
                "mentioned_products": {"type": "keyword"},
                
                # 提及的行业
                "mentioned_industries": {"type": "keyword"},
                
                # 提及的话题
                "mentioned_topics": {"type": "keyword"},
                
                # 提及的问题/抱怨
                "mentioned_complaints": {"type": "keyword"},
                
                # 会话标签（可由大模型自动生成或人工标注）
                "conversation_tags": {"type": "keyword"}
            }
        },
        "settings": {
            "number_of_shards": 3,
            "number_of_replicas": 1,
            "analysis": {
                "analyzer": {
                    "text_analyzer": {
                        "type": "custom",
                        "tokenizer": "standard",
                        "filter": ["lowercase", "asciifolding"]
                    }
                }
            }
        }
    }
    
    # 创建索引
    es_client.indices.create(index="conversation_contents", **mapping)
    print("会话索引创建成功")


# 索引会话数据
def index_conversation(es_client: Elasticsearch, conversation_data):
    try:
        # 索引文档
        es_client.index(
            index="conversation_contents",
            id=conversation_data["conversation_id"],
            document=conversation_data
        )
        return True
    except Exception as e:
        print(f"索引会话数据失败: {str(e)}")
        return False


# 批量索引会话数据
def bulk_index_conversations(es_client: Elasticsearch, conversations):
    try:
        bulk_data = []
        for conversation in conversations:
            # 添加索引操作
            bulk_data.append({
                "index": {
                    "_index": "conversation_contents",
                    "_id": conversation["conversation_id"]
                }
            })
            # 添加文档数据
            bulk_data.append(conversation)
        
        # 执行批量操作
        if bulk_data:
            print(f"准备上传 {len(conversations)} 个会话文档")
            response = es_client.bulk(body=bulk_data)
            print(f"批量操作响应: {response}")
            
            # 检查是否有错误
            if response.get('errors', False):
                print("批量操作中有错误:")
                for item in response.get('items', []):
                    if 'index' in item and 'error' in item['index']:
                        print(f"错误: {item['index']['error']}")
                return False
            else:
                print("所有文档上传成功")
        return True
    except Exception as e:
        print(f"批量索引会话数据失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False