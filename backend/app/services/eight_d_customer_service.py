"""
8D Customer Report Service
客诉8D报告业务逻辑服务
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
from datetime import datetime, timedelta
import logging

from app.models.eight_d_customer import EightDCustomer, EightDStatus, ApprovalLevel
from app.models.customer_complaint import CustomerComplaint, ComplaintStatus, SeverityLevel
from app.models.lesson_learned import LessonLearned, SourceType
from app.schemas.eight_d_customer import (
    D4D7Request,
    D8Request,
    EightDReviewRequest,
    EightDCustomerResponse,
    SLAStatus
)

logger = logging.getLogger(__name__)


class EightDCustomerService:
    """客诉8D报告服务类"""
    
    @staticmethod
    async def get_by_complaint_id(db: AsyncSession, complaint_id: int) -> Optional[EightDCustomer]:
        """根据客诉单ID获取8D报告"""
        result = await db.execute(
            select(EightDCustomer).where(EightDCustomer.complaint_id == complaint_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def submit_d4_d7(
        db: AsyncSession,
        complaint_id: int,
        data: D4D7Request,
        user_id: int
    ) -> EightDCustomer:
        """
        责任板块提交D4-D7阶段数据
        
        业务逻辑：
        1. 验证8D报告存在且状态为D4_D7_IN_PROGRESS
        2. 保存D4-D7数据
        3. 更新状态为D4_D7_COMPLETED
        4. 更新客诉单状态
        """
        # 获取8D报告
        eight_d = await EightDCustomerService.get_by_complaint_id(db, complaint_id)
        if not eight_d:
            raise ValueError(f"客诉单 {complaint_id} 的8D报告不存在")
        
        # 验证状态
        if eight_d.status != EightDStatus.D4_D7_IN_PROGRESS:
            raise ValueError(f"8D报告状态错误，当前状态：{eight_d.status}，期望状态：D4_D7_IN_PROGRESS")
        
        # 构建D4-D7数据
        d4_d7_data = {
            "d4_root_cause": {
                "analysis_method": data.d4_root_cause.analysis_method,
                "root_cause": data.d4_root_cause.root_cause,
                "evidence": data.d4_root_cause.evidence_files
            },
            "d5_corrective_actions": [
                {
                    "action": action.action,
                    "responsible": action.responsible,
                    "deadline": action.deadline
                }
                for action in data.d5_corrective_actions
            ],
            "d6_verification": {
                "verification_report": data.d6_verification.verification_report,
                "test_data": data.d6_verification.test_data,
                "result": data.d6_verification.result
            },
            "d7_standardization": {
                "document_modified": data.d7_standardization.document_modified,
                "modified_files": data.d7_standardization.modified_files,
                "attachments": data.d7_standardization.attachment_paths
            }
        }
        
        # 更新8D报告
        eight_d.d4_d7_responsible = d4_d7_data
        eight_d.status = EightDStatus.D4_D7_COMPLETED
        eight_d.submitted_at = datetime.utcnow()
        
        # 更新客诉单状态
        complaint = await db.get(CustomerComplaint, complaint_id)
        if complaint:
            complaint.status = ComplaintStatus.IN_REVIEW
        
        await db.commit()
        await db.refresh(eight_d)
        
        logger.info(f"8D报告 {eight_d.id} 的D4-D7阶段已提交，客诉单 {complaint_id}")
        return eight_d
    
    @staticmethod
    async def submit_d8(
        db: AsyncSession,
        complaint_id: int,
        data: D8Request,
        user_id: int
    ) -> EightDCustomer:
        """
        提交D8水平展开与经验教训
        
        业务逻辑：
        1. 验证8D报告状态
        2. 保存D8数据
        3. 如果勾选沉淀经验教训，创建LessonLearned记录
        4. 更新状态为IN_REVIEW（等待审批）
        """
        # 获取8D报告
        eight_d = await EightDCustomerService.get_by_complaint_id(db, complaint_id)
        if not eight_d:
            raise ValueError(f"客诉单 {complaint_id} 的8D报告不存在")
        
        # 验证状态（D4_D7_COMPLETED或D8_IN_PROGRESS都可以提交D8）
        if eight_d.status not in [EightDStatus.D4_D7_COMPLETED, EightDStatus.D8_IN_PROGRESS]:
            raise ValueError(f"8D报告状态错误，当前状态：{eight_d.status}")
        
        # 处理经验教训
        lesson_id = None
        if data.lesson_learned.should_archive:
            # 创建经验教训记录
            lesson = LessonLearned(
                source_type=SourceType.CUSTOMER_COMPLAINT,
                source_id=complaint_id,
                lesson_title=data.lesson_learned.lesson_title or "客诉经验教训",
                lesson_content=data.lesson_learned.lesson_content or "",
                root_cause=eight_d.d4_d7_responsible.get("d4_root_cause", {}).get("root_cause", "") if eight_d.d4_d7_responsible else "",
                preventive_action=data.lesson_learned.preventive_action or "",
                approved_by=user_id,
                is_active=True
            )
            db.add(lesson)
            await db.flush()
            lesson_id = lesson.id
            logger.info(f"创建经验教训记录 {lesson_id}，来源客诉单 {complaint_id}")
        
        # 构建D8数据
        d8_data = {
            "horizontal_deployment": [
                {
                    "product": item.product,
                    "action": item.action,
                    "status": item.status
                }
                for item in data.horizontal_deployment
            ],
            "lesson_learned": {
                "should_archive": data.lesson_learned.should_archive,
                "lesson_id": lesson_id
            }
        }
        
        # 更新8D报告
        eight_d.d8_horizontal = d8_data
        eight_d.status = EightDStatus.IN_REVIEW
        
        # 确定审批级别（根据客诉严重度）
        complaint = await db.get(CustomerComplaint, complaint_id)
        if complaint:
            if complaint.severity_level == SeverityLevel.MINOR:
                eight_d.approval_level = ApprovalLevel.SECTION_MANAGER
            else:
                eight_d.approval_level = ApprovalLevel.DEPARTMENT_HEAD
        
        await db.commit()
        await db.refresh(eight_d)
        
        logger.info(f"8D报告 {eight_d.id} 的D8阶段已提交，进入审批流程")
        return eight_d
    
    @staticmethod
    async def review_8d(
        db: AsyncSession,
        complaint_id: int,
        review_data: EightDReviewRequest,
        reviewer_id: int
    ) -> EightDCustomer:
        """
        审核8D报告
        
        业务逻辑：
        1. 验证8D报告状态为IN_REVIEW
        2. 如果批准，更新状态为APPROVED
        3. 如果驳回，更新状态为REJECTED，并回退到D4_D7_IN_PROGRESS
        4. 记录审核人和审核意见
        """
        # 获取8D报告
        eight_d = await EightDCustomerService.get_by_complaint_id(db, complaint_id)
        if not eight_d:
            raise ValueError(f"客诉单 {complaint_id} 的8D报告不存在")
        
        # 验证状态
        if eight_d.status != EightDStatus.IN_REVIEW:
            raise ValueError(f"8D报告状态错误，当前状态：{eight_d.status}，期望状态：IN_REVIEW")
        
        # 更新审核信息
        eight_d.reviewed_by = reviewer_id
        eight_d.reviewed_at = datetime.utcnow()
        eight_d.review_comments = review_data.review_comments
        
        if review_data.approved:
            # 批准
            eight_d.status = EightDStatus.APPROVED
            logger.info(f"8D报告 {eight_d.id} 已批准")
        else:
            # 驳回，回退到D4_D7_IN_PROGRESS
            eight_d.status = EightDStatus.REJECTED
            # 清空D4-D7和D8数据，要求重新填写
            eight_d.d4_d7_responsible = None
            eight_d.d8_horizontal = None
            logger.info(f"8D报告 {eight_d.id} 已驳回，原因：{review_data.review_comments}")
            
            # 更新客诉单状态回到IN_RESPONSE
            complaint = await db.get(CustomerComplaint, complaint_id)
            if complaint:
                complaint.status = ComplaintStatus.IN_RESPONSE
        
        await db.commit()
        await db.refresh(eight_d)
        
        return eight_d
    
    @staticmethod
    async def archive_8d(
        db: AsyncSession,
        complaint_id: int,
        user_id: int
    ) -> EightDCustomer:
        """
        归档8D报告
        
        业务逻辑：
        1. 验证8D报告状态为APPROVED
        2. 执行归档检查表核对（预留逻辑）
        3. 更新状态为CLOSED
        4. 更新客诉单状态为CLOSED
        """
        # 获取8D报告
        eight_d = await EightDCustomerService.get_by_complaint_id(db, complaint_id)
        if not eight_d:
            raise ValueError(f"客诉单 {complaint_id} 的8D报告不存在")
        
        # 验证状态
        if eight_d.status != EightDStatus.APPROVED:
            raise ValueError(f"8D报告状态错误，当前状态：{eight_d.status}，期望状态：APPROVED")
        
        # TODO: 执行归档检查表核对逻辑（预留）
        # 检查项：D0-D8是否完整、附件是否齐全、经验教训是否沉淀等
        
        # 更新8D报告状态
        eight_d.status = EightDStatus.CLOSED
        
        # 更新客诉单状态
        complaint = await db.get(CustomerComplaint, complaint_id)
        if complaint:
            complaint.status = ComplaintStatus.CLOSED
        
        await db.commit()
        await db.refresh(eight_d)
        
        logger.info(f"8D报告 {eight_d.id} 已归档，客诉单 {complaint_id} 已关闭")
        return eight_d
    
    @staticmethod
    async def calculate_sla_status(
        db: AsyncSession,
        complaint_id: int
    ) -> SLAStatus:
        """
        计算SLA时效状态
        
        SLA规则：
        - 8D报告提交：7个工作日内
        - 报告归档：10个工作日内
        
        注：此处简化为自然日计算，实际应排除周末和节假日
        """
        # 获取客诉单
        complaint = await db.get(CustomerComplaint, complaint_id)
        if not complaint:
            raise ValueError(f"客诉单 {complaint_id} 不存在")
        
        # 获取8D报告
        eight_d = await EightDCustomerService.get_by_complaint_id(db, complaint_id)
        if not eight_d:
            raise ValueError(f"客诉单 {complaint_id} 的8D报告不存在")
        
        # 计算天数
        days_since_creation = (datetime.utcnow() - complaint.created_at).days
        
        # SLA期限
        submission_deadline = 7  # 7个工作日
        archive_deadline = 10  # 10个工作日
        
        # 判断是否超期
        is_submission_overdue = False
        is_archive_overdue = False
        remaining_days = 0
        
        if eight_d.status in [EightDStatus.DRAFT, EightDStatus.D0_D3_COMPLETED, EightDStatus.D4_D7_IN_PROGRESS]:
            # 尚未提交D4-D7
            remaining_days = submission_deadline - days_since_creation
            is_submission_overdue = remaining_days < 0
        elif eight_d.status in [EightDStatus.D4_D7_COMPLETED, EightDStatus.D8_IN_PROGRESS, EightDStatus.IN_REVIEW, EightDStatus.APPROVED]:
            # 已提交但未归档
            remaining_days = archive_deadline - days_since_creation
            is_archive_overdue = remaining_days < 0
        else:
            # 已归档或已驳回
            remaining_days = 0
        
        return SLAStatus(
            complaint_id=complaint_id,
            complaint_number=complaint.complaint_number,
            eight_d_status=eight_d.status,
            days_since_creation=days_since_creation,
            submission_deadline=submission_deadline,
            archive_deadline=archive_deadline,
            is_submission_overdue=is_submission_overdue,
            is_archive_overdue=is_archive_overdue,
            remaining_days=remaining_days
        )
    
    @staticmethod
    async def get_overdue_reports(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100
    ) -> List[SLAStatus]:
        """
        获取所有超期的8D报告列表
        
        用于管理员监控和督办
        """
        # 查询所有未关闭的客诉单
        result = await db.execute(
            select(CustomerComplaint)
            .where(CustomerComplaint.status != ComplaintStatus.CLOSED)
            .offset(skip)
            .limit(limit)
        )
        complaints = result.scalars().all()
        
        # 计算每个客诉单的SLA状态
        overdue_list = []
        for complaint in complaints:
            try:
                sla_status = await EightDCustomerService.calculate_sla_status(db, complaint.id)
                if sla_status.is_submission_overdue or sla_status.is_archive_overdue:
                    overdue_list.append(sla_status)
            except ValueError:
                # 如果8D报告不存在，跳过
                continue
        
        return overdue_list
