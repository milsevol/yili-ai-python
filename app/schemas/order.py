from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime


class OrderItemBase(BaseModel):
    """订单项基本信息模型"""
    product_id: int
    quantity: int
    unit_price: float


class OrderItemCreate(OrderItemBase):
    """创建订单项请求模型"""
    pass


class OrderItemResponse(OrderItemBase):
    """订单项响应模型"""
    id: int
    subtotal: float

    class Config:
        from_attributes = True


class OrderBase(BaseModel):
    """订单基本信息模型"""
    user_id: int
    status: str = "pending"  # pending, paid, shipped, delivered, cancelled
    shipping_address: str
    payment_method: str


class OrderCreate(OrderBase):
    """创建订单请求模型"""
    items: List[OrderItemCreate]


class OrderUpdate(BaseModel):
    """更新订单请求模型"""
    status: Optional[str] = None
    shipping_address: Optional[str] = None
    payment_method: Optional[str] = None


class OrderResponse(OrderBase):
    """订单响应模型"""
    id: int
    items: List[OrderItemResponse]
    total_amount: float
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True