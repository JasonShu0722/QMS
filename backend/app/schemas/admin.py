"""
管理员相关的 Pydantic 数据校验模型
Admin Schemas - 用于管理员操作的 API 请求/响应验证
"""
from typing import Optional
from pydantic import BaseModel, Field


class UserApprovalRequest(BaseModel):
    """
    用户审核请求模型
    """
    reason: Optional[str] = Field(None, max_length=500, description="驳回原因（驳回时必填）")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "reason": "提供的资料不完整，请补充供应商资质证明"
                }
            ]
        }
    }


class UserFreezeRequest(BaseModel):
    """
    用户冻结请求模型
    """
    reason: Optional[str] = Field(None, max_length=500, description="冻结原因")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "reason": "供应商合作暂停"
                }
            ]
        }
    }


class PasswordResetResponse(BaseModel):
    """
    密码重置响应模型
    """
    message: str
    temporary_password: str
    email_sent: bool
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "message": "密码已重置，临时密码已发送至用户邮箱",
                    "temporary_password": "TempPass123!",
                    "email_sent": True
                }
            ]
        }
    }


class UserActionResponse(BaseModel):
    """
    用户操作响应模型
    """
    message: str
    user_id: int
    username: str
    status: str
    email_sent: bool = False
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "message": "用户已批准",
                    "user_id": 1,
                    "username": "zhang_san",
                    "status": "active",
                    "email_sent": True
                }
            ]
        }
    }
