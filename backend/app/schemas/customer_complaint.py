"""
Customer Complaint Schemas
客诉单数据校验模型
"""
from pydantic import BaseModel, Field, model_validator
from typing import Optional
from datetime import date, datetime
from enum import Enum


class ComplaintTypeEnum(str, Enum):
    """客诉类型枚举"""
    ZERO_KM = "0km"
    AFTER_SALES = "after_sales"


class ComplaintStatusEnum(str, Enum):
    """客诉状态枚举"""
    PENDING = "pending"
    IN_ANALYSIS = "in_analysis"
    IN_RESPONSE = "in_response"
    IN_REVIEW = "in_review"
    CLOSED = "closed"
    REJECTED = "rejected"


class SeverityLevelEnum(str, Enum):
    """严重度等级枚举"""
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"
    TBD = "tbd"


class CustomerComplaintCreate(BaseModel):
    """创建客诉单请求模型"""
    complaint_type: ComplaintTypeEnum = Field(..., description="客诉类型：0km/售后")
    customer_id: Optional[int] = Field(None, ge=1, description="客户主数据 ID")
    customer_code: Optional[str] = Field(None, min_length=1, max_length=50, description="客户代码（兼容旧数据）")
    customer_name: Optional[str] = Field(None, min_length=1, max_length=200, description="客户名称（兼容旧数据）")
    end_customer_name: Optional[str] = Field(None, max_length=200, description="终端客户名称")
    product_type: str = Field(..., min_length=1, max_length=100, description="产品类型")
    defect_description: str = Field(..., min_length=10, description="缺陷描述（至少10字）")
    is_return_required: bool = Field(False, description="是否涉及退件")
    requires_physical_analysis: bool = Field(False, description="是否需要实物解析")
    
    # 售后客诉特有字段
    vin_code: Optional[str] = Field(None, max_length=50, description="VIN码（售后客诉必填）")
    mileage: Optional[int] = Field(None, ge=0, description="失效里程（售后客诉必填）")
    purchase_date: Optional[date] = Field(None, description="购车日期（售后客诉必填）")
    
    @model_validator(mode='after')
    def validate_after_sales_fields(self) -> 'CustomerComplaintCreate':
        """售后客诉时，VIN码、里程、购车日期必填"""
        if self.customer_id is None and not self.customer_code:
            raise ValueError("请选择客户或填写客户代码")
        if self.complaint_type == ComplaintTypeEnum.AFTER_SALES:
            if not self.vin_code:
                raise ValueError("售后客诉时，VIN码为必填项")
            if self.mileage is None:
                raise ValueError("售后客诉时，失效里程为必填项")
            if not self.purchase_date:
                raise ValueError("售后客诉时，购车日期为必填项")
        return self
    
    class Config:
        json_schema_extra = {
            "example": {
                "complaint_type": "after_sales",
                "customer_id": 1,
                "product_type": "MCU控制器",
                "defect_description": "客户反馈车辆行驶中突然断电，检查发现MCU主板烧毁",
                "end_customer_name": "比亚迪终端项目",
                "is_return_required": True,
                "requires_physical_analysis": True,
                "vin_code": "LSVAA4182E2123456",
                "mileage": 15000,
                "purchase_date": "2023-06-15"
            }
        }


class PreliminaryAnalysisRequest(BaseModel):
    """CQE一次因解析请求模型（D0-D3）"""
    # D0: 紧急响应行动
    emergency_action: str = Field(..., min_length=10, description="紧急响应措施（围堵措施）")
    
    # D1: 团队组建
    team_members: str = Field(..., description="团队成员（逗号分隔）")
    
    # D2: 问题描述（5W2H）
    problem_description_5w2h: str = Field(..., min_length=20, description="问题描述（5W2H格式）")
    
    # D3: 临时围堵措施
    containment_action: str = Field(..., min_length=10, description="临时围堵措施详情")
    containment_verification: str = Field(..., description="围堵措施验证结果")
    
    # 责任判定
    responsible_dept: str = Field(..., description="责任部门")
    root_cause_preliminary: Optional[str] = Field(None, description="初步原因分析")
    
    # IMS追溯信息（可选）
    ims_work_order: Optional[str] = Field(None, description="关联的IMS工单号")
    ims_batch_number: Optional[str] = Field(None, description="关联的批次号")
    
    class Config:
        json_schema_extra = {
            "example": {
                "emergency_action": "立即通知客户停止使用该批次产品，启动召回程序",
                "team_members": "张三(CQE), 李四(设计), 王五(制造)",
                "problem_description_5w2h": "What: MCU主板烧毁; When: 2024-01-10; Where: 客户产线; Who: 终端用户; Why: 待分析; How: 行驶中突然断电; How Many: 1台",
                "containment_action": "1. 冻结库存同批次产品; 2. 通知客户排查在途品; 3. 启动现场调查",
                "containment_verification": "已完成库存冻结50台，客户端排查在途品20台",
                "responsible_dept": "设计部",
                "root_cause_preliminary": "初步怀疑电源模块设计裕量不足",
                "ims_work_order": "WO202401001",
                "ims_batch_number": "BATCH20240105"
            }
        }


class CustomerComplaintResponse(BaseModel):
    """客诉单响应模型"""
    id: int
    complaint_number: str
    complaint_type: ComplaintTypeEnum
    customer_id: Optional[int]
    customer_code: str
    customer_name: Optional[str]
    end_customer_name: Optional[str]
    product_type: str
    defect_description: str
    severity_level: SeverityLevelEnum
    is_return_required: bool
    requires_physical_analysis: bool
    
    # 售后客诉字段
    vin_code: Optional[str]
    mileage: Optional[int]
    purchase_date: Optional[date]
    
    # 流程控制
    status: ComplaintStatusEnum
    cqe_id: Optional[int]
    responsible_dept: Optional[str]
    
    # 审计字段
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int]
    
    class Config:
        from_attributes = True


class CustomerComplaintListResponse(BaseModel):
    """客诉单列表响应模型"""
    total: int
    items: list[CustomerComplaintResponse]
    page: int
    page_size: int


class CustomerComplaintCustomerOption(BaseModel):
    id: int
    code: str
    name: str

    class Config:
        from_attributes = True


class IMSTracebackRequest(BaseModel):
    """IMS自动追溯请求模型"""
    work_order: Optional[str] = Field(None, description="工单号")
    batch_number: Optional[str] = Field(None, description="批次号")
    material_code: Optional[str] = Field(None, description="物料编码")
    production_date: Optional[date] = Field(None, description="生产日期")
    
    class Config:
        json_schema_extra = {
            "example": {
                "work_order": "WO202401001",
                "batch_number": "BATCH20240105",
                "material_code": "MAT-MCU-001"
            }
        }


class IMSTracebackResponse(BaseModel):
    """IMS追溯结果响应模型"""
    found: bool = Field(..., description="是否找到追溯记录")
    work_order: Optional[str] = None
    batch_number: Optional[str] = None
    production_date: Optional[date] = None
    process_records: list[dict] = Field(default_factory=list, description="过程记录列表")
    defect_records: list[dict] = Field(default_factory=list, description="不良记录列表")
    material_records: list[dict] = Field(default_factory=list, description="物料追溯记录")
    anomaly_detected: bool = Field(False, description="是否检测到异常")
    anomaly_description: Optional[str] = Field(None, description="异常描述")
    
    class Config:
        json_schema_extra = {
            "example": {
                "found": True,
                "work_order": "WO202401001",
                "batch_number": "BATCH20240105",
                "production_date": "2024-01-05",
                "process_records": [
                    {"process": "SMT贴片", "operator": "张三", "result": "OK"},
                    {"process": "波峰焊", "operator": "李四", "result": "OK"}
                ],
                "defect_records": [
                    {"defect_type": "虚焊", "qty": 2, "date": "2024-01-05"}
                ],
                "material_records": [
                    {"material_code": "MAT-001", "supplier": "SUP-A", "batch": "B001"}
                ],
                "anomaly_detected": True,
                "anomaly_description": "该批次在波峰焊工序出现2次虚焊不良"
            }
        }
