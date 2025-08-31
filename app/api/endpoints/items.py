from typing import List
from fastapi import APIRouter, HTTPException, Depends

from app.schemas.item import ItemCreate, ItemResponse, ItemUpdate

router = APIRouter()


@router.get("/", response_model=List[ItemResponse])
async def get_items():
    """获取所有项目"""
    # 这里应该是从数据库获取项目的逻辑
    # 目前返回模拟数据
    return [
        {"id": 1, "title": "Item 1", "description": "Description for Item 1", "owner_id": 1},
        {"id": 2, "title": "Item 2", "description": "Description for Item 2", "owner_id": 1},
    ]


@router.get("/{item_id}", response_model=ItemResponse)
async def get_item(item_id: int):
    """获取特定项目"""
    # 这里应该是从数据库获取特定项目的逻辑
    # 目前返回模拟数据
    if item_id not in [1, 2]:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"id": item_id, "title": f"Item {item_id}", "description": f"Description for Item {item_id}", "owner_id": 1}


@router.post("/", response_model=ItemResponse, status_code=201)
async def create_item(item: ItemCreate):
    """创建新项目"""
    # 这里应该是创建项目的逻辑
    # 目前返回模拟数据
    return {"id": 3, "title": item.title, "description": item.description, "owner_id": item.owner_id}


@router.put("/{item_id}", response_model=ItemResponse)
async def update_item(item_id: int, item: ItemUpdate):
    """更新项目信息"""
    # 这里应该是更新项目的逻辑
    # 目前返回模拟数据
    if item_id not in [1, 2, 3]:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"id": item_id, "title": item.title, "description": item.description, "owner_id": item.owner_id}


@router.delete("/{item_id}", status_code=204)
async def delete_item(item_id: int):
    """删除项目"""
    # 这里应该是删除项目的逻辑
    if item_id not in [1, 2, 3]:
        raise HTTPException(status_code=404, detail="Item not found")
    return None