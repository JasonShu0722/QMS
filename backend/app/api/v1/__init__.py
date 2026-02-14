"""
API Version 1
统一管理所有 v1 版本的 API 路由
"""
from fastapi import APIRouter
from app.api.v1 import auth, tasks, notifications, profile, announcements, feature_flags, quality_metrics, ai, scar, supplier_lifecycle, supplier_targets, supplier_meetings, ppap, inspection_specs, barcode_validation, process_defects, process_issues, customer_complaints, eight_d_customer, customer_claims, supplier_claims, lesson_learned, new_product_projects, trial_production
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
api_router.include_router(quality_metrics.router)
api_router.include_router(ai.router)
api_router.include_router(scar.router)
api_router.include_router(supplier_lifecycle.router)
api_router.include_router(supplier_targets.router)
api_router.include_router(supplier_meetings.router)
api_router.include_router(ppap.router)
api_router.include_router(inspection_specs.router)
api_router.include_router(barcode_validation.router)
api_router.include_router(process_defects.router)
api_router.include_router(process_issues.router)
api_router.include_router(customer_complaints.router)
api_router.include_router(eight_d_customer.router)
api_router.include_router(customer_claims.router)
api_router.include_router(supplier_claims.router)
api_router.include_router(lesson_learned.router)
api_router.include_router(new_product_projects.router)
api_router.include_router(trial_production.router)
api_router.include_router(permissions.router)
api_router.include_router(users.router)
api_router.include_router(operation_logs.router)
api_router.include_router(admin_tasks.router)
api_router.include_router(notification_rules.router)
api_router.include_router(admin_feature_flags.router)
api_router.include_router(system_config.router)

__all__ = ["api_router"]
