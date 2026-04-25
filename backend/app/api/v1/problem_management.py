"""
Shared problem-management metadata and first-batch read-only issue summary APIs.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
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
    ProblemIssueSummaryListResponse,
    ProblemIssueSummaryQuery,
    ProblemManagementCatalogResponse,
    UnifiedProblemStatus,
)
from app.services.problem_management_service import ProblemManagementService

router = APIRouter(
    prefix="/problem-management",
    tags=["Problem Management - Shared Capabilities"],
)


@router.get(
    "/catalog",
    response_model=ProblemManagementCatalogResponse,
    summary="Get shared problem-management catalog",
)
async def get_problem_management_catalog(
    current_user: User = Depends(get_current_user),
):
    """Return the confirmed cross-module problem-management metadata."""

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


@router.get(
    "/issues",
    response_model=ProblemIssueSummaryListResponse,
    summary="Get first-batch unified problem summaries",
)
async def list_problem_issue_summaries(
    module_key: str | None = Query(None, description="Module key"),
    problem_category_key: str | None = Query(None, description="Problem category key"),
    unified_status: UnifiedProblemStatus | None = Query(None, description="Unified status"),
    keyword: str | None = Query(None, description="Keyword"),
    only_assigned_to_me: bool = Query(False, description="Only include items assigned to the current user"),
    only_actionable_to_me: bool = Query(
        False,
        description="Only include items that the current user can handle directly from the problem center",
    ),
    only_created_by_me: bool = Query(False, description="Only include items created by the current user"),
    only_overdue: bool = Query(False, description="Only include overdue items"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return the first read-only unified issue summary list across confirmed modules."""

    query = ProblemIssueSummaryQuery(
        module_key=module_key,
        problem_category_key=problem_category_key,
        unified_status=unified_status,
        keyword=keyword,
        only_assigned_to_me=only_assigned_to_me,
        only_actionable_to_me=only_actionable_to_me,
        only_created_by_me=only_created_by_me,
        only_overdue=only_overdue,
        page=page,
        page_size=page_size,
    )

    return await ProblemManagementService.list_problem_issue_summaries(
        db=db,
        current_user=current_user,
        query=query,
    )
