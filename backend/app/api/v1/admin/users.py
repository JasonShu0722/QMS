"""
用户管理 API 路由
Admin User Management - 管理员用户审核、冻结、重置密码等操作
"""
from typing import List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.core.database import get_db
from app.core.platform_admin import get_current_platform_admin
from app.models.user import User, UserStatus
from app.schemas.user import UserResponseSchema
from app.schemas.admin import (
    UserApprovalRequest,
    UserFreezeRequest,
    PasswordResetResponse,
    UserActionResponse
)
from app.services.notification_service import notification_service
from app.core.auth_strategy import LocalAuthStrategy
from app.services.user_session_service import build_user_responses


router = APIRouter(prefix="/admin/users", tags=["Admin - User Management"])


@router.get(
    "/pending",
    response_model=List[UserResponseSchema],
    summary="获取待审核用户列表",
    description="获取所有状态为 'pending' 的用户注册申请"
)
async def get_pending_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_platform_admin)
):
    """
    获取待审核用户列表
    
    权限要求：管理员
    
    Returns:
        List[UserResponseSchema]: 待审核用户列表
    """
    # 查询待审核用户
    result = await db.execute(
        select(User)
        .where(User.status == UserStatus.PENDING)
        .order_by(User.created_at.desc())
    )
    pending_users = result.scalars().all()
    
    return await build_user_responses(db, pending_users)


@router.post(
    "/{user_id}/approve",
    response_model=UserActionResponse,
    summary="批准用户注册",
    description="将用户状态更新为 'active' 并发送激活通知邮件"
)
async def approve_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_platform_admin)
):
    """
    批准用户注册
    
    操作流程：
    1. 验证用户存在且状态为 pending
    2. 更新用户状态为 active
    3. 发送激活通知邮件
    
    Args:
        user_id: 用户ID
        
    Returns:
        UserActionResponse: 操作结果
    """
    # 查询用户
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    if user.status != UserStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"用户状态为 {user.status}，无法批准"
        )
    
    # 更新用户状态
    await db.execute(
        update(User)
        .where(User.id == user_id)
        .values(
            status=UserStatus.ACTIVE,
            updated_at=datetime.utcnow(),
            updated_by=current_user.id
        )
    )
    await db.commit()
    
    # 刷新用户对象
    await db.refresh(user)
    
    # 发送激活通知邮件
    email_sent = await notification_service.send_approval_notification(user)
    
    return UserActionResponse(
        message="用户已批准",
        user_id=user.id,
        username=user.username,
        status=user.status,
        email_sent=email_sent
    )


@router.post(
    "/{user_id}/reject",
    response_model=UserActionResponse,
    summary="拒绝用户注册",
    description="将用户状态更新为 'rejected' 并记录拒绝原因"
)
async def reject_user(
    user_id: int,
    request: UserApprovalRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_platform_admin)
):
    """
    拒绝用户注册
    
    操作流程：
    1. 验证用户存在且状态为 pending
    2. 验证拒绝原因已填写
    3. 更新用户状态为 rejected
    4. 发送驳回通知邮件
    
    Args:
        user_id: 用户ID
        request: 审核请求（包含拒绝原因）
        
    Returns:
        UserActionResponse: 操作结果
    """
    # 验证拒绝原因
    if not request.reason or not request.reason.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="拒绝用户时必须填写拒绝原因"
        )
    
    # 查询用户
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    if user.status != UserStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"用户状态为 {user.status}，无法拒绝"
        )
    
    # 更新用户状态
    await db.execute(
        update(User)
        .where(User.id == user_id)
        .values(
            status=UserStatus.REJECTED,
            updated_at=datetime.utcnow(),
            updated_by=current_user.id
        )
    )
    await db.commit()
    
    # 刷新用户对象
    await db.refresh(user)
    
    # 发送驳回通知邮件
    email_sent = await notification_service.send_rejection_notification(
        user,
        request.reason
    )
    
    return UserActionResponse(
        message=f"用户已拒绝：{request.reason}",
        user_id=user.id,
        username=user.username,
        status=user.status,
        email_sent=email_sent
    )


@router.post(
    "/{user_id}/freeze",
    response_model=UserActionResponse,
    summary="冻结用户账号",
    description="将用户状态更新为 'frozen'，阻止其登录"
)
async def freeze_user(
    user_id: int,
    request: UserFreezeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_platform_admin)
):
    """
    冻结用户账号
    
    操作流程：
    1. 验证用户存在且状态为 active
    2. 更新用户状态为 frozen
    
    Args:
        user_id: 用户ID
        request: 冻结请求（包含冻结原因）
        
    Returns:
        UserActionResponse: 操作结果
    """
    # 查询用户
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    if user.status == UserStatus.FROZEN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户已处于冻结状态"
        )
    
    # 更新用户状态
    await db.execute(
        update(User)
        .where(User.id == user_id)
        .values(
            status=UserStatus.FROZEN,
            updated_at=datetime.utcnow(),
            updated_by=current_user.id
        )
    )
    await db.commit()
    
    # 刷新用户对象
    await db.refresh(user)
    
    reason_msg = f"：{request.reason}" if request.reason else ""
    
    return UserActionResponse(
        message=f"用户已冻结{reason_msg}",
        user_id=user.id,
        username=user.username,
        status=user.status,
        email_sent=False
    )


@router.post(
    "/{user_id}/unfreeze",
    response_model=UserActionResponse,
    summary="解冻用户账号",
    description="将用户状态从 'frozen' 恢复为 'active'"
)
async def unfreeze_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_platform_admin)
):
    """
    解冻用户账号
    
    操作流程：
    1. 验证用户存在且状态为 frozen
    2. 更新用户状态为 active
    
    Args:
        user_id: 用户ID
        
    Returns:
        UserActionResponse: 操作结果
    """
    # 查询用户
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    if user.status != UserStatus.FROZEN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"用户状态为 {user.status}，无法解冻"
        )
    
    # 更新用户状态
    await db.execute(
        update(User)
        .where(User.id == user_id)
        .values(
            status=UserStatus.ACTIVE,
            updated_at=datetime.utcnow(),
            updated_by=current_user.id
        )
    )
    await db.commit()
    
    # 刷新用户对象
    await db.refresh(user)
    
    return UserActionResponse(
        message="用户已解冻",
        user_id=user.id,
        username=user.username,
        status=user.status,
        email_sent=False
    )


@router.post(
    "/{user_id}/reset-password",
    response_model=PasswordResetResponse,
    summary="重置用户密码",
    description="生成临时密码并发送邮件通知，强制用户下次登录修改"
)
async def reset_user_password(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_platform_admin)
):
    """
    重置用户密码
    
    操作流程：
    1. 验证用户存在
    2. 生成临时密码
    3. 更新密码哈希
    4. 清空 password_changed_at（强制下次登录修改）
    5. 发送密码重置通知邮件
    
    Args:
        user_id: 用户ID
        
    Returns:
        PasswordResetResponse: 操作结果（包含临时密码）
    """
    # 查询用户
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 生成临时密码
    temporary_password = notification_service.generate_temporary_password()
    
    # 哈希临时密码
    auth_strategy = LocalAuthStrategy()
    hashed_password = auth_strategy.hash_password(temporary_password)
    
    # 更新密码并清空 password_changed_at（强制下次登录修改）
    await db.execute(
        update(User)
        .where(User.id == user_id)
        .values(
            password_hash=hashed_password,
            password_changed_at=None,  # 清空，强制修改
            failed_login_attempts=0,  # 重置登录失败计数
            locked_until=None,  # 解除锁定
            updated_at=datetime.utcnow(),
            updated_by=current_user.id
        )
    )
    await db.commit()
    
    # 刷新用户对象
    await db.refresh(user)
    
    # 发送密码重置通知邮件
    email_sent = await notification_service.send_password_reset_notification(
        user,
        temporary_password
    )
    
    return PasswordResetResponse(
        message="密码已重置，临时密码已发送至用户邮箱",
        temporary_password=temporary_password,
        email_sent=email_sent
    )
