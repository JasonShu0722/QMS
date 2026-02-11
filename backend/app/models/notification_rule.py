"""
NotificationRule Model - 通知规则配置模型

用于配置业务触发器和自动化消息推送规则,支持升级策略和多通道发送。
"""
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, ARRAY
from sqlalchemy.orm import relationship

from app.models.base import Base


class ActionType(str, Enum):
    """通知动作类型枚举"""
    SEND_EMAIL = "send_email"              # 发送邮件
    SEND_NOTIFICATION = "send_notification"  # 发送站内信
    SEND_WEBHOOK = "send_webhook"          # 发送Webhook（企业微信/钉钉）


class NotificationRule(Base):
    """
    通知规则配置模型
    
    定义业务触发条件和自动化通知动作，支持超时升级策略。
    管理员可通过配置界面创建规则，系统自动执行。
    """
    __tablename__ = "notification_rules"

    # 主键
    id = Column(Integer, primary_key=True, index=True, comment="规则ID")
    
    # 规则基本信息
    rule_name = Column(String(200), nullable=False, comment="规则名称")
    business_object = Column(
        String(100),
        nullable=False,
        index=True,
        comment="业务对象: scar/ppap/audit/customer_complaint等"
    )
    
    # 触发条件（JSON格式存储复杂条件）
    trigger_condition = Column(
        JSON,
        nullable=False,
        comment='触发条件JSON: {"field": "status", "operator": "equals", "value": "rejected"}'
    )
    
    # 执行动作
    action_type = Column(
        String(50),
        nullable=False,
        comment="动作类型: send_email/send_notification/send_webhook"
    )
    action_config = Column(
        JSON,
        nullable=False,
        comment='动作配置JSON: {"recipients": ["user_id"], "template": "rejection_notice"}'
    )
    
    # 升级策略
    escalation_enabled = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否启用超时升级"
    )
    escalation_hours = Column(
        Integer,
        nullable=True,
        comment="超时小时数（触发升级）"
    )
    escalation_recipients = Column(
        ARRAY(Integer),
        nullable=True,
        comment="升级抄送人ID列表"
    )
    
    # 状态管理
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        comment="是否激活"
    )
    
    # 审计字段
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="创建时间"
    )
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment="更新时间"
    )
    created_by = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="创建人ID"
    )
    
    # 关系定义
    creator = relationship("User", foreign_keys=[created_by])

    def __repr__(self):
        return f"<NotificationRule(id={self.id}, name={self.rule_name}, object={self.business_object}, active={self.is_active})>"

    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "rule_name": self.rule_name,
            "business_object": self.business_object,
            "trigger_condition": self.trigger_condition,
            "action_type": self.action_type,
            "action_config": self.action_config,
            "escalation_enabled": self.escalation_enabled,
            "escalation_hours": self.escalation_hours,
            "escalation_recipients": self.escalation_recipients,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by,
        }
