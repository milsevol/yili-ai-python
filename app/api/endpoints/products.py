from typing import List
from fastapi import APIRouter, HTTPException, Path, Query
from datetime import datetime

from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate

router = APIRouter()

# 模拟数据库
products_db = [
    {
        "id": 1,
        "name": "笔记本电脑",
        "description": "高性能笔记本电脑，适合办公和游戏",
        "price": 6999.00,
        "stock": 100,
        "category": "电子产品",
        "created_at": datetime.now(),
        "updated_at": None
    },
    {
        "id": 2,
        "name": "智能手机",
        "description": "最新款智能手机，拍照性能出色",
        "price": 4999.00,
        "stock": 200,
        "category": "电子产品",
        "created_at": datetime.now(),
        "updated_at": None
    },
    {
        "id": 3,
        "name": "无线耳机",
        "description": "高音质无线蓝牙耳机",
        "price": 999.00,
        "stock": 300,
        "category": "配件",
        "created_at": datetime.now(),
        "updated_at": None
    }
]


@router.get("/", response_model=List[ProductResponse])
async def get_products(
    skip: int = Query(0, description="跳过的记录数"),
    limit: int = Query(10, description="返回的最大记录数"),
    category: str = Query(None, description="按类别筛选")
):
    """获取所有产品，支持分页和按类别筛选"""
    if category:
        filtered_products = [p for p in products_db if p["category"] == category]
    else:
        filtered_products = products_db
    
    return filtered_products[skip:skip+limit]


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int = Path(..., description="产品ID")):
    """获取特定产品"""
    for product in products_db:
        if product["id"] == product_id:
            return product
    raise HTTPException(status_code=404, detail="产品不存在")


@router.post("/", response_model=ProductResponse, status_code=201)
async def create_product(product: ProductCreate):
    """创建新产品"""
    # 模拟创建新产品
    new_product = product.dict()
    new_product["id"] = max(p["id"] for p in products_db) + 1 if products_db else 1
    new_product["created_at"] = datetime.now()
    new_product["updated_at"] = None
    
    # 在实际应用中，这里会将产品保存到数据库
    products_db.append(new_product)
    
    return new_product


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(product_id: int, product: ProductUpdate):
    """更新产品信息"""
    for i, p in enumerate(products_db):
        if p["id"] == product_id:
            # 更新非空字段
            update_data = product.dict(exclude_unset=True)
            updated_product = {**p, **update_data, "updated_at": datetime.now()}
            products_db[i] = updated_product
            return updated_product
    
    raise HTTPException(status_code=404, detail="产品不存在")


@router.delete("/{product_id}", status_code=204)
async def delete_product(product_id: int):
    """删除产品"""
    for i, p in enumerate(products_db):
        if p["id"] == product_id:
            # 在实际应用中，这里会从数据库中删除产品
            products_db.pop(i)
            return
    
    raise HTTPException(status_code=404, detail="产品不存在")