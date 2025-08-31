from fastapi import APIRouter

from app.api.endpoints import health, users, items, products, orders, customers, conversation_search

router = APIRouter()

router.include_router(health.router, prefix="/health", tags=["health"])
router.include_router(users.router, prefix="/users", tags=["users"])
router.include_router(items.router, prefix="/items", tags=["items"])
router.include_router(products.router, prefix="/products", tags=["products"])
router.include_router(orders.router, prefix="/orders", tags=["orders"])
router.include_router(customers.router, prefix="/customers", tags=["customers"])
router.include_router(conversation_search.router, prefix="/conversations", tags=["conversations"])