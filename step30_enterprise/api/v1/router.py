"""v1 路由聚合"""
from fastapi import APIRouter
from .endpoints import users

router = APIRouter()
router.include_router(users.router, prefix="/users", tags=["v1/users"])
