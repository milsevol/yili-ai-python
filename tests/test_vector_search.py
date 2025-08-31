import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock

from main import app

client = TestClient(app)


@pytest.fixture
def mock_es_client():
    """模拟 Elasticsearch 客户端"""
    mock_client = MagicMock()
    # 模拟向量搜索结果
    mock_client.search.return_value = {
        "hits": {
            "hits": [
                {
                    "_score": 0.85,
                    "_source": {
                        "customer_id": "customer_001",
                        "customer_name": "张三",
                        "advisor_id": "advisor_001",
                        "advisor_name": "李顾问",
                        "conversation_id": "conv_001",
                        "conversation_time": "2024-01-15T10:30:00Z",
                        "summary": "讨论投资理财产品",
                        "mentioned_products": ["基金", "股票"],
                        "mentioned_industries": ["金融"],
                        "mentioned_topics": ["投资", "理财"],
                        "mentioned_complaints": []
                    }
                },
                {
                    "_score": 0.78,
                    "_source": {
                        "customer_id": "customer_002",
                        "customer_name": "李四",
                        "advisor_id": "advisor_002",
                        "advisor_name": "王顾问",
                        "conversation_id": "conv_002",
                        "conversation_time": "2024-01-14T14:20:00Z",
                        "summary": "咨询保险产品",
                        "mentioned_products": ["保险"],
                        "mentioned_industries": ["保险"],
                        "mentioned_topics": ["保障", "风险"],
                        "mentioned_complaints": ["理赔慢"]
                    }
                }
            ],
            "total": {"value": 2}
        }
    }
    return mock_client


@pytest.fixture
def mock_langchain_client():
    """模拟 LangChain 客户端"""
    mock_client = {
        "embedding_model": MagicMock()
    }
    # 模拟向量生成
    mock_client["embedding_model"].aembed_query = AsyncMock(
        return_value=[0.1, 0.2, 0.3] * 341 + [0.1]  # 1024维向量
    )
    return mock_client


class TestVectorSearchCustomers:
    """客户向量搜索接口测试"""

    @patch('app.services.es_service.get_es_client')
    @patch('app.services.langchain_service.get_langchain_client')
    def test_vector_search_customers_success(self, mock_langchain_dep, mock_es_dep, 
                                           mock_es_client, mock_langchain_client):
        """测试向量搜索客户成功"""
        mock_es_dep.return_value = mock_es_client
        mock_langchain_dep.return_value = mock_langchain_client
        
        # 测试数据
        query_data = {
            "query_text": "投资理财产品",
            "advisor_id": "advisor_001",
            "page": 1,
            "page_size": 10,
            "similarity_threshold": 0.7,
            "k": 50
        }
        
        response = client.post("/api/v1/conversations/vector-search-customers", json=query_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # 验证响应结构
        assert "total" in data
        assert "customers" in data
        assert "query_info" in data
        
        # 验证查询信息
        assert data["query_info"]["query_text"] == "投资理财产品"
        assert data["query_info"]["similarity_threshold"] == 0.7
        assert data["query_info"]["k"] == 50
        assert data["query_info"]["vector_dimension"] == 1024
        
        # 验证客户数据
        assert data["total"] >= 0
        if data["customers"]:
            customer = data["customers"][0]
            assert "customer_id" in customer
            assert "customer_name" in customer
            assert "advisor_id" in customer
            assert "advisor_name" in customer
            assert "conversation_count" in customer
            assert "similarity_score" in customer
            assert "matched_conversations" in customer

    @patch('app.services.es_service.get_es_client')
    @patch('app.services.langchain_service.get_langchain_client')
    def test_vector_search_customers_with_time_filter(self, mock_langchain_dep, mock_es_dep,
                                                     mock_es_client, mock_langchain_client):
        """测试带时间过滤的向量搜索"""
        mock_es_dep.return_value = mock_es_client
        mock_langchain_dep.return_value = mock_langchain_client
        
        # 测试数据
        start_time = datetime.now() - timedelta(days=30)
        end_time = datetime.now()
        
        query_data = {
            "query_text": "保险产品咨询",
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "page": 1,
            "page_size": 5,
            "similarity_threshold": 0.8,
            "k": 30
        }
        
        response = client.post("/api/v1/conversations/vector-search-customers", json=query_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # 验证时间过滤参数传递
        mock_es_client.search.assert_called_once()
        call_args = mock_es_client.search.call_args
        
        # 验证kNN查询结构
        assert "knn" in call_args[1]["body"]
        knn_query = call_args[1]["body"]["knn"]
        assert knn_query["field"] == "content_vector"
        assert knn_query["k"] == 30
        assert len(knn_query["query_vector"]) == 1024

    @patch('app.services.es_service.get_es_client')
    @patch('app.services.langchain_service.get_langchain_client')
    def test_vector_search_customers_pagination(self, mock_langchain_dep, mock_es_dep,
                                              mock_es_client, mock_langchain_client):
        """测试向量搜索分页功能"""
        mock_es_dep.return_value = mock_es_client
        mock_langchain_dep.return_value = mock_langchain_client
        
        # 测试数据
        query_data = {
            "query_text": "客户服务问题",
            "page": 2,
            "page_size": 5,
            "similarity_threshold": 0.6,
            "k": 20
        }
        
        response = client.post("/api/v1/conversations/vector-search-customers", json=query_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # 验证分页参数
        assert len(data["customers"]) <= 5  # 每页最多5条

    @patch('app.services.es_service.get_es_client')
    @patch('app.services.langchain_service.get_langchain_client')
    def test_vector_search_customers_embedding_failure(self, mock_langchain_dep, mock_es_dep,
                                                      mock_es_client):
        """测试向量生成失败的情况"""
        mock_es_dep.return_value = mock_es_client
        
        # 模拟向量生成失败
        mock_langchain_client = {
            "embedding_model": MagicMock()
        }
        mock_langchain_client["embedding_model"].aembed_query = AsyncMock(return_value=None)
        mock_langchain_dep.return_value = mock_langchain_client
        
        query_data = {
            "query_text": "测试查询",
            "page": 1,
            "page_size": 10
        }
        
        response = client.post("/api/v1/conversations/vector-search-customers", json=query_data)
        
        assert response.status_code == 400
        assert "无法生成查询向量" in response.json()["detail"]

    def test_vector_search_customers_invalid_params(self):
        """测试无效参数"""
        # 缺少必需参数
        query_data = {
            "page": 1,
            "page_size": 10
        }
        
        response = client.post("/api/v1/conversations/vector-search-customers", json=query_data)
        
        assert response.status_code == 422  # 参数验证失败

    def test_vector_search_customers_invalid_similarity_threshold(self):
        """测试无效的相似度阈值"""
        query_data = {
            "query_text": "测试查询",
            "similarity_threshold": 1.5,  # 超出范围
            "page": 1,
            "page_size": 10
        }
        
        response = client.post("/api/v1/conversations/vector-search-customers", json=query_data)
        
        assert response.status_code == 422  # 参数验证失败

    @patch('app.services.es_service.get_es_client')
    @patch('app.services.langchain_service.get_langchain_client')
    def test_vector_search_customers_es_error(self, mock_langchain_dep, mock_es_dep,
                                             mock_langchain_client):
        """测试Elasticsearch错误"""
        mock_langchain_dep.return_value = mock_langchain_client
        
        # 模拟ES搜索失败
        mock_es_client = MagicMock()
        mock_es_client.search.side_effect = Exception("ES连接失败")
        mock_es_dep.return_value = mock_es_client
        
        query_data = {
            "query_text": "测试查询",
            "page": 1,
            "page_size": 10
        }
        
        response = client.post("/api/v1/conversations/vector-search-customers", json=query_data)
        
        assert response.status_code == 500
        assert "向量搜索客户失败" in response.json()["detail"]