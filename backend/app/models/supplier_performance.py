"""
供应商绩效数据模型
Supplier Performance - 供应商月度绩效评价
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Float, DateTime, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from .base import Base


class PerformanceGrade(str, enum.Enum):
    """绩效等级枚举"""
    A = "A"  # 优秀（>95分）
    B = "B"  # 良好（80-95分）
    C = "C"  # 一般（70-79分）
    D = "D"  # 差（<70分）


class SupplierPerformance(Base):
    """
    供应商绩效模型
    用于记录供应商月度绩效评价结果
    采用60分制扣分模型，按100分满分折算百分制
    """
    __tablename__ = "supplier_performances"
    
    # 主键
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # 供应商信息
    supplier_id: Mapped[int] = mapped_column(ForeignKey("suppliers.id"), nullable=False, index=True, comment="供应商ID")
    
    # 评价月份（格式：YYYY-MM）
    month: Mapped[str] = mapped_column(String(7), nullable=False, index=True, comment="评价月份")
    
    # 来料质量得分（基于2.4.1指标计算）
    incoming_quality_score: Mapped[float] = mapped_column(Float, nullable=False, comment="来料质量得分")
    
    # 制程质量得分（基于物料上线不良PPM）
    process_quality_score: Mapped[float] = mapped_column(Float, nullable=False, comment="制程质量得分")
    
    # 配合度得分（SQE人工评价）
    cooperation_score: Mapped[float] = mapped_column(Float, nullable=False, comment="配合度得分")
    
    # 0公里/售后质量扣分
    customer_quality_deduction: Mapped[float] = mapped_column(Float, default=0.0, nullable=False, comment="客户质量扣分")
    
    # 最终得分（60分制扣分后按100分满分折算）
    final_score: Mapped[float] = mapped_column(Float, nullable=False, comment="最终得分")
    
    # 等级评定
    grade: Mapped[str] = mapped_column(
        SQLEnum(PerformanceGrade, native_enum=False, length=1),
        nullable=False,
        index=True,
        comment="绩效等级"
    )
    
    # SQE人工校核标记
    is_reviewed: Mapped[bool] = mapped_column(default=False, nullable=False, comment="是否已人工校核")
    reviewed_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), comment="校核人ID")
    review_notes: Mapped[Optional[str]] = mapped_column(String(500), comment="校核备注")
    
    # 审计字段
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment="更新时间")
    
    # 唯一约束：每个供应商每月只能有一条绩效记录
    __table_args__ = (
        {"comment": "供应商月度绩效评价表"},
    )
    
    # 关系映射
    # supplier: Mapped["Supplier"] = relationship("Supplier", back_populates="performances")
    # reviewer: Mapped["User"] = relationship("User", foreign_keys=[reviewed_by])
    
    def __repr__(self) -> str:
        return f"<SupplierPerformance(id={self.id}, supplier_id={self.supplier_id}, month='{self.month}', grade='{self.grade}')>"
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "id": self.id,
            "supplier_id": self.supplier_id,
            "month": self.month,
            "incoming_quality_score": self.incoming_quality_score,
            "process_quality_score": self.process_quality_score,
            "cooperation_score": self.cooperation_score,
            "customer_quality_deduction": self.customer_quality_deduction,
            "final_score": self.final_score,
            "grade": self.grade,
            "is_reviewed": self.is_reviewed,
            "reviewed_by": self.reviewed_by,
            "review_notes": self.review_notes,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
