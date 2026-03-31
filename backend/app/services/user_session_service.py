"""
Helpers for building stable user/session API payloads.
"""
from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.platform_admin import is_platform_admin
from app.models.supplier import Supplier
from app.models.user import User
from app.schemas.user import UserResponseSchema


async def _load_supplier_names(db: AsyncSession, users: Iterable[User]) -> dict[int, str]:
    supplier_ids = sorted({user.supplier_id for user in users if user.supplier_id})
    if not supplier_ids:
        return {}

    result = await db.execute(
        select(Supplier.id, Supplier.name).where(Supplier.id.in_(supplier_ids))
    )
    return {supplier_id: name for supplier_id, name in result.all()}


def _serialize_user(user: User, supplier_name: str | None = None) -> UserResponseSchema:
    return UserResponseSchema(
        id=user.id,
        username=user.username,
        full_name=user.full_name,
        email=user.email,
        phone=user.phone,
        user_type=user.user_type,
        status=user.status,
        department=user.department,
        position=user.position,
        supplier_id=user.supplier_id,
        supplier_name=supplier_name,
        avatar_image_path=user.avatar_image_path,
        signature_image_path=user.digital_signature,
        digital_signature=user.digital_signature,
        allowed_environments=user.allowed_environments,
        is_platform_admin=is_platform_admin(user),
        last_login_at=user.last_login_at,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


async def build_user_response(db: AsyncSession, user: User) -> UserResponseSchema:
    supplier_name_map = await _load_supplier_names(db, [user])
    return _serialize_user(user, supplier_name_map.get(user.supplier_id))


async def build_user_responses(db: AsyncSession, users: Iterable[User]) -> list[UserResponseSchema]:
    user_list = list(users)
    supplier_name_map = await _load_supplier_names(db, user_list)
    return [
        _serialize_user(user, supplier_name_map.get(user.supplier_id))
        for user in user_list
    ]
