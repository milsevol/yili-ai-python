from typing import Optional
from pydantic import BaseModel


class ItemBase(BaseModel):
    """项目基本信息模型"""
    title: str
    description: Optional[str] = None
    owner_id: int


class ItemCreate(ItemBase):
    """创建项目请求模型"""
    pass


class ItemUpdate(BaseModel):
    """更新项目请求模型"""
    title: Optional[str] = None
    description: Optional[str] = None
    owner_id: Optional[int] = None


class ItemResponse(ItemBase):
    """项目响应模型"""
    id: int

    class Config:
        from_attributes = True