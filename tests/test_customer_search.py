import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from main import app

client = TestClient(app)


@pytest.fixture
def mock_es_client():
    """模拟 Elasticsearch 客户端"""
    mock_client = MagicMock()
    # 模拟聚合查询结果
    mock_client.search.return_value = {
        "aggregations": {
            "customers": {
                "buckets": [
                    {
                        "key": "customer_001",
                        "customer_info": {
                            "hits": {
                                "hits": [{
                                    "_source": {
                                        "customer_name": "张三",
                                        "advisor_id": "advisor_001",
                                        "advisor_name": "李顾问"
                                    }
                                }]
                            }
                        },
                        "conversation_count": {"value": 5},
                        "latest_conversation": {"value_as_string": "2024-01-15T10:30:00Z"},
                        "earliest_conversation": {"value_as_string": "2024-01-01T09:00:00Z"},
                        "avg_score": {"value": 0.85},
                        "summaries": {
                            "buckets": [
                                {"key": "讨论投资理财产品"},
                                {"key": "咨询基金收益"}
                            ]
                        },
                        "products": {
                            "buckets": [
                                {"key": "基金"},
                                {"key": "股票"}
                            ]
                        },
                        "industries": {
                            "buckets": [
                                {"key": "金融"},
                                {"key": "科技"}
                            ]
                        },
                        "topics": {
                            "buckets": [
                                {"key": "投资理财"},
                                {"key": "风险管理"}
                            ]
                        },
                        "complaints": {
                            "buckets": [
                                {"key": "收益不达预期"}
                            ]
                        }
                    }
                ]
            }
        }
    }
    return mock_client


@pytest.fixture
def mock_langchain_client():
    """模拟 LangChain 客户端"""
    return MagicMock()


def test_customer_search_basic(mock_es_client, mock_langchain_client):
    """测试基础客户搜索功能"""
    with patch('app.services.es_service.get_es_client', return_value=mock_es_client), \
         patch('app.services.langchain_service.convert_nl_to_es_query', return_value={
             "query": {
                 "bool": {
                     "must": []
                 }
             }
         }):
        
        # 测试数据
        test_query = {
            "query_text": "投资理财产品",
            "advisor_id": "all",
            "start_time": (datetime.now() - timedelta(days=30)).isoformat(),
            "end_time": datetime.now().isoformat(),
            "page": 1,
            "page_size": 10
        }
        
        # 发送请求
        response = client.post("/api/v1/conversations/search_customers", json=test_query)
        
        # 验证响应
        assert response.status_code == 200
        result = response.json()
        
        # 验证返回数据结构
        assert "total" in result
        assert "customers" in result
        assert isinstance(result["customers"], list)
        
        if result["customers"]:
            customer = result["customers"][0]
            assert "customer_id" in customer
            assert "customer_name" in customer
            assert "advisor_id" in customer
            assert "advisor_name" in customer
            assert "conversation_count" in customer
            assert "latest_conversation_time" in customer
            assert "earliest_conversation_time" in customer
            assert "avg_score" in customer
            assert "mentioned_products" in customer
            assert "mentioned_industries" in customer
            assert "mentioned_topics" in customer
            assert "mentioned_complaints" in customer
            assert "conversation_summaries" in customer


def test_customer_search_with_advisor_filter(mock_es_client, mock_langchain_client):
    """测试带顾问筛选的客户搜索"""
    with patch('app.services.es_service.get_es_client', return_value=mock_es_client), \
         patch('app.services.langchain_service.convert_nl_to_es_query', return_value={
             "query": {
                 "bool": {
                     "must": []
                 }
             }
         }):
        
        # 测试数据
        test_query = {
            "query_text": "股票投资",
            "advisor_id": "advisor_001",
            "page": 1,
            "page_size": 5
        }
        
        # 发送请求
        response = client.post("/api/v1/conversations/search_customers", json=test_query)
        
        # 验证响应
        assert response.status_code == 200
        result = response.json()
        assert "total" in result
        assert "customers" in result


def test_customer_search_with_time_range(mock_es_client, mock_langchain_client):
    """测试带时间范围的客户搜索"""
    with patch('app.services.es_service.get_es_client', return_value=mock_es_client), \
         patch('app.services.langchain_service.convert_nl_to_es_query', return_value={
             "query": {
                 "bool": {
                     "must": []
                 }
             }
         }):
        
        # 测试数据
        start_time = datetime.now() - timedelta(days=7)
        end_time = datetime.now()
        
        test_query = {
            "query_text": "基金理财",
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "page": 1,
            "page_size": 5
        }
        
        # 发送请求
        response = client.post("/api/v1/conversations/search_customers", json=test_query)
        
        # 验证响应
        assert response.status_code == 200
        result = response.json()
        assert "total" in result
        assert "customers" in result


def test_customer_search_missing_query_text():
    """测试缺少查询文本的情况"""
    test_query = {
        "page": 1,
        "page_size": 10
    }
    
    # 发送请求
    response = client.post("/api/v1/conversations/search_customers", json=test_query)
    
    # 验证响应 - 应该返回 422 验证错误
    assert response.status_code == 422


def test_customer_search_invalid_page_size():
    """测试无效的分页参数"""
    test_query = {
        "query_text": "投资理财",
        "page": 0,  # 无效的页码
        "page_size": -1  # 无效的页面大小
    }
    
    # 发送请求
    response = client.post("/api/v1/conversations/search_customers", json=test_query)
    
    # 验证响应 - 应该返回 422 验证错误
    assert response.status_code == 422


@patch('app.services.es_service.get_es_client')
def test_customer_search_elasticsearch_error(mock_get_es_client):
    """测试 Elasticsearch 错误处理"""
    # 模拟 Elasticsearch 错误
    mock_es_client = MagicMock()
    mock_es_client.search.side_effect = Exception("Elasticsearch connection failed")
    mock_get_es_client.return_value = mock_es_client
    
    test_query = {
        "query_text": "投资理财",
        "page": 1,
        "page_size": 10
    }
    
    # 发送请求
    response = client.post("/api/v1/conversations/search_customers", json=test_query)
    
    # 验证响应 - 应该返回 500 服务器错误
    assert response.status_code == 500
    assert "搜索客户失败" in response.json()["detail"]