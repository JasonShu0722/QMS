"""
管理员相关的 Pydantic 数据校验模型
Admin Schemas - 用于管理员操作的 API 请求/响应验证
"""
import re
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.schemas.user import UserResponseSchema


USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_]+$")


def _normalize_allowed_environments(value: str) -> str:
    allowed = {"stable", "preview"}
    parts = [item.strip() for item in value.split(",") if item.strip()]
    if not parts or any(item not in allowed for item in parts):
        raise ValueError("allowed_environments 仅支持 stable 和 preview，用逗号分隔")
    return ",".join(dict.fromkeys(parts))


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


class UserUpdateRequest(BaseModel):
    """
    用户基本信息更新请求
    """

    full_name: str = Field(..., min_length=2, max_length=100, description="姓名")
    email: EmailStr = Field(..., description="邮箱")
    phone: Optional[str] = Field(None, max_length=20, description="电话")
    department: Optional[str] = Field(None, max_length=100, description="部门")
    position: Optional[str] = Field(None, max_length=100, description="岗位")
    allowed_environments: str = Field(..., min_length=6, max_length=50, description="允许访问环境")

    @field_validator("allowed_environments")
    @classmethod
    def validate_allowed_environments(cls, value: str) -> str:
        return _normalize_allowed_environments(value)


class _AdminUserProvisionBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    full_name: str = Field(..., min_length=2, max_length=100, description="姓名")
    email: EmailStr = Field(..., description="邮箱")
    phone: Optional[str] = Field(None, max_length=20, description="电话")
    department: Optional[str] = Field(None, max_length=100, description="部门")
    position: Optional[str] = Field(None, max_length=100, description="岗位")
    supplier_identifier: Optional[str] = Field(
        None,
        max_length=200,
        description="供应商标识，支持供应商ID、供应商代码或供应商名称",
    )

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        normalized = value.strip()
        if not USERNAME_PATTERN.match(normalized):
            raise ValueError("用户名仅支持字母、数字和下划线")
        return normalized

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, value: str) -> str:
        return value.strip()

    @field_validator("phone", "department", "position", "supplier_identifier")
    @classmethod
    def normalize_optional_text(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class AdminUserCreateRequest(_AdminUserProvisionBase):
    user_type: Literal["internal", "supplier"] = Field(..., description="用户类型")
    allowed_environments: str = Field(..., min_length=6, max_length=50, description="允许访问环境")
    role_tag_ids: list[int] = Field(default_factory=list, description="创建后直接分配的角色标签")

    @field_validator("allowed_environments")
    @classmethod
    def validate_allowed_environments(cls, value: str) -> str:
        return _normalize_allowed_environments(value)


class AdminBulkUserCreateItem(_AdminUserProvisionBase):
    pass


class AdminBulkUserCreateRequest(BaseModel):
    user_type: Literal["internal", "supplier"] = Field(..., description="本批次创建的用户类型")
    allowed_environments: str = Field(..., min_length=6, max_length=50, description="允许访问环境")
    role_tag_ids: list[int] = Field(default_factory=list, description="本批次统一分配的角色标签")
    items: list[AdminBulkUserCreateItem] = Field(..., min_length=1, max_length=200, description="批量创建明细")

    @field_validator("allowed_environments")
    @classmethod
    def validate_allowed_environments(cls, value: str) -> str:
        return _normalize_allowed_environments(value)


class AdminUserCreateResponse(BaseModel):
    message: str
    user: UserResponseSchema
    temporary_password: str
    email_sent: bool = False


class AdminBulkUserCreateItemResponse(BaseModel):
    row_number: int
    user: UserResponseSchema
    temporary_password: str
    email_sent: bool = False


class AdminBulkUserCreateResponse(BaseModel):
    message: str
    total_count: int
    created_count: int
    results: list[AdminBulkUserCreateItemResponse]


class UserRoleAssignmentRequest(BaseModel):
    """
    用户角色分配请求
    """

    role_tag_ids: list[int] = Field(default_factory=list, description="角色标签ID列表")


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
