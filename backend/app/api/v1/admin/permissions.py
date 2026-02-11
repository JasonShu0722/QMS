"""
权限配置管理 API
Admin Permissions API - 管理员用于配置用户权限的接口
"""
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.core.permissions import PermissionChecker
from app.models.user import User, UserType
from app.models.permission import Permission, OperationType
from app.schemas.permission import (
    PermissionMatrixResponse,
    UserPermissionSummary,
    PermissionGrantRequest,
    PermissionRevokeRequest,
    PermissionOperationResponse,
    UserPermissionDetailResponse,
    PermissionResponse
)


router = APIRouter(prefix="/admin/permissions", tags=["Admin - Permissions"])


# 系统中所有可用的功能模块（可以从配置文件或数据库读取）
# 这里先硬编码一些示例模块，实际应用中应该从配置中心读取
AVAILABLE_MODULES = [
    "supplier.management",
    "supplier.performance",
    "supplier.audit",
    "supplier.ppap",
    "supplier.scar",
    "quality.incoming",
    "quality.process",
    "quality.customer",
    "quality.data_panel",
    "audit.system",
    "audit.process",
    "audit.product",
    "newproduct.management",
    "newproduct.trial",
    "system.config",
    "system.users",
    "system.notifications",
]


@router.get(
    "/matrix",
    response_model=PermissionMatrixResponse,
    summary="获取权限矩阵",
    description="""
    获取权限矩阵配置界面所需的数据。
    
    返回：
    - 所有用户列表及其当前权限配置
    - 系统中所有可用的功能模块
    - 所有可用的操作类型
    
    用于前端渲染网格化的权限配置界面。
    """
)
async def get_permission_matrix(
    user_type: str = Query(None, description="按用户类型筛选（internal/supplier）"),
    department: str = Query(None, description="按部门筛选（仅内部员工）"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取权限矩阵
    
    返回用户列表和功能-操作组合，标识每个用户的权限授予状态
    """
    # TODO: 添加管理员权限检查
    # 暂时允许所有激活用户访问，实际应用中应该检查管理员权限
    
    # 构建用户查询
    user_query = select(User).where(User.status == "active")
    
    # 应用筛选条件
    if user_type:
        user_query = user_query.where(User.user_type == user_type)
    if department:
        user_query = user_query.where(User.department == department)
    
    # 执行查询
    result = await db.execute(user_query)
    users = result.scalars().all()
    
    # 为每个用户获取权限
    user_summaries: List[UserPermissionSummary] = []
    
    for user in users:
        # 获取用户的权限树
        permission_tree = await PermissionChecker.get_user_permissions(user.id, db)
        
        user_summary = UserPermissionSummary(
            user_id=user.id,
            username=user.username,
            full_name=user.full_name,
            user_type=user.user_type,
            department=user.department,
            position=user.position,
            permissions=permission_tree
        )
        user_summaries.append(user_summary)
    
    # 返回权限矩阵
    return PermissionMatrixResponse(
        users=user_summaries,
        available_modules=AVAILABLE_MODULES,
        available_operations=[op.value for op in OperationType]
    )


@router.put(
    "/grant",
    response_model=PermissionOperationResponse,
    summary="批量授予权限",
    description="""
    批量授予权限给一个或多个用户。
    
    支持：
    - 多个用户同时授予
    - 多个权限同时授予
    - 实时生效（自动清除 Redis 缓存）
    
    如果权限记录已存在，则更新 is_granted 为 True。
    如果权限记录不存在，则创建新记录。
    """
)
async def grant_permissions(
    request: PermissionGrantRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    批量授予权限
    
    支持多个用户、多个权限的批量授予，实时生效（清除 Redis 缓存）
    """
    # TODO: 添加管理员权限检查
    
    affected_users = 0
    affected_permissions = 0
    
    # 遍历每个用户
    for user_id in request.user_ids:
        # 验证用户是否存在
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"用户 ID {user_id} 不存在"
            )
        
        user_affected = False
        
        # 遍历每个权限
        for perm_data in request.permissions:
            module_path = perm_data['module_path']
            operation_type = perm_data['operation_type']
            
            # 检查权限记录是否已存在
            perm_query = select(Permission).where(
                and_(
                    Permission.user_id == user_id,
                    Permission.module_path == module_path,
                    Permission.operation_type == operation_type
                )
            )
            perm_result = await db.execute(perm_query)
            existing_perm = perm_result.scalar_one_or_none()
            
            if existing_perm:
                # 权限记录已存在，更新 is_granted
                if not existing_perm.is_granted:
                    existing_perm.is_granted = True
                    affected_permissions += 1
                    user_affected = True
            else:
                # 权限记录不存在，创建新记录
                new_perm = Permission(
                    user_id=user_id,
                    module_path=module_path,
                    operation_type=operation_type,
                    is_granted=True,
                    created_by=current_user.id
                )
                db.add(new_perm)
                affected_permissions += 1
                user_affected = True
        
        if user_affected:
            affected_users += 1
            # 清除用户权限缓存
            await PermissionChecker.clear_user_cache(user_id)
    
    # 提交事务
    await db.commit()
    
    return PermissionOperationResponse(
        success=True,
        message=f"成功授予权限给 {affected_users} 个用户，共 {affected_permissions} 条权限记录",
        affected_users=affected_users,
        affected_permissions=affected_permissions
    )


@router.put(
    "/revoke",
    response_model=PermissionOperationResponse,
    summary="批量撤销权限",
    description="""
    批量撤销一个或多个用户的权限。
    
    支持：
    - 多个用户同时撤销
    - 多个权限同时撤销
    - 实时生效（自动清除 Redis 缓存）
    
    撤销权限时，将 is_granted 设置为 False（软删除），而不是物理删除记录。
    """
)
async def revoke_permissions(
    request: PermissionRevokeRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    批量撤销权限
    
    将指定用户的指定权限的 is_granted 设置为 False
    """
    # TODO: 添加管理员权限检查
    
    affected_users = 0
    affected_permissions = 0
    
    # 遍历每个用户
    for user_id in request.user_ids:
        # 验证用户是否存在
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"用户 ID {user_id} 不存在"
            )
        
        user_affected = False
        
        # 遍历每个权限
        for perm_data in request.permissions:
            module_path = perm_data['module_path']
            operation_type = perm_data['operation_type']
            
            # 查找权限记录
            perm_query = select(Permission).where(
                and_(
                    Permission.user_id == user_id,
                    Permission.module_path == module_path,
                    Permission.operation_type == operation_type
                )
            )
            perm_result = await db.execute(perm_query)
            existing_perm = perm_result.scalar_one_or_none()
            
            if existing_perm and existing_perm.is_granted:
                # 撤销权限（软删除）
                existing_perm.is_granted = False
                affected_permissions += 1
                user_affected = True
        
        if user_affected:
            affected_users += 1
            # 清除用户权限缓存
            await PermissionChecker.clear_user_cache(user_id)
    
    # 提交事务
    await db.commit()
    
    return PermissionOperationResponse(
        success=True,
        message=f"成功撤销 {affected_users} 个用户的权限，共 {affected_permissions} 条权限记录",
        affected_users=affected_users,
        affected_permissions=affected_permissions
    )


@router.get(
    "/users/{user_id}",
    response_model=UserPermissionDetailResponse,
    summary="获取用户权限详情",
    description="""
    获取指定用户的所有权限详情。
    
    返回：
    - 用户基本信息
    - 用户的所有权限记录（包括已授予和已撤销的）
    - 结构化的权限树（仅包含已授予的权限）
    """
)
async def get_user_permissions(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取用户权限详情
    
    返回指定用户的所有权限记录和结构化的权限树
    """
    # TODO: 添加管理员权限检查
    
    # 验证用户是否存在
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"用户 ID {user_id} 不存在"
        )
    
    # 获取用户的所有权限记录（包括已撤销的）
    perm_query = select(Permission).where(Permission.user_id == user_id)
    perm_result = await db.execute(perm_query)
    permissions = perm_result.scalars().all()
    
    # 转换为响应模型
    permission_responses = [
        PermissionResponse(
            id=perm.id,
            user_id=perm.user_id,
            module_path=perm.module_path,
            operation_type=perm.operation_type,
            is_granted=perm.is_granted,
            created_at=perm.created_at,
            updated_at=perm.updated_at
        )
        for perm in permissions
    ]
    
    # 获取结构化的权限树（仅包含已授予的权限）
    permission_tree = await PermissionChecker.get_user_permissions(user_id, db)
    
    return UserPermissionDetailResponse(
        user_id=user.id,
        username=user.username,
        full_name=user.full_name,
        user_type=user.user_type,
        permissions=permission_responses,
        permission_tree=permission_tree
    )
