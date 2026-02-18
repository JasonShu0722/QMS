"""
审核不符合项 (NC) API 路由
Audit NC API Routes - 处理审核问题整改与闭环管理
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.audit_nc_service import AuditNCService
from app.schemas.audit_nc import (
    AuditNCAssign,
    AuditNCResponse,
    AuditNCVerify,
    AuditNCClose,
    AuditNCQuery,
    AuditNCDetail,
    AuditNCListResponse
)
from app.core.exceptions import NotFoundException, ValidationException, PermissionDeniedException

router = APIRouter(prefix="/audit-nc", tags=["审核不符合项管理"])


@router.post("/{nc_id}/assign", response_model=AuditNCDetail, summary="指派NC给责任板块")
async def assign_nc(
    nc_id: int,
    data: AuditNCAssign,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    指派NC给责任板块
    
    实现逻辑：
    - 验证NC记录存在且状态为open
    - 验证被指派人存在
    - 更新指派信息和期限
    - 发送通知给被指派人
    
    权限要求：审核员
    """
    try:
        nc = await AuditNCService.assign_nc(db, nc_id, data, current_user.id)
        return await AuditNCService.get_nc_detail(db, nc.id)
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{nc_id}/response", response_model=AuditNCDetail, summary="责任人填写原因和措施")
async def submit_nc_response(
    nc_id: int,
    data: AuditNCResponse,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    责任人填写原因和措施
    
    实现逻辑：
    - 验证NC记录存在且已指派给当前用户
    - 填写根本原因和纠正措施
    - 上传整改证据
    - 状态变更为submitted（待验证）
    - 通知审核员进行验证
    
    权限要求：被指派的责任人
    """
    try:
        nc = await AuditNCService.submit_response(db, nc_id, data, current_user.id)
        return await AuditNCService.get_nc_detail(db, nc.id)
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionDeniedException as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{nc_id}/verify", response_model=AuditNCDetail, summary="审核员验证有效性")
async def verify_nc(
    nc_id: int,
    data: AuditNCVerify,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    审核员验证有效性
    
    实现逻辑：
    - 验证NC记录存在且状态为submitted
    - 审核员填写验证意见
    - 如果验证通过，状态变更为verified
    - 如果验证不通过，状态变更为rejected，需要责任人重新提交
    - 通知责任人验证结果
    
    权限要求：审核员
    """
    try:
        nc = await AuditNCService.verify_nc(db, nc_id, data, current_user.id)
        return await AuditNCService.get_nc_detail(db, nc.id)
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionDeniedException as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{nc_id}/close", response_model=AuditNCDetail, summary="关闭NC")
async def close_nc(
    nc_id: int,
    data: AuditNCClose,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    关闭NC
    
    实现逻辑：
    - 验证NC记录存在且状态为verified
    - 填写关闭备注
    - 状态变更为closed
    - 记录关闭时间
    - 检查该审核的所有NC是否都已关闭，如果是则更新审核状态为completed
    
    权限要求：审核员
    """
    try:
        nc = await AuditNCService.close_nc(db, nc_id, data, current_user.id)
        return await AuditNCService.get_nc_detail(db, nc.id)
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionDeniedException as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{nc_id}", response_model=AuditNCDetail, summary="获取NC详情")
async def get_nc_detail(
    nc_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取NC详情
    
    返回NC的完整信息，包括：
    - 基本信息
    - 指派信息
    - 整改信息
    - 验证信息
    - 是否逾期
    - 剩余时间
    """
    nc_detail = await AuditNCService.get_nc_detail(db, nc_id)
    if not nc_detail:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"NC记录 ID {nc_id} 不存在")
    return nc_detail


@router.get("", response_model=AuditNCListResponse, summary="获取NC列表")
async def list_ncs(
    audit_id: int = Query(None, description="审核执行记录ID"),
    assigned_to: int = Query(None, description="指派给"),
    responsible_dept: str = Query(None, description="责任部门"),
    verification_status: str = Query(None, description="验证状态"),
    is_overdue: bool = Query(None, description="是否逾期"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页记录数"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取NC列表
    
    支持多维度筛选：
    - 按审核执行记录ID筛选
    - 按指派人筛选
    - 按责任部门筛选
    - 按验证状态筛选
    - 按是否逾期筛选
    
    返回分页结果，按期限升序排序
    """
    query_params = AuditNCQuery(
        audit_id=audit_id,
        assigned_to=assigned_to,
        responsible_dept=responsible_dept,
        verification_status=verification_status,
        is_overdue=is_overdue,
        page=page,
        page_size=page_size
    )
    
    ncs, total = await AuditNCService.list_ncs(db, query_params)
    
    total_pages = (total + page_size - 1) // page_size
    
    return AuditNCListResponse(
        items=ncs,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )
