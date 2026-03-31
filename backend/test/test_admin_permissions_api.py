"""
Admin permissions API tests aligned to the current matrix contract.
"""
from datetime import datetime

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth_strategy import LocalAuthStrategy
from app.core.config import settings
from app.models.permission import OperationType, Permission
from app.models.supplier import Supplier, SupplierStatus
from app.models.user import User, UserStatus, UserType

pytestmark = pytest.mark.foundation_smoke


async def _create_user(
    db_session: AsyncSession,
    *,
    username: str,
    password: str = "TestPass123!",
    full_name: str = "Test User",
    email: str | None = None,
    user_type: UserType = UserType.INTERNAL,
    status: UserStatus = UserStatus.ACTIVE,
    department: str | None = "Quality",
    position: str | None = "SQE",
    supplier_id: int | None = None,
) -> User:
    user = User(
        username=username,
        password_hash=LocalAuthStrategy().hash_password(password),
        full_name=full_name,
        email=email or f"{username}@example.com",
        user_type=user_type,
        status=status,
        department=department if user_type == UserType.INTERNAL else None,
        position=position,
        supplier_id=supplier_id,
        password_changed_at=datetime.utcnow(),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


async def _create_supplier(
    db_session: AsyncSession,
    *,
    name: str,
    code: str,
) -> Supplier:
    supplier = Supplier(
        name=name,
        code=code,
        status=SupplierStatus.ACTIVE,
    )
    db_session.add(supplier)
    await db_session.commit()
    await db_session.refresh(supplier)
    return supplier


def _auth_headers(user: User) -> dict[str, str]:
    token = LocalAuthStrategy().create_access_token(user.id)
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_get_permission_matrix_returns_modules_and_rows(
    async_client: AsyncClient, db_session: AsyncSession
):
    admin_username = settings.PLATFORM_ADMIN_USERNAMES.split(",")[0].strip() or "admin"
    admin_user = await _create_user(
        db_session,
        username=admin_username,
        password="AdminPass123!",
        full_name="Permission Admin",
    )
    internal_user = await _create_user(
        db_session,
        username="permission_internal",
        full_name="Permission Internal",
    )
    supplier = await _create_supplier(
        db_session,
        name="Permission Matrix Supplier",
        code="SUP-PERM-001",
    )
    supplier_user = await _create_user(
        db_session,
        username="permission_supplier",
        user_type=UserType.SUPPLIER,
        supplier_id=supplier.id,
        full_name="Permission Supplier User",
    )

    db_session.add(
        Permission(
            user_id=internal_user.id,
            module_path="supplier.management",
            operation_type=OperationType.READ,
            is_granted=True,
            created_by=admin_user.id,
        )
    )
    await db_session.commit()

    response = await async_client.get(
        "/api/v1/admin/permissions/matrix",
        headers=_auth_headers(admin_user),
    )

    assert response.status_code == 200
    data = response.json()
    assert sorted(data.keys()) == ["modules", "rows"]
    assert any(module["module_path"] == "supplier.management" for module in data["modules"])

    internal_row = next(row for row in data["rows"] if row["user"]["username"] == "permission_internal")
    supplier_row = next(row for row in data["rows"] if row["user"]["username"] == "permission_supplier")
    assert internal_row["permissions"]["supplier.management.read"] is True
    assert supplier_row["user"]["supplier_name"] == "Permission Matrix Supplier"
    assert supplier_row["user"]["is_platform_admin"] is False


@pytest.mark.asyncio
async def test_permission_matrix_requires_platform_admin(
    async_client: AsyncClient, db_session: AsyncSession
):
    regular_user = await _create_user(
        db_session,
        username="permission_viewer",
        password="ViewerPass123!",
    )

    response = await async_client.get(
        "/api/v1/admin/permissions/matrix",
        headers=_auth_headers(regular_user),
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_grant_permissions_creates_records(
    async_client: AsyncClient, db_session: AsyncSession
):
    admin_username = settings.PLATFORM_ADMIN_USERNAMES.split(",")[0].strip() or "admin"
    admin_user = await _create_user(
        db_session,
        username=admin_username,
        password="GrantAdmin123!",
    )
    target_user = await _create_user(
        db_session,
        username="grant_target_user",
        password="GrantTarget123!",
    )

    response = await async_client.put(
        "/api/v1/admin/permissions/grant",
        headers=_auth_headers(admin_user),
        json={
            "user_ids": [target_user.id],
            "permissions": [
                {"module_path": "supplier.management", "operation_type": "read"},
                {"module_path": "quality.incoming", "operation_type": "create"},
            ],
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["affected_users"] == 1
    assert data["affected_permissions"] == 2

    result = await db_session.execute(select(Permission).where(Permission.user_id == target_user.id))
    permissions = result.scalars().all()
    assert len(permissions) == 2
    assert all(permission.is_granted for permission in permissions)


@pytest.mark.asyncio
async def test_revoke_permissions_marks_existing_records_ungranted(
    async_client: AsyncClient, db_session: AsyncSession
):
    admin_username = settings.PLATFORM_ADMIN_USERNAMES.split(",")[0].strip() or "admin"
    admin_user = await _create_user(
        db_session,
        username=admin_username,
        password="RevokeAdmin123!",
    )
    target_user = await _create_user(
        db_session,
        username="revoke_target_user",
        password="RevokeTarget123!",
    )
    permission = Permission(
        user_id=target_user.id,
        module_path="test.module",
        operation_type=OperationType.READ,
        is_granted=True,
        created_by=admin_user.id,
    )
    db_session.add(permission)
    await db_session.commit()

    response = await async_client.put(
        "/api/v1/admin/permissions/revoke",
        headers=_auth_headers(admin_user),
        json={
            "user_ids": [target_user.id],
            "permissions": [
                {"module_path": "test.module", "operation_type": "read"},
            ],
        },
    )

    assert response.status_code == 200
    assert response.json()["affected_permissions"] == 1

    await db_session.refresh(permission)
    assert permission.is_granted is False
