"""
任务聚合服务测试
Test Task Aggregator Service
"""
import pytest
from datetime import datetime, timedelta
from app.services.task_aggregator import TaskAggregator, TaskItem


class TestTaskAggregator:
    """任务聚合器测试类"""
    
    def test_calculate_remaining_future_deadline(self):
        """测试计算未来截止时间的剩余小时数"""
        # 设置一个未来的截止时间（48小时后）
        future_deadline = datetime.utcnow() + timedelta(hours=48)
        
        remaining = TaskAggregator._calculate_remaining(future_deadline)
        
        # 剩余时间应该接近48小时（允许几秒的误差）
        assert 47.9 < remaining < 48.1
    
    def test_calculate_remaining_past_deadline(self):
        """测试计算过去截止时间的剩余小时数"""
        # 设置一个过去的截止时间（24小时前）
        past_deadline = datetime.utcnow() - timedelta(hours=24)
        
        remaining = TaskAggregator._calculate_remaining(past_deadline)
        
        # 剩余时间应该是负数，接近-24小时
        assert -24.1 < remaining < -23.9
    
    def test_calculate_remaining_none_deadline(self):
        """测试无截止时间的情况"""
        remaining = TaskAggregator._calculate_remaining(None)
        
        # 无截止时间应该返回无穷大
        assert remaining == float('inf')
    
    def test_calculate_urgency_overdue(self):
        """测试已超期任务的紧急程度"""
        # 设置一个过去的截止时间
        past_deadline = datetime.utcnow() - timedelta(hours=1)
        
        urgency, color = TaskAggregator._calculate_urgency(past_deadline)
        
        assert urgency == "overdue"
        assert color == "red"
    
    def test_calculate_urgency_urgent(self):
        """测试即将超期任务的紧急程度"""
        # 设置一个即将到期的截止时间（48小时后）
        urgent_deadline = datetime.utcnow() + timedelta(hours=48)
        
        urgency, color = TaskAggregator._calculate_urgency(urgent_deadline)
        
        assert urgency == "urgent"
        assert color == "yellow"
    
    def test_calculate_urgency_normal(self):
        """测试正常任务的紧急程度"""
        # 设置一个较远的截止时间（100小时后）
        normal_deadline = datetime.utcnow() + timedelta(hours=100)
        
        urgency, color = TaskAggregator._calculate_urgency(normal_deadline)
        
        assert urgency == "normal"
        assert color == "green"
    
    def test_calculate_urgency_boundary_72_hours(self):
        """测试72小时边界情况"""
        # 设置恰好72小时后的截止时间
        boundary_deadline = datetime.utcnow() + timedelta(hours=72)
        
        urgency, color = TaskAggregator._calculate_urgency(boundary_deadline)
        
        # 72小时应该被判定为urgent
        assert urgency == "urgent"
        assert color == "yellow"
    
    def test_task_item_creation(self):
        """测试任务项创建"""
        deadline = datetime.utcnow() + timedelta(hours=48)
        
        task = TaskItem(
            task_type="SCAR报告处理",
            task_id=123,
            task_number="SCAR-2024-001",
            deadline=deadline,
            urgency="urgent",
            color="yellow",
            remaining_hours=48.0,
            link="/supplier/scar/123",
            description="测试任务"
        )
        
        assert task.task_type == "SCAR报告处理"
        assert task.task_id == 123
        assert task.task_number == "SCAR-2024-001"
        assert task.urgency == "urgent"
        assert task.color == "yellow"
    
    def test_task_item_to_dict(self):
        """测试任务项转换为字典"""
        deadline = datetime.utcnow() + timedelta(hours=48)
        
        task = TaskItem(
            task_type="SCAR报告处理",
            task_id=123,
            task_number="SCAR-2024-001",
            deadline=deadline,
            urgency="urgent",
            color="yellow",
            remaining_hours=48.5,
            link="/supplier/scar/123",
            description="测试任务"
        )
        
        task_dict = task.to_dict()
        
        assert task_dict["task_type"] == "SCAR报告处理"
        assert task_dict["task_id"] == 123
        assert task_dict["task_number"] == "SCAR-2024-001"
        assert task_dict["urgency"] == "urgent"
        assert task_dict["color"] == "yellow"
        assert task_dict["remaining_hours"] == 48.5
        assert task_dict["link"] == "/supplier/scar/123"
        assert task_dict["description"] == "测试任务"
        assert "deadline" in task_dict
    
    @pytest.mark.asyncio
    async def test_get_user_tasks_empty(self, async_db_session):
        """测试获取用户待办任务（空列表）"""
        # Phase 1 阶段，业务表未创建，应该返回空列表
        tasks = await TaskAggregator.get_user_tasks(async_db_session, user_id=1)
        
        assert isinstance(tasks, list)
        assert len(tasks) == 0
    
    @pytest.mark.asyncio
    async def test_get_task_statistics_empty(self, async_db_session):
        """测试获取任务统计信息（空数据）"""
        # Phase 1 阶段，业务表未创建，应该返回全0统计
        statistics = await TaskAggregator.get_task_statistics(async_db_session, user_id=1)
        
        assert statistics["total"] == 0
        assert statistics["overdue"] == 0
        assert statistics["urgent"] == 0
        assert statistics["normal"] == 0

