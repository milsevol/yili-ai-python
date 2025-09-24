from fastapi import APIRouter,HTTPException
from app.schemas.demo import DemoPostForm
router = APIRouter()

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

@router.post("/post01")
async def post01(item: DemoPostForm):
    """post请求示例
    
    这个接口演示post请求，以及参数校验
    
    - **return**: DemoPostForm对象
    """
    return item