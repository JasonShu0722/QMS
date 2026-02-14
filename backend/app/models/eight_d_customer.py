"""
8D Customer Report Model
客诉8D报告模型 - 记录客诉问题的8D分析过程
"""
from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.core.database import Base


class EightDStatus(str, enum.Enum):
    """8D报告状态枚举"""
    DRAFT = "draft"  # 草稿
    D0_D3_COMPLETED = "d0_d3_completed"  # D0-D3已完成（CQE完成）
    D4_D7_IN_PROGRESS = "d4_d7_in_progress"  # D4-D7进行中（责任板块填写）
    D4_D7_COMPLETED = "d4_d7_completed"  # D4-D7已完成
    D8_IN_PROGRESS = "d8_in_progress"  # D8进行中（水平展开）
    IN_REVIEW = "in_review"  # 审核中
    APPROVED = "approved"  # 已批准
    REJECTED = "rejected"  # 已驳回
    CLOSED = "closed"  # 已归档


class ApprovalLevel(str, enum.Enum):
    """审批级别枚举"""
    SECTION_MANAGER = "section_manager"  # C级：科室经理审批
    DEPARTMENT_HEAD = "department_head"  # A/B级：部长联合审批
    NONE = "none"  # 无需审批


class EightDCustomer(Base):
    """
    客诉8D报告模型
    遵循8D方法论，分阶段记录问题分析和解决过程
    """
    __tablename__ = "eight_d_customer"

    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(Integer, ForeignKey("customer_complaints.id"), nullable=False, unique=True, comment="关联的客诉单ID")
    
    # D0-D3阶段数据（CQE负责）
    d0_d3_cqe = Column(JSON, nullable=True, comment="""
        D0-D3阶段数据（JSON格式）:
        {
            "d0_team": ["成员1", "成员2"],  # D0: 组建团队
            "d1_problem": "问题描述(5W2H)",  # D1: 问题描述
            "d2_containment": {  # D2: 围堵措施
                "in_transit": "在途品处理方案",
                "inventory": "库存品处理方案",
                "customer_site": "客户端库存处理方案"
            },
            "d3_root_cause_initial": "初步原因分析"  # D3: 初步根本原因
        }
    """)
    
    # D4-D7阶段数据（责任板块负责）
    d4_d7_responsible = Column(JSON, nullable=True, comment="""
        D4-D7阶段数据（JSON格式）:
        {
            "d4_root_cause": {  # D4: 根本原因分析
                "analysis_method": "5Why/鱼骨图/FTA/流程分析",
                "root_cause": "根本原因描述",
                "evidence": ["证据文件路径1", "证据文件路径2"]
            },
            "d5_corrective_actions": [  # D5: 纠正措施
                {"action": "措施1", "responsible": "责任人", "deadline": "2024-01-01"}
            ],
            "d6_verification": {  # D6: 验证有效性
                "verification_report": "验证报告文件路径",
                "test_data": "测试数据文件路径",
                "result": "验证结果"
            },
            "d7_standardization": {  # D7: 标准化
                "document_modified": true,
                "modified_files": ["PFMEA更新", "CP更新", "SOP更新"],
                "attachments": ["文件路径1", "文件路径2"]
            }
        }
    """)
    
    # D8阶段数据（水平展开与经验教训）
    d8_horizontal = Column(JSON, nullable=True, comment="""
        D8阶段数据（JSON格式）:
        {
            "horizontal_deployment": [  # 水平展开
                {"product": "类似产品A", "action": "推送对策", "status": "已完成"}
            ],
            "lesson_learned": {  # 经验教训
                "should_archive": true,
                "lesson_id": 123  # 关联到LessonLearned表的ID
            }
        }
    """)
    
    # 流程控制
    status = Column(SQLEnum(EightDStatus), nullable=False, default=EightDStatus.DRAFT, comment="8D报告状态")
    approval_level = Column(SQLEnum(ApprovalLevel), nullable=False, default=ApprovalLevel.NONE, comment="审批级别")
    
    # 审计字段
    submitted_at = Column(DateTime, nullable=True, comment="提交时间")
    reviewed_at = Column(DateTime, nullable=True, comment="审核时间")
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True, comment="审核人ID")
    review_comments = Column(Text, nullable=True, comment="审核意见")
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    # 关系
    complaint = relationship("CustomerComplaint", back_populates="eight_d_report")
    reviewer = relationship("User", foreign_keys=[reviewed_by], backref="reviewed_customer_8d")
    
    def __repr__(self):
        return f"<EightDCustomer(id={self.id}, complaint_id={self.complaint_id}, status={self.status})>"
