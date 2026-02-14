"""
Customer Complaint API Endpoints
客诉管理API接口
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import date

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.customer_complaint import (
    CustomerComplaintCreate,
    CustomerComplaintResponse,
    CustomerComplaintListResponse,
    PreliminaryAnalysisRequest,
    IMSTracebackRequest,
    IMSTracebackResponse
)
from app.services.customer_complaint_service import CustomerComplaintService

router = APIRouter(prefix="/customer-complaints", tags=["客户质量管理"])


@router.post(
    "",
    response_model=CustomerComplaintResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建客诉单",
    description="""
    创建客诉单（0KM客诉或售后客诉）
    
    业务逻辑：
    - 自动生成客诉单号（格式：CC-YYYYMMDD-序号）
    - 根据缺陷描述自动界定严重度等级
    - 售后客诉时，VIN码、里程、购车日期为必填项
    - 初始状态为"待处理"
    
    权限要求：需要"客诉管理-录入"权限
    """
)
async def create_complaint(
    complaint_data: CustomerComplaintCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建客诉单"""
    try:
        complaint = await CustomerComplaintService.create_complaint(
            db=db,
            complaint_data=complaint_data,
            created_by_id=current_user.id
        )
        return complaint
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"创建客诉单失败: {str(e)}")


@router.get(
    "",
    response_model=CustomerComplaintListResponse,
    summary="获取客诉单列表",
    description="""
    查询客诉单列表（支持多条件筛选）
    
    筛选条件：
    - complaint_type: 客诉类型（0km/after_sales）
    - status: 客诉状态
    - customer_code: 客户代码
    - severity_level: 严重度等级
    - cqe_id: 负责CQE的用户ID
    - responsible_dept: 责任部门
    - start_date/end_date: 创建时间范围
    
    权限要求：需要"客诉管理-查阅"权限
    """
)
async def list_complaints(
    complaint_type: Optional[str] = Query(None, description="客诉类型：0km/after_sales"),
    status: Optional[str] = Query(None, description="客诉状态"),
    customer_code: Optional[str] = Query(None, description="客户代码"),
    severity_level: Optional[str] = Query(None, description="严重度等级"),
    cqe_id: Optional[int] = Query(None, description="负责CQE的用户ID"),
    responsible_dept: Optional[str] = Query(None, description="责任部门"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取客诉单列表"""
    try:
        complaints, total = await CustomerComplaintService.list_complaints(
            db=db,
            complaint_type=complaint_type,
            status=status,
            customer_code=customer_code,
            severity_level=severity_level,
            cqe_id=cqe_id,
            responsible_dept=responsible_dept,
            start_date=start_date,
            end_date=end_date,
            page=page,
            page_size=page_size
        )
        
        return CustomerComplaintListResponse(
            total=total,
            items=complaints,
            page=page,
            page_size=page_size
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"查询客诉单列表失败: {str(e)}")


@router.get(
    "/{complaint_id}",
    response_model=CustomerComplaintResponse,
    summary="获取客诉单详情",
    description="根据ID查询客诉单详细信息"
)
async def get_complaint(
    complaint_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取客诉单详情"""
    complaint = await CustomerComplaintService.get_complaint_by_id(db, complaint_id)
    
    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"客诉单不存在: ID={complaint_id}")
    
    return complaint


@router.post(
    "/{complaint_id}/preliminary-analysis",
    response_model=CustomerComplaintResponse,
    summary="CQE提交一次因解析（D0-D3）",
    description="""
    CQE完成一次因解析（D0-D3阶段）
    
    业务逻辑：
    - D0: 紧急响应行动（围堵措施）
    - D1: 团队组建
    - D2: 问题描述（5W2H格式）
    - D3: 临时围堵措施及验证
    - 责任判定：指定责任部门
    - 自动追溯：如果提供IMS工单号/批次号，自动调用IMS接口查询过程记录
    - 任务流转：CQE -> 责任板块（状态变更为"待回复"）
    
    权限要求：需要"客诉管理-修改"权限，且当前用户为CQE角色
    """
)
async def submit_preliminary_analysis(
    complaint_id: int,
    analysis_data: PreliminaryAnalysisRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """CQE提交一次因解析"""
    try:
        complaint = await CustomerComplaintService.submit_preliminary_analysis(
            db=db,
            complaint_id=complaint_id,
            analysis_data=analysis_data,
            cqe_id=current_user.id
        )
        return complaint
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"提交一次因解析失败: {str(e)}")


@router.post(
    "/traceback/ims",
    response_model=IMSTracebackResponse,
    summary="IMS自动追溯",
    description="""
    联动IMS系统查询过程记录
    
    功能：
    - 根据工单号/批次号/物料编码查询IMS生产记录
    - 自动检测是否存在异常（不良记录、特采记录等）
    - 返回过程记录、不良记录、物料追溯信息
    
    使用场景：
    - CQE在D0-D3阶段进行根因分析时调用
    - 责任板块在D4-D7阶段进行深度分析时调用
    
    权限要求：需要"客诉管理-查阅"权限
    """
)
async def traceback_ims(
    traceback_request: IMSTracebackRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """IMS自动追溯"""
    try:
        result = await CustomerComplaintService.auto_traceback_ims(
            db=db,
            work_order=traceback_request.work_order,
            batch_number=traceback_request.batch_number,
            material_code=traceback_request.material_code
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"IMS追溯失败: {str(e)}")
