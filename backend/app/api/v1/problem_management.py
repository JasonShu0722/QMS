"""
跨模块问题管理共享元数据 API
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user
from app.core.problem_management import (
    EIGHT_D_NUMBER_PREFIX,
    ISSUE_NUMBER_PREFIX,
    PROBLEM_CATEGORY_CATALOG,
    HandlingLevel,
    ResponseMode,
)
from app.models.user import User
from app.schemas.problem_management import (
    NumberingRuleItem,
    ProblemCategoryItem,
    ProblemManagementCatalogResponse,
)

router = APIRouter(
    prefix="/problem-management",
    tags=["Problem Management - 问题管理共享能力"],
)


@router.get(
    "/catalog",
    response_model=ProblemManagementCatalogResponse,
    summary="获取问题管理共享字典",
    description="""
    返回跨模块问题管理当前已确认的共享元数据：
    - 回复形式
    - 处理复杂度
    - 分类编码
    - 统一编号规则
    """,
)
async def get_problem_management_catalog(
    current_user: User = Depends(get_current_user),
):
    """获取问题管理共享字典"""

    return ProblemManagementCatalogResponse(
        response_modes=[mode.value for mode in ResponseMode],
        handling_levels=[level.value for level in HandlingLevel],
        categories=[
            ProblemCategoryItem(
                key=item.key,
                category_code=item.category_code,
                subcategory_code=item.subcategory_code,
                module_key=item.module_key,
                label=item.label,
            )
            for item in PROBLEM_CATEGORY_CATALOG.values()
        ],
        numbering_rule=NumberingRuleItem(
            issue_prefix=ISSUE_NUMBER_PREFIX,
            report_prefix=EIGHT_D_NUMBER_PREFIX,
            issue_pattern="ZXQ-<分类子类>-<YYMM>-<SEQ3>",
            report_pattern="ZX8D-<分类子类>-<YYMM>-<SEQ3>",
        ),
    )
