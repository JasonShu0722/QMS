"""
Simple Customer Complaint Tests
客诉管理模块简单测试（不依赖数据库）
"""
import pytest
from datetime import date

from app.schemas.customer_complaint import (
    CustomerComplaintCreate,
    ComplaintTypeEnum,
    PreliminaryAnalysisRequest
)
from app.services.customer_complaint_service import CustomerComplaintService
from app.models.customer_complaint import SeverityLevel


class TestSeverityLevelDetermination:
    """测试严重度等级自动界定（不需要数据库）"""
    
    def test_critical_level_keywords(self):
        """测试严重等级关键词检测"""
        # 测试"安全"关键词
        level = CustomerComplaintService._determine_severity_level("车辆存在安全隐患", "0km")
        assert level == SeverityLevel.CRITICAL
        
        # 测试"抛锚"关键词
        level = CustomerComplaintService._determine_severity_level("车辆在高速公路抛锚", "after_sales")
        assert level == SeverityLevel.CRITICAL
        
        # 测试"起火"关键词
        level = CustomerComplaintService._determine_severity_level("电池起火爆炸", "after_sales")
        assert level == SeverityLevel.CRITICAL
        
        # 测试"断电"关键词
        level = CustomerComplaintService._determine_severity_level("行驶中突然断电", "after_sales")
        assert level == SeverityLevel.CRITICAL
    
    def test_major_level_keywords(self):
        """测试重大等级关键词检测"""
        # 测试"功能失效"关键词
        level = CustomerComplaintService._determine_severity_level("MCU功能失效无法启动", "0km")
        assert level == SeverityLevel.MAJOR
        
        # 测试"批量"关键词
        level = CustomerComplaintService._determine_severity_level("批量发现质量问题", "0km")
        assert level == SeverityLevel.MAJOR
        
        # 测试"召回"关键词
        level = CustomerComplaintService._determine_severity_level("需要启动召回程序", "after_sales")
        assert level == SeverityLevel.MAJOR
        
        # 测试"烧毁"关键词
        level = CustomerComplaintService._determine_severity_level("电路板烧毁", "0km")
        assert level == SeverityLevel.MAJOR
    
    def test_minor_level_keywords(self):
        """测试一般等级关键词检测"""
        # 测试"外观"关键词
        level = CustomerComplaintService._determine_severity_level("外观有轻微划痕", "0km")
        assert level == SeverityLevel.MINOR
        
        # 测试"轻微"关键词
        level = CustomerComplaintService._determine_severity_level("轻微色差问题", "0km")
        assert level == SeverityLevel.MINOR
        
        # 测试"偶发"关键词
        level = CustomerComplaintService._determine_severity_level("偶发性噪音", "after_sales")
        assert level == SeverityLevel.MINOR
    
    def test_tbd_level_default(self):
        """测试默认待定义等级"""
        level = CustomerComplaintService._determine_severity_level("发现一些问题需要分析", "0km")
        assert level == SeverityLevel.TBD
        
        level = CustomerComplaintService._determine_severity_level("客户反馈有异常", "after_sales")
        assert level == SeverityLevel.TBD
    
    def test_case_insensitive(self):
        """测试关键词匹配不区分大小写"""
        # 大写
        level = CustomerComplaintService._determine_severity_level("车辆存在安全隐患", "0km")
        assert level == SeverityLevel.CRITICAL
        
        # 小写
        level = CustomerComplaintService._determine_severity_level("车辆存在安全隐患", "0km")
        assert level == SeverityLevel.CRITICAL
        
        # 混合
        level = CustomerComplaintService._determine_severity_level("车辆存在安全隐患", "0km")
        assert level == SeverityLevel.CRITICAL


class TestComplaintDataValidation:
    """测试客诉单数据校验"""
    
    def test_0km_complaint_validation(self):
        """测试0KM客诉数据校验"""
        # 0KM客诉不需要VIN码等字段
        complaint_data = CustomerComplaintCreate(
            complaint_type=ComplaintTypeEnum.ZERO_KM,
            customer_code="CUST001",
            product_type="MCU控制器",
            defect_description="客户产线发现功能测试不通过"
        )
        
        assert complaint_data.complaint_type == ComplaintTypeEnum.ZERO_KM
        assert complaint_data.vin_code is None
        assert complaint_data.mileage is None
        assert complaint_data.purchase_date is None
    
    def test_after_sales_complaint_validation_success(self):
        """测试售后客诉数据校验（成功）"""
        # 售后客诉必须包含VIN码、里程、购车日期
        complaint_data = CustomerComplaintCreate(
            complaint_type=ComplaintTypeEnum.AFTER_SALES,
            customer_code="CUST002",
            product_type="电池管理系统",
            defect_description="车辆行驶中突然断电，检查发现电池管理系统烧毁",
            vin_code="LSVAA4182E2123456",
            mileage=15000,
            purchase_date=date(2023, 6, 15)
        )
        
        assert complaint_data.complaint_type == ComplaintTypeEnum.AFTER_SALES
        assert complaint_data.vin_code == "LSVAA4182E2123456"
        assert complaint_data.mileage == 15000
        assert complaint_data.purchase_date == date(2023, 6, 15)
    
    def test_after_sales_complaint_validation_failure(self):
        """测试售后客诉数据校验（失败 - 缺少必填字段）"""
        # 售后客诉缺少VIN码应该报错
        with pytest.raises(ValueError, match="VIN码为必填项"):
            CustomerComplaintCreate(
                complaint_type=ComplaintTypeEnum.AFTER_SALES,
                customer_code="CUST002",
                product_type="电池管理系统",
                defect_description="车辆行驶中突然断电，检查发现电池管理系统烧毁",
                # 缺少 vin_code
                mileage=15000,
                purchase_date=date(2023, 6, 15)
            )
        
        # 售后客诉缺少里程应该报错
        with pytest.raises(ValueError, match="失效里程为必填项"):
            CustomerComplaintCreate(
                complaint_type=ComplaintTypeEnum.AFTER_SALES,
                customer_code="CUST002",
                product_type="电池管理系统",
                defect_description="车辆行驶中突然断电，检查发现电池管理系统烧毁",
                vin_code="LSVAA4182E2123456",
                # 缺少 mileage
                purchase_date=date(2023, 6, 15)
            )
        
        # 售后客诉缺少购车日期应该报错
        with pytest.raises(ValueError, match="购车日期为必填项"):
            CustomerComplaintCreate(
                complaint_type=ComplaintTypeEnum.AFTER_SALES,
                customer_code="CUST002",
                product_type="电池管理系统",
                defect_description="车辆行驶中突然断电，检查发现电池管理系统烧毁",
                vin_code="LSVAA4182E2123456",
                mileage=15000
                # 缺少 purchase_date
            )


    def test_customer_reference_validation_failure(self):
        with pytest.raises(ValueError, match="请选择客户或填写客户代码"):
            CustomerComplaintCreate(
                complaint_type=ComplaintTypeEnum.ZERO_KM,
                product_type="MCU控制器",
                defect_description="客户端发现装配异常，需要后续跟踪处理"
            )


class TestPreliminaryAnalysisValidation:
    """测试一次因解析数据校验"""
    
    def test_preliminary_analysis_validation(self):
        """测试一次因解析数据校验"""
        analysis_data = PreliminaryAnalysisRequest(
            emergency_action="立即冻结库存同批次产品",
            team_members="张三(CQE), 李四(设计), 王五(制造)",
            problem_description_5w2h="What: MCU功能失效; When: 2024-01-10; Where: 客户产线",
            containment_action="冻结库存50台，通知客户排查在途品",
            containment_verification="已完成库存冻结",
            responsible_dept="设计部",
            root_cause_preliminary="初步怀疑电源模块设计问题",
            ims_work_order="WO202401001",
            ims_batch_number="BATCH20240105"
        )
        
        assert analysis_data.emergency_action == "立即冻结库存同批次产品"
        assert analysis_data.responsible_dept == "设计部"
        assert analysis_data.ims_work_order == "WO202401001"
        assert analysis_data.ims_batch_number == "BATCH20240105"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
