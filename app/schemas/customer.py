from typing import Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime


class CustomerBase(BaseModel):
    """客户基本信息模型"""
    name: str
    email: EmailStr
    phone: str
    address: Optional[str] = None
    vip_level: int = 0  # 0-5，0表示普通客户


class CustomerCreate(CustomerBase):
    """创建客户请求模型"""
    pass


class CustomerUpdate(BaseModel):
    """更新客户请求模型"""
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    vip_level: Optional[int] = None


class CustomerResponse(CustomerBase):
    """客户响应模型"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    total_orders: int = 0
    total_spent: float = 0.0

    class Config:
        from_attributes = True