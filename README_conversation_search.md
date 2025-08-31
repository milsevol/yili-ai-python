# 会话客群搜索和业务洞察功能

本文档介绍如何使用会话客群搜索和业务洞察功能。

## 功能概述

该功能主要包含两个核心部分：

1. **会话客群搜索**：通过自然语言查询或结构化条件筛选客户会话，支持基于会话内容的精准筛选。
2. **业务洞察**：对会话内容进行分析，生成热点话题、行业、产品、投诉等词云，帮助理解客户关注点。

## 技术实现

- **Elasticsearch**：用于存储和索引会话数据，支持全文搜索和结构化查询
- **DeepSeek**：用于自然语言处理，包括实体提取、情感分析、会话摘要和向量生成
- **FastAPI**：提供RESTful API接口

## API接口

### 1. 会话搜索

```
POST /api/v1/conversations/search
```

请求参数：

```json
{
  "query_text": "客户对哪些产品感兴趣",  // 自然语言查询
  "advisor_id": "adv001",           // 可选，财富顾问ID
  "start_time": "2023-01-01T00:00:00", // 可选，开始时间
  "end_time": "2023-12-31T23:59:59",   // 可选，结束时间
  "page": 1,                        // 页码
  "page_size": 10                   // 每页数量
}
```

响应：

```json
{
  "total": 100,                     // 总匹配数量
  "conversations": [                // 会话列表
    {
      "conversation_id": "conv001",
      "customer_id": "cust001",
      "customer_name": "客户001",
      "advisor_id": "adv001",
      "advisor_name": "顾问001",
      "conversation_time": "2023-05-01T10:30:00",
      "summary": "客户咨询科技类基金产品，对风险适中的固收+产品表示兴趣",
      "highlight": {                 // 高亮片段
        "full_content": [
          "我想了解一下最近的<em>基金产品</em>，特别是科技类的"
        ]
      },
      "score": 0.85                 // 相关性得分
    }
  ]
}
```

### 2. 业务洞察

```
GET /api/v1/conversations/insights
```

请求参数：

```
advisor_id: adv001                 // 可选，财富顾问ID
start_date: 2023-01-01              // 可选，开始日期
end_date: 2023-12-31                // 可选，结束日期
custom_query: 基金产品              // 可选，自定义查询
```

响应：

```json
{
  "topics": [                       // 热点话题
    { "term": "基金", "count": 50 },
    { "term": "理财", "count": 35 },
    { "term": "投资", "count": 30 }
  ],
  "industries": [                   // 行业
    { "term": "科技", "count": 40 },
    { "term": "医疗", "count": 25 },
    { "term": "消费", "count": 20 }
  ],
  "products": [                     // 产品
    { "term": "科技创新混合型基金", "count": 30 },
    { "term": "固收+产品", "count": 25 },
    { "term": "稳健理财产品", "count": 20 }
  ],
  "complaints": [                   // 投诉
    { "term": "收益低", "count": 15 },
    { "term": "风险高", "count": 10 },
    { "term": "费率高", "count": 5 }
  ]
}
```

## 使用示例

可以参考 `examples/conversation_search_demo.py` 文件，该文件演示了如何：

1. 创建和索引示例会话数据
2. 使用自然语言查询搜索会话
3. 获取会话洞察数据

运行示例：

```bash
python examples/conversation_search_demo.py
```

## 注意事项

1. 确保Elasticsearch服务已启动并可访问
2. 确保DeepSeek API密钥已正确配置
3. 首次使用时会自动创建必要的索引