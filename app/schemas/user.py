from typing import Optional
from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    """用户基本信息模型"""
    username: str
    email: EmailStr
    is_active: Optional[bool] = True


class UserCreate(UserBase):
    """创建用户请求模型"""
    password: str


class UserUpdate(BaseModel):
    """更新用户请求模型"""
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    """用户响应模型"""
    id: int

    class Config:
        from_attributes = True