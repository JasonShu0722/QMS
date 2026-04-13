"""
用户相关的 Pydantic 数据校验模型
User Schemas - 用于 API 请求/响应的数据验证
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator

from app.schemas.role_tag import RoleTagSummarySchema


class UserRegisterSchema(BaseModel):
    """
    用户注册表单校验模型
    
    支持内部员工和供应商用户的注册
    """
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=8, description="密码")
    full_name: str = Field(..., min_length=2, max_length=100, description="姓名")
    email: EmailStr = Field(..., description="邮箱")
    phone: Optional[str] = Field(None, max_length=20, description="电话")
    user_type: str = Field(..., description="用户类型: internal 或 supplier")
    
    # 内部员工专属字段
    department: Optional[str] = Field(None, max_length=100, description="部门（内部员工必填）")
    position: Optional[str] = Field(None, max_length=100, description="职位")
    
    # 供应商用户专属字段
    supplier_id: Optional[int] = Field(None, description="供应商ID（供应商用户必填）")
    
    @field_validator('user_type')
    @classmethod
    def validate_user_type(cls, v: str) -> str:
        """验证用户类型"""
        if v not in ['internal', 'supplier']:
            raise ValueError('用户类型必须是 internal 或 supplier')
        return v
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        """验证用户名格式"""
        if not v.isalnum() and '_' not in v:
            raise ValueError('用户名只能包含字母、数字和下划线')
        return v
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "username": "zhang_san",
                    "password": "SecurePass123!",
                    "full_name": "张三",
                    "email": "zhangsan@company.com",
                    "phone": "13800138000",
                    "user_type": "internal",
                    "department": "质量部",
                    "position": "质量工程师"
                },
                {
                    "username": "supplier_user",
                    "password": "SupplierPass456!",
                    "full_name": "李四",
                    "email": "lisi@supplier.com",
                    "phone": "13900139000",
                    "user_type": "supplier",
                    "supplier_id": 1,
                    "position": "质量经理"
                }
            ]
        }
    }


class UserApprovalSchema(BaseModel):
    """
    用户审核操作校验模型
    
    用于管理员审批或驳回用户注册申请
    """
    action: str = Field(..., description="审核动作: approve 或 reject")
    reason: Optional[str] = Field(None, max_length=500, description="驳回原因（驳回时必填）")
    
    @field_validator('action')
    @classmethod
    def validate_action(cls, v: str) -> str:
        """验证审核动作"""
        if v not in ['approve', 'reject']:
            raise ValueError('审核动作必须是 approve 或 reject')
        return v
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "action": "approve"
                },
                {
                    "action": "reject",
                    "reason": "提供的资料不完整，请补充供应商资质证明"
                }
            ]
        }
    }


class UserResponseSchema(BaseModel):
    """
    用户信息响应模型
    """
    id: int
    username: str
    full_name: str
    email: str
    phone: Optional[str]
    user_type: str
    status: str
    department: Optional[str]
    position: Optional[str]
    supplier_id: Optional[int]
    supplier_name: Optional[str] = None
    avatar_image_path: Optional[str]
    signature_image_path: Optional[str] = None
    digital_signature: Optional[str] = None
    allowed_environments: Optional[str]
    is_platform_admin: bool = False
    role_tags: list[RoleTagSummarySchema] = Field(default_factory=list)
    last_login_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    model_config = {
        "from_attributes": True
    }


class SupplierSearchResponseSchema(BaseModel):
    """
    供应商搜索结果响应模型
    """
    id: int
    name: str
    code: str
    status: str
    
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": 1,
                    "name": "深圳市某某电子有限公司",
                    "code": "SUP001",
                    "status": "active"
                }
            ]
        }
    }


class RegisterResponseSchema(BaseModel):
    """
    注册成功响应模型
    """
    message: str
    user_id: int
    username: str
    status: str
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "message": "注册成功，请等待管理员审核",
                    "user_id": 1,
                    "username": "zhang_san",
                    "status": "pending"
                }
            ]
        }
    }



class LoginRequestSchema(BaseModel):
    """
    登录请求模型
    """
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=1, description="密码")
    user_type: str = Field(..., description="用户类型: internal 或 supplier")
    captcha: Optional[str] = Field(None, description="图形验证码（供应商登录必填）")
    captcha_id: Optional[str] = Field(None, description="验证码ID（供应商登录必填）")
    environment: Optional[str] = Field("stable", description="登录目标环境：stable（正式版）或 preview（预览版）")
    
    @field_validator('user_type')
    @classmethod
    def validate_user_type(cls, v: str) -> str:
        """验证用户类型"""
        if v not in ['internal', 'supplier']:
            raise ValueError('用户类型必须是 internal 或 supplier')
        return v
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "username": "zhang_san",
                    "password": "SecurePass123!",
                    "user_type": "internal"
                },
                {
                    "username": "supplier_user",
                    "password": "SupplierPass456!",
                    "user_type": "supplier",
                    "captcha": "ABCD",
                    "captcha_id": "550e8400-e29b-41d4-a716-446655440000"
                }
            ]
        }
    }


class LoginResponseSchema(BaseModel):
    """
    登录成功响应模型
    """
    access_token: str
    token_type: str = "bearer"
    user_info: UserResponseSchema
    environment: str = "stable"
    allowed_environments: list[str] = Field(default_factory=list, description="当前用户可访问的环境列表")
    password_expired: bool = Field(default=False, description="密码是否过期（需要强制修改）")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "bearer",
                    "password_expired": False,
                    "user_info": {
                        "id": 1,
                        "username": "zhang_san",
                        "full_name": "张三",
                        "email": "zhangsan@company.com",
                        "user_type": "internal",
                        "status": "active"
                    }
                }
            ]
        }
    }


class CaptchaResponseSchema(BaseModel):
    """
    验证码响应模型
    """
    captcha_id: str = Field(..., description="验证码ID（用于验证时关联）")
    captcha_image: str = Field(..., description="Base64编码的验证码图片")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "captcha_id": "550e8400-e29b-41d4-a716-446655440000",
                    "captcha_image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA..."
                }
            ]
        }
    }
