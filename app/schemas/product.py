from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class ProductBase(BaseModel):
    """产品基本信息模型"""
    name: str
    description: Optional[str] = None
    price: float
    stock: int = 0
    category: str


class ProductCreate(ProductBase):
    """创建产品请求模型"""
    pass


class ProductUpdate(BaseModel):
    """更新产品请求模型"""
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[int] = None
    category: Optional[str] = None


class ProductResponse(ProductBase):
    """产品响应模型"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True