from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, validator

class DemoPostForm(BaseModel):
    """demo模型 - 基本表单示例"""
    name: str
    description: Optional[str] = None
    price: float
    txt: float

class DemoItem(BaseModel):
    """商品模型 - 请求体验证示例"""
    name: str
    description: Optional[str] = None
    price: float = Field(..., gt=0, description="商品价格，必须大于0")
    tax: Optional[float] = Field(None, ge=0, description="税费，必须大于等于0")
    tags: List[str] = Field(default_factory=list, description="标签列表")
    
    @validator('name')
    def name_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('名称不能为空')
        return v.strip()

class DemoResponse(BaseModel):
    """响应模型示例"""
    id: int
    name: str
    description: Optional[str] = None
    price: float
    tax: Optional[float] = None
    tags: List[str] = []
    created_at: str
    
    class Config:
        schema_extra = {
            "example": {
                "id": 123,
                "name": "示例商品",
                "description": "这是一个示例商品描述",
                "price": 99.9,
                "tax": 9.99,
                "tags": ["示例", "商品"],
                "created_at": "2023-01-01T12:00:00"
            }
        }

class DemoUpdate(BaseModel):
    """更新模型示例"""
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0, description="商品价格，必须大于0")
    
    class Config:
        # 允许部分更新
        extra = "forbid"  # 禁止额外字段