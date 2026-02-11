"""
QualityCost Model - 质量成本管理模型（预留功能）

用于记录和分析质量相关的成本数据,包括内部损失、外部损失、鉴定成本和预防成本。
当前为预留功能,所有字段设置为Nullable以兼容双轨环境。
"""
from datetime import datetime, date
from enum import Enum
from sqlalchemy import Column, Integer, String, Text, Date, DateTime, Numeric

from app.models.base import Base


class CostType(str, Enum):
    """成本类型枚举"""
    INTERNAL_FAILURE = "internal_failure"    # 内部损失成本
    EXTERNAL_FAILURE = "external_failure"    # 外部损失成本
    APPRAISAL = "appraisal"                  # 鉴定成本
    PREVENTION = "prevention"                # 预防成本


class QualityCost(Base):
    """
    质量成本管理模型（预留功能）
    
    记录质量相关的各类成本数据，支持按供应商、产品、时间等维度进行分析。
    所有字段设置为Nullable，确保预览环境新增此表时不影响正式环境。
    """
    __tablename__ = "quality_costs"

    # 主键
    id = Column(Integer, primary_key=True, index=True, comment="成本记录ID")
    
    # 成本分类
    cost_type = Column(
        String(50),
        nullable=True,
        index=True,
        comment="成本类型: internal_failure/external_failure/appraisal/prevention"
    )
    cost_category = Column(
        String(100),
        nullable=True,
        comment="成本细分类别（如：报废、返工、索赔等）"
    )
    
    # 金额信息
    amount = Column(
        Numeric(15, 2),
        nullable=True,
        comment="成本金额"
    )
    currency = Column(
        String(10),
        nullable=True,
        default="CNY",
        comment="货币单位（默认人民币）"
    )
    
    # 关联业务对象
    related_business_type = Column(
        String(50),
        nullable=True,
        index=True,
        comment="关联业务类型: scar/customer_complaint/scrap/rework等"
    )
    related_business_id = Column(
        Integer,
        nullable=True,
        index=True,
        comment="关联业务对象ID"
    )
    
    # 维度信息
    supplier_id = Column(
        Integer,
        nullable=True,
        index=True,
        comment="关联供应商ID（如果适用）"
    )
    product_id = Column(
        Integer,
        nullable=True,
        comment="关联产品ID（如果适用）"
    )
    
    # 时间信息
    occurred_date = Column(
        Date,
        nullable=True,
        index=True,
        comment="成本发生日期"
    )
    
    # 描述信息
    description = Column(
        Text,
        nullable=True,
        comment="成本描述"
    )
    
    # 审计字段
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=True,
        comment="创建时间"
    )
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=True,
        comment="更新时间"
    )

    def __repr__(self):
        return f"<QualityCost(id={self.id}, type={self.cost_type}, amount={self.amount}, date={self.occurred_date})>"

    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "cost_type": self.cost_type,
            "cost_category": self.cost_category,
            "amount": float(self.amount) if self.amount else None,
            "currency": self.currency,
            "related_business_type": self.related_business_type,
            "related_business_id": self.related_business_id,
            "supplier_id": self.supplier_id,
            "product_id": self.product_id,
            "occurred_date": self.occurred_date.isoformat() if self.occurred_date else None,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
