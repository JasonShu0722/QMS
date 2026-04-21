"""
Customer Complaint Model
客诉单模型 - 记录客户质量投诉信息
"""
from sqlalchemy import Boolean, Column, Integer, String, Text, Date, DateTime, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from .base import Base


class ComplaintType(str, enum.Enum):
    """客诉类型枚举"""
    ZERO_KM = "0km"  # 0公里客诉（客户产线端发现）
    AFTER_SALES = "after_sales"  # 售后客诉（终端市场反馈）


class ComplaintStatus(str, enum.Enum):
    """客诉状态枚举"""
    PENDING = "pending"  # 待处理
    IN_ANALYSIS = "in_analysis"  # 分析中（D0-D3）
    IN_RESPONSE = "in_response"  # 待回复（D4-D7）
    IN_REVIEW = "in_review"  # 审核中
    CLOSED = "closed"  # 已关闭
    REJECTED = "rejected"  # 已驳回


class SeverityLevel(str, enum.Enum):
    """严重度等级枚举 - TBD（待产品定义）"""
    CRITICAL = "critical"  # 严重（预留）
    MAJOR = "major"  # 重大（预留）
    MINOR = "minor"  # 一般（预留）
    TBD = "tbd"  # 待定义


class CustomerComplaint(Base):
    """
    客诉单模型
    记录0KM客诉和售后客诉的完整信息
    """
    __tablename__ = "customer_complaints"

    id = Column(Integer, primary_key=True, index=True)
    complaint_number = Column(String(50), unique=True, nullable=False, index=True, comment="客诉单号")
    
    # 基本信息
    complaint_type = Column(SQLEnum(ComplaintType), nullable=False, comment="客诉类型：0km/售后")
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True, index=True, comment="客户主数据ID")
    customer_code = Column(String(50), nullable=False, index=True, comment="客户代码")
    customer_name_snapshot = Column(String(200), nullable=True, comment="客户名称快照")
    end_customer_name = Column(String(200), nullable=True, comment="终端客户名称")
    product_type = Column(String(100), nullable=False, comment="产品类型")
    is_return_required = Column(Boolean, nullable=False, default=False, comment="是否涉及退件")
    requires_physical_analysis = Column(Boolean, nullable=False, default=False, comment="是否需要实物解析")
    
    # 缺陷描述
    defect_description = Column(Text, nullable=False, comment="缺陷描述")
    severity_level = Column(SQLEnum(SeverityLevel), nullable=False, default=SeverityLevel.TBD, comment="严重度等级")
    
    # 售后客诉特有字段（0KM客诉时可为空）
    vin_code = Column(String(50), nullable=True, comment="VIN码（车架号）")
    mileage = Column(Integer, nullable=True, comment="失效里程（公里）")
    purchase_date = Column(Date, nullable=True, comment="购车日期")
    
    # 流程控制
    status = Column(SQLEnum(ComplaintStatus), nullable=False, default=ComplaintStatus.PENDING, comment="客诉状态")
    cqe_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="负责CQE的用户ID")
    responsible_dept = Column(String(100), nullable=True, comment="责任部门")
    
    # 审计字段
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True, comment="创建人ID")
    
    # 关系
    customer_master = relationship("CustomerMaster", foreign_keys=[customer_id], backref="customer_complaints")
    cqe = relationship("User", foreign_keys=[cqe_id], backref="assigned_complaints")
    creator = relationship("User", foreign_keys=[created_by], backref="created_complaints")
    eight_d_report = relationship("EightDCustomer", back_populates="complaint", uselist=False)
    customer_claims = relationship("CustomerClaim", back_populates="complaint")
    supplier_claims = relationship("SupplierClaim", back_populates="complaint")

    @property
    def customer_name(self):
        return self.customer_name_snapshot
    
    def __repr__(self):
        return f"<CustomerComplaint(id={self.id}, number={self.complaint_number}, type={self.complaint_type})>"
