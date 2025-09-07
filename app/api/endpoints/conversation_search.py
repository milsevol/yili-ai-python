from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
from elasticsearch import Elasticsearch
from app.core.config import settings
from app.schemas.conversation import ConversationSearchQuery, ConversationSearchResult, CustomerSearchResult, CustomerVectorSearchQuery, CustomerVectorSearchResult
from app.services.es_service import get_es_client
from app.services.langchain_service import get_langchain_client, convert_nl_to_es_query, generate_query_vector, vector_search_conversations, aggregate_customer_data, preprocess_query_text, generate_query_vector_with_preprocessing

router = APIRouter()


@router.post("/search", response_model=ConversationSearchResult)
async def search_conversations(
    query: ConversationSearchQuery,
    es_client: Elasticsearch = Depends(get_es_client),
    langchain_client: Any = Depends(get_langchain_client)
):
    """
    根据自然语言查询搜索会话内容
    """
    try:
        # 使用LangChain将自然语言查询转换为Elasticsearch查询
        es_query = await convert_nl_to_es_query(query.query_text, langchain_client)
        
        # 添加基础筛选条件
        if query.advisor_id and query.advisor_id != "all":
            es_query["query"]["bool"]["must"].append({
                "term": {"advisor_id": query.advisor_id}
            })
        
        # 添加时间范围筛选
        if query.start_time or query.end_time:
            time_range = {}
            if query.start_time:
                time_range["gte"] = query.start_time
            if query.end_time:
                time_range["lte"] = query.end_time
                
            es_query["query"]["bool"]["must"].append({
                "range": {"conversation_time": time_range}
            })
        
        # 执行Elasticsearch查询
        search_results = es_client.search(
            index="conversation_contents",
            body=es_query,
            size=query.page_size,
            from_=(query.page - 1) * query.page_size
        )
        
        # 处理搜索结果
        conversations = []
        for hit in search_results["hits"]["hits"]:
            source = hit["_source"]
            conversations.append({
                "conversation_id": source["conversation_id"],
                "customer_id": source["customer_id"],
                "customer_name": source["customer_name"],
                "advisor_id": source["advisor_id"],
                "advisor_name": source["advisor_name"],
                "conversation_time": source["conversation_time"],
                "summary": source["summary"],
                "highlight": hit.get("highlight", {}),
                "score": hit["_score"]
            })
        
        return {
            "total": search_results["hits"]["total"]["value"],
            "conversations": conversations
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索会话失败: {str(e)}")


@router.post("/insights")
async def get_conversation_insights(
    query: ConversationSearchQuery,
    es_client: Elasticsearch = Depends(get_es_client),
    langchain_client: Any = Depends(get_langchain_client)
):
    """
    获取会话洞察数据
    """
    try:
        # 构建基础查询
        base_query = {
            "query": {
                "bool": {
                    "must": []
                }
            }
        }
        
        # 添加基础筛选条件
        if query.advisor_id and query.advisor_id != "all":
            base_query["query"]["bool"]["must"].append({
                "term": {"advisor_id": query.advisor_id}
            })
        
        # 添加时间范围筛选
        if query.start_time or query.end_time:
            time_range = {}
            if query.start_time:
                time_range["gte"] = query.start_time
            if query.end_time:
                time_range["lte"] = query.end_time
                
            base_query["query"]["bool"]["must"].append({
                "range": {"conversation_time": time_range}
            })
        
        # 如果有业务洞察关键词，添加到查询中
        if query.query_text:
            # 使用LangChain将自然语言查询转换为Elasticsearch查询
            insight_query = await convert_nl_to_es_query(langchain_client, query.query_text)
            base_query["query"]["bool"]["must"].extend(insight_query["query"]["bool"]["must"])
        
        # 获取热点话题词云
        topics_agg = await get_top_terms_aggregation(es_client, base_query, "mentioned_topics", 10)
        
        # 获取热点行业词云
        industries_agg = await get_top_terms_aggregation(es_client, base_query, "mentioned_industries", 10)
        
        # 获取热点产品词云
        products_agg = await get_top_terms_aggregation(es_client, base_query, "mentioned_products", 10)
        
        # 获取投诉热点词云
        complaints_agg = await get_top_terms_aggregation(es_client, base_query, "mentioned_complaints", 10)
        
        return {
            "topics": topics_agg,
            "industries": industries_agg,
            "products": products_agg,
            "complaints": complaints_agg
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取会话洞察失败: {str(e)}")


# 此函数已移至langchain_service.py
# 保留此处的函数签名以便在其他地方调用时不需要修改
async def convert_nl_to_es_query(query_text: str, client: Any) -> Dict:
    """
    使用LangChain将自然语言查询转换为Elasticsearch查询
    此函数已移至langchain_service.py，此处保留函数签名以兼容现有代码
    """
    from app.services.langchain_service import convert_nl_to_es_query as langchain_convert
    return await langchain_convert(query_text, client)


async def get_top_terms_aggregation(es_client: Elasticsearch, base_query: Dict, field: str, size: int) -> List[Dict]:
    """
    获取指定字段的top terms聚合结果
    """
    # 复制基础查询，添加聚合
    agg_query = base_query.copy()
    agg_query["size"] = 0  # 不需要返回文档，只需要聚合结果
    agg_query["aggs"] = {
        "top_terms": {
            "terms": {
                "field": field,
                "size": size
            }
        }
    }
    
    # 执行聚合查询
    result = es_client.search(
        index="conversation_contents",
        body=agg_query
    )
    
    # 处理聚合结果
    terms_result = []
    for bucket in result["aggregations"]["top_terms"]["buckets"]:
        terms_result.append({
            "term": bucket["key"],
            "count": bucket["doc_count"]
        })
    
    return terms_result


@router.post("/search_customers", response_model=CustomerSearchResult)
async def search_customers(
    query: ConversationSearchQuery,
    es_client: Elasticsearch = Depends(get_es_client),
    langchain_client: Any = Depends(get_langchain_client)
):
    """
    根据自然语言查询搜索客户列表（去重）
    """
    try:
        # 使用LangChain将自然语言查询转换为Elasticsearch查询
        es_query = await convert_nl_to_es_query(query.query_text, langchain_client)
        
        # 添加基础筛选条件
        if query.advisor_id and query.advisor_id != "all":
            es_query["query"]["bool"]["must"].append({
                "term": {"advisor_id": query.advisor_id}
            })
        
        # 添加时间范围筛选
        if query.start_time or query.end_time:
            time_range = {}
            if query.start_time:
                time_range["gte"] = query.start_time
            if query.end_time:
                time_range["lte"] = query.end_time
                
            es_query["query"]["bool"]["must"].append({
                "range": {"conversation_time": time_range}
            })
        
        # 添加客户聚合查询
        es_query["size"] = 0  # 不需要返回文档，只需要聚合结果
        es_query["aggs"] = {
            "customers": {
                "terms": {
                    "field": "customer_id",
                    "size": query.page_size,
                    "order": {"avg_score": "desc"}
                },
                "aggs": {
                    "customer_info": {
                        "top_hits": {
                            "size": 1,
                            "_source": ["customer_name", "advisor_id", "advisor_name"]
                        }
                    },
                    "conversation_count": {
                        "value_count": {
                            "field": "conversation_id"
                        }
                    },
                    "latest_conversation": {
                        "max": {
                            "field": "conversation_time"
                        }
                    },
                    "earliest_conversation": {
                        "min": {
                            "field": "conversation_time"
                        }
                    },
                    "avg_score": {
                        "avg": {
                            "script": "_score"
                        }
                    },
                    "summaries": {
                        "terms": {
                            "field": "summary.keyword",
                            "size": 5
                        }
                    },
                    "products": {
                        "terms": {
                            "field": "mentioned_products",
                            "size": 10
                        }
                    },
                    "industries": {
                        "terms": {
                            "field": "mentioned_industries",
                            "size": 10
                        }
                    },
                    "topics": {
                        "terms": {
                            "field": "mentioned_topics",
                            "size": 10
                        }
                    },
                    "complaints": {
                        "terms": {
                            "field": "mentioned_complaints",
                            "size": 10
                        }
                    }
                }
            }
        }
        
        # 执行Elasticsearch查询
        search_results = es_client.search(
            index="conversation_contents",
            body=es_query
        )
        
        # 处理聚合结果
        customers = []
        customer_buckets = search_results["aggregations"]["customers"]["buckets"]
        
        for bucket in customer_buckets:
            customer_info = bucket["customer_info"]["hits"]["hits"][0]["_source"]
            
            # 提取聚合数据
            summaries = [b["key"] for b in bucket["summaries"]["buckets"]]
            products = [b["key"] for b in bucket["products"]["buckets"]]
            industries = [b["key"] for b in bucket["industries"]["buckets"]]
            topics = [b["key"] for b in bucket["topics"]["buckets"]]
            complaints = [b["key"] for b in bucket["complaints"]["buckets"]]
            
            customers.append({
                "customer_id": bucket["key"],
                "customer_name": customer_info["customer_name"],
                "advisor_id": customer_info["advisor_id"],
                "advisor_name": customer_info["advisor_name"],
                "conversation_count": bucket["conversation_count"]["value"],
                "latest_conversation_time": bucket["latest_conversation"]["value_as_string"],
                "earliest_conversation_time": bucket["earliest_conversation"]["value_as_string"],
                "conversation_summaries": summaries,
                "mentioned_products": products,
                "mentioned_industries": industries,
                "mentioned_topics": topics,
                "mentioned_complaints": complaints,
                "avg_score": bucket["avg_score"]["value"] or 0.0
            })
        
        # 计算总数（这里使用聚合结果的数量，实际应用中可能需要单独查询）
        total_customers = len(customer_buckets)
        
        return {
            "total": total_customers,
            "customers": customers
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索客户失败: {str(e)}")


@router.post("/vector-search-customers", response_model=CustomerVectorSearchResult)
async def vector_search_customers(
    query: CustomerVectorSearchQuery,
    es_client: Elasticsearch = Depends(get_es_client),
    langchain_client: Any = Depends(get_langchain_client)
):
    """
    使用向量搜索客户
    """
    try:
        # 生成查询向量（包含智能预处理）
        query_vector, processed_query = await generate_query_vector_with_preprocessing(langchain_client, query.query_text)
        if not query_vector:
            raise HTTPException(status_code=400, detail="无法生成查询向量")
        
        # 构建过滤条件
        filters = []
        
        # 顾问ID过滤
        if query.advisor_id and query.advisor_id != "all":
            filters.append({
                "term": {"advisor_id": query.advisor_id}
            })
        
        # 时间范围过滤
        if query.start_time or query.end_time:
            time_filter = {"range": {"conversation_time": {}}}
            if query.start_time:
                time_filter["range"]["conversation_time"]["gte"] = query.start_time.isoformat()
            if query.end_time:
                time_filter["range"]["conversation_time"]["lte"] = query.end_time.isoformat()
            filters.append(time_filter)
        
        # 合并过滤条件
        combined_filter = None
        if filters:
            if len(filters) == 1:
                combined_filter = filters[0]
            else:
                combined_filter = {"bool": {"must": filters}}
        
        # 打印ES查询参数，方便在ES-head中调试
        print("=== ES查询参数 ===")
        import json
        query_params = {
            "query_vector": query_vector[:5] if query_vector else None,  # 只显示前5个向量值
            "filters": combined_filter,
            "k": query.k,
            "similarity_threshold": query.similarity_threshold,
            "index": "conversation_contents"
        }
        print(json.dumps(query_params, indent=2, ensure_ascii=False))
        print("==================")
        
        # 执行向量搜索
        search_results = await vector_search_conversations(
            es_client=es_client,
            query_vector=query_vector,
            filters=combined_filter,
            k=query.k,
            similarity_threshold=query.similarity_threshold
        )
        
        # 聚合客户数据
        customers_data = aggregate_customer_data(search_results)
        
        # 分页处理
        start_idx = (query.page - 1) * query.page_size
        end_idx = start_idx + query.page_size
        paginated_customers = customers_data[start_idx:end_idx]
        
        return {
            "total": len(customers_data),
            "customers": paginated_customers,
            "query_info": {
                "original_query": query.query_text,
                "processed_query": processed_query,
                "similarity_threshold": query.similarity_threshold,
                "k": query.k,
                "vector_dimension": len(query_vector) if query_vector else 0,
                "total_matches": search_results["hits"]["total"]["value"],
                "filtered_matches": len(search_results["hits"]["hits"])
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"向量搜索客户失败: {str(e)}")