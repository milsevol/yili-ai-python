from typing import List
from fastapi import APIRouter, HTTPException, Path, Query, status
from datetime import datetime

from app.schemas.customer import CustomerCreate, CustomerResponse, CustomerUpdate

router = APIRouter()

# 模拟数据库
customers_db = [
    {
        "id": 1,
        "name": "张三",
        "email": "zhangsan@example.com",
        "phone": "13800138001",
        "address": "北京市朝阳区建国路1号",
        "vip_level": 3,
        "created_at": datetime.now(),
        "updated_at": None,
        "total_orders": 5,
        "total_spent": 25000.00
    },
    {
        "id": 2,
        "name": "李四",
        "email": "lisi@example.com",
        "phone": "13900139002",
        "address": "上海市黄浦区南京路123号",
        "vip_level": 1,
        "created_at": datetime.now(),
        "updated_at": None,
        "total_orders": 2,
        "total_spent": 8000.00
    },
    {
        "id": 3,
        "name": "王五",
        "email": "wangwu@example.com",
        "phone": "13700137003",
        "address": "广州市天河区天河路456号",
        "vip_level": 0,
        "created_at": datetime.now(),
        "updated_at": None,
        "total_orders": 1,
        "total_spent": 2000.00
    }
]


@router.get("/", response_model=List[CustomerResponse])
async def get_customers(
    skip: int = Query(0, description="跳过的记录数"),
    limit: int = Query(10, description="返回的最大记录数"),
    vip_level: int = Query(None, description="按VIP等级筛选"),
    search: str = Query(None, description="按名称或邮箱搜索")
):
    """获取所有客户，支持分页、按VIP等级筛选和搜索"""
    filtered_customers = customers_db
    
    if vip_level is not None:
        filtered_customers = [c for c in filtered_customers if c["vip_level"] == vip_level]
    
    if search:
        search = search.lower()
        filtered_customers = [c for c in filtered_customers if 
                            search in c["name"].lower() or 
                            search in c["email"].lower()]
    
    return filtered_customers[skip:skip+limit]


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(customer_id: int = Path(..., description="客户ID")):
    """获取特定客户"""
    for customer in customers_db:
        if customer["id"] == customer_id:
            return customer
    
    raise HTTPException(status_code=404, detail="客户不存在")


@router.post("/", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(customer: CustomerCreate):
    """创建新客户"""
    # 检查邮箱是否已存在
    if any(c["email"] == customer.email for c in customers_db):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该邮箱已被注册"
        )
    
    # 模拟创建新客户
    new_customer = customer.dict()
    new_customer["id"] = max(c["id"] for c in customers_db) + 1 if customers_db else 1
    new_customer["created_at"] = datetime.now()
    new_customer["updated_at"] = None
    new_customer["total_orders"] = 0
    new_customer["total_spent"] = 0.0
    
    customers_db.append(new_customer)
    
    return new_customer


@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(customer_id: int, customer: CustomerUpdate):
    """更新客户信息"""
    for i, c in enumerate(customers_db):
        if c["id"] == customer_id:
            # 检查邮箱是否已被其他用户使用
            if customer.email and customer.email != c["email"] and \
               any(other["email"] == customer.email for other in customers_db if other["id"] != customer_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="该邮箱已被其他客户注册"
                )
            
            # 更新非空字段
            update_data = customer.dict(exclude_unset=True)
            updated_customer = {**c, **update_data, "updated_at": datetime.now()}
            customers_db[i] = updated_customer
            
            return updated_customer
    
    raise HTTPException(status_code=404, detail="客户不存在")


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_customer(customer_id: int):
    """删除客户"""
    for i, c in enumerate(customers_db):
        if c["id"] == customer_id:
            customers_db.pop(i)
            return
    
    raise HTTPException(status_code=404, detail="客户不存在")