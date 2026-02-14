"""
8D Customer Report API Endpoints
客诉8D报告API接口
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.eight_d_customer_service import EightDCustomerService
from app.schemas.eight_d_customer import (
    D4D7Request,
    D8Request,
    EightDReviewRequest,
    EightDCustomerResponse,
    SLAStatus
)

router = APIRouter(prefix="/customer-complaints", tags=["8D Customer Reports"])


@router.post("/{complaint_id}/8d/d4-d7", response_model=EightDCustomerResponse)
async def submit_d4_d7(
    complaint_id: int,
    data: D4D7Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    责任板块提交D4-D7阶段数据
    
    **业务流程**：
    1. 责任板块担当填写D4（根本原因分析）
    2. 填写D5（纠正措施）
    3. 填写D6（验证有效性，必须上传验证报告）
    4. 填写D7（标准化，勾选是否涉及文件修改）
    
    **权限要求**：责任板块成员
    
    **SLA要求**：7个工作日内提交
    """
    try:
        eight_d = await EightDCustomerService.submit_d4_d7(
            db=db,
            complaint_id=complaint_id,
            data=data,
            user_id=current_user.id
        )
        return eight_d
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"提交D4-D7失败：{str(e)}")


@router.post("/{complaint_id}/8d/d8", response_model=EightDCustomerResponse)
async def submit_d8(
    complaint_id: int,
    data: D8Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    提交D8水平展开与经验教训
    
    **业务流程**：
    1. 搜索并关联类似产品/类似工艺
    2. 将对策推送到相关项目组
    3. 勾选是否沉淀经验教训
    4. 如果勾选，系统自动弹出《经验教训总结表》
    5. 提交后由责任部门部长审批
    
    **权限要求**：责任板块成员
    """
    try:
        eight_d = await EightDCustomerService.submit_d8(
            db=db,
            complaint_id=complaint_id,
            data=data,
            user_id=current_user.id
        )
        return eight_d
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"提交D8失败：{str(e)}")


@router.post("/{complaint_id}/8d/review", response_model=EightDCustomerResponse)
async def review_8d_report(
    complaint_id: int,
    review_data: EightDReviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    审核8D报告
    
    **分级审批流**：
    - C级问题：科室经理审批
    - A/B级问题：质量部长 + 责任部门部长联合审批
    
    **审批结果**：
    - 批准：8D报告状态变为APPROVED，可以归档
    - 驳回：8D报告状态变为REJECTED，回退到D4_D7_IN_PROGRESS，需重新填写
    
    **权限要求**：科室经理或部长
    """
    try:
        eight_d = await EightDCustomerService.review_8d(
            db=db,
            complaint_id=complaint_id,
            review_data=review_data,
            reviewer_id=current_user.id
        )
        return eight_d
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"审核8D报告失败：{str(e)}")


@router.post("/{complaint_id}/8d/archive", response_model=EightDCustomerResponse)
async def archive_8d_report(
    complaint_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    归档8D报告
    
    **归档条件**：
    1. 8D报告状态为APPROVED（已批准）
    2. 通过归档检查表核对（预留功能）
    
    **归档后**：
    - 8D报告状态变为CLOSED
    - 客诉单状态变为CLOSED
    
    **SLA要求**：10个工作日内归档
    
    **权限要求**：CQE或质量经理
    """
    try:
        eight_d = await EightDCustomerService.archive_8d(
            db=db,
            complaint_id=complaint_id,
            user_id=current_user.id
        )
        return eight_d
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"归档8D报告失败：{str(e)}")


@router.get("/{complaint_id}/8d/sla", response_model=SLAStatus)
async def get_sla_status(
    complaint_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取8D报告的SLA时效状态
    
    **SLA规则**：
    - 8D报告提交：7个工作日内
    - 报告归档：10个工作日内
    
    **返回信息**：
    - 自创建以来的天数
    - 是否提交超期
    - 是否归档超期
    - 剩余天数（负数表示超期）
    
    **用途**：
    - 个人中心待办任务显示倒计时
    - 管理员监控超期报告
    """
    try:
        sla_status = await EightDCustomerService.calculate_sla_status(db, complaint_id)
        return sla_status
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取SLA状态失败：{str(e)}")


@router.get("/8d/overdue", response_model=List[SLAStatus])
async def get_overdue_reports(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取所有超期的8D报告列表
    
    **用途**：
    - 管理员监控和督办
    - 质量部长查看团队整体工作负载
    
    **返回**：所有提交超期或归档超期的8D报告
    
    **权限要求**：质量经理或管理员
    """
    try:
        overdue_list = await EightDCustomerService.get_overdue_reports(
            db=db,
            skip=skip,
            limit=limit
        )
        return overdue_list
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取超期报告失败：{str(e)}")


@router.get("/{complaint_id}/8d", response_model=EightDCustomerResponse)
async def get_8d_report(
    complaint_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取8D报告详情
    
    **返回**：完整的8D报告数据（D0-D3, D4-D7, D8）
    
    **权限要求**：相关人员（CQE、责任板块、审批人）
    """
    try:
        eight_d = await EightDCustomerService.get_by_complaint_id(db, complaint_id)
        if not eight_d:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"客诉单 {complaint_id} 的8D报告不存在")
        return eight_d
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取8D报告失败：{str(e)}")
