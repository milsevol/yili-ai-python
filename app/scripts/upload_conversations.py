import os
import json
import re
from datetime import datetime
import asyncio
from pathlib import Path
import sys
from typing import List, Dict, Any

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.services.es_service import get_es_client, bulk_index_conversations
from app.services.langchain_service import get_langchain_client, generate_conversation_summary, extract_conversation_entities


async def process_conversation_file(file_path):
    """
    处理单个会话文件并转换为ES索引格式
    """
    # 从文件名中提取会话ID、顾问ID和客户ID
    file_name = os.path.basename(file_path)
    match = re.match(r'(\d{8})-(FA\d+)-(CL\d+)\.txt', file_name)
    
    if not match:
        print(f"文件名格式不正确: {file_name}")
        return None
    
    date_str, advisor_id, customer_id = match.groups()
    conversation_id = f"{date_str}-{advisor_id}-{customer_id}"
    
    # 解析日期
    try:
        conversation_date = datetime.strptime(date_str, "%Y%m%d").isoformat()
    except ValueError:
        print(f"日期格式不正确: {date_str}")
        conversation_date = datetime.now().isoformat()
    
    # 读取会话内容
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"读取文件失败: {file_path}, 错误: {str(e)}")
        return None
    
    # 解析会话消息
    messages = []
    full_content = ""
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # 解析发送者和内容
        if line.startswith("顾问："):
            sender_type = "advisor"
            sender_id = advisor_id
            sender_name = f"顾问{advisor_id}"
            content = line[3:]
        elif line.startswith("客户："):
            sender_type = "customer"
            sender_id = customer_id
            sender_name = f"客户{customer_id}"
            content = line[3:]
        else:
            # 如果没有明确的前缀，假设是上一条消息的延续
            if messages:
                messages[-1]["content"] += "\n" + line
                full_content += "\n" + line
            continue
        
        # 创建消息对象
        message = {
            "sender_type": sender_type,
            "sender_id": sender_id,
            "sender_name": sender_name,
            "content": content,
            "send_time": conversation_date,  # 这里简化处理，使用同一个日期
            "message_type": "text"
        }
        
        messages.append(message)
        full_content += ("\n" if full_content else "") + f"{sender_name}: {content}"
    
    # 使用LangChain生成会话摘要和提取实体
    langchain_client = get_langchain_client()
    
    # 创建临时会话对象用于摘要生成和实体提取
    temp_conversation = {
        "conversation_id": conversation_id,
        "full_content": full_content,
        "messages": messages
    }
    
    # 生成会话摘要
    summary = await generate_conversation_summary(langchain_client, temp_conversation)
    
    # 使用LangChain提取实体，增强关键词提取准确性
    try:
        entities_data = await extract_conversation_entities(langchain_client, temp_conversation)
        # 直接使用返回的字典
        mentioned_products = entities_data.get("mentioned_products", [])
        mentioned_industries = entities_data.get("mentioned_industries", [])
        mentioned_topics = entities_data.get("mentioned_topics", [])
        mentioned_complaints = entities_data.get("mentioned_complaints", [])
        sentiment_analysis = entities_data.get("sentiment", "neutral")
    except Exception as e:
        print(f"提取会话实体失败: {str(e)}")
        # 回退到简单的关键词提取
        mentioned_products = extract_keywords(full_content, ["基金", "股票", "债券", "理财产品", "保险"])
        mentioned_industries = extract_keywords(full_content, ["金融", "科技", "医疗", "教育", "房地产"])
        mentioned_topics = extract_keywords(full_content, ["投资", "理财", "风险", "收益", "市场"])
        mentioned_complaints = extract_keywords(full_content, ["不满", "问题", "投诉", "差", "失望"])
        sentiment_analysis = "neutral"
        
    # 生成向量表示用于语义搜索
    try:
        content_vector = await generate_content_vector(full_content, langchain_client)
    except Exception as e:
        print(f"生成内容向量失败: {str(e)}")
        content_vector = None
    
    # 构建情感分析结果
    sentiment_data = []
    for i, message in enumerate(messages):
        sentiment_data.append({
            "message_index": i,
            "sentiment_type": sentiment_analysis,  # 这里简化处理，实际应用中可以对每条消息单独分析
            "sentiment_score": 0.5  # 默认中性分数
        })
    
    # 构建会话文档
    conversation_doc = {
        "conversation_id": conversation_id,
        "customer_id": customer_id,
        "customer_name": f"客户{customer_id}",
        "advisor_id": advisor_id,
        "advisor_name": f"顾问{advisor_id}",
        "conversation_time": conversation_date,
        "full_content": full_content,
        "messages": messages,
        "summary": summary,
        "content_vector": content_vector,  # 添加向量表示
        "mentioned_products": mentioned_products,
        "mentioned_industries": mentioned_industries,
        "mentioned_topics": mentioned_topics,
        "mentioned_complaints": mentioned_complaints,
        "sentiment": sentiment_data,  # 添加情感分析结果
        "conversation_tags": []  # 可以后续添加标签
    }
    
    return conversation_doc


def extract_keywords(text, keyword_list):
    """
    从文本中提取关键词（作为备用方法）
    """
    found_keywords = []
    for keyword in keyword_list:
        if keyword in text:
            found_keywords.append(keyword)
    return found_keywords


async def generate_content_vector(text, langchain_client):
    """
    生成文本的向量表示
    """
    try:
        embedding_model = langchain_client["embedding_model"]
        # 确保输入是字符串类型且不为空
        if not isinstance(text, str):
            text = str(text)
        
        # 确保文本不为空
        if not text.strip():
            print("警告: 尝试为空文本生成向量，跳过")
            return None
            
        # 使用LangChain的嵌入模型生成向量
        try:
            # 尝试使用异步方法
            vector = await embedding_model.aembed_query(text)
            return vector
        except AttributeError:
            # 如果异步方法不可用，尝试使用同步方法
            vector = embedding_model.embed_query(text)
            return vector
    except Exception as e:
        print(f"生成向量失败: {str(e)}")
        return None


async def upload_conversations_to_es():
    """
    将会话记录上传到Elasticsearch
    """
    # 获取ES客户端
    es_client = get_es_client()
    
    # 获取会话文件目录
    conversations_dir = Path(__file__).parent.parent.parent / "doc" / "会话搜索和洞察" / "原始的会话记录"
    
    if not os.path.exists(conversations_dir):
        print(f"会话目录不存在: {conversations_dir}")
        return
    
    # 获取所有会话文件
    conversation_files = [os.path.join(conversations_dir, f) for f in os.listdir(conversations_dir) if f.endswith('.txt')]
    
    if not conversation_files:
        print("没有找到会话文件")
        return
    
    print(f"找到 {len(conversation_files)} 个会话文件")
    
    # 处理所有会话文件
    conversations = []
    for file_path in conversation_files:
        print(f"处理文件: {os.path.basename(file_path)}")
        conversation_doc = await process_conversation_file(file_path)
        if conversation_doc:
            conversations.append(conversation_doc)
    
    # 批量上传到ES
    if conversations:
        print(f"上传 {len(conversations)} 个会话到Elasticsearch")
        success = bulk_index_conversations(es_client, conversations)
        if success:
            print("上传成功")
        else:
            print("上传失败")
    else:
        print("没有有效的会话数据可上传")


async def main():
    await upload_conversations_to_es()


if __name__ == "__main__":
    asyncio.run(main())