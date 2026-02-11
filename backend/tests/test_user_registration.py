"""
用户注册 API 测试
测试用户注册和供应商搜索接口
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.main import app
from app.core.database import get_db
from app.models.base import Base
from app.models.user import User, UserType, UserStatus
from app.models.supplier import Supplier, SupplierStatus


# 测试数据库 URL（使用 SQLite 内存数据库）
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# 创建测试数据库引擎
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    poolclass=NullPool,
    future=True,
)

# 创建测试会话工厂
TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def override_get_db():
    """覆盖数据库依赖，使用测试数据库"""
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# 覆盖应用的数据库依赖
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function")
async def db_session():
    """创建测试数据库会话"""
    # 创建所有表
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # 创建会话
    async with TestSessionLocal() as session:
        yield session
    
    # 清理所有表
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def test_supplier(db_session: AsyncSession):
    """创建测试供应商"""
    supplier = Supplier(
        name="深圳市测试电子有限公司",
        code="SUP001",
        contact_person="张三",
        contact_email="zhangsan@test.com",
        contact_phone="13800138000",
        status=SupplierStatus.ACTIVE
    )
    db_session.add(supplier)
    await db_session.commit()
    await db_session.refresh(supplier)
    return supplier


@pytest.fixture
async def client():
    """创建测试客户端"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


class TestUserRegistration:
    """测试用户注册接口"""
    
    @pytest.mark.asyncio
    async def test_register_internal_user_success(self, client: AsyncClient, db_session: AsyncSession):
        """测试内部员工注册成功"""
        register_data = {
            "username": "zhang_san",
            "password": "SecurePass123!",
            "full_name": "张三",
            "email": "zhangsan@company.com",
            "phone": "13800138000",
            "user_type": "internal",
            "department": "质量部",
            "position": "质量工程师"
        }
        
        response = await client.post("/api/v1/auth/register", json=register_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "注册成功，请等待管理员审核"
        assert data["username"] == "zhang_san"
        assert data["status"] == "pending"
        assert "user_id" in data
    
    @pytest.mark.asyncio
    async def test_register_supplier_user_success(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_supplier: Supplier
    ):
        """测试供应商用户注册成功"""
        register_data = {
            "username": "supplier_user",
            "password": "SupplierPass456!",
            "full_name": "李四",
            "email": "lisi@supplier.com",
            "phone": "13900139000",
            "user_type": "supplier",
            "supplier_id": test_supplier.id,
            "position": "质量经理"
        }
        
        response = await client.post("/api/v1/auth/register", json=register_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "注册成功，请等待管理员审核"
        assert data["username"] == "supplier_user"
        assert data["status"] == "pending"
    
    @pytest.mark.asyncio
    async def test_register_duplicate_username(self, client: AsyncClient, db_session: AsyncSession):
        """测试重复用户名注册失败"""
        # 第一次注册
        register_data = {
            "username": "duplicate_user",
            "password": "SecurePass123!",
            "full_name": "测试用户",
            "email": "test@company.com",
            "user_type": "internal",
            "department": "质量部"
        }
        
        response1 = await client.post("/api/v1/auth/register", json=register_data)
        assert response1.status_code == 201
        
        # 第二次注册相同用户名
        response2 = await client.post("/api/v1/auth/register", json=register_data)
        assert response2.status_code == 400
        assert "用户名已存在" in response2.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_register_weak_password(self, client: AsyncClient, db_session: AsyncSession):
        """测试弱密码注册失败"""
        register_data = {
            "username": "weak_pass_user",
            "password": "weak123",  # 只有小写和数字，复杂度不足
            "full_name": "测试用户",
            "email": "test@company.com",
            "user_type": "internal",
            "department": "质量部"
        }
        
        response = await client.post("/api/v1/auth/register", json=register_data)
        assert response.status_code == 400
        assert "至少三种" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_register_internal_without_department(self, client: AsyncClient, db_session: AsyncSession):
        """测试内部员工注册缺少部门字段"""
        register_data = {
            "username": "no_dept_user",
            "password": "SecurePass123!",
            "full_name": "测试用户",
            "email": "test@company.com",
            "user_type": "internal"
            # 缺少 department 字段
        }
        
        response = await client.post("/api/v1/auth/register", json=register_data)
        assert response.status_code == 400
        assert "部门为必填项" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_register_supplier_without_supplier_id(self, client: AsyncClient, db_session: AsyncSession):
        """测试供应商用户注册缺少供应商ID"""
        register_data = {
            "username": "no_supplier_user",
            "password": "SecurePass123!",
            "full_name": "测试用户",
            "email": "test@supplier.com",
            "user_type": "supplier"
            # 缺少 supplier_id 字段
        }
        
        response = await client.post("/api/v1/auth/register", json=register_data)
        assert response.status_code == 400
        assert "必须选择供应商名称" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_register_supplier_invalid_supplier_id(self, client: AsyncClient, db_session: AsyncSession):
        """测试供应商用户注册使用无效的供应商ID"""
        register_data = {
            "username": "invalid_supplier_user",
            "password": "SecurePass123!",
            "full_name": "测试用户",
            "email": "test@supplier.com",
            "user_type": "supplier",
            "supplier_id": 99999  # 不存在的供应商ID
        }
        
        response = await client.post("/api/v1/auth/register", json=register_data)
        assert response.status_code == 400
        assert "供应商不存在" in response.json()["detail"]


class TestSupplierSearch:
    """测试供应商搜索接口"""
    
    @pytest.mark.asyncio
    async def test_search_suppliers_by_name(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_supplier: Supplier
    ):
        """测试按名称搜索供应商"""
        response = await client.get("/api/v1/auth/suppliers/search?q=测试")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert data[0]["name"] == "深圳市测试电子有限公司"
        assert data[0]["code"] == "SUP001"
        assert data[0]["status"] == "active"
    
    @pytest.mark.asyncio
    async def test_search_suppliers_by_code(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_supplier: Supplier
    ):
        """测试按代码搜索供应商"""
        response = await client.get("/api/v1/auth/suppliers/search?q=SUP001")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert data[0]["code"] == "SUP001"
    
    @pytest.mark.asyncio
    async def test_search_suppliers_no_results(self, client: AsyncClient, db_session: AsyncSession):
        """测试搜索无结果"""
        response = await client.get("/api/v1/auth/suppliers/search?q=不存在的供应商")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0
    
    @pytest.mark.asyncio
    async def test_search_suppliers_empty_query(self, client: AsyncClient, db_session: AsyncSession):
        """测试空搜索关键词"""
        response = await client.get("/api/v1/auth/suppliers/search?q=")
        
        # 应该返回 422 验证错误（min_length=1）
        assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

