from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class Message(BaseModel):
    """会话消息模型"""
    sender_type: str = Field(..., description="发送者类型：customer/advisor")
    sender_id: str = Field(..., description="发送者ID")
    sender_name: str = Field(..., description="发送者姓名")
    content: str = Field(..., description="消息内容")
    send_time: datetime = Field(..., description="发送时间")
    message_type: str = Field("text", description="消息类型：text/image/file等")


class Entity(BaseModel):
    """提取的实体模型"""
    entity_type: str = Field(..., description="实体类型：product/industry/topic/emotion等")
    entity_value: str = Field(..., description="实体值")
    confidence: float = Field(..., description="置信度")
    positions: List[Dict[str, int]] = Field(default_factory=list, description="在会话中的位置")


class Sentiment(BaseModel):
    """情感分析结果模型"""
    message_index: int = Field(..., description="对应消息索引")
    sentiment_type: str = Field(..., description="情感类型：positive/negative/neutral")
    sentiment_score: float = Field(..., description="情感分数")


class Conversation(BaseModel):
    """会话模型"""
    conversation_id: str = Field(..., description="会话ID")
    customer_id: str = Field(..., description="客户ID")
    customer_name: str = Field(..., description="客户姓名")
    advisor_id: str = Field(..., description="财富顾问ID")
    advisor_name: str = Field(..., description="财富顾问姓名")
    conversation_time: datetime = Field(..., description="会话时间")
    full_content: str = Field(..., description="完整会话内容")
    messages: List[Message] = Field(default_factory=list, description="会话消息数组")
    summary: str = Field("", description="会话摘要")
    extracted_entities: List[Entity] = Field(default_factory=list, description="提取的实体")
    sentiment: List[Sentiment] = Field(default_factory=list, description="情感分析结果")
    mentioned_products: List[str] = Field(default_factory=list, description="提及的产品")
    mentioned_industries: List[str] = Field(default_factory=list, description="提及的行业")
    mentioned_topics: List[str] = Field(default_factory=list, description="提及的话题")
    mentioned_complaints: List[str] = Field(default_factory=list, description="提及的问题/抱怨")
    conversation_tags: List[str] = Field(default_factory=list, description="会话标签")
    content_vector: Optional[List[float]] = Field(None, description="会话向量表示")


class ConversationSearchQuery(BaseModel):
    """会话搜索查询参数"""
    query_text: str = Field(..., description="自然语言查询文本")
    advisor_id: Optional[str] = Field(None, description="财富顾问ID，为'all'时表示所有顾问")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    page: int = Field(1, description="页码，从1开始")
    page_size: int = Field(10, description="每页数量")


class ConversationResult(BaseModel):
    """会话搜索结果项"""
    conversation_id: str
    customer_id: str
    customer_name: str
    advisor_id: str
    advisor_name: str
    conversation_time: datetime
    summary: str
    highlight: Dict[str, List[str]] = Field(default_factory=dict)
    score: float


class ConversationSearchResult(BaseModel):
    """会话搜索结果"""
    total: int
    conversations: List[ConversationResult]


class InsightTerm(BaseModel):
    """洞察词项"""
    term: str
    count: int


class ConversationInsights(BaseModel):
    """会话洞察结果"""
    topics: List[InsightTerm]
    industries: List[InsightTerm]
    products: List[InsightTerm]
    complaints: List[InsightTerm]


class CustomerResult(BaseModel):
    """客户搜索结果项"""
    customer_id: str
    customer_name: str
    advisor_id: str
    advisor_name: str
    conversation_count: int = Field(..., description="会话数量")
    latest_conversation_time: datetime = Field(..., description="最新会话时间")
    earliest_conversation_time: datetime = Field(..., description="最早会话时间")
    conversation_summaries: List[str] = Field(default_factory=list, description="会话摘要列表")
    mentioned_products: List[str] = Field(default_factory=list, description="提及的产品")
    mentioned_industries: List[str] = Field(default_factory=list, description="提及的行业")
    mentioned_topics: List[str] = Field(default_factory=list, description="提及的话题")
    mentioned_complaints: List[str] = Field(default_factory=list, description="提及的问题/抱怨")
    avg_score: float = Field(..., description="平均相关性评分")


class CustomerSearchResult(BaseModel):
    """客户搜索结果"""
    total: int
    customers: List[CustomerResult]


class CustomerVectorSearchQuery(BaseModel):
    """客户向量搜索查询参数"""
    query_text: str = Field(..., description="自然语言查询文本，用于语义搜索")
    advisor_id: Optional[str] = Field(None, description="财富顾问ID，为'all'时表示所有顾问")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    page: int = Field(1, description="页码，从1开始")
    page_size: int = Field(10, description="每页数量")
    similarity_threshold: float = Field(0.3, description="相似度阈值，范围0-1，降低阈值以获得更多相关结果")
    k: int = Field(50, description="kNN搜索返回的候选数量")


class CustomerVectorResult(BaseModel):
    """客户向量搜索结果项"""
    customer_id: str
    customer_name: str
    advisor_id: str
    advisor_name: str
    conversation_count: int = Field(..., description="会话数量")
    latest_conversation_time: datetime = Field(..., description="最新会话时间")
    earliest_conversation_time: datetime = Field(..., description="最早会话时间")
    conversation_summaries: List[str] = Field(default_factory=list, description="会话摘要列表")
    mentioned_products: List[str] = Field(default_factory=list, description="提及的产品")
    mentioned_industries: List[str] = Field(default_factory=list, description="提及的行业")
    mentioned_topics: List[str] = Field(default_factory=list, description="提及的话题")
    mentioned_complaints: List[str] = Field(default_factory=list, description="提及的问题/抱怨")
    similarity_score: float = Field(..., description="语义相似度评分")
    matched_conversations: List[str] = Field(default_factory=list, description="匹配的会话ID列表")


class CustomerVectorSearchResult(BaseModel):
    """客户向量搜索结果"""
    total: int
    customers: List[CustomerVectorResult]
    query_info: Optional[Dict[str, Any]] = Field(None, description="查询信息")