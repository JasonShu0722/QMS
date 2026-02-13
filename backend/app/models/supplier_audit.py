"""
供应商审核数据模型
Supplier Audit - 供应商审核记录
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Date, DateTime, Enum as SQLEnum, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from .base import Base


class AuditType(str, enum.Enum):
    """审核类型枚举"""
    SYSTEM = "system"        # 体系审核
    PROCESS = "process"      # 过程审核
    PRODUCT = "product"      # 产品审核
    QUALIFICATION = "qualification"  # 准入审核
    ANNUAL = "annual"        # 年度审核


class AuditResult(str, enum.Enum):
    """审核结果枚举"""
    PASSED = "passed"        # 通过
    CONDITIONAL = "conditional"  # 有条件通过
    FAILED = "failed"        # 不通过


class SupplierAudit(Base):
    """
    供应商审核模型
    用于记录供应商审核计划、执行和结果
    """
    __tablename__ = "supplier_audits"
    
    # 主键
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # 供应商信息
    supplier_id: Mapped[int] = mapped_column(ForeignKey("suppliers.id"), nullable=False, index=True, comment="供应商ID")
    
    # 审核类型
    audit_type: Mapped[str] = mapped_column(
        SQLEnum(AuditType, native_enum=False, length=20),
        nullable=False,
        index=True,
        comment="审核类型"
    )
    
    # 审核日期
    audit_date: Mapped[datetime] = mapped_column(Date, nullable=False, index=True, comment="审核日期")
    
    # 审核员
    auditor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, comment="审核员ID")
    
    # 审核结果
    audit_result: Mapped[str] = mapped_column(
        SQLEnum(AuditResult, native_enum=False, length=20),
        nullable=False,
        comment="审核结果"
    )
    
    # 审核得分
    score: Mapped[Optional[int]] = mapped_column(Integer, comment="审核得分（0-100）")
    
    # 不符合项（JSON 格式存储）
    # 包含：条款编号、问题描述、严重度、整改要求等
    nc_items: Mapped[Optional[dict]] = mapped_column(JSON, comment="不符合项清单")
    
    # 审计字段
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment="更新时间")
    created_by: Mapped[Optional[int]] = mapped_column(comment="创建人ID")
    updated_by: Mapped[Optional[int]] = mapped_column(comment="更新人ID")
    
    # 关系映射
    # supplier: Mapped["Supplier"] = relationship("Supplier", back_populates="audits")
    # auditor: Mapped["User"] = relationship("User", foreign_keys=[auditor_id])
    
    def __repr__(self) -> str:
        return f"<SupplierAudit(id={self.id}, supplier_id={self.supplier_id}, audit_type='{self.audit_type}', result='{self.audit_result}')>"
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "id": self.id,
            "supplier_id": self.supplier_id,
            "audit_type": self.audit_type,
            "audit_date": self.audit_date.isoformat(),
            "auditor_id": self.auditor_id,
            "audit_result": self.audit_result,
            "score": self.score,
            "nc_items": self.nc_items,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
