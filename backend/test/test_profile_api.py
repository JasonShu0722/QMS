"""
个人信息管理 API 测试
测试个人信息查询、密码修改、电子签名上传功能
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from pathlib import Path
import io
from PIL import Image

from app.models.user import User, UserStatus, UserType
from app.core.auth_strategy import LocalAuthStrategy

pytestmark = pytest.mark.foundation_smoke


class TestGetProfile:
    """测试获取个人信息"""
    
    @pytest.mark.asyncio
    async def test_get_profile_success(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_user_token: str
    ):
        """测试成功获取个人信息"""
        response = await async_client.get(
            "/api/v1/profile",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == test_user.id
        assert data["username"] == test_user.username
        assert data["full_name"] == test_user.full_name
        assert data["email"] == test_user.email
        assert data["user_type"] == test_user.user_type
        assert data["status"] == test_user.status
        assert data["department"] == test_user.department
        assert data["position"] == test_user.position
    
    @pytest.mark.asyncio
    async def test_get_profile_without_token(self, async_client: AsyncClient):
        """测试未提供 Token 时返回 403"""
        response = await async_client.get("/api/v1/profile")
        
        assert response.status_code == 401


class TestUpdateProfile:
    """测试更新个人信息"""

    @pytest.mark.asyncio
    async def test_update_profile_success(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_user_token: str,
        db_session: AsyncSession
    ):
        response = await async_client.patch(
            "/api/v1/profile",
            headers={"Authorization": f"Bearer {test_user_token}"},
            json={
                "full_name": "新测试用户",
                "email": "updated@example.com",
                "phone": "13900001111",
                "department": "信息技术部",
                "position": "平台管理员"
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert data["full_name"] == "新测试用户"
        assert data["email"] == "updated@example.com"
        assert data["phone"] == "13900001111"
        assert data["department"] == "信息技术部"
        assert data["position"] == "平台管理员"

        await db_session.refresh(test_user)
        assert test_user.full_name == "新测试用户"
        assert test_user.email == "updated@example.com"
        assert test_user.phone == "13900001111"
        assert test_user.department == "信息技术部"
        assert test_user.position == "平台管理员"

    @pytest.mark.asyncio
    async def test_update_profile_requires_payload(
        self,
        async_client: AsyncClient,
        test_user_token: str
    ):
        response = await async_client.patch(
            "/api/v1/profile",
            headers={"Authorization": f"Bearer {test_user_token}"},
            json={}
        )

        assert response.status_code == 400
        assert "至少提供一项需要更新的信息" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_update_profile_can_clear_optional_fields(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_user_token: str,
        db_session: AsyncSession
    ):
        test_user.phone = "13900001111"
        test_user.department = "质量部"
        test_user.position = "质量工程师"
        await db_session.commit()
        await db_session.refresh(test_user)

        response = await async_client.patch(
            "/api/v1/profile",
            headers={"Authorization": f"Bearer {test_user_token}"},
            json={
                "phone": None,
                "department": None,
                "position": None
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert data["phone"] is None
        assert data["department"] is None
        assert data["position"] is None

        await db_session.refresh(test_user)
        assert test_user.phone is None
        assert test_user.department is None
        assert test_user.position is None

    @pytest.mark.asyncio
    async def test_update_profile_blank_full_name_rejected(
        self,
        async_client: AsyncClient,
        test_user_token: str
    ):
        response = await async_client.patch(
            "/api/v1/profile",
            headers={"Authorization": f"Bearer {test_user_token}"},
            json={
                "full_name": "   ",
                "phone": "13900001111"
            }
        )

        assert response.status_code == 422
        errors = response.json()["detail"]
        assert any("姓名不能为空" in error["msg"] for error in errors)

    @pytest.mark.asyncio
    async def test_supplier_cannot_update_department(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession
    ):
        auth_strategy = LocalAuthStrategy()
        supplier_user = User(
            username="supplier_profile_user",
            password_hash=auth_strategy.hash_password("Test@1234"),
            full_name="供应商用户",
            email="supplier@example.com",
            phone="13800138001",
            user_type=UserType.SUPPLIER,
            status=UserStatus.ACTIVE,
            department=None,
            position="质量接口人",
            password_changed_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(supplier_user)
        await db_session.commit()
        await db_session.refresh(supplier_user)

        supplier_token = auth_strategy.create_access_token(supplier_user.id)

        response = await async_client.patch(
            "/api/v1/profile",
            headers={"Authorization": f"Bearer {supplier_token}"},
            json={
                "department": "信息技术部",
                "position": "供应商经理"
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert data["department"] is None
        assert data["position"] == "供应商经理"

        await db_session.refresh(supplier_user)
        assert supplier_user.department is None
        assert supplier_user.position == "供应商经理"


class TestChangePassword:
    """测试修改密码"""
    
    @pytest.mark.asyncio
    async def test_change_password_success(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_user_token: str,
        db_session: AsyncSession
    ):
        """测试成功修改密码"""
        response = await async_client.put(
            "/api/v1/profile/password",
            headers={"Authorization": f"Bearer {test_user_token}"},
            json={
                "old_password": "Test@1234",
                "new_password": "NewPass@5678"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["message"] == "密码修改成功，请重新登录"
        assert "password_changed_at" in data
        
        # 验证数据库中密码已更新
        await db_session.refresh(test_user)
        auth_strategy = LocalAuthStrategy()
        assert auth_strategy.verify_password("NewPass@5678", test_user.password_hash)
        assert test_user.password_changed_at is not None
    
    @pytest.mark.asyncio
    async def test_change_password_wrong_old_password(
        self,
        async_client: AsyncClient,
        test_user_token: str
    ):
        """测试旧密码错误"""
        response = await async_client.put(
            "/api/v1/profile/password",
            headers={"Authorization": f"Bearer {test_user_token}"},
            json={
                "old_password": "WrongPassword",
                "new_password": "NewPass@5678"
            }
        )
        
        assert response.status_code == 400
        assert "旧密码错误" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_change_password_same_as_old(
        self,
        async_client: AsyncClient,
        test_user_token: str
    ):
        """测试新密码与旧密码相同"""
        response = await async_client.put(
            "/api/v1/profile/password",
            headers={"Authorization": f"Bearer {test_user_token}"},
            json={
                "old_password": "Test@1234",
                "new_password": "Test@1234"
            }
        )
        
        assert response.status_code == 400
        assert "新密码不能与旧密码相同" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_change_password_weak_password(
        self,
        async_client: AsyncClient,
        test_user_token: str
    ):
        """测试弱密码（不符合复杂度要求）"""
        # 测试长度不足
        response = await async_client.put(
            "/api/v1/profile/password",
            headers={"Authorization": f"Bearer {test_user_token}"},
            json={
                "old_password": "Test@1234",
                "new_password": "Short1"
            }
        )
        
        assert response.status_code == 422
        
        # 测试复杂度不足（只有小写和数字）
        response = await async_client.put(
            "/api/v1/profile/password",
            headers={"Authorization": f"Bearer {test_user_token}"},
            json={
                "old_password": "Test@1234",
                "new_password": "onlylowercase123"
            }
        )
        
        assert response.status_code == 422


class TestUploadSignature:
    """测试上传电子签名"""
    
    @pytest.mark.asyncio
    async def test_upload_signature_success(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_user_token: str,
        db_session: AsyncSession,
        tmp_path: Path
    ):
        """测试成功上传电子签名"""
        # 创建测试图片
        image = Image.new('RGB', (200, 100), color='white')
        # 在图片上绘制一些黑色内容（模拟签名）
        from PIL import ImageDraw
        draw = ImageDraw.Draw(image)
        draw.text((50, 40), "签名", fill='black')
        
        # 保存到内存
        img_bytes = io.BytesIO()
        image.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        # 上传签名
        response = await async_client.post(
            "/api/v1/profile/signature",
            headers={"Authorization": f"Bearer {test_user_token}"},
            files={"file": ("signature.png", img_bytes, "image/png")}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["message"] == "电子签名上传成功"
        assert "signature_path" in data
        assert data["signature_path"].startswith("/uploads/signatures/")
        assert data["signature_path"].endswith(".png")
        
        # 验证数据库中签名路径已更新
        await db_session.refresh(test_user)
        assert test_user.digital_signature == data["signature_path"]
    
    @pytest.mark.asyncio
    async def test_upload_signature_invalid_format(
        self,
        async_client: AsyncClient,
        test_user_token: str
    ):
        """测试上传不支持的文件格式"""
        # 创建一个文本文件
        file_content = b"This is not an image"
        
        response = await async_client.post(
            "/api/v1/profile/signature",
            headers={"Authorization": f"Bearer {test_user_token}"},
            files={"file": ("signature.txt", io.BytesIO(file_content), "text/plain")}
        )
        
        assert response.status_code == 400
        assert "不支持的文件格式" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_upload_signature_without_token(self, async_client: AsyncClient):
        """测试未提供 Token 时返回 403"""
        image = Image.new('RGB', (200, 100), color='white')
        img_bytes = io.BytesIO()
        image.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        response = await async_client.post(
            "/api/v1/profile/signature",
            files={"file": ("signature.png", img_bytes, "image/png")}
        )
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_upload_signature_replaces_old(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_user_token: str,
        db_session: AsyncSession
    ):
        """测试上传新签名会替换旧签名"""
        # 第一次上传
        image1 = Image.new('RGB', (200, 100), color='white')
        img_bytes1 = io.BytesIO()
        image1.save(img_bytes1, format='PNG')
        img_bytes1.seek(0)
        
        response1 = await async_client.post(
            "/api/v1/profile/signature",
            headers={"Authorization": f"Bearer {test_user_token}"},
            files={"file": ("signature1.png", img_bytes1, "image/png")}
        )
        
        assert response1.status_code == 200
        first_signature_path = response1.json()["signature_path"]
        
        # 第二次上传
        image2 = Image.new('RGB', (200, 100), color='blue')
        img_bytes2 = io.BytesIO()
        image2.save(img_bytes2, format='PNG')
        img_bytes2.seek(0)
        
        response2 = await async_client.post(
            "/api/v1/profile/signature",
            headers={"Authorization": f"Bearer {test_user_token}"},
            files={"file": ("signature2.png", img_bytes2, "image/png")}
        )
        
        assert response2.status_code == 200
        second_signature_path = response2.json()["signature_path"]
        
        # 验证签名路径已更新
        assert first_signature_path != second_signature_path
        
        await db_session.refresh(test_user)
        assert test_user.digital_signature == second_signature_path
