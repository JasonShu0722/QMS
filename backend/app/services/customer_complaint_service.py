"""
Customer Complaint Service
客诉管理服务层 - 处理客诉录入、分级、流转等业务逻辑
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from typing import Optional, List
from datetime import datetime, date
import logging

from app.models.customer_complaint import CustomerComplaint, ComplaintType, ComplaintStatus, SeverityLevel
from app.models.user import User
from app.schemas.customer_complaint import (
    CustomerComplaintCreate,
    PreliminaryAnalysisRequest,
    IMSTracebackRequest,
    IMSTracebackResponse
)
from app.services.ims_integration_service import IMSIntegrationService

logger = logging.getLogger(__name__)


class CustomerComplaintService:
    """客诉管理服务"""
    
    @staticmethod
    async def create_complaint(
        db: AsyncSession,
        complaint_data: CustomerComplaintCreate,
        created_by_id: int
    ) -> CustomerComplaint:
        """
        创建客诉单
        
        业务逻辑：
        1. 生成唯一客诉单号（格式：CC-YYYYMMDD-序号）
        2. 根据缺陷描述自动界定严重度等级（内置分级逻辑）
        3. 创建客诉记录并设置初始状态为"待处理"
        """
        # 生成客诉单号
        complaint_number = await CustomerComplaintService._generate_complaint_number(db)
        
        # 自动界定严重度等级
        severity_level = CustomerComplaintService._determine_severity_level(
            complaint_data.defect_description,
            complaint_data.complaint_type
        )
        
        # 创建客诉单
        complaint = CustomerComplaint(
            complaint_number=complaint_number,
            complaint_type=ComplaintType(complaint_data.complaint_type.value),
            customer_code=complaint_data.customer_code,
            product_type=complaint_data.product_type,
            defect_description=complaint_data.defect_description,
            severity_level=severity_level,
            vin_code=complaint_data.vin_code,
            mileage=complaint_data.mileage,
            purchase_date=complaint_data.purchase_date,
            status=ComplaintStatus.PENDING,
            created_by=created_by_id
        )
        
        db.add(complaint)
        await db.commit()
        await db.refresh(complaint)
        
        logger.info(f"创建客诉单成功: {complaint_number}, 严重度: {severity_level}")
        
        return complaint
    
    @staticmethod
    async def _generate_complaint_number(db: AsyncSession) -> str:
        """
        生成客诉单号
        格式：CC-YYYYMMDD-序号（如：CC-20240115-001）
        """
        today = datetime.now().strftime("%Y%m%d")
        prefix = f"CC-{today}-"
        
        # 查询今日最大序号
        result = await db.execute(
            select(func.max(CustomerComplaint.complaint_number))
            .where(CustomerComplaint.complaint_number.like(f"{prefix}%"))
        )
        max_number = result.scalar()
        
        if max_number:
            # 提取序号并加1
            last_seq = int(max_number.split("-")[-1])
            new_seq = last_seq + 1
        else:
            new_seq = 1
        
        return f"{prefix}{new_seq:03d}"
    
    @staticmethod
    def _determine_severity_level(defect_description: str, complaint_type: str) -> SeverityLevel:
        """
        根据缺陷描述自动界定严重度等级
        
        分级逻辑（内置规则）：
        - CRITICAL（严重）：涉及安全、抛锚、起火、爆炸等关键词
        - MAJOR（重大）：涉及功能失效、批量、召回等关键词
        - MINOR（一般）：涉及外观、轻微、偶发等关键词
        - TBD（待定义）：无法自动判定时的默认值
        """
        description_lower = defect_description.lower()
        
        # 严重等级关键词
        critical_keywords = ["安全", "抛锚", "起火", "爆炸", "人身伤害", "断电", "失控", "刹车失效"]
        if any(keyword in description_lower for keyword in critical_keywords):
            return SeverityLevel.CRITICAL
        
        # 重大等级关键词
        major_keywords = ["功能失效", "批量", "召回", "停产", "无法使用", "烧毁", "短路"]
        if any(keyword in description_lower for keyword in major_keywords):
            return SeverityLevel.MAJOR
        
        # 一般等级关键词
        minor_keywords = ["外观", "轻微", "偶发", "划痕", "色差", "噪音"]
        if any(keyword in description_lower for keyword in minor_keywords):
            return SeverityLevel.MINOR
        
        # 默认待定义
        return SeverityLevel.TBD
    
    @staticmethod
    async def submit_preliminary_analysis(
        db: AsyncSession,
        complaint_id: int,
        analysis_data: PreliminaryAnalysisRequest,
        cqe_id: int
    ) -> CustomerComplaint:
        """
        CQE提交一次因解析（D0-D3）
        
        业务逻辑：
        1. 更新客诉单状态为"分析中"
        2. 记录D0-D3阶段的分析内容
        3. 指定责任部门
        4. 如果提供了IMS追溯信息，自动调用IMS接口查询
        5. 任务流转：CQE -> 责任板块
        """
        # 查询客诉单
        result = await db.execute(
            select(CustomerComplaint).where(CustomerComplaint.id == complaint_id)
        )
        complaint = result.scalar_one_or_none()
        
        if not complaint:
            raise ValueError(f"客诉单不存在: ID={complaint_id}")
        
        if complaint.status != ComplaintStatus.PENDING:
            raise ValueError(f"客诉单状态不正确，当前状态: {complaint.status}")
        
        # 更新客诉单
        complaint.status = ComplaintStatus.IN_RESPONSE
        complaint.cqe_id = cqe_id
        complaint.responsible_dept = analysis_data.responsible_dept
        
        # TODO: 将D0-D3数据存储到EightDCustomer表（在12.4任务中实现）
        # 当前阶段仅更新客诉单基本信息
        
        await db.commit()
        await db.refresh(complaint)
        
        logger.info(f"客诉单 {complaint.complaint_number} 完成一次因解析，责任部门: {analysis_data.responsible_dept}")
        
        # 如果提供了IMS追溯信息，执行自动追溯
        if analysis_data.ims_work_order or analysis_data.ims_batch_number:
            traceback_result = await CustomerComplaintService.auto_traceback_ims(
                db=db,
                work_order=analysis_data.ims_work_order,
                batch_number=analysis_data.ims_batch_number
            )
            logger.info(f"IMS自动追溯完成: 发现异常={traceback_result.anomaly_detected}")
        
        return complaint
    
    @staticmethod
    async def auto_traceback_ims(
        db: AsyncSession,
        work_order: Optional[str] = None,
        batch_number: Optional[str] = None,
        material_code: Optional[str] = None
    ) -> IMSTracebackResponse:
        """
        自动追溯IMS系统
        
        联动IMS查询过程记录，检测是否存在异常
        """
        try:
            ims_service = IMSIntegrationService()
            
            # 调用IMS接口查询过程记录
            # 注意：这里需要IMS系统提供追溯接口，当前为模拟实现
            process_records = []
            defect_records = []
            material_records = []
            anomaly_detected = False
            anomaly_description = None
            
            # TODO: 实际调用IMS接口
            # process_data = await ims_service.query_process_records(work_order, batch_number)
            # defect_data = await ims_service.query_defect_records(work_order, batch_number)
            # material_data = await ims_service.query_material_records(material_code)
            
            # 模拟数据（实际应从IMS获取）
            if work_order:
                process_records = [
                    {"process": "SMT贴片", "operator": "张三", "result": "OK", "timestamp": "2024-01-05 08:30:00"},
                    {"process": "波峰焊", "operator": "李四", "result": "OK", "timestamp": "2024-01-05 09:15:00"},
                    {"process": "功能测试", "operator": "王五", "result": "OK", "timestamp": "2024-01-05 10:00:00"}
                ]
            
            if batch_number:
                # 模拟检测到不良记录
                defect_records = [
                    {"defect_type": "虚焊", "qty": 2, "date": "2024-01-05", "process": "波峰焊"}
                ]
                
                if defect_records:
                    anomaly_detected = True
                    anomaly_description = f"该批次在{defect_records[0]['process']}工序出现{defect_records[0]['qty']}次{defect_records[0]['defect_type']}不良"
            
            if material_code:
                material_records = [
                    {"material_code": material_code, "supplier": "SUP-A", "batch": "B001", "incoming_date": "2024-01-03"}
                ]
            
            return IMSTracebackResponse(
                found=bool(work_order or batch_number),
                work_order=work_order,
                batch_number=batch_number,
                production_date=date(2024, 1, 5) if work_order else None,
                process_records=process_records,
                defect_records=defect_records,
                material_records=material_records,
                anomaly_detected=anomaly_detected,
                anomaly_description=anomaly_description
            )
            
        except Exception as e:
            logger.error(f"IMS自动追溯失败: {str(e)}")
            return IMSTracebackResponse(
                found=False,
                anomaly_detected=False
            )
    
    @staticmethod
    async def get_complaint_by_id(
        db: AsyncSession,
        complaint_id: int
    ) -> Optional[CustomerComplaint]:
        """根据ID查询客诉单"""
        result = await db.execute(
            select(CustomerComplaint).where(CustomerComplaint.id == complaint_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def list_complaints(
        db: AsyncSession,
        complaint_type: Optional[str] = None,
        status: Optional[str] = None,
        customer_code: Optional[str] = None,
        severity_level: Optional[str] = None,
        cqe_id: Optional[int] = None,
        responsible_dept: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        page: int = 1,
        page_size: int = 50
    ) -> tuple[List[CustomerComplaint], int]:
        """
        查询客诉单列表（支持多条件筛选）
        
        返回：(客诉单列表, 总数)
        """
        # 构建查询条件
        conditions = []
        
        if complaint_type:
            conditions.append(CustomerComplaint.complaint_type == ComplaintType(complaint_type))
        
        if status:
            conditions.append(CustomerComplaint.status == ComplaintStatus(status))
        
        if customer_code:
            conditions.append(CustomerComplaint.customer_code == customer_code)
        
        if severity_level:
            conditions.append(CustomerComplaint.severity_level == SeverityLevel(severity_level))
        
        if cqe_id:
            conditions.append(CustomerComplaint.cqe_id == cqe_id)
        
        if responsible_dept:
            conditions.append(CustomerComplaint.responsible_dept == responsible_dept)
        
        if start_date:
            conditions.append(CustomerComplaint.created_at >= datetime.combine(start_date, datetime.min.time()))
        
        if end_date:
            conditions.append(CustomerComplaint.created_at <= datetime.combine(end_date, datetime.max.time()))
        
        # 查询总数
        count_query = select(func.count(CustomerComplaint.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        
        result = await db.execute(count_query)
        total = result.scalar()
        
        # 查询列表
        query = select(CustomerComplaint)
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(CustomerComplaint.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await db.execute(query)
        complaints = result.scalars().all()
        
        return list(complaints), total
