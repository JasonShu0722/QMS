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
from app.core.dependencies import get_current_user
from app.models.user import User, UserType, UserStatus
from app.models.supplier import Supplier, SupplierStatus
from app.schemas.user import (
    UserRegisterSchema,
    RegisterResponseSchema,
    SupplierSearchResponseSchema,
    LoginRequestSchema,
    LoginResponseSchema,
    CaptchaResponseSchema,
    UserResponseSchema
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



@router.post(
    "/login",
    response_model=LoginResponseSchema,
    summary="统一登录接口",
    description="""
    统一登录接口，支持内部员工和供应商用户登录。
    
    **登录流程：**
    1. 验证用户名和密码
    2. 供应商登录：验证图形验证码
    3. 检查账号状态（active/frozen/pending）
    4. 检查密码是否需要强制修改（首次登录或超过 90 天）
    5. 生成 JWT Token
    6. 记录登录日志（last_login_at, ip_address）
    
    **内部员工登录：**
    - user_type: "internal"
    - 仅需用户名和密码
    
    **供应商登录：**
    - user_type: "supplier"
    - 需要用户名、密码和图形验证码
    - 先调用 /auth/captcha 获取验证码
    """
)
async def login(
    login_data: LoginRequestSchema,
    db: AsyncSession = Depends(get_db)
):
    """
    统一登录接口
    
    Requirements: 2.1.5
    """
    from app.services.captcha_service import captcha_service
    from app.core.auth_strategy import (
        InvalidCredentialsError,
        AccountLockedError,
        PasswordExpiredError,
        AccountInactiveError
    )
    
    # 1. 供应商登录：验证图形验证码
    if login_data.user_type == UserType.SUPPLIER:
        if not login_data.captcha or not login_data.captcha_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="供应商登录必须提供图形验证码"
            )
        
        # 验证验证码
        is_captcha_valid = captcha_service.verify_captcha(
            login_data.captcha_id,
            login_data.captcha
        )
        
        if not is_captcha_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="验证码错误或已过期，请重新获取"
            )
    
    # 2. 执行认证
    try:
        user = await local_auth.authenticate(
            db,
            login_data.username,
            login_data.password
        )
    except InvalidCredentialsError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except AccountLockedError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except AccountInactiveError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except PasswordExpiredError as e:
        # 密码过期：仍然返回 Token，但标记 password_expired=True
        # 前端收到后应引导用户修改密码
        user = await db.execute(
            select(User).where(User.username == login_data.username)
        )
        user = user.scalar_one()
        
        access_token = local_auth.create_access_token(user.id)
        
        return LoginResponseSchema(
            access_token=access_token,
            token_type="bearer",
            user_info=UserResponseSchema.model_validate(user),
            password_expired=True
        )
    
    # 3. 生成 Token
    access_token = local_auth.create_access_token(user.id)
    
    # 4. 返回登录结果
    return LoginResponseSchema(
        access_token=access_token,
        token_type="bearer",
        user_info=UserResponseSchema.model_validate(user),
        password_expired=False
    )


@router.get(
    "/captcha",
    response_model=CaptchaResponseSchema,
    summary="生成图形验证码",
    description="""
    生成图形验证码接口，用于供应商登录。
    
    **使用流程：**
    1. 前端调用此接口获取验证码图片和 captcha_id
    2. 用户输入验证码
    3. 登录时将 captcha_id 和用户输入的验证码一起提交
    
    **验证码特性：**
    - 有效期：5 分钟
    - 长度：4 位字符（大写字母和数字）
    - 一次性使用：验证后自动失效
    """
)
async def get_captcha():
    """
    生成图形验证码
    
    Requirements: 2.1.5
    """
    from app.services.captcha_service import captcha_service
    
    # 生成验证码
    captcha_id, captcha_image = captcha_service.generate_captcha()
    
    return CaptchaResponseSchema(
        captcha_id=captcha_id,
        captcha_image=captcha_image
    )


@router.get(
    "/me",
    response_model=UserResponseSchema,
    summary="获取当前用户信息",
    description="""
    获取当前登录用户的详细信息。
    
    **认证要求：**
    - 需要在请求头中携带有效的 JWT Token
    - Header: Authorization: Bearer <token>
    
    **返回信息：**
    - 用户基本信息（姓名、邮箱、电话）
    - 用户类型和状态
    - 部门和职位（内部员工）
    - 关联供应商（供应商用户）
    - 最后登录时间
    """
)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    获取当前用户信息
    
    Requirements: 2.1.5
    """
    return UserResponseSchema.model_validate(current_user)


@router.post(
    "/check-permission",
    summary="检查当前用户权限",
    description="""
    检查当前登录用户是否拥有指定的模块操作权限。
    
    **请求参数：**
    - module_path: 功能模块路径（如 "system.users"）
    - operation: 操作类型（create/read/update/delete/export）
    
    **返回值：**
    - has_permission: 是否拥有权限（布尔值）
    
    **应用场景：**
    - 前端路由守卫：在导航到受保护页面前进行权限验证
    - 前端 UI 控制：根据权限动态隐藏/禁用按钮
    """
)
async def check_permission(
    request_data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    检查当前用户是否拥有指定权限

    Args:
        request_data: 包含 module_path 和 operation 的字典
        current_user: 当前登录用户
        db: 数据库会话

    Returns:
        dict: { has_permission: bool }
    """
    from app.core.permissions import PermissionChecker
    from app.models.permission import OperationType

    module_path = request_data.get("module_path", "")
    operation = request_data.get("operation", "")

    if not module_path or not operation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="module_path 和 operation 为必填参数"
        )

    # 验证操作类型是否合法
    try:
        op_type = OperationType(operation)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的操作类型: {operation}，可选值: create/read/update/delete/export"
        )

    try:
        has_permission = await PermissionChecker.check_permission(
            user_id=current_user.id,
            module_path=module_path,
            operation=op_type,
            db=db
        )
        return {"has_permission": has_permission}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"权限检查失败: {str(e)}"
        )

