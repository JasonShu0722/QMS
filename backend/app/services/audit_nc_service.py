"""
审核不符合项 (NC) 服务
Audit NC Service - 处理审核问题整改与闭环管理
"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload

from app.models.audit import AuditNC, AuditExecution
from app.models.user import User
from app.schemas.audit_nc import (
    AuditNCAssign,
    AuditNCResponse,
    AuditNCVerify,
    AuditNCClose,
    AuditNCQuery,
    AuditNCDetail
)
from app.core.exceptions import NotFoundException, ValidationException, PermissionException


class AuditNCService:
    """审核不符合项服务类"""
    
    @staticmethod
    async def assign_nc(
        db: AsyncSession,
        nc_id: int,
        data: AuditNCAssign,
        current_user_id: int
    ) -> AuditNC:
        """
        指派NC给责任板块
        
        实现逻辑：
        1. 验证NC记录存在且状态为open
        2. 验证被指派人存在
        3. 更新指派信息和期限
        4. 发送通知给被指派人
        
        Args:
            db: 数据库会话
            nc_id: NC记录ID
            data: 指派数据
            current_user_id: 当前用户ID（审核员）
            
        Returns:
            更新后的NC记录
        """
        # 获取NC记录
        nc = await db.get(AuditNC, nc_id)
        if not nc:
            raise NotFoundException(f"NC记录 ID {nc_id} 不存在")
        
        # 验证状态
        if nc.verification_status not in ["open", "rejected"]:
            raise ValidationException(f"NC状态为 {nc.verification_status}，无法指派")
        
        # 验证被指派人存在
        assigned_user = await db.get(User, data.assigned_to)
        if not assigned_user:
            raise NotFoundException(f"用户 ID {data.assigned_to} 不存在")
        
        # 更新指派信息
        nc.assigned_to = data.assigned_to
        nc.deadline = data.deadline
        nc.verification_status = "assigned"
        nc.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(nc)
        
        # TODO: 发送通知给被指派人
        # await NotificationService.send_notification(
        #     db,
        #     user_ids=[data.assigned_to],
        #     title="审核NC指派通知",
        #     content=f"您被指派处理审核不符合项：{nc.nc_item}",
        #     notification_type="workflow",
        #     link=f"/audit/nc/{nc.id}"
        # )
        
        return nc
    
    @staticmethod
    async def submit_response(
        db: AsyncSession,
        nc_id: int,
        data: AuditNCResponse,
        current_user_id: int
    ) -> AuditNC:
        """
        责任人填写原因和措施
        
        实现逻辑：
        1. 验证NC记录存在且已指派给当前用户
        2. 填写根本原因和纠正措施
        3. 上传整改证据
        4. 状态变更为submitted（待验证）
        5. 通知审核员进行验证
        
        Args:
            db: 数据库会话
            nc_id: NC记录ID
            data: 响应数据
            current_user_id: 当前用户ID（责任人）
            
        Returns:
            更新后的NC记录
        """
        # 获取NC记录
        nc = await db.get(AuditNC, nc_id)
        if not nc:
            raise NotFoundException(f"NC记录 ID {nc_id} 不存在")
        
        # 验证权限：只有被指派人可以提交响应
        if nc.assigned_to != current_user_id:
            raise PermissionException("您无权提交此NC的响应")
        
        # 验证状态
        if nc.verification_status not in ["assigned", "rejected"]:
            raise ValidationException(f"NC状态为 {nc.verification_status}，无法提交响应")
        
        # 更新响应信息
        nc.root_cause = data.root_cause
        nc.corrective_action = data.corrective_action
        nc.corrective_evidence = data.corrective_evidence
        nc.verification_status = "submitted"
        nc.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(nc)
        
        # 获取审核执行记录以获取审核员ID
        audit_execution = await db.get(AuditExecution, nc.audit_id)
        if audit_execution and audit_execution.auditor_id:
            # TODO: 发送通知给审核员
            # await NotificationService.send_notification(
            #     db,
            #     user_ids=[audit_execution.auditor_id],
            #     title="NC整改响应提交通知",
            #     content=f"NC {nc.nc_item} 的整改措施已提交，请验证",
            #     notification_type="workflow",
            #     link=f"/audit/nc/{nc.id}"
            # )
            pass
        
        return nc
    
    @staticmethod
    async def verify_nc(
        db: AsyncSession,
        nc_id: int,
        data: AuditNCVerify,
        current_user_id: int
    ) -> AuditNC:
        """
        审核员验证有效性
        
        实现逻辑：
        1. 验证NC记录存在且状态为submitted
        2. 审核员填写验证意见
        3. 如果验证通过，状态变更为verified
        4. 如果验证不通过，状态变更为rejected，需要责任人重新提交
        5. 通知责任人验证结果
        
        Args:
            db: 数据库会话
            nc_id: NC记录ID
            data: 验证数据
            current_user_id: 当前用户ID（审核员）
            
        Returns:
            更新后的NC记录
        """
        # 获取NC记录
        nc = await db.get(AuditNC, nc_id)
        if not nc:
            raise NotFoundException(f"NC记录 ID {nc_id} 不存在")
        
        # 验证状态
        if nc.verification_status != "submitted":
            raise ValidationException(f"NC状态为 {nc.verification_status}，无法验证")
        
        # 获取审核执行记录以验证权限
        audit_execution = await db.get(AuditExecution, nc.audit_id)
        if not audit_execution:
            raise NotFoundException(f"审核执行记录 ID {nc.audit_id} 不存在")
        
        # 验证权限：只有审核员可以验证
        if audit_execution.auditor_id != current_user_id:
            raise PermissionException("您无权验证此NC")
        
        # 更新验证信息
        nc.verified_by = current_user_id
        nc.verified_at = datetime.utcnow()
        nc.verification_comment = data.verification_comment
        
        if data.is_approved:
            nc.verification_status = "verified"
        else:
            nc.verification_status = "rejected"
        
        nc.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(nc)
        
        # TODO: 发送通知给责任人
        if nc.assigned_to:
            status_text = "验证通过" if data.is_approved else "验证不通过，需重新提交"
            # await NotificationService.send_notification(
            #     db,
            #     user_ids=[nc.assigned_to],
            #     title=f"NC验证结果通知",
            #     content=f"NC {nc.nc_item} {status_text}",
            #     notification_type="workflow",
            #     link=f"/audit/nc/{nc.id}"
            # )
            pass
        
        return nc
    
    @staticmethod
    async def close_nc(
        db: AsyncSession,
        nc_id: int,
        data: AuditNCClose,
        current_user_id: int
    ) -> AuditNC:
        """
        关闭NC
        
        实现逻辑：
        1. 验证NC记录存在且状态为verified
        2. 填写关闭备注
        3. 状态变更为closed
        4. 记录关闭时间
        
        Args:
            db: 数据库会话
            nc_id: NC记录ID
            data: 关闭数据
            current_user_id: 当前用户ID（审核员）
            
        Returns:
            更新后的NC记录
        """
        # 获取NC记录
        nc = await db.get(AuditNC, nc_id)
        if not nc:
            raise NotFoundException(f"NC记录 ID {nc_id} 不存在")
        
        # 验证状态
        if nc.verification_status != "verified":
            raise ValidationException(f"NC状态为 {nc.verification_status}，无法关闭。必须先验证通过。")
        
        # 获取审核执行记录以验证权限
        audit_execution = await db.get(AuditExecution, nc.audit_id)
        if not audit_execution:
            raise NotFoundException(f"审核执行记录 ID {nc.audit_id} 不存在")
        
        # 验证权限：只有审核员可以关闭
        if audit_execution.auditor_id != current_user_id:
            raise PermissionException("您无权关闭此NC")
        
        # 更新关闭信息
        nc.verification_status = "closed"
        nc.closed_at = datetime.utcnow()
        nc.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(nc)
        
        # 检查该审核的所有NC是否都已关闭
        await AuditNCService._check_and_update_audit_status(db, nc.audit_id)
        
        return nc
    
    @staticmethod
    async def _check_and_update_audit_status(
        db: AsyncSession,
        audit_id: int
    ):
        """
        检查审核的所有NC是否都已关闭，如果是则更新审核状态
        
        Args:
            db: 数据库会话
            audit_id: 审核执行记录ID
        """
        # 查询该审核的所有NC
        query = select(AuditNC).where(AuditNC.audit_id == audit_id)
        result = await db.execute(query)
        all_ncs = result.scalars().all()
        
        # 检查是否所有NC都已关闭
        all_closed = all(nc.verification_status == "closed" for nc in all_ncs)
        
        if all_closed:
            # 更新审核执行记录状态为completed
            audit_execution = await db.get(AuditExecution, audit_id)
            if audit_execution and audit_execution.status == "nc_open":
                audit_execution.status = "completed"
                await db.commit()
    
    @staticmethod
    async def get_nc_detail(
        db: AsyncSession,
        nc_id: int
    ) -> Optional[AuditNCDetail]:
        """
        获取NC详情
        
        Args:
            db: 数据库会话
            nc_id: NC记录ID
            
        Returns:
            NC详情或None
        """
        nc = await db.get(AuditNC, nc_id)
        if not nc:
            return None
        
        # 计算是否逾期和剩余时间
        now = datetime.utcnow()
        remaining_hours = (nc.deadline - now).total_seconds() / 3600
        is_overdue = remaining_hours < 0 and nc.verification_status not in ["closed", "verified"]
        
        nc_dict = nc.to_dict()
        nc_dict["is_overdue"] = is_overdue
        nc_dict["remaining_hours"] = remaining_hours
        
        return AuditNCDetail(**nc_dict)
    
    @staticmethod
    async def list_ncs(
        db: AsyncSession,
        query_params: AuditNCQuery
    ) -> tuple[List[AuditNCDetail], int]:
        """
        获取NC列表
        
        Args:
            db: 数据库会话
            query_params: 查询参数
            
        Returns:
            (NC列表, 总记录数)
        """
        # 构建查询条件
        conditions = []
        
        if query_params.audit_id:
            conditions.append(AuditNC.audit_id == query_params.audit_id)
        
        if query_params.assigned_to:
            conditions.append(AuditNC.assigned_to == query_params.assigned_to)
        
        if query_params.responsible_dept:
            conditions.append(AuditNC.responsible_dept == query_params.responsible_dept)
        
        if query_params.verification_status:
            conditions.append(AuditNC.verification_status == query_params.verification_status)
        
        # 逾期筛选
        if query_params.is_overdue:
            now = datetime.utcnow()
            conditions.append(
                and_(
                    AuditNC.deadline < now,
                    AuditNC.verification_status.notin_(["closed", "verified"])
                )
            )
        
        # 查询总数
        count_query = select(func.count(AuditNC.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        result = await db.execute(count_query)
        total = result.scalar_one()
        
        # 查询列表
        query = select(AuditNC)
        if conditions:
            query = query.where(and_(*conditions))
        query = query.order_by(AuditNC.deadline.asc())  # 按期限升序排序
        query = query.offset((query_params.page - 1) * query_params.page_size).limit(query_params.page_size)
        
        result = await db.execute(query)
        ncs = result.scalars().all()
        
        # 转换为详情对象
        nc_details = []
        now = datetime.utcnow()
        for nc in ncs:
            remaining_hours = (nc.deadline - now).total_seconds() / 3600
            is_overdue = remaining_hours < 0 and nc.verification_status not in ["closed", "verified"]
            
            nc_dict = nc.to_dict()
            nc_dict["is_overdue"] = is_overdue
            nc_dict["remaining_hours"] = remaining_hours
            
            nc_details.append(AuditNCDetail(**nc_dict))
        
        return nc_details, total
    
    @staticmethod
    async def get_overdue_ncs(
        db: AsyncSession
    ) -> List[AuditNC]:
        """
        获取所有逾期的NC（用于定时任务升级）
        
        Args:
            db: 数据库会话
            
        Returns:
            逾期NC列表
        """
        now = datetime.utcnow()
        
        query = select(AuditNC).where(
            and_(
                AuditNC.deadline < now,
                AuditNC.verification_status.notin_(["closed", "verified"])
            )
        )
        
        result = await db.execute(query)
        return list(result.scalars().all())
