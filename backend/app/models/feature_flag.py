"""
功能特性开关数据模型
Feature Flag Model - 灰度发布与功能控制
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, DateTime, Integer, Boolean, Enum as SQLEnum, JSON
from sqlalchemy.orm import Mapped, mapped_column
import enum

from .base import Base


class FeatureFlagScope(str, enum.Enum):
    """功能开关作用域枚举"""
    GLOBAL = "global"        # 全局启用
    WHITELIST = "whitelist"  # 白名单机制


class FeatureFlagEnvironment(str, enum.Enum):
    """环境标识枚举"""
    STABLE = "stable"    # 正式环境
    PREVIEW = "preview"  # 预览环境


class FeatureFlag(Base):
    """
    功能特性开关模型
    用于灰度发布和功能控制，支持按用户或供应商进行白名单管理
    """
    __tablename__ = "feature_flags"
    
    # 主键
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # 功能标识
    feature_key: Mapped[str] = mapped_column(
        String(100), 
        unique=True, 
        nullable=False, 
        index=True, 
        comment="功能唯一标识键"
    )
    feature_name: Mapped[str] = mapped_column(String(200), nullable=False, comment="功能名称")
    description: Mapped[Optional[str]] = mapped_column(String(500), comment="功能描述")
    
    # 开关状态
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, comment="是否启用")
    scope: Mapped[str] = mapped_column(
        SQLEnum(FeatureFlagScope, native_enum=False, length=20),
        default=FeatureFlagScope.GLOBAL,
        nullable=False,
        comment="作用域"
    )
    
    # 白名单配置（JSON Array 存储 ID 列表）
    whitelist_user_ids: Mapped[Optional[List[int]]] = mapped_column(
        JSON,
        default=list,
        comment="白名单用户ID列表"
    )
    whitelist_supplier_ids: Mapped[Optional[List[int]]] = mapped_column(
        JSON,
        default=list,
        comment="白名单供应商ID列表"
    )
    
    # 环境标识
    environment: Mapped[str] = mapped_column(
        SQLEnum(FeatureFlagEnvironment, native_enum=False, length=20),
        default=FeatureFlagEnvironment.STABLE,
        nullable=False,
        index=True,
        comment="环境标识"
    )
    
    # 审计字段
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        nullable=False, 
        comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow, 
        nullable=False, 
        comment="更新时间"
    )
    created_by: Mapped[Optional[int]] = mapped_column(Integer, comment="创建人ID")
    
    def __repr__(self) -> str:
        return f"<FeatureFlag(id={self.id}, key='{self.feature_key}', enabled={self.is_enabled}, scope='{self.scope}')>"
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "id": self.id,
            "feature_key": self.feature_key,
            "feature_name": self.feature_name,
            "description": self.description,
            "is_enabled": self.is_enabled,
            "scope": self.scope,
            "whitelist_user_ids": self.whitelist_user_ids or [],
            "whitelist_supplier_ids": self.whitelist_supplier_ids or [],
            "environment": self.environment,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "created_by": self.created_by,
        }
    
    def is_enabled_for_user(self, user_id: int) -> bool:
        """
        检查功能是否对指定用户启用
        
        Args:
            user_id: 用户ID
            
        Returns:
            bool: 是否启用
        """
        if not self.is_enabled:
            return False
        
        if self.scope == FeatureFlagScope.GLOBAL:
            return True
        
        if self.scope == FeatureFlagScope.WHITELIST:
            return user_id in (self.whitelist_user_ids or [])
        
        return False
    
    def is_enabled_for_supplier(self, supplier_id: int) -> bool:
        """
        检查功能是否对指定供应商启用
        
        Args:
            supplier_id: 供应商ID
            
        Returns:
            bool: 是否启用
        """
        if not self.is_enabled:
            return False
        
        if self.scope == FeatureFlagScope.GLOBAL:
            return True
        
        if self.scope == FeatureFlagScope.WHITELIST:
            return supplier_id in (self.whitelist_supplier_ids or [])
        
        return False
