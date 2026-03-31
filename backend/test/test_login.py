"""
登录功能测试
Test Login Functionality - 测试统一登录接口
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.models.user import User, UserType, UserStatus
from app.core.auth_strategy import LocalAuthStrategy

pytestmark = pytest.mark.foundation_smoke


@pytest.mark.asyncio
async def test_internal_user_login_success(async_client: AsyncClient, db_session: AsyncSession):
    """测试内部员工登录成功"""
    # 创建测试用户
    local_auth = LocalAuthStrategy()
    hashed_password = local_auth.hash_password("TestPass123!")
    
    test_user = User(
        username="test_internal",
        password_hash=hashed_password,
        full_name="测试员工",
        email="test@company.com",
        user_type=UserType.INTERNAL,
        status=UserStatus.ACTIVE,
        department="质量部",
        password_changed_at=datetime.utcnow()
    )
    
    db_session.add(test_user)
    await db_session.commit()
    await db_session.refresh(test_user)
    
    # 执行登录
    response = await async_client.post(
        "/api/v1/auth/login",
        json={
            "username": "test_internal",
            "password": "TestPass123!",
            "user_type": "internal"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["password_expired"] is False
    assert data["user_info"]["username"] == "test_internal"
    assert data["user_info"]["user_type"] == "internal"


@pytest.mark.asyncio
async def test_login_invalid_credentials(async_client: AsyncClient, db_session: AsyncSession):
    """测试登录失败：错误的密码"""
    # 创建测试用户
    local_auth = LocalAuthStrategy()
    hashed_password = local_auth.hash_password("TestPass123!")
    
    test_user = User(
        username="test_user_fail",
        password_hash=hashed_password,
        full_name="测试用户",
        email="testfail@company.com",
        user_type=UserType.INTERNAL,
        status=UserStatus.ACTIVE,
        department="质量部",
        password_changed_at=datetime.utcnow()
    )
    
    db_session.add(test_user)
    await db_session.commit()
    
    # 使用错误密码登录
    response = await async_client.post(
        "/api/v1/auth/login",
        json={
            "username": "test_user_fail",
            "password": "WrongPassword123!",
            "user_type": "internal"
        }
    )
    
    assert response.status_code == 401
    assert "用户名或密码错误" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_pending_user(async_client: AsyncClient, db_session: AsyncSession):
    """测试登录失败：待审核用户"""
    # 创建待审核用户
    local_auth = LocalAuthStrategy()
    hashed_password = local_auth.hash_password("TestPass123!")
    
    test_user = User(
        username="test_pending",
        password_hash=hashed_password,
        full_name="待审核用户",
        email="pending@company.com",
        user_type=UserType.INTERNAL,
        status=UserStatus.PENDING,  # 待审核状态
        department="质量部"
    )
    
    db_session.add(test_user)
    await db_session.commit()
    
    # 尝试登录
    response = await async_client.post(
        "/api/v1/auth/login",
        json={
            "username": "test_pending",
            "password": "TestPass123!",
            "user_type": "internal"
        }
    )
    
    assert response.status_code == 403
    assert "待审核" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_captcha(async_client: AsyncClient):
    """测试获取验证码"""
    response = await async_client.get("/api/v1/auth/captcha")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "captcha_id" in data
    assert "captcha_image" in data
    assert data["captcha_image"].startswith("data:image/png;base64,")


@pytest.mark.asyncio
async def test_supplier_login_without_captcha(async_client: AsyncClient, db_session: AsyncSession):
    """测试供应商登录失败：未提供验证码"""
    # 创建供应商用户
    local_auth = LocalAuthStrategy()
    hashed_password = local_auth.hash_password("TestPass123!")
    
    test_user = User(
        username="test_supplier",
        password_hash=hashed_password,
        full_name="供应商用户",
        email="supplier@test.com",
        user_type=UserType.SUPPLIER,
        status=UserStatus.ACTIVE,
        supplier_id=1,
        password_changed_at=datetime.utcnow()
    )
    
    db_session.add(test_user)
    await db_session.commit()
    
    # 不提供验证码尝试登录
    response = await async_client.post(
        "/api/v1/auth/login",
        json={
            "username": "test_supplier",
            "password": "TestPass123!",
            "user_type": "supplier"
        }
    )
    
    assert response.status_code == 400
    assert "验证码" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_current_user_info(async_client: AsyncClient, db_session: AsyncSession):
    """测试获取当前用户信息"""
    # 创建测试用户
    local_auth = LocalAuthStrategy()
    hashed_password = local_auth.hash_password("TestPass123!")
    
    test_user = User(
        username="test_me",
        password_hash=hashed_password,
        full_name="测试用户",
        email="testme@company.com",
        user_type=UserType.INTERNAL,
        status=UserStatus.ACTIVE,
        department="质量部",
        position="工程师",
        password_changed_at=datetime.utcnow()
    )
    
    db_session.add(test_user)
    await db_session.commit()
    await db_session.refresh(test_user)
    
    # 先登录获取 Token
    login_response = await async_client.post(
        "/api/v1/auth/login",
        json={
            "username": "test_me",
            "password": "TestPass123!",
            "user_type": "internal"
        }
    )
    
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    
    # 使用 Token 获取用户信息
    response = await async_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["username"] == "test_me"
    assert data["full_name"] == "测试用户"
    assert data["email"] == "testme@company.com"
    assert data["department"] == "质量部"
    assert data["position"] == "工程师"


@pytest.mark.asyncio
async def test_get_current_user_info_without_token(async_client: AsyncClient):
    """测试未提供 Token 时获取用户信息失败"""
    response = await async_client.get("/api/v1/auth/me")
    
    assert response.status_code == 401
