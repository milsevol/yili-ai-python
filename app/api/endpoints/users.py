from typing import List
from fastapi import APIRouter, HTTPException, Depends

from app.schemas.user import UserCreate, UserResponse, UserUpdate

router = APIRouter()


@router.get("/", response_model=List[UserResponse])
async def get_users():
    """获取所有用户"""
    # 这里应该是从数据库获取用户的逻辑
    # 目前返回模拟数据
    return [
        {"id": 1, "username": "user1", "email": "user1@example.com", "is_active": True},
        {"id": 2, "username": "user2", "email": "user2@example.com", "is_active": True},
    ]


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int):
    """获取特定用户"""
    # 这里应该是从数据库获取特定用户的逻辑
    # 目前返回模拟数据
    if user_id not in [1, 2]:
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": user_id, "username": f"user{user_id}", "email": f"user{user_id}@example.com", "is_active": True}


@router.post("/", response_model=UserResponse, status_code=201)
async def create_user(user: UserCreate):
    """创建新用户"""
    # 这里应该是创建用户的逻辑
    # 目前返回模拟数据
    return {"id": 3, "username": user.username, "email": user.email, "is_active": True}


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, user: UserUpdate):
    """更新用户信息"""
    # 这里应该是更新用户的逻辑
    # 目前返回模拟数据
    if user_id not in [1, 2, 3]:
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": user_id, "username": user.username, "email": user.email, "is_active": user.is_active}


@router.delete("/{user_id}", status_code=204)
async def delete_user(user_id: int):
    """删除用户"""
    # 这里应该是删除用户的逻辑
    if user_id not in [1, 2, 3]:
        raise HTTPException(status_code=404, detail="User not found")
    return None