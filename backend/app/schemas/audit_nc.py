"""
审核不符合项 (NC) Schemas
Audit Non-Conformance Schemas - 用于审核问题整改与闭环管理
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# ==================== 审核NC指派 ====================

class AuditNCAssign(BaseModel):
    """审核NC指派"""
    assigned_to: int = Field(..., description="指派给(用户ID)")
    deadline: datetime = Field(..., description="整改期限")
    comment: Optional[str] = Field(None, description="指派说明")


# ==================== 审核NC响应 ====================

class AuditNCResponse(BaseModel):
    """审核NC响应（责任人填写原因和措施）"""
    root_cause: str = Field(..., description="根本原因", min_length=10)
    corrective_action: str = Field(..., description="纠正措施", min_length=10)
    corrective_evidence: Optional[str] = Field(None, description="整改证据文件路径")


# ==================== 审核NC验证 ====================

class AuditNCVerify(BaseModel):
    """审核NC验证（审核员验证有效性）"""
    is_approved: bool = Field(..., description="是否验证通过")
    verification_comment: str = Field(..., description="验证意见", min_length=5)


# ==================== 审核NC关闭 ====================

class AuditNCClose(BaseModel):
    """审核NC关闭"""
    closing_comment: Optional[str] = Field(None, description="关闭备注")


# ==================== 审核NC查询 ====================

class AuditNCQuery(BaseModel):
    """审核NC查询参数"""
    audit_id: Optional[int] = Field(None, description="审核执行记录ID")
    assigned_to: Optional[int] = Field(None, description="指派给")
    responsible_dept: Optional[str] = Field(None, description="责任部门")
    verification_status: Optional[str] = Field(None, description="验证状态")
    is_overdue: Optional[bool] = Field(None, description="是否逾期")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页记录数")


# ==================== 审核NC响应模型 ====================

class AuditNCDetail(BaseModel):
    """审核NC详情响应"""
    id: int
    audit_id: int
    nc_item: str
    nc_description: str
    evidence_photo_path: Optional[str]
    responsible_dept: str
    assigned_to: Optional[int]
    root_cause: Optional[str]
    corrective_action: Optional[str]
    corrective_evidence: Optional[str]
    verification_status: str
    verified_by: Optional[int]
    verified_at: Optional[datetime]
    verification_comment: Optional[str]
    deadline: datetime
    closed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int]
    
    # 计算字段
    is_overdue: bool = Field(default=False, description="是否逾期")
    remaining_hours: Optional[float] = Field(None, description="剩余小时数")
    
    class Config:
        from_attributes = True


class AuditNCListResponse(BaseModel):
    """审核NC列表响应"""
    items: List[AuditNCDetail]
    total: int
    page: int
    page_size: int
    total_pages: int
