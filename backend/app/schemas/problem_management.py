"""
Shared schemas for cross-module problem management metadata and issue summaries.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ProblemCategoryItem(BaseModel):
    """Confirmed problem category definition."""

    key: str = Field(..., description="Category key, for example CQ1")
    category_code: str = Field(..., description="Category code")
    subcategory_code: str = Field(..., description="Subcategory code")
    module_key: str = Field(..., description="Owning module key")
    label: str = Field(..., description="Category label")


class NumberingRuleItem(BaseModel):
    """Unified numbering rule summary."""

    issue_prefix: str = Field(..., description="Problem issue prefix")
    report_prefix: str = Field(..., description="8D report prefix")
    issue_pattern: str = Field(..., description="Problem issue number pattern")
    report_pattern: str = Field(..., description="8D report number pattern")


class ProblemManagementCatalogResponse(BaseModel):
    """Shared problem-management catalog response."""

    response_modes: list[str] = Field(default_factory=list, description="Response modes")
    handling_levels: list[str] = Field(default_factory=list, description="Handling levels")
    categories: list[ProblemCategoryItem] = Field(default_factory=list, description="Category catalog")
    numbering_rule: NumberingRuleItem = Field(..., description="Unified numbering rule")


class InternalUserOption(BaseModel):
    """Shared internal user option for cross-module assignment dialogs."""

    id: int
    username: str
    full_name: str
    department: Optional[str] = None
    position: Optional[str] = None

    class Config:
        from_attributes = True


class UnifiedProblemStatus(str, Enum):
    OPEN = "open"
    ASSIGNED = "assigned"
    RESPONDING = "responding"
    PENDING_REVIEW = "pending_review"
    VERIFYING = "verifying"
    CLOSED = "closed"
    REJECTED = "rejected"


class ProblemIssueSummaryQuery(BaseModel):
    """Query filters for the first read-only unified problem list."""

    module_key: Optional[str] = Field(default=None, description="Module key filter")
    problem_category_key: Optional[str] = Field(default=None, description="Problem category filter")
    unified_status: Optional[UnifiedProblemStatus] = Field(default=None, description="Unified status filter")
    keyword: Optional[str] = Field(default=None, description="Keyword filter")
    only_assigned_to_me: bool = Field(default=False, description="Only include issues assigned to the current user")
    only_actionable_to_me: bool = Field(
        default=False,
        description="Only include issues that the current user can handle directly from the problem center",
    )
    only_created_by_me: bool = Field(default=False, description="Only include issues created by the current user")
    only_overdue: bool = Field(default=False, description="Only include overdue issues")
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Page size")


class ProblemIssueSummaryItem(BaseModel):
    """Normalized issue summary item for the unified problem center."""

    source_type: str = Field(..., description="Source entity type")
    source_id: int = Field(..., description="Source entity id")
    source_parent_id: Optional[int] = Field(default=None, description="Parent source entity id when applicable")
    source_label: str = Field(..., description="Source label")
    module_key: str = Field(..., description="Module key")
    problem_category_key: str = Field(..., description="Problem category key")
    problem_category_label: str = Field(..., description="Problem category label")
    reference_no: Optional[str] = Field(default=None, description="Source reference number")
    title: str = Field(..., description="Summary title")
    raw_status: str = Field(..., description="Original module status")
    unified_status: UnifiedProblemStatus = Field(..., description="Normalized unified status")
    responsible_dept: Optional[str] = Field(default=None, description="Responsible department")
    assigned_to: Optional[int] = Field(default=None, description="Current assignee")
    action_owner_id: Optional[int] = Field(
        default=None,
        description="Current action owner for the active stage in the unified center",
    )
    created_by_id: Optional[int] = Field(default=None, description="Original creator id")
    owner_id: Optional[int] = Field(default=None, description="Owner or creator id")
    verified_by: Optional[int] = Field(
        default=None,
        description="Verifier id when the source workflow has entered verification",
    )
    response_mode: Optional[str] = Field(default=None, description="Current response mode")
    customer_name: Optional[str] = Field(default=None, description="Customer name when applicable")
    requires_physical_analysis: Optional[bool] = Field(
        default=None,
        description="Whether the customer complaint requires physical analysis before disposition",
    )
    is_overdue: bool = Field(default=False, description="Whether the item is overdue")
    due_at: Optional[datetime] = Field(default=None, description="Due date/time")
    created_at: datetime = Field(..., description="Created at")
    updated_at: datetime = Field(..., description="Updated at")


class ProblemIssueSummaryListResponse(BaseModel):
    """Paginated unified problem summary list response."""

    total: int = Field(..., description="Total matching records")
    page: int = Field(..., description="Current page")
    page_size: int = Field(..., description="Current page size")
    module_counts: dict[str, int] = Field(
        default_factory=dict,
        description="Matching item counts grouped by module key before pagination",
    )
    items: list[ProblemIssueSummaryItem] = Field(default_factory=list, description="Summary items")
