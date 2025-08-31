from typing import List
from fastapi import APIRouter, HTTPException, Path, Query, status
from datetime import datetime

from app.schemas.order import OrderCreate, OrderResponse, OrderUpdate, OrderItemResponse

router = APIRouter()

# 模拟数据库
order_items_db = [
    {"id": 1, "order_id": 1, "product_id": 1, "quantity": 2, "unit_price": 6999.00, "subtotal": 13998.00},
    {"id": 2, "order_id": 1, "product_id": 3, "quantity": 1, "unit_price": 999.00, "subtotal": 999.00},
    {"id": 3, "order_id": 2, "product_id": 2, "quantity": 1, "unit_price": 4999.00, "subtotal": 4999.00},
]

orders_db = [
    {
        "id": 1,
        "user_id": 1,
        "status": "paid",
        "shipping_address": "北京市海淀区中关村大街1号",
        "payment_method": "支付宝",
        "total_amount": 14997.00,
        "created_at": datetime.now(),
        "updated_at": None
    },
    {
        "id": 2,
        "user_id": 2,
        "status": "shipped",
        "shipping_address": "上海市浦东新区张江高科技园区",
        "payment_method": "微信支付",
        "total_amount": 4999.00,
        "created_at": datetime.now(),
        "updated_at": None
    }
]


@router.get("/", response_model=List[OrderResponse])
async def get_orders(
    skip: int = Query(0, description="跳过的记录数"),
    limit: int = Query(10, description="返回的最大记录数"),
    status: str = Query(None, description="按状态筛选"),
    user_id: int = Query(None, description="按用户ID筛选")
):
    """获取所有订单，支持分页和按状态、用户筛选"""
    filtered_orders = orders_db
    
    if status:
        filtered_orders = [o for o in filtered_orders if o["status"] == status]
    
    if user_id:
        filtered_orders = [o for o in filtered_orders if o["user_id"] == user_id]
    
    result = filtered_orders[skip:skip+limit]
    
    # 为每个订单添加订单项
    for order in result:
        order_items = [item for item in order_items_db if item["order_id"] == order["id"]]
        order["items"] = order_items
    
    return result


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(order_id: int = Path(..., description="订单ID")):
    """获取特定订单"""
    for order in orders_db:
        if order["id"] == order_id:
            # 添加订单项
            order_items = [item for item in order_items_db if item["order_id"] == order_id]
            order_copy = dict(order)
            order_copy["items"] = order_items
            return order_copy
    
    raise HTTPException(status_code=404, detail="订单不存在")


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(order: OrderCreate):
    """创建新订单"""
    # 模拟创建新订单
    new_order = order.dict(exclude={"items"})
    new_order["id"] = max(o["id"] for o in orders_db) + 1 if orders_db else 1
    new_order["created_at"] = datetime.now()
    new_order["updated_at"] = None
    
    # 计算订单总金额并创建订单项
    total_amount = 0
    new_order_items = []
    
    for i, item in enumerate(order.items):
        # 在实际应用中，这里会从数据库获取产品价格
        # 这里使用模拟价格
        product_price = 0
        if item.product_id == 1:
            product_price = 6999.00
        elif item.product_id == 2:
            product_price = 4999.00
        elif item.product_id == 3:
            product_price = 999.00
        else:
            product_price = item.unit_price
        
        subtotal = product_price * item.quantity
        total_amount += subtotal
        
        new_item = item.dict()
        new_item["id"] = max(i["id"] for i in order_items_db) + 1 + i if order_items_db else 1 + i
        new_item["order_id"] = new_order["id"]
        new_item["unit_price"] = product_price
        new_item["subtotal"] = subtotal
        
        new_order_items.append(new_item)
    
    new_order["total_amount"] = total_amount
    
    # 在实际应用中，这里会将订单和订单项保存到数据库
    orders_db.append(new_order)
    order_items_db.extend(new_order_items)
    
    # 返回完整订单信息
    result = dict(new_order)
    result["items"] = new_order_items
    
    return result


@router.put("/{order_id}", response_model=OrderResponse)
async def update_order(order_id: int, order: OrderUpdate):
    """更新订单信息"""
    for i, o in enumerate(orders_db):
        if o["id"] == order_id:
            # 更新非空字段
            update_data = order.dict(exclude_unset=True)
            updated_order = {**o, **update_data, "updated_at": datetime.now()}
            orders_db[i] = updated_order
            
            # 添加订单项
            order_items = [item for item in order_items_db if item["order_id"] == order_id]
            result = dict(updated_order)
            result["items"] = order_items
            
            return result
    
    raise HTTPException(status_code=404, detail="订单不存在")


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_order(order_id: int):
    """删除订单"""
    for i, o in enumerate(orders_db):
        if o["id"] == order_id:
            # 在实际应用中，这里会从数据库中删除订单和相关订单项
            orders_db.pop(i)
            
            # 删除相关订单项
            global order_items_db
            order_items_db = [item for item in order_items_db if item["order_id"] != order_id]
            
            return
    
    raise HTTPException(status_code=404, detail="订单不存在")