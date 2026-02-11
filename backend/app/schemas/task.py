"""
任务相关的 Pydantic 数据模型
Task Schemas - 用于 API 请求和响应的数据校验
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class TaskItemResponse(BaseModel):
    """
    待办任务项响应模型
    """
    task_type: str = Field(..., description="任务类型")
    task_id: int = Field(..., description="任务ID")
    task_number: str = Field(..., description="任务单据编号")
    deadline: Optional[datetime] = Field(None, description="截止时间")
    urgency: str = Field(..., description="紧急程度: overdue/urgent/normal")
    color: str = Field(..., description="颜色标识: red/yellow/green")
    remaining_hours: float = Field(..., description="剩余处理时间（小时）")
    link: str = Field(..., description="跳转链接")
    description: Optional[str] = Field(None, description="任务描述")
    
    class Config:
        json_schema_extra = {
            "example": {
                "task_type": "SCAR报告处理",
                "task_id": 123,
                "task_number": "SCAR-2024-001",
                "deadline": "2024-01-20T10:00:00",
                "urgency": "urgent",
                "color": "yellow",
                "remaining_hours": 48.5,
                "link": "/supplier/scar/123",
                "description": "供应商A物料不良问题"
            }
        }


class TaskListResponse(BaseModel):
    """
    待办任务列表响应模型
    """
    total: int = Field(..., description="总任务数")
    tasks: list[TaskItemResponse] = Field(..., description="任务列表")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total": 5,
                "tasks": [
                    {
                        "task_type": "SCAR报告处理",
                        "task_id": 123,
                        "task_number": "SCAR-2024-001",
                        "deadline": "2024-01-20T10:00:00",
                        "urgency": "urgent",
                        "color": "yellow",
                        "remaining_hours": 48.5,
                        "link": "/supplier/scar/123",
                        "description": "供应商A物料不良问题"
                    }
                ]
            }
        }


class TaskStatisticsResponse(BaseModel):
    """
    任务统计信息响应模型
    """
    total: int = Field(..., description="总任务数")
    overdue: int = Field(..., description="已超期任务数")
    urgent: int = Field(..., description="紧急任务数")
    normal: int = Field(..., description="正常任务数")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total": 10,
                "overdue": 2,
                "urgent": 3,
                "normal": 5
            }
        }

