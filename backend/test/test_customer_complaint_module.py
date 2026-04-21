"""
Customer Complaint Module Tests
客诉管理模块测试
"""
import pytest
from datetime import date, datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customer_complaint import CustomerComplaint, ComplaintType, ComplaintStatus, SeverityLevel
from app.models.customer_master import CustomerMaster, CustomerStatus
from app.models.user import User, UserStatus, UserType
from app.schemas.customer_complaint import (
    CustomerComplaintCreate,
    PreliminaryAnalysisRequest,
    ComplaintTypeEnum,
    IMSTracebackRequest
)
from app.services.customer_complaint_service import CustomerComplaintService


@pytest.fixture
async def test_user(db_session: AsyncSession):
    """创建测试用户（CQE）"""
    user = User(
        username="test_cqe",
        password_hash="hashed_password",
        full_name="测试CQE",
        email="cqe@test.com",
        user_type=UserType.INTERNAL,
        department="质量部",
        position="CQE工程师",
        status=UserStatus.ACTIVE
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def customer_master(db_session: AsyncSession):
    customer = CustomerMaster(
        code="CUSTM001",
        name="BYD Auto",
        status=CustomerStatus.ACTIVE,
    )
    db_session.add(customer)
    await db_session.commit()
    await db_session.refresh(customer)
    return customer


@pytest.mark.asyncio
class TestCustomerComplaintCreation:
    """测试客诉单创建功能"""
    
    async def test_create_0km_complaint(self, db_session: AsyncSession, test_user: User):
        """测试创建0KM客诉单"""
        complaint_data = CustomerComplaintCreate(
            complaint_type=ComplaintTypeEnum.ZERO_KM,
            customer_code="CUST001",
            product_type="MCU控制器",
            defect_description="客户产线发现MCU功能测试不通过，无法正常启动"
        )
        
        complaint = await CustomerComplaintService.create_complaint(
            db=db_session,
            complaint_data=complaint_data,
            created_by_id=test_user.id
        )
        
        assert complaint.id is not None
        assert complaint.complaint_number.startswith("CC-")
        assert complaint.complaint_type == ComplaintType.ZERO_KM
        assert complaint.customer_code == "CUST001"
        assert complaint.status == ComplaintStatus.PENDING
        assert complaint.created_by == test_user.id
        
        # 0KM客诉不需要VIN码等字段
        assert complaint.vin_code is None
        assert complaint.mileage is None
        assert complaint.purchase_date is None
    
    async def test_create_after_sales_complaint(self, db_session: AsyncSession, test_user: User):
        """测试创建售后客诉单"""
        complaint_data = CustomerComplaintCreate(
            complaint_type=ComplaintTypeEnum.AFTER_SALES,
            customer_code="CUST002",
            product_type="电池管理系统",
            defect_description="车辆行驶中突然断电，检查发现电池管理系统烧毁",
            vin_code="LSVAA4182E2123456",
            mileage=15000,
            purchase_date=date(2023, 6, 15)
        )
        
        complaint = await CustomerComplaintService.create_complaint(
            db=db_session,
            complaint_data=complaint_data,
            created_by_id=test_user.id
        )
        
        assert complaint.id is not None
        assert complaint.complaint_type == ComplaintType.AFTER_SALES
        assert complaint.vin_code == "LSVAA4182E2123456"
        assert complaint.mileage == 15000
        assert complaint.purchase_date == date(2023, 6, 15)

    async def test_create_complaint_with_customer_master(
        self,
        db_session: AsyncSession,
        test_user: User,
        customer_master: CustomerMaster,
    ):
        complaint_data = CustomerComplaintCreate(
            complaint_type=ComplaintTypeEnum.ZERO_KM,
            customer_id=customer_master.id,
            product_type="MCU控制器",
            defect_description="客户产线发现批量功能异常，需进一步分析处理",
            end_customer_name="终端项目A",
            is_return_required=True,
            requires_physical_analysis=True,
        )

        complaint = await CustomerComplaintService.create_complaint(
            db=db_session,
            complaint_data=complaint_data,
            created_by_id=test_user.id,
        )

        assert complaint.customer_id == customer_master.id
        assert complaint.customer_code == customer_master.code
        assert complaint.customer_name_snapshot == customer_master.name
        assert complaint.end_customer_name == "终端项目A"
        assert complaint.is_return_required is True
        assert complaint.requires_physical_analysis is True
    
    async def test_complaint_number_generation(self, db_session: AsyncSession, test_user: User):
        """测试客诉单号生成逻辑（同一天多个单据）"""
        # 创建第一个客诉单
        complaint_data_1 = CustomerComplaintCreate(
            complaint_type=ComplaintTypeEnum.ZERO_KM,
            customer_code="CUST001",
            product_type="产品A",
            defect_description="测试缺陷描述001，需要进一步确认"
        )
        complaint_1 = await CustomerComplaintService.create_complaint(
            db=db_session,
            complaint_data=complaint_data_1,
            created_by_id=test_user.id
        )
        
        # 创建第二个客诉单
        complaint_data_2 = CustomerComplaintCreate(
            complaint_type=ComplaintTypeEnum.ZERO_KM,
            customer_code="CUST002",
            product_type="产品B",
            defect_description="测试缺陷描述002，需要进一步确认"
        )
        complaint_2 = await CustomerComplaintService.create_complaint(
            db=db_session,
            complaint_data=complaint_data_2,
            created_by_id=test_user.id
        )
        
        # 验证单号递增
        assert complaint_1.complaint_number != complaint_2.complaint_number
        
        # 提取序号
        seq_1 = int(complaint_1.complaint_number.split("-")[-1])
        seq_2 = int(complaint_2.complaint_number.split("-")[-1])
        assert seq_2 == seq_1 + 1


@pytest.mark.asyncio
class TestSeverityLevelDetermination:
    """测试严重度等级自动界定"""
    
    async def test_critical_level_detection(self, db_session: AsyncSession, test_user: User):
        """测试严重等级检测（涉及安全关键词）"""
        complaint_data = CustomerComplaintCreate(
            complaint_type=ComplaintTypeEnum.AFTER_SALES,
            customer_code="CUST001",
            product_type="制动系统",
            defect_description="车辆高速行驶时刹车失效，差点造成人身伤害",
            vin_code="VIN123",
            mileage=5000,
            purchase_date=date(2023, 1, 1)
        )
        
        complaint = await CustomerComplaintService.create_complaint(
            db=db_session,
            complaint_data=complaint_data,
            created_by_id=test_user.id
        )
        
        assert complaint.severity_level == SeverityLevel.CRITICAL
    
    async def test_major_level_detection(self, db_session: AsyncSession, test_user: User):
        """测试重大等级检测（涉及功能失效关键词）"""
        complaint_data = CustomerComplaintCreate(
            complaint_type=ComplaintTypeEnum.ZERO_KM,
            customer_code="CUST002",
            product_type="MCU控制器",
            defect_description="批量发现MCU功能失效，无法正常使用"
        )
        
        complaint = await CustomerComplaintService.create_complaint(
            db=db_session,
            complaint_data=complaint_data,
            created_by_id=test_user.id
        )
        
        assert complaint.severity_level == SeverityLevel.MAJOR
    
    async def test_minor_level_detection(self, db_session: AsyncSession, test_user: User):
        """测试一般等级检测（涉及外观关键词）"""
        complaint_data = CustomerComplaintCreate(
            complaint_type=ComplaintTypeEnum.ZERO_KM,
            customer_code="CUST003",
            product_type="外壳",
            defect_description="外观轻微划痕，不影响功能"
        )
        
        complaint = await CustomerComplaintService.create_complaint(
            db=db_session,
            complaint_data=complaint_data,
            created_by_id=test_user.id
        )
        
        assert complaint.severity_level == SeverityLevel.MINOR
    
    async def test_tbd_level_default(self, db_session: AsyncSession, test_user: User):
        """测试默认待定义等级"""
        complaint_data = CustomerComplaintCreate(
            complaint_type=ComplaintTypeEnum.ZERO_KM,
            customer_code="CUST004",
            product_type="产品X",
            defect_description="发现一些问题需要进一步分析"
        )
        
        complaint = await CustomerComplaintService.create_complaint(
            db=db_session,
            complaint_data=complaint_data,
            created_by_id=test_user.id
        )
        
        assert complaint.severity_level == SeverityLevel.TBD


@pytest.mark.asyncio
class TestPreliminaryAnalysis:
    """测试CQE一次因解析（D0-D3）"""
    
    async def test_submit_preliminary_analysis(self, db_session: AsyncSession, test_user: User):
        """测试提交一次因解析"""
        # 先创建客诉单
        complaint_data = CustomerComplaintCreate(
            complaint_type=ComplaintTypeEnum.ZERO_KM,
            customer_code="CUST001",
            product_type="MCU控制器",
            defect_description="客户端功能测试不通过，需要一次因分析"
        )
        complaint = await CustomerComplaintService.create_complaint(
            db=db_session,
            complaint_data=complaint_data,
            created_by_id=test_user.id
        )
        
        # 提交一次因解析
        analysis_data = PreliminaryAnalysisRequest(
            emergency_action="立即冻结库存同批次产品",
            team_members="张三(CQE), 李四(设计), 王五(制造)",
            problem_description_5w2h="What: MCU功能失效; When: 2024-01-10; Where: 客户产线",
            containment_action="冻结库存50台，通知客户排查在途品",
            containment_verification="已完成库存冻结",
            responsible_dept="设计部",
            root_cause_preliminary="初步怀疑电源模块设计问题"
        )
        
        updated_complaint = await CustomerComplaintService.submit_preliminary_analysis(
            db=db_session,
            complaint_id=complaint.id,
            analysis_data=analysis_data,
            cqe_id=test_user.id
        )
        
        assert updated_complaint.status == ComplaintStatus.IN_RESPONSE
        assert updated_complaint.cqe_id == test_user.id
        assert updated_complaint.responsible_dept == "设计部"
    
    async def test_preliminary_analysis_with_ims_traceback(self, db_session: AsyncSession, test_user: User):
        """测试带IMS追溯的一次因解析"""
        # 创建客诉单
        complaint_data = CustomerComplaintCreate(
            complaint_type=ComplaintTypeEnum.ZERO_KM,
            customer_code="CUST001",
            product_type="产品A",
            defect_description="客户端批量不良，需要结合IMS追溯"
        )
        complaint = await CustomerComplaintService.create_complaint(
            db=db_session,
            complaint_data=complaint_data,
            created_by_id=test_user.id
        )
        
        # 提交一次因解析（包含IMS追溯信息）
        analysis_data = PreliminaryAnalysisRequest(
            emergency_action="立即冻结相关库存并通知现场隔离",
            team_members="团队成员A, 团队成员B",
            problem_description_5w2h="What: 批量不良; When: 今日; Where: 客户线体; Who: 客户检验; How Many: 多台",
            containment_action="立即围堵库存并追溯在制与在途产品",
            containment_verification="验证结果",
            responsible_dept="制造部",
            ims_work_order="WO202401001",
            ims_batch_number="BATCH20240105"
        )
        
        updated_complaint = await CustomerComplaintService.submit_preliminary_analysis(
            db=db_session,
            complaint_id=complaint.id,
            analysis_data=analysis_data,
            cqe_id=test_user.id
        )
        
        assert updated_complaint.status == ComplaintStatus.IN_RESPONSE
        # IMS追溯应该在后台执行（当前为模拟实现）


@pytest.mark.asyncio
class TestIMSTraceback:
    """测试IMS自动追溯功能"""
    
    async def test_ims_traceback_with_work_order(self, db_session: AsyncSession):
        """测试通过工单号追溯"""
        result = await CustomerComplaintService.auto_traceback_ims(
            db=db_session,
            work_order="WO202401001"
        )
        
        assert result.found is True
        assert result.work_order == "WO202401001"
        assert len(result.process_records) > 0
    
    async def test_ims_traceback_with_batch_number(self, db_session: AsyncSession):
        """测试通过批次号追溯（检测到异常）"""
        result = await CustomerComplaintService.auto_traceback_ims(
            db=db_session,
            batch_number="BATCH20240105"
        )
        
        assert result.found is True
        assert result.batch_number == "BATCH20240105"
        assert result.anomaly_detected is True
        assert result.anomaly_description is not None
        assert len(result.defect_records) > 0
    
    async def test_ims_traceback_no_data(self, db_session: AsyncSession):
        """测试追溯无数据的情况"""
        result = await CustomerComplaintService.auto_traceback_ims(
            db=db_session
        )
        
        assert result.found is False
        assert result.anomaly_detected is False


@pytest.mark.asyncio
class TestComplaintQuery:
    """测试客诉单查询功能"""
    
    async def test_list_complaints_with_filters(self, db_session: AsyncSession, test_user: User):
        """测试带筛选条件的客诉单列表查询"""
        # 创建多个客诉单
        for i in range(3):
            complaint_data = CustomerComplaintCreate(
                complaint_type=ComplaintTypeEnum.ZERO_KM,
                customer_code=f"CUST00{i+1}",
                product_type="产品A",
                defect_description=f"测试缺陷{i+1}，用于列表筛选验证"
            )
            await CustomerComplaintService.create_complaint(
                db=db_session,
                complaint_data=complaint_data,
                created_by_id=test_user.id
            )
        
        # 查询所有客诉单
        complaints, total = await CustomerComplaintService.list_complaints(
            db=db_session,
            page=1,
            page_size=10
        )
        
        assert total >= 3
        assert len(complaints) >= 3
    
    async def test_list_complaints_by_type(self, db_session: AsyncSession, test_user: User):
        """测试按类型筛选客诉单"""
        # 创建0KM客诉
        complaint_data_0km = CustomerComplaintCreate(
            complaint_type=ComplaintTypeEnum.ZERO_KM,
            customer_code="CUST001",
            product_type="产品A",
            defect_description="0KM批量缺陷，需要按类型过滤"
        )
        await CustomerComplaintService.create_complaint(
            db=db_session,
            complaint_data=complaint_data_0km,
            created_by_id=test_user.id
        )
        
        # 创建售后客诉
        complaint_data_after_sales = CustomerComplaintCreate(
            complaint_type=ComplaintTypeEnum.AFTER_SALES,
            customer_code="CUST002",
            product_type="产品B",
            defect_description="售后市场缺陷，需要按类型过滤",
            vin_code="VIN123",
            mileage=10000,
            purchase_date=date(2023, 1, 1)
        )
        await CustomerComplaintService.create_complaint(
            db=db_session,
            complaint_data=complaint_data_after_sales,
            created_by_id=test_user.id
        )
        
        # 筛选0KM客诉
        complaints_0km, total_0km = await CustomerComplaintService.list_complaints(
            db=db_session,
            complaint_type="0km",
            page=1,
            page_size=10
        )
        
        assert total_0km >= 1
        assert all(c.complaint_type == ComplaintType.ZERO_KM for c in complaints_0km)
    
    async def test_get_complaint_by_id(self, db_session: AsyncSession, test_user: User):
        """测试根据ID查询客诉单"""
        # 创建客诉单
        complaint_data = CustomerComplaintCreate(
            complaint_type=ComplaintTypeEnum.ZERO_KM,
            customer_code="CUST001",
            product_type="产品A",
            defect_description="测试缺陷内容，用于详情查询"
        )
        created_complaint = await CustomerComplaintService.create_complaint(
            db=db_session,
            complaint_data=complaint_data,
            created_by_id=test_user.id
        )
        
        # 查询客诉单
        found_complaint = await CustomerComplaintService.get_complaint_by_id(
            db=db_session,
            complaint_id=created_complaint.id
        )
        
        assert found_complaint is not None
        assert found_complaint.id == created_complaint.id
        assert found_complaint.complaint_number == created_complaint.complaint_number

    async def test_list_complaints_by_customer_id(
        self,
        db_session: AsyncSession,
        test_user: User,
        customer_master: CustomerMaster,
    ):
        complaint_data = CustomerComplaintCreate(
            complaint_type=ComplaintTypeEnum.ZERO_KM,
            customer_id=customer_master.id,
            product_type="产品A",
            defect_description="客户端发现装配不良，需要区分责任和处理方式",
        )
        await CustomerComplaintService.create_complaint(
            db=db_session,
            complaint_data=complaint_data,
            created_by_id=test_user.id,
        )

        complaints, total = await CustomerComplaintService.list_complaints(
            db=db_session,
            customer_id=customer_master.id,
            page=1,
            page_size=10,
        )

        assert total >= 1
        assert all(item.customer_id == customer_master.id for item in complaints)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
