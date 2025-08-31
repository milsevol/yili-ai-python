# LangChain迁移指南

## 概述

本项目已从DeepSeek服务迁移到LangChain框架，以支持使用OpenAI模型进行会话搜索和业务洞察功能。本文档提供了迁移的主要变更和使用说明。

## 主要变更

1. 将`deepseek_service.py`替换为`langchain_service.py`
2. 更新了`conversation_search.py`中的API接口，使用LangChain客户端替代DeepSeek客户端
3. 更新了`conversation_search_demo.py`示例代码
4. 更新了配置文件，将DeepSeek API Key配置改为OpenAI API Key配置
5. 更新了`requirements.txt`，添加了LangChain相关依赖

## 配置说明

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置OpenAI API Key

在`配置说明.md`文件中设置您的OpenAI API Key：

```
## openai配置
api-key:your-openai-api-key
```

### 3. 配置Elasticsearch

确保Elasticsearch 7.17.0已正确安装和配置：

```
## es配置说明
ip:localhost,port:9200
```

## 功能说明

### 1. LangChain服务

`app/services/langchain_service.py`提供以下功能：

- `get_langchain_client()`: 创建LangChain客户端
- `extract_conversation_entities()`: 从会话中提取实体
- `generate_conversation_summary()`: 生成会话摘要
- `analyze_conversation_sentiment()`: 分析会话情感
- `generate_conversation_vector()`: 生成会话向量
- `process_conversation()`: 处理会话数据
- `convert_nl_to_es_query()`: 将自然语言查询转换为Elasticsearch查询

### 2. API接口

`app/api/endpoints/conversation_search.py`提供以下API接口：

- `/search`: 根据自然语言查询搜索会话内容
- `/insights`: 获取会话洞察数据

## 使用示例

### 运行示例代码

```bash
python examples/conversation_search_demo.py
```

示例代码演示了：

1. 创建示例会话数据
2. 使用LangChain处理会话数据（实体提取、摘要、情感分析）
3. 将处理后的数据索引到Elasticsearch
4. 执行自然语言搜索
5. 获取会话洞察数据

## 模型配置

当前配置使用以下OpenAI模型：

- 聊天模型：`gpt-3.5-turbo`
- 嵌入模型：`text-embedding-ada-002`

如需使用其他模型，请修改`langchain_service.py`中的相关配置。

## 注意事项

1. 确保您有足够的OpenAI API额度
2. 处理大量会话数据时，请注意API调用频率限制
3. Elasticsearch 7.17.0与之前版本的API可能有所不同，请确保兼容性