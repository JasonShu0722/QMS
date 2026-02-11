"""
功能特性开关服务模块
Feature Flag Service - 灰度发布与功能控制
"""
from typing import Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.models.feature_flag import FeatureFlag, FeatureFlagScope, FeatureFlagEnvironment
from app.core.config import settings


class FeatureFlagService:
    """
    功能特性开关服务类
    
    功能：
    - 检查功能是否对指定用户/供应商启用
    - 更新功能开关配置
    - 获取所有功能开关列表
    - 支持全局开关和白名单机制
    - 支持环境隔离（stable/preview）
    """
    
    @staticmethod
    async def is_feature_enabled(
        db: AsyncSession,
        feature_key: str,
        user_id: Optional[int] = None,
        supplier_id: Optional[int] = None,
        environment: Optional[str] = None
    ) -> bool:
        """
        检查功能是否启用
        
        逻辑：
        1. 查询功能开关配置
        2. 检查功能是否启用（is_enabled）
        3. 检查环境匹配（如果指定）
        4. 根据作用域判断：
           - global: 所有用户生效
           - whitelist: 仅白名单用户/供应商可见
        
        Args:
            db: 数据库会话
            feature_key: 功能唯一标识键
            user_id: 用户ID（可选）
            supplier_id: 供应商ID（可选）
            environment: 环境标识（stable/preview，可选，默认使用配置中的环境）
            
        Returns:
            bool: 功能是否启用
        """
        try:
            # 查询功能开关
            query = select(FeatureFlag).where(FeatureFlag.feature_key == feature_key)
            result = await db.execute(query)
            flag = result.scalar_one_or_none()
            
            # 功能开关不存在或未启用
            if not flag or not flag.is_enabled:
                return False
            
            # 检查环境匹配（如果指定）
            current_environment = environment or settings.ENVIRONMENT
            if flag.environment != current_environment:
                return False
            
            # 全局启用
            if flag.scope == FeatureFlagScope.GLOBAL:
                return True
            
            # 白名单机制
            if flag.scope == FeatureFlagScope.WHITELIST:
                # 检查用户白名单
                if user_id and user_id in (flag.whitelist_user_ids or []):
                    return True
                
                # 检查供应商白名单
                if supplier_id and supplier_id in (flag.whitelist_supplier_ids or []):
                    return True
                
                return False
            
            return False
            
        except Exception as e:
            print(f"检查功能开关失败: {str(e)}")
            return False
    
    @staticmethod
    async def update_feature_flag(
        db: AsyncSession,
        feature_key: str,
        is_enabled: bool,
        scope: str = "global",
        whitelist_user_ids: Optional[List[int]] = None,
        whitelist_supplier_ids: Optional[List[int]] = None,
        environment: Optional[str] = None,
        updated_by: Optional[int] = None
    ) -> FeatureFlag:
        """
        更新功能开关配置
        
        功能：
        - 更新开关状态（启用/禁用）
        - 更新作用域（全局/白名单）
        - 更新白名单列表
        - 更新环境标识
        - 立即生效（无需重启服务）
        
        Args:
            db: 数据库会话
            feature_key: 功能唯一标识键
            is_enabled: 是否启用
            scope: 作用域（global/whitelist）
            whitelist_user_ids: 白名单用户ID列表
            whitelist_supplier_ids: 白名单供应商ID列表
            environment: 环境标识（stable/preview）
            updated_by: 更新人ID
            
        Returns:
            FeatureFlag: 更新后的功能开关对象
            
        Raises:
            ValueError: 功能开关不存在
        """
        # 查询功能开关
        query = select(FeatureFlag).where(FeatureFlag.feature_key == feature_key)
        result = await db.execute(query)
        flag = result.scalar_one_or_none()
        
        if not flag:
            raise ValueError(f"功能开关不存在: {feature_key}")
        
        # 更新字段
        flag.is_enabled = is_enabled
        flag.scope = scope
        flag.whitelist_user_ids = whitelist_user_ids or []
        flag.whitelist_supplier_ids = whitelist_supplier_ids or []
        
        if environment:
            flag.environment = environment
        
        flag.updated_at = datetime.utcnow()
        
        # 提交更改
        await db.commit()
        await db.refresh(flag)
        
        return flag
    
    @staticmethod
    async def get_all_feature_flags(
        db: AsyncSession,
        environment: Optional[str] = None
    ) -> List[FeatureFlag]:
        """
        获取所有功能开关列表
        
        Args:
            db: 数据库会话
            environment: 环境标识（可选，用于过滤）
            
        Returns:
            List[FeatureFlag]: 功能开关列表
        """
        query = select(FeatureFlag)
        
        # 如果指定环境，进行过滤
        if environment:
            query = query.where(FeatureFlag.environment == environment)
        
        # 按创建时间倒序
        query = query.order_by(FeatureFlag.created_at.desc())
        
        result = await db.execute(query)
        flags = result.scalars().all()
        
        return list(flags)
    
    @staticmethod
    async def get_user_enabled_features(
        db: AsyncSession,
        user_id: int,
        supplier_id: Optional[int] = None,
        environment: Optional[str] = None
    ) -> List[str]:
        """
        获取当前用户可用的功能列表
        
        功能：
        - 遍历所有功能开关
        - 检查每个功能是否对当前用户启用
        - 返回启用的功能键列表
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            supplier_id: 供应商ID（可选）
            environment: 环境标识（可选）
            
        Returns:
            List[str]: 启用的功能键列表
        """
        # 获取所有功能开关
        all_flags = await FeatureFlagService.get_all_feature_flags(db, environment)
        
        # 筛选启用的功能
        enabled_features = []
        for flag in all_flags:
            if await FeatureFlagService.is_feature_enabled(
                db=db,
                feature_key=flag.feature_key,
                user_id=user_id,
                supplier_id=supplier_id,
                environment=environment
            ):
                enabled_features.append(flag.feature_key)
        
        return enabled_features
    
    @staticmethod
    async def create_feature_flag(
        db: AsyncSession,
        feature_key: str,
        feature_name: str,
        description: Optional[str] = None,
        is_enabled: bool = False,
        scope: str = "global",
        whitelist_user_ids: Optional[List[int]] = None,
        whitelist_supplier_ids: Optional[List[int]] = None,
        environment: str = "stable",
        created_by: Optional[int] = None
    ) -> FeatureFlag:
        """
        创建新的功能开关
        
        Args:
            db: 数据库会话
            feature_key: 功能唯一标识键
            feature_name: 功能名称
            description: 功能描述
            is_enabled: 是否启用
            scope: 作用域（global/whitelist）
            whitelist_user_ids: 白名单用户ID列表
            whitelist_supplier_ids: 白名单供应商ID列表
            environment: 环境标识（stable/preview）
            created_by: 创建人ID
            
        Returns:
            FeatureFlag: 创建的功能开关对象
            
        Raises:
            ValueError: 功能开关已存在
        """
        # 检查是否已存在
        query = select(FeatureFlag).where(FeatureFlag.feature_key == feature_key)
        result = await db.execute(query)
        existing_flag = result.scalar_one_or_none()
        
        if existing_flag:
            raise ValueError(f"功能开关已存在: {feature_key}")
        
        # 创建新的功能开关
        flag = FeatureFlag(
            feature_key=feature_key,
            feature_name=feature_name,
            description=description,
            is_enabled=is_enabled,
            scope=scope,
            whitelist_user_ids=whitelist_user_ids or [],
            whitelist_supplier_ids=whitelist_supplier_ids or [],
            environment=environment,
            created_by=created_by,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(flag)
        await db.commit()
        await db.refresh(flag)
        
        return flag


# 创建全局功能开关服务实例
feature_flag_service = FeatureFlagService()
