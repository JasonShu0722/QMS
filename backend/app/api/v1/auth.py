"""
认证相关 API 路由
Authentication Routes - 用户注册、登录、供应商搜索等接口
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.core.database import get_db
from app.core.auth_strategy import LocalAuthStrategy
from app.models.user import User, UserType, UserStatus
from app.models.supplier import Supplier, SupplierStatus
from app.schemas.user import (
    UserRegisterSchema,
    RegisterResponseSchema,
    SupplierSearchResponseSchema
)

router = APIRouter(prefix="/auth", tags=["认证管理"])

# 初始化本地认证策略（用于密码哈希和验证）
local_auth = LocalAuthStrategy()


@router.post(
    "/register",
    response_model=RegisterResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="用户注册",
    description="""
    用户注册接口，支持内部员工和供应商用户注册。
    
    **注册流程：**
    1. 验证用户名唯一性
    2. 验证密码复杂度（大写、小写、数字、特殊字符中至少三种，长度>8位）
    3. 供应商用户：验证供应商ID必须从 Supplier 表中选择
    4. 创建状态为 "pending" 的用户记录
    5. 密码哈希存储
    
    **内部员工注册要求：**
    - user_type: "internal"
    - department: 必填
    
    **供应商用户注册要求：**
    - user_type: "supplier"
    - supplier_id: 必填（需先通过 /auth/suppliers/search 接口搜索供应商）
    """
)
async def register_user(
    user_data: UserRegisterSchema,
    db: AsyncSession = Depends(get_db)
):
    """
    用户注册接口
    
    Requirements: 2.1.3
    """
    # 1. 验证用户名唯一性
    result = await db.execute(
        select(User).where(User.username == user_data.username)
    )
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在，请选择其他用户名"
        )
    
    # 2. 验证密码复杂度
    is_valid, error_message = local_auth.validate_password_complexity(user_data.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message
        )
    
    # 3. 根据用户类型进行特定验证
    if user_data.user_type == UserType.INTERNAL:
        # 内部员工：验证部门必填
        if not user_data.department:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="内部员工注册时部门为必填项"
            )
    
    elif user_data.user_type == UserType.SUPPLIER:
        # 供应商用户：验证供应商ID必填且存在
        if not user_data.supplier_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="供应商用户注册时必须选择供应商名称"
            )
        
        # 验证供应商是否存在
        supplier_result = await db.execute(
            select(Supplier).where(Supplier.id == user_data.supplier_id)
        )
        supplier = supplier_result.scalar_one_or_none()
        
        if not supplier:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="选择的供应商不存在，请通过搜索接口选择有效的供应商"
            )
        
        # 验证供应商状态（可选：只允许激活状态的供应商注册用户）
        if supplier.status != SupplierStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"该供应商当前状态为 {supplier.status}，无法注册用户"
            )
    
    # 4. 哈希密码
    hashed_password = local_auth.hash_password(user_data.password)
    
    # 5. 创建用户记录（状态为 pending）
    new_user = User(
        username=user_data.username,
        password_hash=hashed_password,
        full_name=user_data.full_name,
        email=user_data.email,
        phone=user_data.phone,
        user_type=user_data.user_type,
        status=UserStatus.PENDING,  # 默认待审核
        department=user_data.department,
        position=user_data.position,
        supplier_id=user_data.supplier_id
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return RegisterResponseSchema(
        message="注册成功，请等待管理员审核",
        user_id=new_user.id,
        username=new_user.username,
        status=new_user.status
    )


@router.get(
    "/suppliers/search",
    response_model=List[SupplierSearchResponseSchema],
    summary="供应商模糊搜索",
    description="""
    供应商模糊搜索接口，用于供应商用户注册时选择供应商名称。
    
    **搜索逻辑：**
    - 支持按供应商名称或代码进行模糊搜索
    - 仅返回状态为 "active" 的供应商
    - 最多返回 20 条结果
    
    **使用场景：**
    - 供应商用户注册时，输入供应商名称关键词，前端调用此接口获取匹配的供应商列表
    - 用户从列表中选择正确的供应商，获取 supplier_id 后提交注册表单
    """
)
async def search_suppliers(
    q: str = Query(..., min_length=1, description="搜索关键词（供应商名称或代码）"),
    db: AsyncSession = Depends(get_db)
):
    """
    供应商模糊搜索接口
    
    Requirements: 2.1.3
    
    Args:
        q: 搜索关键词
        db: 数据库会话
        
    Returns:
        List[SupplierSearchResponseSchema]: 匹配的供应商列表
    """
    # 模糊搜索供应商名称或代码
    # 使用 ilike 实现不区分大小写的模糊匹配
    search_pattern = f"%{q}%"
    
    result = await db.execute(
        select(Supplier)
        .where(
            or_(
                Supplier.name.ilike(search_pattern),
                Supplier.code.ilike(search_pattern)
            )
        )
        .where(Supplier.status == SupplierStatus.ACTIVE)  # 仅返回激活状态的供应商
        .limit(20)  # 限制返回数量
    )
    
    suppliers = result.scalars().all()
    
    return [
        SupplierSearchResponseSchema(
            id=supplier.id,
            name=supplier.name,
            code=supplier.code,
            status=supplier.status
        )
        for supplier in suppliers
    ]

