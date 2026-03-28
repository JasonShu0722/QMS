"""
权限配置管理 API 测试
测试管理员权限配置接口的功能
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.models.user import User, UserType, UserStatus
from app.models.permission import Permission, OperationType
from app.core.auth_strategy import LocalAuthStrategy


@pytest.fixture
async def auth_headers(async_client: AsyncClient, db_session: AsyncSession):
    """创建认证头部（用于测试需要认证的接口�?""
    # 创建测试管理员用�?
    local_auth = LocalAuthStrategy()
    hashed_password = local_auth.hash_password("AdminPass123!")
    
    admin_user = User(
        username="test_admin",
        password_hash=hashed_password,
        full_name="Test Admin",
        email="admin@test.com",
        user_type=UserType.INTERNAL,
        status=UserStatus.ACTIVE,
        department="IT",
        position="Admin",
        password_changed_at=datetime.utcnow()
    )
    
    db_session.add(admin_user)
    await db_session.commit()
    await db_session.refresh(admin_user)
    
    # 登录获取 Token
    login_response = await async_client.post(
        "/api/v1/auth/login",
        json={
            "username": "test_admin",
            "password": "AdminPass123!",
            "user_type": "internal"
        }
    )
    
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_get_permission_matrix(async_client: AsyncClient, db_session: AsyncSession, auth_headers):
    """测试获取权限矩阵"""
    # 创建测试用户
    user1 = User(
        username="user1",
        password_hash="hashed",
        full_name="User One",
        email="user1@example.com",
        user_type=UserType.INTERNAL,
        status=UserStatus.ACTIVE,
        department="Quality",
        position="SQE"
    )
    user2 = User(
        username="user2",
        password_hash="hashed",
        full_name="User Two",
        email="user2@example.com",
        user_type=UserType.SUPPLIER,
        status=UserStatus.ACTIVE
    )
    db_session.add_all([user1, user2])
    await db_session.commit()
    await db_session.refresh(user1)
    await db_session.refresh(user2)
    
    # �?user1 创建权限
    perm1 = Permission(
        user_id=user1.id,
        module_path="supplier.performance",
        operation_type=OperationType.READ,
        is_granted=True
    )
    perm2 = Permission(
        user_id=user1.id,
        module_path="supplier.performance",
        operation_type=OperationType.CREATE,
        is_granted=True
    )
    db_session.add_all([perm1, perm2])
    await db_session.commit()
    
    # 调用 API
    response = await async_client.get(
        "/api/v1/admin/permissions/matrix",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # 验证响应结构
    assert "users" in data
    assert "available_modules" in data
    assert "available_operations" in data
    
    # 验证用户列表
    assert len(data["users"]) >= 2
    
    # 验证操作类型列表
    assert "create" in data["available_operations"]
    assert "read" in data["available_operations"]
    assert "update" in data["available_operations"]
    assert "delete" in data["available_operations"]
    assert "export" in data["available_operations"]


@pytest.mark.asyncio
async def test_grant_permissions(async_client: AsyncClient, db_session: AsyncSession, auth_headers):
    """测试批量授予权限"""
    # 创建测试用户
    user = User(
        username="test_grant_user",
        password_hash="hashed",
        full_name="Test Grant User",
        email="grant@example.com",
        user_type=UserType.INTERNAL,
        status=UserStatus.ACTIVE
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    # 准备请求数据
    request_data = {
        "user_ids": [user.id],
        "permissions": [
            {"module_path": "supplier.management", "operation_type": "read"},
            {"module_path": "supplier.management", "operation_type": "create"},
            {"module_path": "quality.incoming", "operation_type": "read"}
        ]
    }
    
    # 调用 API
    response = await async_client.put(
        "/api/v1/admin/permissions/grant",
        json=request_data,
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # 验证响应
    assert data["success"] is True
    assert data["affected_users"] == 1
    assert data["affected_permissions"] == 3
    
    # 验证数据库中的权限记�?
    from sqlalchemy import select
    stmt = select(Permission).where(Permission.user_id == user.id)
    result = await db_session.execute(stmt)
    permissions = result.scalars().all()
    
    assert len(permissions) == 3
    assert all(perm.is_granted for perm in permissions)


@pytest.mark.asyncio
async def test_grant_permissions_update_existing(async_client: AsyncClient, db_session: AsyncSession, auth_headers):
    """测试授予权限 - 更新已存在的权限记录"""
    # 创建测试用户
    user = User(
        username="test_update_user",
        password_hash="hashed",
        full_name="Test Update User",
        email="update@example.com",
        user_type=UserType.INTERNAL,
        status=UserStatus.ACTIVE
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    # 创建一个已撤销的权限记�?
    existing_perm = Permission(
        user_id=user.id,
        module_path="test.module",
        operation_type=OperationType.READ,
        is_granted=False  # 已撤销
    )
    db_session.add(existing_perm)
    await db_session.commit()
    
    # 重新授予权限
    request_data = {
        "user_ids": [user.id],
        "permissions": [
            {"module_path": "test.module", "operation_type": "read"}
        ]
    }
    
    response = await async_client.put(
        "/api/v1/admin/permissions/grant",
        json=request_data,
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["affected_permissions"] == 1
    
    # 验证权限已更�?
    await db_session.refresh(existing_perm)
    assert existing_perm.is_granted is True


@pytest.mark.asyncio
async def test_revoke_permissions(async_client: AsyncClient, db_session: AsyncSession, auth_headers):
    """测试批量撤销权限"""
    # 创建测试用户
    user = User(
        username="test_revoke_user",
        password_hash="hashed",
        full_name="Test Revoke User",
        email="revoke@example.com",
        user_type=UserType.INTERNAL,
        status=UserStatus.ACTIVE
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    # 创建权限记录
    perms = [
        Permission(
            user_id=user.id,
            module_path="test.module",
            operation_type=OperationType.READ,
            is_granted=True
        ),
        Permission(
            user_id=user.id,
            module_path="test.module",
            operation_type=OperationType.CREATE,
            is_granted=True
        )
    ]
    db_session.add_all(perms)
    await db_session.commit()
    
    # 撤销权限
    request_data = {
        "user_ids": [user.id],
        "permissions": [
            {"module_path": "test.module", "operation_type": "read"},
            {"module_path": "test.module", "operation_type": "create"}
        ]
    }
    
    response = await async_client.put(
        "/api/v1/admin/permissions/revoke",
        json=request_data,
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert data["affected_users"] == 1
    assert data["affected_permissions"] == 2
    
    # 验证权限已撤销
    from sqlalchemy import select
    stmt = select(Permission).where(Permission.user_id == user.id)
    result = await db_session.execute(stmt)
    permissions = result.scalars().all()
    
    assert all(not perm.is_granted for perm in permissions)


@pytest.mark.asyncio
async def test_get_user_permissions_detail(async_client: AsyncClient, db_session: AsyncSession, auth_headers):
    """测试获取用户权限详情"""
    # 创建测试用户
    user = User(
        username="test_detail_user",
        password_hash="hashed",
        full_name="Test Detail User",
        email="detail@example.com",
        user_type=UserType.INTERNAL,
        status=UserStatus.ACTIVE
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    # 创建权限记录
    perms = [
        Permission(
            user_id=user.id,
            module_path="module.a",
            operation_type=OperationType.READ,
            is_granted=True
        ),
        Permission(
            user_id=user.id,
            module_path="module.a",
            operation_type=OperationType.CREATE,
            is_granted=False  # 已撤销
        ),
        Permission(
            user_id=user.id,
            module_path="module.b",
            operation_type=OperationType.READ,
            is_granted=True
        )
    ]
    db_session.add_all(perms)
    await db_session.commit()
    
    # 调用 API
    response = await async_client.get(
        f"/api/v1/admin/permissions/users/{user.id}",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # 验证响应结构
    assert data["user_id"] == user.id
    assert data["username"] == user.username
    assert "permissions" in data
    assert "permission_tree" in data
    
    # 验证权限列表（包含所有记录，包括已撤销的）
    assert len(data["permissions"]) == 3
    
    # 验证权限树（仅包含已授予的权限）
    assert "module.a" in data["permission_tree"]
    assert data["permission_tree"]["module.a"]["read"] is True
    assert "create" not in data["permission_tree"]["module.a"]  # 已撤销，不应出�?
    assert "module.b" in data["permission_tree"]
    assert data["permission_tree"]["module.b"]["read"] is True


@pytest.mark.asyncio
async def test_grant_permissions_invalid_user(async_client: AsyncClient, db_session: AsyncSession, auth_headers):
    """测试授予权限 - 用户不存�?""
    request_data = {
        "user_ids": [99999],  # 不存在的用户ID
        "permissions": [
            {"module_path": "test.module", "operation_type": "read"}
        ]
    }
    
    response = await async_client.put(
        "/api/v1/admin/permissions/grant",
        json=request_data,
        headers=auth_headers
    )
    
    assert response.status_code == 404
    assert "不存�? in response.json()["detail"]


@pytest.mark.asyncio
async def test_grant_permissions_invalid_operation_type(async_client: AsyncClient, db_session: AsyncSession, auth_headers):
    """测试授予权限 - 无效的操作类�?""
    # 创建测试用户
    user = User(
        username="test_invalid_op",
        password_hash="hashed",
        full_name="Test Invalid Op",
        email="invalidop@example.com",
        user_type=UserType.INTERNAL,
        status=UserStatus.ACTIVE
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    request_data = {
        "user_ids": [user.id],
        "permissions": [
            {"module_path": "test.module", "operation_type": "invalid_operation"}
        ]
    }
    
    response = await async_client.put(
        "/api/v1/admin/permissions/grant",
        json=request_data,
        headers=auth_headers
    )
    
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_batch_grant_multiple_users(async_client: AsyncClient, db_session: AsyncSession, auth_headers):
    """测试批量授予权限 - 多个用户"""
    # 创建多个测试用户
    users = [
        User(
            username=f"batch_user_{i}",
            password_hash="hashed",
            full_name=f"Batch User {i}",
            email=f"batch{i}@example.com",
            user_type=UserType.INTERNAL,
            status=UserStatus.ACTIVE
        )
        for i in range(3)
    ]
    db_session.add_all(users)
    await db_session.commit()
    
    user_ids = [user.id for user in users]
    
    # 批量授予权限
    request_data = {
        "user_ids": user_ids,
        "permissions": [
            {"module_path": "batch.module", "operation_type": "read"},
            {"module_path": "batch.module", "operation_type": "create"}
        ]
    }
    
    response = await async_client.put(
        "/api/v1/admin/permissions/grant",
        json=request_data,
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["affected_users"] == 3
    assert data["affected_permissions"] == 6  # 3 users × 2 permissions
