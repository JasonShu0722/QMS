"""
Foundation-aware task aggregation service.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.platform_admin import is_platform_admin
from app.models.feature_flag import FeatureFlag, FeatureFlagEnvironment
from app.models.permission import Permission
from app.models.user import User, UserStatus


class TaskItem:
    """
    Lightweight task item for workbench usage.
    """

    def __init__(
        self,
        task_type: str,
        task_id: int,
        task_number: str,
        deadline: Optional[datetime],
        urgency: str,
        color: str,
        remaining_hours: float,
        link: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
    ):
        self.task_type = task_type
        self.task_id = task_id
        self.task_number = task_number
        self.deadline = deadline
        self.urgency = urgency
        self.color = color
        self.remaining_hours = remaining_hours
        self.link = link
        self.title = title
        self.description = description


class TaskAggregator:
    """
    Aggregates a v1 set of real foundation-domain tasks and optional business tasks.
    """

    @staticmethod
    def _calculate_remaining(deadline: Optional[datetime]) -> float:
        if deadline is None:
            return float("inf")

        return (deadline - datetime.utcnow()).total_seconds() / 3600

    @staticmethod
    def _calculate_urgency(deadline: Optional[datetime]) -> tuple[str, str]:
        remaining_hours = TaskAggregator._calculate_remaining(deadline)
        if remaining_hours < 0:
            return ("overdue", "red")
        if remaining_hours <= 72:
            return ("urgent", "yellow")
        return ("normal", "green")

    @staticmethod
    async def _load_pending_user_tasks(db: AsyncSession) -> list[TaskItem]:
        result = await db.execute(
            select(User).where(User.status == UserStatus.PENDING).order_by(User.created_at.asc())
        )
        pending_users = result.scalars().all()

        tasks: list[TaskItem] = []
        for user in pending_users:
            deadline = user.created_at + timedelta(days=2)
            urgency, color = TaskAggregator._calculate_urgency(deadline)
            target_name = user.department or (
                f"Supplier {user.supplier_id}" if user.supplier_id else "Unassigned"
            )
            tasks.append(
                TaskItem(
                    task_type="注册审批",
                    task_id=100000 + user.id,
                    task_number=f"USR-{user.id}",
                    deadline=deadline,
                    urgency=urgency,
                    color=color,
                    remaining_hours=TaskAggregator._calculate_remaining(deadline),
                    link="/admin/users",
                    title=f"审核注册申请：{user.full_name}",
                    description=f"账号 {user.username} 待审核，用户类型为 {user.user_type}，归属对象：{target_name}",
                )
            )

        return tasks

    @staticmethod
    async def _load_permission_bootstrap_task(db: AsyncSession) -> list[TaskItem]:
        permission_count = await db.scalar(select(func.count(Permission.id)))
        if permission_count and permission_count > 0:
            return []

        deadline = datetime.utcnow() + timedelta(days=1)
        urgency, color = TaskAggregator._calculate_urgency(deadline)
        return [
            TaskItem(
                task_type="权限初始化",
                task_id=200001,
                task_number="PERM-BOOTSTRAP",
                deadline=deadline,
                urgency=urgency,
                color=color,
                remaining_hours=TaskAggregator._calculate_remaining(deadline),
                link="/admin/permissions",
                title="初始化平台权限矩阵",
                description="当前尚未生成权限记录，请完成首轮模块授权配置。",
            )
        ]

    @staticmethod
    async def _load_preview_flag_review_task(db: AsyncSession) -> list[TaskItem]:
        preview_count = await db.scalar(
            select(func.count(FeatureFlag.id)).where(
                FeatureFlag.environment == FeatureFlagEnvironment.PREVIEW,
                FeatureFlag.is_enabled == True,
            )
        )
        if not preview_count:
            return []

        deadline = datetime.utcnow() + timedelta(days=3)
        urgency, color = TaskAggregator._calculate_urgency(deadline)
        return [
            TaskItem(
                task_type="预览环境治理",
                task_id=200002,
                task_number="FLAG-PREVIEW",
                deadline=deadline,
                urgency=urgency,
                color=color,
                remaining_hours=TaskAggregator._calculate_remaining(deadline),
                link="/admin/feature-flags",
                title="复核预览环境功能开关",
                description=f"当前共有 {preview_count} 个预览环境功能已启用，请确认灰度范围与发布节奏。",
            )
        ]

    @staticmethod
    async def get_user_tasks(db: AsyncSession, user_id: int) -> list[TaskItem]:
        user = await db.get(User, user_id)
        if not user:
            return []

        tasks: list[TaskItem] = []
        if is_platform_admin(user):
            tasks.extend(await TaskAggregator._load_pending_user_tasks(db))
            tasks.extend(await TaskAggregator._load_permission_bootstrap_task(db))
            tasks.extend(await TaskAggregator._load_preview_flag_review_task(db))

        tasks.sort(key=lambda item: item.remaining_hours)
        return tasks

    @staticmethod
    async def get_task_statistics(db: AsyncSession, user_id: int) -> dict[str, Any]:
        tasks = await TaskAggregator.get_user_tasks(db, user_id)
        return {
            "total": len(tasks),
            "overdue": sum(1 for task in tasks if task.urgency == "overdue"),
            "urgent": sum(1 for task in tasks if task.urgency == "urgent"),
            "normal": sum(1 for task in tasks if task.urgency == "normal"),
        }


task_aggregator = TaskAggregator()
