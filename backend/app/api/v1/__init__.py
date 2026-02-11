"""
API Version 1
统一管理所有 v1 版本的 API 路由
"""
from fastapi import APIRouter
from app.api.v1 import auth
from app.api.v1.admin import permissions, users

# 创建 v1 API 路由器
api_router = APIRouter(prefix="/v1")

# 注册子路由
api_router.include_router(auth.router)
api_router.include_router(permissions.router)
api_router.include_router(users.router)

__all__ = ["api_router"]
