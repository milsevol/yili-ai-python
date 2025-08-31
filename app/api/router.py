from fastapi import APIRouter

from app.api.endpoints import items, users, health

router = APIRouter()

router.include_router(health.router, prefix="/health", tags=["health"])
router.include_router(users.router, prefix="/users", tags=["users"])
router.include_router(items.router, prefix="/items", tags=["items"])