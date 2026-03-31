"""
用户管理 API 测试
测试管理员用户审核、冻结、重置密码等操作
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.models.user import User, UserStatus, UserType
from app.core.auth_strategy import LocalAuthStrategy

pytestmark = pytest.mark.foundation_smoke


@pytest.fixture
async def admin_user(db_session: AsyncSession) -> User:
    """创建管理员用户"""
    auth_strategy = LocalAuthStrategy()
    hashed_password = auth_strategy.hash_password("AdminPass123!")
    
    admin = User(
        username="admin",
        password_hash=hashed_password,
        full_name="管理员",
        email="admin@company.com",
        phone="13800138000",
        user_type=UserType.INTERNAL,
        status=UserStatus.ACTIVE,
        department="质量部",
        position="系统管理员",
        password_changed_at=datetime.utcnow()
    )
    
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    
    return admin


@pytest.fixture
async def pending_user(db_session: AsyncSession) -> User:
    """创建待审核用户"""
    auth_strategy = LocalAuthStrategy()
    hashed_password = auth_strategy.hash_password("UserPass123!")
    
    user = User(
        username="pending_user",
        password_hash=hashed_password,
        full_name="张三",
        email="zhangsan@company.com",
        phone="13900139000",
        user_type=UserType.INTERNAL,
        status=UserStatus.PENDING,
        department="生产部",
        position="质量工程师"
    )
    
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    return user


@pytest.fixture
async def active_user(db_session: AsyncSession) -> User:
    """创建已激活用户"""
    auth_strategy = LocalAuthStrategy()
    hashed_password = auth_strategy.hash_password("UserPass123!")
    
    user = User(
        username="active_user",
        password_hash=hashed_password,
        full_name="李四",
        email="lisi@company.com",
        phone="13800138001",
        user_type=UserType.INTERNAL,
        status=UserStatus.ACTIVE,
        department="质量部",
        position="质量工程师",
        password_changed_at=datetime.utcnow()
    )
    
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    return user


@pytest.fixture
async def admin_token(async_client: AsyncClient, admin_user: User) -> str:
    """获取管理员 Token"""
    response = await async_client.post(
        "/api/v1/auth/login",
        json={
            "username": "admin",
            "password": "AdminPass123!",
            "user_type": "internal"
        }
    )
    assert response.status_code == 200
    return response.json()["access_token"]


class TestGetPendingUsers:
    """测试获取待审核用户列表"""
    
    @pytest.mark.asyncio
    async def test_get_pending_users_success(
        self,
        async_client: AsyncClient,
        admin_token: str,
        pending_user: User
    ):
        """测试成功获取待审核用户列表"""
        response = await async_client.get(
            "/api/v1/admin/users/pending",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        
        # 验证返回的用户信息
        pending_users = [u for u in data if u["username"] == "pending_user"]
        assert len(pending_users) == 1
        assert pending_users[0]["status"] == "pending"
        assert pending_users[0]["full_name"] == "张三"
    
    @pytest.mark.asyncio
    async def test_get_pending_users_unauthorized(
        self,
        async_client: AsyncClient,
        pending_user: User
    ):
        """测试未认证访问"""
        response = await async_client.get("/api/v1/admin/users/pending")
        assert response.status_code == 401


class TestApproveUser:
    """测试批准用户注册"""
    
    @pytest.mark.asyncio
    async def test_approve_user_success(
        self,
        async_client: AsyncClient,
        admin_token: str,
        pending_user: User,
        db_session: AsyncSession
    ):
        """测试成功批准用户"""
        response = await async_client.post(
            f"/api/v1/admin/users/{pending_user.id}/approve",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "用户已批准"
        assert data["user_id"] == pending_user.id
        assert data["username"] == "pending_user"
        assert data["status"] == "active"
        
        # 验证数据库中的状态已更新
        await db_session.refresh(pending_user)
        assert pending_user.status == UserStatus.ACTIVE
    
    @pytest.mark.asyncio
    async def test_approve_user_not_found(
        self,
        async_client: AsyncClient,
        admin_token: str
    ):
        """测试批准不存在的用户"""
        response = await async_client.post(
            "/api/v1/admin/users/99999/approve",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 404
        assert "用户不存在" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_approve_user_already_active(
        self,
        async_client: AsyncClient,
        admin_token: str,
        active_user: User
    ):
        """测试批准已激活的用户"""
        response = await async_client.post(
            f"/api/v1/admin/users/{active_user.id}/approve",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 400
        assert "无法批准" in response.json()["detail"]


class TestRejectUser:
    """测试拒绝用户注册"""
    
    @pytest.mark.asyncio
    async def test_reject_user_success(
        self,
        async_client: AsyncClient,
        admin_token: str,
        pending_user: User,
        db_session: AsyncSession
    ):
        """测试成功拒绝用户"""
        response = await async_client.post(
            f"/api/v1/admin/users/{pending_user.id}/reject",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"reason": "资料不完整"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "用户已拒绝" in data["message"]
        assert "资料不完整" in data["message"]
        assert data["user_id"] == pending_user.id
        assert data["status"] == "rejected"
        
        # 验证数据库中的状态已更新
        await db_session.refresh(pending_user)
        assert pending_user.status == UserStatus.REJECTED
    
    @pytest.mark.asyncio
    async def test_reject_user_without_reason(
        self,
        async_client: AsyncClient,
        admin_token: str,
        pending_user: User
    ):
        """测试拒绝用户时未填写原因"""
        response = await async_client.post(
            f"/api/v1/admin/users/{pending_user.id}/reject",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"reason": ""}
        )
        
        assert response.status_code == 400
        assert "必须填写拒绝原因" in response.json()["detail"]


class TestFreezeUser:
    """测试冻结用户账号"""
    
    @pytest.mark.asyncio
    async def test_freeze_user_success(
        self,
        async_client: AsyncClient,
        admin_token: str,
        active_user: User,
        db_session: AsyncSession
    ):
        """测试成功冻结用户"""
        response = await async_client.post(
            f"/api/v1/admin/users/{active_user.id}/freeze",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"reason": "供应商合作暂停"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "用户已冻结" in data["message"]
        assert data["status"] == "frozen"
        
        # 验证数据库中的状态已更新
        await db_session.refresh(active_user)
        assert active_user.status == UserStatus.FROZEN
    
    @pytest.mark.asyncio
    async def test_freeze_user_already_frozen(
        self,
        async_client: AsyncClient,
        admin_token: str,
        active_user: User,
        db_session: AsyncSession
    ):
        """测试冻结已冻结的用户"""
        # 先冻结用户
        active_user.status = UserStatus.FROZEN
        await db_session.commit()
        
        response = await async_client.post(
            f"/api/v1/admin/users/{active_user.id}/freeze",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"reason": "测试"}
        )
        
        assert response.status_code == 400
        assert "已处于冻结状态" in response.json()["detail"]


class TestUnfreezeUser:
    """测试解冻用户账号"""
    
    @pytest.mark.asyncio
    async def test_unfreeze_user_success(
        self,
        async_client: AsyncClient,
        admin_token: str,
        active_user: User,
        db_session: AsyncSession
    ):
        """测试成功解冻用户"""
        # 先冻结用户
        active_user.status = UserStatus.FROZEN
        await db_session.commit()
        
        response = await async_client.post(
            f"/api/v1/admin/users/{active_user.id}/unfreeze",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "用户已解冻"
        assert data["status"] == "active"
        
        # 验证数据库中的状态已更新
        await db_session.refresh(active_user)
        assert active_user.status == UserStatus.ACTIVE
    
    @pytest.mark.asyncio
    async def test_unfreeze_user_not_frozen(
        self,
        async_client: AsyncClient,
        admin_token: str,
        active_user: User
    ):
        """测试解冻未冻结的用户"""
        response = await async_client.post(
            f"/api/v1/admin/users/{active_user.id}/unfreeze",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 400
        assert "无法解冻" in response.json()["detail"]


class TestResetPassword:
    """测试重置用户密码"""
    
    @pytest.mark.asyncio
    async def test_reset_password_success(
        self,
        async_client: AsyncClient,
        admin_token: str,
        active_user: User,
        db_session: AsyncSession
    ):
        """测试成功重置密码"""
        response = await async_client.post(
            f"/api/v1/admin/users/{active_user.id}/reset-password",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "密码已重置" in data["message"]
        assert "temporary_password" in data
        assert len(data["temporary_password"]) >= 12
        
        # 验证临时密码包含所需字符类型
        temp_pass = data["temporary_password"]
        assert any(c.isupper() for c in temp_pass)  # 大写字母
        assert any(c.islower() for c in temp_pass)  # 小写字母
        assert any(c.isdigit() for c in temp_pass)  # 数字
        assert any(c in "!@#$%^&*" for c in temp_pass)  # 特殊字符
        
        # 验证数据库中的密码已更新且 password_changed_at 被清空
        await db_session.refresh(active_user)
        assert active_user.password_changed_at is None
        assert active_user.failed_login_attempts == 0
        assert active_user.locked_until is None
    
    @pytest.mark.asyncio
    async def test_reset_password_user_not_found(
        self,
        async_client: AsyncClient,
        admin_token: str
    ):
        """测试重置不存在用户的密码"""
        response = await async_client.post(
            "/api/v1/admin/users/99999/reset-password",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 404
        assert "用户不存在" in response.json()["detail"]
