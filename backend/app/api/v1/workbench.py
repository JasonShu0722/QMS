"""
工作台 API 路由
Workbench API - 工作台首页数据聚合接口
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import Optional, List, Any

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.platform_admin import is_platform_admin
from app.core.config import settings
from app.models.user import User, UserType
from app.services.feature_flag_service import FeatureFlagService
from app.services.task_aggregator import task_aggregator
from app.services.user_session_service import build_user_response


router = APIRouter(prefix="/workbench", tags=["workbench"])


# ==================== 响应模型 ====================

class MetricItem(BaseModel):
    """指标数据项"""
    key: str = Field(..., description="指标唯一标识")
    name: str = Field(..., description="指标名称")
    value: Any = Field(..., description="指标值")
    status: str = Field("good", description="状态: good/warning/danger")
    achievement: Optional[float] = Field(None, description="达成率（百分比）")
    unit: Optional[str] = Field(None, description="单位")


class TodoTaskItem(BaseModel):
    """待办任务项（轻量版，用于工作台）"""
    task_type: str = Field(..., description="任务类型")
    task_id: Any = Field(..., description="单据编号")
    deadline: Optional[str] = Field(None, description="截止时间")
    remaining_hours: float = Field(0, description="剩余处理时间（小时）")
    urgency: str = Field("normal", description="紧急程度: overdue/urgent/normal")
    color: str = Field("green", description="颜色标识: red/yellow/green")
    link: str = Field("", description="跳转链接")
    title: Optional[str] = Field(None, description="任务标题")
    description: Optional[str] = Field(None, description="任务描述")


class PerformanceStatus(BaseModel):
    """供应商绩效状态"""
    grade: str = Field("B", description="绩效等级: A/B/C/D")
    score: float = Field(0, description="当前得分")
    deduction_this_month: float = Field(0, description="本月扣分")


class InternalDashboardResponse(BaseModel):
    """内部员工工作台数据"""
    user_info: Any = Field(..., description="稳定的用户会话信息")
    environment: str = Field(..., description="当前环境")
    quick_actions: List[dict[str, str]] = Field(default_factory=list, description="快捷入口")
    feature_blocks: dict[str, bool] = Field(default_factory=dict, description="按能力区块暴露的开关状态")
    metrics: List[MetricItem] = Field(default_factory=list, description="指标监控")
    todos: List[TodoTaskItem] = Field(default_factory=list, description="待办任务")
    notifications: int = Field(0, description="未读消息数量")


class SupplierDashboardResponse(BaseModel):
    """供应商工作台数据"""
    user_info: Any = Field(..., description="稳定的用户会话信息")
    environment: str = Field(..., description="当前环境")
    quick_actions: List[dict[str, str]] = Field(default_factory=list, description="快捷入口")
    feature_blocks: dict[str, bool] = Field(default_factory=dict, description="按能力区块暴露的开关状态")
    performance_status: Optional[PerformanceStatus] = Field(None, description="绩效状态")
    action_required_tasks: List[TodoTaskItem] = Field(default_factory=list, description="待处理任务")


# ==================== 路由 ====================

@router.get(
    "/dashboard",
    summary="获取工作台数据",
    description="""
    获取当前用户的工作台首页数据。
    
    根据用户类型返回不同的数据结构：
    - 内部员工：指标监控 + 待办任务 + 未读消息数
    - 供应商用户：绩效状态 + 待处理任务
    
    注：指标监控和绩效数据为预留接口，当前阶段返回空数据。
    待办任务通过任务聚合服务从各业务表动态聚合。
    """
)
async def get_dashboard_data(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取工作台数据

    Args:
        current_user: 当前登录用户
        db: 数据库会话

    Returns:
        工作台数据（内部员工或供应商视图）
    """
    try:
        # 获取待办任务
        tasks = await task_aggregator.get_user_tasks(db, current_user.id)
        todo_items = [
            TodoTaskItem(
                task_type=t.task_type,
                task_id=t.task_number if hasattr(t, 'task_number') else t.task_id,
                deadline=t.deadline.isoformat() if t.deadline else None,
                remaining_hours=t.remaining_hours,
                urgency=t.urgency,
                color=t.color,
                link=t.link,
                title=t.title if hasattr(t, 'title') else None,
                description=t.description if hasattr(t, 'description') else None,
            )
            for t in tasks
        ]
    except Exception:
        # 任务聚合服务可能因业务表未创建而失败，返回空列表
        todo_items = []

    session_user = await build_user_response(db, current_user)
    metrics_enabled = await FeatureFlagService.is_feature_enabled(
        db, "foundation.workbench.metrics", current_user.id, current_user.supplier_id, settings.ENVIRONMENT
    )
    announcements_enabled = await FeatureFlagService.is_feature_enabled(
        db, "foundation.workbench.announcements", current_user.id, current_user.supplier_id, settings.ENVIRONMENT
    )

    quick_actions = [
        {"title": "个人中心", "description": "查看资料、修改密码与电子签名", "link": "/workbench"},
    ]
    if is_platform_admin(current_user):
        quick_actions.extend(
            [
                {"title": "用户管理", "description": "审核注册申请并治理平台账号", "link": "/admin/users"},
                {"title": "权限矩阵", "description": "配置平台模块与操作权限矩阵", "link": "/admin/permissions"},
                {"title": "功能开关", "description": "管理正式与预览环境的功能可见性", "link": "/admin/feature-flags"},
            ]
        )

    feature_blocks = {
        "metrics": metrics_enabled,
        "announcements": announcements_enabled,
        "notifications": False,
    }

    if current_user.user_type == UserType.INTERNAL:
        # 内部员工视图
        return InternalDashboardResponse(
            user_info=session_user.model_dump(mode="json"),
            environment=settings.ENVIRONMENT,
            quick_actions=quick_actions,
            feature_blocks=feature_blocks,
            metrics=[
                MetricItem(
                    key="foundation.pending_reviews",
                    name="待处理事项",
                    value=len(todo_items),
                    status="warning" if todo_items else "good",
                    achievement=100 if not todo_items else max(0, 100 - len(todo_items) * 10),
                )
            ] if metrics_enabled else [],
            todos=todo_items,
            notifications=0,  # 未读消息数预留
        )
    else:
        # 供应商视图
        return SupplierDashboardResponse(
            user_info=session_user.model_dump(mode="json"),
            environment=settings.ENVIRONMENT,
            quick_actions=quick_actions,
            feature_blocks=feature_blocks,
            performance_status=None,  # 绩效数据预留
            action_required_tasks=todo_items,
        )
