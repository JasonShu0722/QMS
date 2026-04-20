"""
跨模块问题管理共享元数据 schema
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class ProblemCategoryItem(BaseModel):
    """问题分类项"""

    key: str = Field(..., description="分类唯一键，例如 CQ1")
    category_code: str = Field(..., description="分类码")
    subcategory_code: str = Field(..., description="子类码")
    module_key: str = Field(..., description="所属模块标识")
    label: str = Field(..., description="分类名称")


class NumberingRuleItem(BaseModel):
    """编号规则摘要"""

    issue_prefix: str = Field(..., description="问题主单号前缀")
    report_prefix: str = Field(..., description="8D 报告号前缀")
    issue_pattern: str = Field(..., description="问题主单号格式说明")
    report_pattern: str = Field(..., description="8D 报告号格式说明")


class ProblemManagementCatalogResponse(BaseModel):
    """问题管理元数据响应"""

    response_modes: list[str] = Field(default_factory=list, description="回复形式列表")
    handling_levels: list[str] = Field(default_factory=list, description="处理复杂度列表")
    categories: list[ProblemCategoryItem] = Field(default_factory=list, description="分类目录")
    numbering_rule: NumberingRuleItem = Field(..., description="统一编号规则")
