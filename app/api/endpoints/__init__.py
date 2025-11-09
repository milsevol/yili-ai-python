from fastapi import APIRouter

from app.api.endpoints import health, users, items, products, orders, customers, conversation_search, llmtest, demo, agents, langgraph

router = APIRouter()

router.include_router(health.router, prefix="/health", tags=["监控度检查"])
router.include_router(users.router, prefix="/users", tags=["users"])
router.include_router(items.router, prefix="/items", tags=["items"])
router.include_router(products.router, prefix="/products", tags=["products"])
router.include_router(orders.router, prefix="/orders", tags=["orders"])
router.include_router(customers.router, prefix="/customers", tags=["customers"])
router.include_router(conversation_search.router, prefix="/conversations", tags=["conversations"])
router.include_router(conversation_search.router, prefix="/conversations", tags=["conversations"])
router.include_router(llmtest.router, prefix="/llmtest", tags=["大模型测试"])
router.include_router(llmtest.router, prefix="/agenttest", tags=["agent学习"])
router.include_router(agents.router, prefix="/agents", tags=["AI Agent"])
router.include_router(demo.router, prefix="/demo", tags=["接口示例测试"])
router.include_router(langgraph.router, prefix="/langgraph", tags=["LangGraph学习示例"])