import os
import json
import re
from typing import Dict, List, Any, Optional
from pydantic import SecretStr
from dotenv import load_dotenv
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain_community.embeddings import DashScopeEmbeddings
from langchain.prompts import ChatPromptTemplate
from langchain.schema import AIMessage, HumanMessage

# 读取配置文件
def read_config():
    # 加载.env文件
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
    load_dotenv(env_path)
    
    # 从环境变量获取API密钥
    deepseek_key = os.getenv('DEEPSEEK_API_KEY', '')
    qwen_key = os.getenv('DASHSCOPE_API_KEY', '')
    
    if not deepseek_key:
        print("警告: DEEPSEEK_API_KEY 环境变量未设置")
    
    if not qwen_key:
        print("警告: DASHSCOPE_API_KEY 环境变量未设置")
    
    return {"deepseek": deepseek_key, "qwen": qwen_key}

# 创建LangChain客户端
def get_langchain_client():
    api_keys = read_config()
    deepseek_key = api_keys["deepseek"]
    qwen_key = api_keys["qwen"]
    
    if not deepseek_key:
        raise ValueError("DeepSeek API Key未配置")
    
    if not qwen_key:
        print("警告: 通义千问 API Key未配置，将使用DeepSeek API Key代替")
        qwen_key = deepseek_key
    
    # 创建LangChain聊天模型，使用DeepSeek API
    chat_model = ChatOpenAI(
        model="deepseek-chat",
        api_key=SecretStr(deepseek_key),
        temperature=0.1,
        base_url="https://api.deepseek.com/v1"
    )
    
    # 创建LangChain嵌入模型，使用通义千问Qwen3-embedding API
    embedding_model = DashScopeEmbeddings(
        model="text-embedding-v4",
        dashscope_api_key=qwen_key
    )
    
    return {"chat_model": chat_model, "embedding_model": embedding_model}

# 生成会话摘要（基于纯文本）
async def generate_conversation_summary_from_text(conversation_text, langchain_client):
    """
    生成会话内容的摘要（基于纯文本输入）
    """
    chat_model = langchain_client["chat_model"]
    
    try:
        # 直接使用消息内容调用模型
        prompt_content = f"""
        请为以下会话内容生成一个简短的摘要，概括主要内容和关键点。
        
        会话内容：
        {conversation_text}
        
        请生成不超过100字的摘要。
        """
        
        # 直接使用消息列表调用模型
        result = await chat_model.ainvoke([HumanMessage(content=prompt_content)])
        return result.content.strip()
    except Exception as e:
        print(f"生成会话摘要失败: {str(e)}")
        return "无法生成摘要"

# 提取会话实体
async def extract_conversation_entities(langchain_client, conversation):
    """
    从会话中提取实体和情感分析，增强多维度匹配逻辑
    """
    chat_model = langchain_client["chat_model"]
    
    try:
        # 构建更精确的提示词，增强实体提取的多维度匹配
        prompt_content = f"""
        请从以下会话内容中提取关键实体信息，特别关注客户特征和投资意向，用于多维度匹配：

        会话内容：
        {conversation['full_content']}

        请提取以下类型的实体：
        1. 客户特征：
           - 身份特征：企业主、公司老板、创业者、高管、个体户等
           - 财务状况：高净值、资金充裕、有资产、收入稳定等
           - 行业背景：所属行业、公司规模、业务类型等
           - 个人属性：年龄段、职业、教育背景等

        2. 投资意向：
           - 投资类型：美股、A股、港股、基金、理财产品、保险等
           - 投资金额：具体金额或资金规模描述
           - 风险偏好：保守、稳健、激进、平衡等
           - 投资期限：短期、中期、长期等

        3. 产品服务：
           - 咨询的产品类型
           - 服务需求类型
           - 具体问题和关注点

        4. 情感和态度：
           - 整体情感倾向
           - 满意度
           - 信任度

        5. 搜索标签：
           - 提取能够用于搜索匹配的关键词标签

        请以JSON格式返回结果，格式如下：
        {{
            "customer_profile": {{
                "identity": ["企业主", "公司老板"],
                "financial_status": ["高净值", "资金充裕"],
                "industry": "行业",
                "personal_attributes": ["年龄段", "职业"]
            }},
            "investment_intent": {{
                "investment_types": ["美股", "股票投资"],
                "amount_range": "投资金额",
                "risk_preference": "风险偏好",
                "time_horizon": "投资期限"
            }},
            "product_service": {{
                "product_types": ["产品类型"],
                "service_needs": ["服务需求"],
                "specific_questions": ["具体问题"]
            }},
            "sentiment_analysis": {{
                "overall_sentiment": "positive/neutral/negative",
                "satisfaction_level": "满意度",
                "trust_level": "信任度"
            }},
            "search_tags": ["关键标签1", "关键标签2"],
            "mentioned_products": ["产品1", "产品2"],
            "mentioned_industries": ["行业1", "行业2"],
            "mentioned_topics": ["话题1", "话题2"],
            "mentioned_complaints": ["问题1", "问题2"]
        }}
        
        如果某些信息不存在，请设置为null或空数组。只返回JSON格式的结果，不要包含任何解释。
        """
        
        # 直接使用消息列表调用模型
        result = await chat_model.ainvoke([HumanMessage(content=prompt_content)])
        result_str = result.content
        
        # 清理响应，确保只有JSON部分
        json_match = re.search(r'\{[\s\S]*\}', result_str)
        if json_match:
            result_str = json_match.group(0)
        
        try:
            result_dict = json.loads(result_str)
            
            # 确保必要字段存在，保持向后兼容
            if "mentioned_products" not in result_dict:
                result_dict["mentioned_products"] = []
            if "mentioned_industries" not in result_dict:
                result_dict["mentioned_industries"] = []
            if "mentioned_topics" not in result_dict:
                result_dict["mentioned_topics"] = []
            if "mentioned_complaints" not in result_dict:
                result_dict["mentioned_complaints"] = []
            if "sentiment" not in result_dict:
                # 从新的结构中提取情感信息
                sentiment_analysis = result_dict.get("sentiment_analysis", {})
                result_dict["sentiment"] = sentiment_analysis.get("overall_sentiment", "neutral")
            
            return result_dict
        except json.JSONDecodeError:
            print("解析实体提取结果失败")
            return {
                "customer_profile": {
                    "identity": [],
                    "financial_status": [],
                    "industry": None,
                    "personal_attributes": []
                },
                "investment_intent": {
                    "investment_types": [],
                    "amount_range": None,
                    "risk_preference": None,
                    "time_horizon": None
                },
                "product_service": {
                    "product_types": [],
                    "service_needs": [],
                    "specific_questions": []
                },
                "sentiment_analysis": {
                    "overall_sentiment": "neutral",
                    "satisfaction_level": None,
                    "trust_level": None
                },
                "search_tags": [],
                "mentioned_products": [],
                "mentioned_industries": [],
                "mentioned_topics": [],
                "mentioned_complaints": [],
                "sentiment": "neutral"
            }
    except Exception as e:
        print(f"提取会话实体失败: {str(e)}")
        return {
            "customer_profile": {
                "identity": [],
                "financial_status": [],
                "industry": None,
                "personal_attributes": []
            },
            "investment_intent": {
                "investment_types": [],
                "amount_range": None,
                "risk_preference": None,
                "time_horizon": None
            },
            "product_service": {
                "product_types": [],
                "service_needs": [],
                "specific_questions": []
            },
            "sentiment_analysis": {
                "overall_sentiment": "neutral",
                "satisfaction_level": None,
                "trust_level": None
            },
            "search_tags": [],
            "mentioned_products": [],
            "mentioned_industries": [],
            "mentioned_topics": [],
            "mentioned_complaints": [],
            "sentiment": "neutral"
        }

# 生成会话摘要
async def generate_conversation_summary(langchain_client, conversation):
    """
    生成会话摘要
    """
    chat_model = langchain_client["chat_model"]
    
    try:
        # 直接使用消息内容调用模型
        prompt_content = f"""
        请为以下财富顾问与客户的会话生成一个简短的摘要，概括主要内容和关键点。
        
        会话内容：
        {conversation['full_content']}
        
        请生成不超过100字的摘要。
        """
        
        # 直接使用消息列表调用模型
        result = await chat_model.ainvoke([HumanMessage(content=prompt_content)])
        summary = result.content.strip()
        return summary
    except Exception as e:
        print(f"生成会话摘要失败: {str(e)}")
        return ""

# 分析会话情感
async def analyze_conversation_sentiment(langchain_client, conversation):
    """
    分析会话中的情感
    """
    chat_model = langchain_client["chat_model"]
    sentiments = []
    
    try:
        for i, message in enumerate(conversation.get("messages", [])):
            if message.get("sender_type") == "customer":  # 只分析客户消息的情感
                try:
                    # 直接使用消息内容调用模型
                    prompt_content = f"""
                    请分析以下消息的情感倾向，并给出情感分数。
                    
                    消息内容：
                    {message.get('content', '')}
                    
                    请以JSON格式返回结果，格式如下：
                    {{"sentiment_type": "positive/negative/neutral", "sentiment_score": 0.8}}
                    
                    情感分数范围从0到1，其中：
                    - 0-0.3表示负面情感
                    - 0.3-0.7表示中性情感
                    - 0.7-1表示正面情感
                    
                    只返回JSON格式的结果，不要包含任何解释。
                    """
                    
                    # 直接使用消息列表调用模型
                    result = await chat_model.ainvoke([HumanMessage(content=prompt_content)])
                    result_str = result.content
                    
                    # 清理响应，确保只有JSON部分
                    json_match = re.search(r'\{[\s\S]*\}', result_str)
                    if json_match:
                        result_str = json_match.group(0)
                    
                    try:
                        result_dict = json.loads(result_str)
                        sentiment = {
                            "message_index": i,
                            "sentiment_type": result_dict.get("sentiment_type", "neutral"),
                            "sentiment_score": result_dict.get("sentiment_score", 0.5)
                        }
                        sentiments.append(sentiment)
                    except json.JSONDecodeError:
                        print(f"解析情感分析结果失败: {result_str}")
                        sentiments.append({
                            "message_index": i,
                            "sentiment_type": "neutral",
                            "sentiment_score": 0.5
                        })
                except Exception as e:
                    print(f"分析单条消息情感失败: {str(e)}")
                    sentiments.append({
                        "message_index": i,
                        "sentiment_type": "neutral",
                        "sentiment_score": 0.5
                    })
    except Exception as e:
        print(f"分析会话情感失败: {str(e)}")
    
    return sentiments

# 生成会话向量
async def generate_conversation_vector(langchain_client, conversation):
    """
    生成会话内容的向量表示
    """
    embedding_model = langchain_client["embedding_model"]
    
    try:
        # 提取会话内容
        content = conversation.get("full_content", "")
        if not content:
            return None
        
        # 调用嵌入API
        vector = await embedding_model.aembed_query(content)
        return vector
    except Exception as e:
        print(f"生成会话向量失败: {str(e)}")
        return None

# 处理会话数据
async def process_conversation(langchain_client, raw_conversation):
    """
    处理原始会话数据，提取实体、生成摘要、分析情感、生成向量
    """
    try:
        # 提取实体
        entities = await extract_conversation_entities(langchain_client, raw_conversation)
        
        # 生成摘要
        summary = await generate_conversation_summary(langchain_client, raw_conversation)
        
        # 分析情感
        sentiment = await analyze_conversation_sentiment(langchain_client, raw_conversation)
        
        # 生成向量
        vector = await generate_conversation_vector(langchain_client, raw_conversation)
        
        # 更新会话数据
        processed_conversation = raw_conversation.copy()
        processed_conversation.update({
            "mentioned_products": entities.get("mentioned_products", []),
            "mentioned_industries": entities.get("mentioned_industries", []),
            "mentioned_topics": entities.get("mentioned_topics", []),
            "mentioned_complaints": entities.get("mentioned_complaints", []),
            "summary": summary,
            "sentiment": sentiment,
            "content_vector": vector
        })
        
        return processed_conversation
    except Exception as e:
        print(f"处理会话数据失败: {str(e)}")
        return raw_conversation

# 将自然语言查询转换为ES查询
async def convert_nl_to_es_query(query_text, client):
    """
    将自然语言查询转换为Elasticsearch查询
    """
    chat_model = client["chat_model"]
    
    # 构建提示词
    prompt = ChatPromptTemplate.from_messages([
        HumanMessage(content=f"""
        请将以下自然语言查询转换为Elasticsearch查询JSON：
        
        查询: {query_text}
        
        目标索引结构:
        - conversation_id: keyword
        - customer_id: keyword
        - customer_name: keyword
        - advisor_id: keyword
        - advisor_name: keyword
        - conversation_time: date
        - full_content: text (使用标准分词)
        - messages: nested对象数组，包含sender_type, content等字段
        - summary: text
        - extracted_entities: nested对象数组，包含entity_type, entity_value等字段
        - sentiment: nested对象数组，包含sentiment_type, sentiment_score等字段
        - mentioned_products: keyword数组
        - mentioned_industries: keyword数组
        - mentioned_topics: keyword数组
        - mentioned_complaints: keyword数组
        
        请生成一个bool查询，使用must、should和must_not组合，确保查询能够准确捕捉用户意图。
        只返回JSON格式的查询体，不要包含任何解释。
        """)
    ])
    
    try:
        # 调用LangChain模型
        # 将ChatPromptTemplate转换为消息列表
        messages = [HumanMessage(content=f"""
        请将以下自然语言查询转换为Elasticsearch查询JSON：
        
        查询: {query_text}
        
        目标索引结构:
        - conversation_id: keyword
        - customer_id: keyword
        - customer_name: keyword
        - advisor_id: keyword
        - advisor_name: keyword
        - conversation_time: date
        - full_content: text (使用标准分词)
        - messages: nested对象数组，包含sender_type, content等字段
        - summary: text
        - extracted_entities: nested对象数组，包含entity_type, entity_value等字段
        - sentiment: nested对象数组，包含sentiment_type, sentiment_score等字段
        - mentioned_products: keyword数组
        - mentioned_industries: keyword数组
        - mentioned_topics: keyword数组
        - mentioned_complaints: keyword数组
        
        请生成一个bool查询，使用must、should和must_not组合，确保查询能够准确捕捉用户意图。
        只返回JSON格式的查询体，不要包含任何解释。
        """)]
        result = await chat_model.ainvoke(messages)
        es_query_str = result.content
        
        # 清理响应，确保只有JSON部分
        json_match = re.search(r'\{[\s\S]*\}', es_query_str)
        if json_match:
            es_query_str = json_match.group(0)
        
        try:
            es_query = json.loads(es_query_str)
            
            # 确保查询结构正确
            if "query" not in es_query:
                es_query = {"query": es_query}
            
            if "bool" not in es_query["query"]:
                es_query["query"] = {"bool": {"must": [es_query["query"]]}}
            
            if "must" not in es_query["query"]["bool"]:
                es_query["query"]["bool"]["must"] = []
                
            # 添加高亮配置
            es_query["highlight"] = {
                "fields": {
                    "full_content": {},
                    "messages.content": {},
                    "summary": {}
                },
                "pre_tags": ["<em>"],
                "post_tags": ["</em>"]
            }
            
            return es_query
        except json.JSONDecodeError:
            # 如果解析失败，返回一个基本的查询
            return {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "match": {
                                    "full_content": query_text
                                }
                            }
                        ]
                    }
                },
                "highlight": {
                    "fields": {
                        "full_content": {},
                        "messages.content": {},
                        "summary": {}
                    },
                    "pre_tags": ["<em>"],
                    "post_tags": ["</em>"]
                }
            }
    except Exception as e:
        print(f"转换自然语言查询失败: {str(e)}")
        # 返回一个基本的查询
        return {
            "query": {
                "bool": {
                    "must": [
                        {
                            "match": {
                                "full_content": query_text
                            }
                        }
                    ]
                }
            },
            "highlight": {
                "fields": {
                    "full_content": {},
                    "messages.content": {},
                    "summary": {}
                },
                "pre_tags": ["<em>"],
                "post_tags": ["</em>"]
            }
        }


# 向量搜索相关函数
async def generate_query_vector(langchain_client, query_text):
    """
    生成查询向量，包含大模型智能预处理和优化
    """
    embedding_model = langchain_client["embedding_model"]
    chat_model = langchain_client.get("chat_model")
    
    try:
        # 使用大模型智能预处理查询文本
        if chat_model:
            processed_query = await llm_preprocess_query(chat_model, query_text)
        else:
            # 回退到基础预处理
            processed_query = preprocess_query_text(query_text)
        
        print(f"原始查询: {query_text}")
        print(f"处理后查询: {processed_query}")
        
        # 调用嵌入API
        vector = await embedding_model.aembed_query(processed_query)
        return vector
    except Exception as e:
        print(f"生成查询向量失败: {str(e)}")
        return None


async def generate_query_vector_with_preprocessing(langchain_client, query_text):
    """
    生成查询向量并返回处理后的查询文本，用于调试和展示
    """
    embedding_model = langchain_client["embedding_model"]
    chat_model = langchain_client.get("chat_model")
    
    try:
        # 使用大模型智能预处理查询文本
        if chat_model:
            processed_query = await llm_preprocess_query(chat_model, query_text)
        else:
            # 回退到基础预处理
            processed_query = preprocess_query_text(query_text)
        
        print(f"原始查询: {query_text}")
        print(f"处理后查询: {processed_query}")
        
        # 调用嵌入API
        vector = await embedding_model.aembed_query(processed_query)
        return vector, processed_query
    except Exception as e:
        print(f"生成查询向量失败: {str(e)}")
        return None, query_text


async def llm_preprocess_query(chat_model, query_text):
    """
    使用大模型智能预处理查询文本
    """
    try:
        # 构建更精确的提示词
        prompt_content = f"""你是一个专业的金融客服搜索助手。请分析用户的查询意图，并优化查询文本以提高搜索准确性。

用户查询：{query_text}

请执行以下任务：
1. 识别查询中的关键实体（客户特征、产品类型、行业、需求等）
2. 提取核心关键词和短语
3. 添加相关的同义词和扩展词汇
4. 补充隐含的搜索意图

优化规则：
- 保持原始查询的核心意图不变
- 针对"想投资美股的有自己公司的客户"这类查询，要识别：
  * 投资意向：美股、股票投资、海外投资
  * 客户特征：企业主、公司老板、创业者、高净值客户
  * 财务状况：有资产、有收入来源、资金充裕
- 添加金融、投资、理财相关的同义词
- 扩展客户画像描述词汇
- 使用更丰富的语义表达

示例：
输入："想投资美股的有自己公司的客户"
输出："想投资美股 股票投资 海外投资 有自己公司 企业主 公司老板 创业者 高净值客户 资金充裕 投资需求 资产配置"

请直接返回优化后的查询文本，不要包含解释："""
        
        # 使用HumanMessage格式调用大模型
        from langchain_core.messages import HumanMessage
        response = await chat_model.ainvoke([HumanMessage(content=prompt_content)])
        
        # 提取响应文本
        if hasattr(response, 'content'):
            processed_query = response.content.strip()
        else:
            processed_query = str(response).strip()
        
        # 如果大模型返回为空或异常，回退到基础处理
        if not processed_query or len(processed_query) < 2:
            return preprocess_query_text(query_text)
        
        return processed_query
        
    except Exception as e:
        print(f"大模型预处理失败，回退到基础处理: {str(e)}")
        return preprocess_query_text(query_text)


def preprocess_query_text(query_text):
    """
    基础预处理查询文本，提高搜索准确性
    """
    # 去除多余空格
    processed = query_text.strip()
    
    # 扩展的同义词映射表
    synonyms_map = {
        # 客户特征相关
        "公司": "企业 公司 机构 公司老板 企业主 创业者",
        "老板": "老板 企业主 公司老板 创业者 企业家 负责人",
        "企业主": "企业主 公司老板 老板 创业者 企业家",
        "创业者": "创业者 企业主 公司老板 老板 企业家",
        
        # 客户类型
        "客户": "客户 用户 顾客 投资者 理财客户",
        "高净值": "高净值 富裕 资金充裕 有钱 财富 资产丰厚",
        "有钱": "有钱 富裕 高净值 资金充裕 财富 资产丰厚",
        
        # 投资相关
        "投资": "投资 理财 资产配置 财富管理 投资理财",
        "美股": "美股 美国股票 海外投资 境外投资 国际投资",
        "股票": "股票 股市 证券 权益投资 股权投资",
        "理财": "理财 投资 资产配置 财富管理 投资理财",
        
        # 产品服务
        "产品": "产品 服务 业务 理财产品 投资产品",
        "基金": "基金 投资基金 理财产品 资产管理",
        "保险": "保险 保障 风险管理 保险产品",
        
        # 需求意向
        "想要": "想要 希望 需要 打算 考虑 有意向",
        "需要": "需要 想要 希望 打算 考虑 有意向",
        "咨询": "咨询 询问 了解 问询 求助",
        
        # 财务状况
        "风险": "风险 安全 保障 风险管理 风险控制",
        "收益": "收益 回报 利润 盈利 收入",
        "资金": "资金 资本 资产 财富 资金实力"
    }
    
    # 智能同义词扩展
    expanded_terms = []
    for key, synonyms in synonyms_map.items():
        if key in processed:
            expanded_terms.extend(synonyms.split())
    
    # 去重并添加到查询中
    if expanded_terms:
        unique_terms = list(set(expanded_terms))
        processed = f"{processed} {' '.join(unique_terms)}"
    
    return processed


async def vector_search_conversations(es_client, query_vector, filters=None, k=50, similarity_threshold=0.5):
    """
    使用向量进行会话搜索
    """
    if not query_vector:
        return {"hits": {"hits": [], "total": {"value": 0}}}
    
    try:
        # 标记使用的查询类型
        used_script_score = False
        
        # 首先尝试使用kNN查询（ES 8.0+）
        try:
            knn_query = {
                "knn": {
                    "field": "content_vector",
                    "query_vector": query_vector,
                    "k": min(k * 5, 200),  # 增加候选结果数量
                    "num_candidates": min(k * 20, 2000),  # 大幅增加候选数量以提高召回率
                    "boost": 1.2  # 增加向量搜索的权重
                }
            }
            
            if filters:
                knn_query["knn"]["filter"] = filters
            
            # 将kNN查询结构输出到文件，方便在ES-head中执行
            import json
            import os
            from datetime import datetime
            
            output_dir = "/Users/cuixueyong/code/github/yili-ai-python/doc/会话搜索和洞察"
            os.makedirs(output_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(output_dir, f"knn_query_{timestamp}.json")
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("=== kNN查询结构 ===\n")
                f.write(json.dumps(knn_query, indent=2, ensure_ascii=False))
                f.write("\n==================\n")
            
            print(f"kNN查询结构已保存到: {output_file}")
            
            response = es_client.search(
                index="conversation_contents",
                body=knn_query,
                size=k
            )
        except Exception as knn_error:
            print(f"kNN查询失败，尝试使用script_score查询: {str(knn_error)}")
            
            # 标记使用了script_score查询
            used_script_score = True
            # 回退到script_score查询（兼容旧版本ES）
            script_query = {
                "query": {
                    "script_score": {
                        "query": {
                            "bool": {
                                "must": []
                            }
                        },
                        "script": {
                            "source": "cosineSimilarity(params.query_vector, 'content_vector') + 1.0",
                            "params": {
                                "query_vector": query_vector
                            }
                        }
                    }
                }
            }
            
            # 添加过滤条件
            if filters:
                if isinstance(filters, dict) and "bool" in filters:
                    script_query["query"]["script_score"]["query"]["bool"]["must"].extend(filters["bool"]["must"])
                else:
                    script_query["query"]["script_score"]["query"]["bool"]["must"].append(filters)
            
            # 将script_score查询结构输出到文件，方便在ES-head中执行
            import json
            import os
            from datetime import datetime
            
            output_dir = "/Users/cuixueyong/code/github/yili-ai-python/doc/会话搜索和洞察"
            os.makedirs(output_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(output_dir, f"script_score_query_{timestamp}.json")
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("=== script_score查询结构 ===\n")
                f.write(json.dumps(script_query, indent=2, ensure_ascii=False))
                f.write("\n=========================\n")
            
            print(f"script_score查询结构已保存到: {output_file}")
            
            response = es_client.search(
                index="conversation_contents",
                body=script_query,
                size=k
            )
        
        # 智能过滤和排序结果
        filtered_hits = []
        
        for hit in response["hits"]["hits"]:
            # 对于script_score查询，分数需要减1（因为我们加了1.0）
            actual_score = hit["_score"] - 1.0 if used_script_score else hit["_score"]
            
            # 应用动态相似度阈值过滤
            # 对于高质量查询，使用较低的阈值以提高召回率
            dynamic_threshold = max(similarity_threshold * 0.8, 0.3)  # 动态降低阈值
            
            if actual_score >= dynamic_threshold:
                # 更新实际分数
                hit["_score"] = actual_score
                filtered_hits.append(hit)
        
        # 按相似度重新排序
        filtered_hits.sort(key=lambda x: x["_score"], reverse=True)
        
        response["hits"]["hits"] = filtered_hits
        response["hits"]["total"]["value"] = len(filtered_hits)
        
        return response
        
    except Exception as e:
        print(f"向量搜索失败: {str(e)}")
        return {"hits": {"hits": [], "total": {"value": 0}}}


def aggregate_customer_data(search_results):
    """
    聚合搜索结果，按客户分组，保持相关性排序
    """
    customer_data = {}
    
    for hit in search_results["hits"]["hits"]:
        source = hit["_source"]
        customer_id = source["customer_id"]
        similarity_score = hit["_score"]
        
        if customer_id not in customer_data:
            customer_data[customer_id] = {
                "customer_id": customer_id,
                "customer_name": source["customer_name"],
                "advisor_id": source["advisor_id"],
                "advisor_name": source["advisor_name"],
                "conversations": [],
                "conversation_times": [],
                "mentioned_products": set(),
                "mentioned_industries": set(),
                "mentioned_topics": set(),
                "mentioned_complaints": set(),
                "similarity_scores": [],
                "conversation_summaries": []
            }
        
        # 添加会话数据
        customer_data[customer_id]["conversations"].append(source["conversation_id"])
        customer_data[customer_id]["conversation_times"].append(source["conversation_time"])
        customer_data[customer_id]["similarity_scores"].append(similarity_score)
        
        if source.get("summary"):
            customer_data[customer_id]["conversation_summaries"].append(source["summary"])
        
        # 聚合提及的内容
        for products in source.get("mentioned_products", []):
            customer_data[customer_id]["mentioned_products"].add(products)
        for industries in source.get("mentioned_industries", []):
            customer_data[customer_id]["mentioned_industries"].add(industries)
        for topics in source.get("mentioned_topics", []):
            customer_data[customer_id]["mentioned_topics"].add(topics)
        for complaints in source.get("mentioned_complaints", []):
            customer_data[customer_id]["mentioned_complaints"].add(complaints)
    
    # 处理聚合结果
    result = []
    for customer_id, data in customer_data.items():
        conversation_times = [datetime.fromisoformat(t.replace('Z', '+00:00')) if isinstance(t, str) else t 
                            for t in data["conversation_times"]]
        
        result.append({
            "customer_id": data["customer_id"],
            "customer_name": data["customer_name"],
            "advisor_id": data["advisor_id"],
            "advisor_name": data["advisor_name"],
            "conversation_count": len(data["conversations"]),
            "latest_conversation_time": max(conversation_times),
            "earliest_conversation_time": min(conversation_times),
            "conversation_summaries": data["conversation_summaries"][:5],  # 最多返回5个摘要
            "mentioned_products": list(data["mentioned_products"]),
            "mentioned_industries": list(data["mentioned_industries"]),
            "mentioned_topics": list(data["mentioned_topics"]),
            "mentioned_complaints": list(data["mentioned_complaints"]),
            "similarity_score": calculate_weighted_similarity(data["similarity_scores"]),  # 加权相似度
            "matched_conversations": data["conversations"]
        })
    
    # 按加权相似度和会话数量排序
    result.sort(key=lambda x: (x["similarity_score"], x["conversation_count"]), reverse=True)
    
    return result


def calculate_weighted_similarity(scores):
    """
    计算加权相似度，给予更高分数更大权重
    """
    if not scores:
        return 0.0
    
    # 按分数排序，给予前面的结果更高权重
    sorted_scores = sorted(scores, reverse=True)
    
    # 使用递减权重：第一个结果权重为1，第二个为0.8，第三个为0.6，以此类推
    weighted_sum = 0.0
    total_weight = 0.0
    
    for i, score in enumerate(sorted_scores):
        weight = max(0.2, 1.0 - i * 0.2)  # 最小权重为0.2
        weighted_sum += score * weight
        total_weight += weight
    
    return weighted_sum / total_weight if total_weight > 0 else 0.0