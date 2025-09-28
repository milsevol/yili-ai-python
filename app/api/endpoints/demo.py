from fastapi import APIRouter, HTTPException, Query, Path, Body, Depends, status
from typing import List, Optional, Dict, Any
from app.schemas.demo import DemoPostForm, DemoItem, DemoUpdate,DemoResponse
from fastapi.responses import StreamingResponse
import asyncio  # 需要导入asyncio模块
router = APIRouter()

# 基础示例 - 简单GET请求
@router.get("/demo01")
async def demo01():
    """获取示例数据
    
    这个接口返回一个包含id和name的示例数据列表
    
    - **return**: 包含id和name的数据列表
    """
    return [
        {
            "id": "jj",
            "name": "tt"
        }
    ]

# 路径参数示例
@router.get("/items/{item_id}")
async def read_item(item_id: int):
    """路径参数示例
    
    演示如何使用路径参数获取特定ID的项目
    
    - **item_id**: 项目ID，必须是整数
    - **return**: 包含ID的项目信息
    """
    return {"item_id": item_id, "name": f"Item {item_id}"}

# 查询参数示例
@router.get("/query")
async def query_items(
    skip: int = 0, 
    limit: int = 10, 
    q: Optional[str] = None
):
    """查询参数示例
    
    演示如何使用查询参数过滤和分页
    
    - **skip**: 跳过的记录数，默认为0
    - **limit**: 返回的最大记录数，默认为10
    - **q**: 可选的搜索关键词
    - **return**: 查询结果
    """
    result = {"skip": skip, "limit": limit, "items": []}
    for i in range(skip, skip + limit):
        item = {"id": i, "name": f"Item {i}"}
        if q:
            item["matched"] = q in item["name"]
        result["items"].append(item)
    
    if q:
        result["search_term"] = q
    
    return result

# 增强的查询参数验证
@router.get("/validated-query")
async def validated_query(
    q: str = Query(None, min_length=3, max_length=50, description="搜索关键词"),
    page: int = Query(1, ge=1, description="页码，从1开始"),
    size: int = Query(10, ge=1, le=100, description="每页记录数")
):
    """增强的查询参数验证
    
    演示如何使用Query对查询参数进行验证
    
    - **q**: 搜索关键词，长度在3-50之间
    - **page**: 页码，必须大于等于1
    - **size**: 每页记录数，必须在1-100之间
    - **return**: 验证后的查询参数
    """
    return {
        "query": q,
        "pagination": {
            "page": page,
            "size": size,
            "offset": (page - 1) * size
        }
    }

# 增强的路径参数验证
@router.get("/items/{item_id}/details")
async def item_details(
    item_id: int = Path(..., ge=1, description="项目ID，必须大于等于1")
):
    """增强的路径参数验证
    
    演示如何使用Path对路径参数进行验证
    
    - **item_id**: 项目ID，必须大于等于1
    - **return**: 项目详情
    """
    return {
        "item_id": item_id,
        "name": f"Item {item_id}",
        "description": f"This is a detailed description of item {item_id}"
    }

# 基本POST请求示例
@router.post("/post01")
async def post01(item: DemoPostForm):
    """post请求示例
    
    这个接口演示post请求，以及参数校验
    
    - **item**: DemoPostForm对象
    - **return**: DemoPostForm对象
    """
    return item

# 请求体验证示例
@router.post("/items/", response_model=DemoResponse, status_code=status.HTTP_201_CREATED)
async def create_item(item: DemoItem):
    """请求体验证示例
    
    演示如何验证请求体并使用响应模型
    
    - **item**: DemoItem对象
    - **return**: 创建的项目信息，使用DemoResponse模型
    """
    # 模拟数据库操作
    created_item = {
        "id": 123,
        "name": item.name,
        "description": item.description,
        "price": item.price,
        "tax": item.tax,
        "tags": item.tags,
        "created_at": "2023-01-01T12:00:00"
    }
    return created_item

# 多个请求体参数示例
@router.put("/items/{item_id}")
async def update_item(
    item_id: int,
    item: DemoUpdate,
    user_id: int = Query(..., description="用户ID"),
    importance: int = Body(1, ge=1, le=5, description="重要性，1-5")
):
    """多个请求体参数示例
    
    演示如何处理路径参数、查询参数和多个请求体参数
    
    - **item_id**: 项目ID
    - **item**: 更新的项目信息
    - **user_id**: 用户ID，查询参数
    - **importance**: 重要性，请求体参数
    - **return**: 更新后的项目信息
    """
    result = {
        "item_id": item_id,
        "item": item,
        "user_id": user_id,
        "importance": importance
    }
    return result

# 依赖注入示例
async def common_parameters(
    q: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
):
    """公共参数依赖
    
    可以被多个端点重用的依赖函数
    """
    return {"q": q, "skip": skip, "limit": limit}

@router.get("/items-with-deps")
async def read_items_with_deps(commons: dict = Depends(common_parameters)):
    """依赖注入示例
    
    演示如何使用依赖注入获取公共参数
    
    - **commons**: 通过依赖注入获取的公共参数
    - **return**: 包含查询参数的结果
    """
    return {
        "message": "这是使用依赖注入的示例",
        "parameters": commons
    }

# 错误处理示例
@router.get("/items/{item_id}/error-demo")
async def read_item_with_error(item_id: int):
    """错误处理示例
    
    演示如何返回HTTP错误响应
    
    - **item_id**: 项目ID
    - **return**: 项目信息或错误响应
    """
    if item_id < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Item ID must be positive",
            headers={"X-Error-Code": "ID_NEGATIVE"},
        )
    elif item_id > 1000:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )
    return {"item_id": item_id, "name": f"Item {item_id}"}

@router.get("/streamDemo01")
async def streamDemo():
    async def test():
        count = 0
        while count < 100:
            yield ('小黑放得开尖峰时刻大姐夫随机发手打会计法手打开发机苏卡达水电费可视对讲福克斯电极法刷卡电极法第三方开机速度快福建师大看法是第三方可视对讲焚枯食淡叫法是老大打开福建省快递费几十块倒垃圾发上啦电极法收到反馈近段时间发多少第三方快进到' + str(count)).encode('utf-8')
            await asyncio.sleep(1)  # 休眠1秒
            count = count + 1   
    return StreamingResponse(test(), media_type="text/plain")