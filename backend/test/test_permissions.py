"""
权限引擎测试
测试权限检查、缓存机制、数据隔离等核心功能
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User, UserType, UserStatus
from app.models.permission import Permission, OperationType
from app.core.permissions import (
    PermissionChecker,
    require_permission,
    has_permission,
    require_any_permission,
    require_all_permissions
)


@pytest.mark.asyncio
async def test_check_permission_granted(db_session: AsyncSession):
    """测试权限检查 - 已授予权限"""
    # 创建测试用户
    user = User(
        username="test_user",
        password_hash="hashed_password",
        full_name="Test User",
        email="test@example.com",
        user_type=UserType.INTERNAL,
        status=UserStatus.ACTIVE
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    # 创建权限记录
    permission = Permission(
        user_id=user.id,
        module_path="supplier.performance",
        operation_type=OperationType.READ,
        is_granted=True
    )
    db_session.add(permission)
    await db_session.commit()
    
    # 检查权限
    has_perm = await PermissionChecker.check_permission(
        user_id=user.id,
        module_path="supplier.performance",
        operation=OperationType.READ,
        db=db_session
    )
    
    assert has_perm is True


@pytest.mark.asyncio
async def test_check_permission_denied(db_session: AsyncSession):
    """测试权限检查 - 未授予权限"""
    # 创建测试用户（无权限）
    user = User(
        username="test_user_no_perm",
        password_hash="hashed_password",
        full_name="Test User No Perm",
        email="noperm@example.com",
        user_type=UserType.INTERNAL,
        status=UserStatus.ACTIVE
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    # 检查权限（用户没有任何权限）
    has_perm = await PermissionChecker.check_permission(
        user_id=user.id,
        module_path="supplier.performance",
        operation=OperationType.CREATE,
        db=db_session
    )
    
    assert has_perm is False


@pytest.mark.asyncio
async def test_check_permission_not_granted_flag(db_session: AsyncSession):
    """测试权限检查 - 权限记录存在但 is_granted=False"""
    # 创建测试用户
    user = User(
        username="test_user_revoked",
        password_hash="hashed_password",
        full_name="Test User Revoked",
        email="revoked@example.com",
        user_type=UserType.INTERNAL,
        status=UserStatus.ACTIVE
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    # 创建权限记录（但未授予）
    permission = Permission(
        user_id=user.id,
        module_path="supplier.performance",
        operation_type=OperationType.DELETE,
        is_granted=False  # 明确拒绝
    )
    db_session.add(permission)
    await db_session.commit()
    
    # 检查权限
    has_perm = await PermissionChecker.check_permission(
        user_id=user.id,
        module_path="supplier.performance",
        operation=OperationType.DELETE,
        db=db_session
    )
    
    assert has_perm is False


@pytest.mark.asyncio
async def test_get_user_permissions_tree(db_session: AsyncSession):
    """测试获取用户权限树（用于前端菜单渲染）"""
    # 创建测试用户
    user = User(
        username="test_user_tree",
        password_hash="hashed_password",
        full_name="Test User Tree",
        email="tree@example.com",
        user_type=UserType.INTERNAL,
        status=UserStatus.ACTIVE
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    # 创建多个权限记录
    permissions = [
        Permission(
            user_id=user.id,
            module_path="supplier.performance",
            operation_type=OperationType.READ,
            is_granted=True
        ),
        Permission(
            user_id=user.id,
            module_path="supplier.performance",
            operation_type=OperationType.CREATE,
            is_granted=True
        ),
        Permission(
            user_id=user.id,
            module_path="quality.incoming",
            operation_type=OperationType.READ,
            is_granted=True
        ),
    ]
    db_session.add_all(permissions)
    await db_session.commit()
    
    # 获取权限树
    perm_tree = await PermissionChecker.get_user_permissions(user.id, db_session)
    
    # 验证结构
    assert "supplier.performance" in perm_tree
    assert perm_tree["supplier.performance"]["read"] is True
    assert perm_tree["supplier.performance"]["create"] is True
    assert "quality.incoming" in perm_tree
    assert perm_tree["quality.incoming"]["read"] is True


@pytest.mark.asyncio
async def test_permission_cache_mechanism(db_session: AsyncSession):
    """测试权限缓存机制"""
    # 创建测试用户
    user = User(
        username="test_user_cache",
        password_hash="hashed_password",
        full_name="Test User Cache",
        email="cache@example.com",
        user_type=UserType.INTERNAL,
        status=UserStatus.ACTIVE
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    # 创建权限
    permission = Permission(
        user_id=user.id,
        module_path="test.module",
        operation_type=OperationType.READ,
        is_granted=True
    )
    db_session.add(permission)
    await db_session.commit()
    
    # 第一次检查（缓存未命中，从数据库加载）
    has_perm_1 = await PermissionChecker.check_permission(
        user_id=user.id,
        module_path="test.module",
        operation=OperationType.READ,
        db=db_session
    )
    assert has_perm_1 is True
    
    # 第二次检查（应该从缓存读取）
    has_perm_2 = await PermissionChecker.check_permission(
        user_id=user.id,
        module_path="test.module",
        operation=OperationType.READ,
        db=db_session
    )
    assert has_perm_2 is True
    
    # 清除缓存
    await PermissionChecker.clear_user_cache(user.id)
    
    # 第三次检查（缓存已清除，重新从数据库加载）
    has_perm_3 = await PermissionChecker.check_permission(
        user_id=user.id,
        module_path="test.module",
        operation=OperationType.READ,
        db=db_session
    )
    assert has_perm_3 is True


@pytest.mark.asyncio
async def test_has_permission_convenience_function(db_session: AsyncSession):
    """测试便捷函数 has_permission"""
    # 创建测试用户
    user = User(
        username="test_convenience",
        password_hash="hashed_password",
        full_name="Test Convenience",
        email="convenience@example.com",
        user_type=UserType.INTERNAL,
        status=UserStatus.ACTIVE
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    # 创建权限
    permission = Permission(
        user_id=user.id,
        module_path="test.convenience",
        operation_type=OperationType.UPDATE,
        is_granted=True
    )
    db_session.add(permission)
    await db_session.commit()
    
    # 使用便捷函数检查权限
    result = await has_permission(
        user=user,
        module_path="test.convenience",
        operation=OperationType.UPDATE,
        db=db_session
    )
    
    assert result is True


@pytest.mark.asyncio
async def test_require_any_permission(db_session: AsyncSession):
    """测试 require_any_permission - 至少有一个权限"""
    # 创建测试用户
    user = User(
        username="test_any_perm",
        password_hash="hashed_password",
        full_name="Test Any Perm",
        email="anyperm@example.com",
        user_type=UserType.INTERNAL,
        status=UserStatus.ACTIVE
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    # 创建一个权限
    permission = Permission(
        user_id=user.id,
        module_path="module.a",
        operation_type=OperationType.READ,
        is_granted=True
    )
    db_session.add(permission)
    await db_session.commit()
    
    # 检查多个权限（只要有一个即可）
    result = await require_any_permission(
        user=user,
        permissions=[
            ("module.a", OperationType.READ),  # 有这个权限
            ("module.b", OperationType.CREATE),  # 没有这个权限
        ],
        db=db_session
    )
    
    assert result is True


@pytest.mark.asyncio
async def test_require_all_permissions(db_session: AsyncSession):
    """测试 require_all_permissions - 必须有所有权限"""
    # 创建测试用户
    user = User(
        username="test_all_perm",
        password_hash="hashed_password",
        full_name="Test All Perm",
        email="allperm@example.com",
        user_type=UserType.INTERNAL,
        status=UserStatus.ACTIVE
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    # 创建两个权限
    permissions = [
        Permission(
            user_id=user.id,
            module_path="module.x",
            operation_type=OperationType.READ,
            is_granted=True
        ),
        Permission(
            user_id=user.id,
            module_path="module.y",
            operation_type=OperationType.CREATE,
            is_granted=True
        ),
    ]
    db_session.add_all(permissions)
    await db_session.commit()
    
    # 检查所有权限（必须全部拥有）
    result_all = await require_all_permissions(
        user=user,
        permissions=[
            ("module.x", OperationType.READ),
            ("module.y", OperationType.CREATE),
        ],
        db=db_session
    )
    assert result_all is True
    
    # 检查所有权限（缺少一个）
    result_missing = await require_all_permissions(
        user=user,
        permissions=[
            ("module.x", OperationType.READ),
            ("module.z", OperationType.DELETE),  # 没有这个权限
        ],
        db=db_session
    )
    assert result_missing is False


@pytest.mark.asyncio
async def test_permission_key_building(db_session: AsyncSession):
    """测试权限键构建逻辑"""
    # 测试静态方法
    key = Permission.build_permission_key("supplier.performance", "read")
    assert key == "supplier.performance.read"
    
    # 测试实例属性
    permission = Permission(
        user_id=1,
        module_path="quality.incoming",
        operation_type=OperationType.CREATE,
        is_granted=True
    )
    assert permission.permission_key == "quality.incoming.create"
