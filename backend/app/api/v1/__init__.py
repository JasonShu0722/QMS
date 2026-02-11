"""
API Version 1
统一管理所有 v1 版本的 API 路由
"""
from fastapi import APIRouter
from app.api.v1 import auth, tasks, notifications, profile, announcements, feature_flags
from app.api.v1.admin import (
    permissions, 
    users, 
    operation_logs, 
    tasks as admin_tasks, 
    notification_rules, 
    feature_flags as admin_feature_flags,
    system_config
)

# 创建 v1 API 路由器
api_router = APIRouter(prefix="/v1")

# 注册子路由
api_router.include_router(auth.router)
api_router.include_router(tasks.router)
api_router.include_router(notifications.router)
api_router.include_router(profile.router)
api_router.include_router(announcements.router)
api_router.include_router(feature_flags.router)
api_router.include_router(permissions.router)
api_router.include_router(users.router)
api_router.include_router(operation_logs.router)
api_router.include_router(admin_tasks.router)
api_router.include_router(notification_rules.router)
api_router.include_router(admin_feature_flags.router)
api_router.include_router(system_config.router)

__all__ = ["api_router"]
