"""
任务聚合服务模块
Task Aggregator Service - 从各业务表聚合待办任务
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text


class TaskItem:
    """
    待办任务项数据模型
    """
    def __init__(
        self,
        task_type: str,
        task_id: int,
        task_number: str,
        deadline: datetime,
        urgency: str,
        color: str,
        remaining_hours: float,
        link: str,
        description: Optional[str] = None
    ):
        self.task_type = task_type
        self.task_id = task_id
        self.task_number = task_number
        self.deadline = deadline
        self.urgency = urgency
        self.color = color
        self.remaining_hours = remaining_hours
        self.link = link
        self.description = description
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "task_type": self.task_type,
            "task_id": self.task_id,
            "task_number": self.task_number,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "urgency": self.urgency,
            "color": self.color,
            "remaining_hours": round(self.remaining_hours, 2),
            "link": self.link,
            "description": self.description
        }


class TaskAggregator:
    """
    任务聚合器
    
    功能：
    - 从各业务表聚合待办任务
    - 计算任务紧急程度
    - 计算剩余处理时间
    """
    
    # 业务表配置：定义哪些表需要聚合待办任务
    # 注：Phase 1 阶段，这些业务表尚未创建，此处为预留配置
    BUSINESS_TABLES = [
        {
            "table": "scar_reports",
            "handler_field": "current_handler_id",
            "task_type": "SCAR报告处理",
            "deadline_field": "deadline",
            "number_field": "report_number",
            "link_pattern": "/supplier/scar/{id}",
            "description_field": "problem_description",
            "enabled": False  # Phase 1 暂不启用
        },
        {
            "table": "ppap_submissions",
            "handler_field": "reviewer_id",
            "task_type": "PPAP审批",
            "deadline_field": "review_deadline",
            "number_field": "submission_number",
            "link_pattern": "/supplier/ppap/{id}",
            "description_field": "material_name",
            "enabled": False  # Phase 1 暂不启用
        },
        {
            "table": "audit_nc_items",
            "handler_field": "responsible_user_id",
            "task_type": "审核整改项",
            "deadline_field": "correction_deadline",
            "number_field": "nc_number",
            "link_pattern": "/audit/nc/{id}",
            "description_field": "nc_description",
            "enabled": False  # Phase 1 暂不启用
        },
        {
            "table": "customer_complaints",
            "handler_field": "current_handler_id",
            "task_type": "客诉8D报告",
            "deadline_field": "response_deadline",
            "number_field": "complaint_number",
            "link_pattern": "/customer/complaint/{id}",
            "description_field": "problem_summary",
            "enabled": False  # Phase 1 暂不启用
        },
        {
            "table": "supplier_change_requests",
            "handler_field": "reviewer_id",
            "task_type": "供应商变更审批",
            "deadline_field": "review_deadline",
            "number_field": "change_number",
            "link_pattern": "/supplier/change/{id}",
            "description_field": "change_description",
            "enabled": False  # Phase 1 暂不启用
        }
    ]
    
    @staticmethod
    def _calculate_remaining(deadline: datetime) -> float:
        """
        计算剩余处理时间（小时数）
        
        Args:
            deadline: 截止时间
            
        Returns:
            float: 剩余小时数（负数表示已超期）
        """
        if deadline is None:
            return float('inf')  # 无截止时间，返回无穷大
        
        now = datetime.utcnow()
        delta = deadline - now
        return delta.total_seconds() / 3600  # 转换为小时
    
    @staticmethod
    def _calculate_urgency(deadline: datetime) -> tuple[str, str]:
        """
        计算任务紧急程度
        
        Args:
            deadline: 截止时间
            
        Returns:
            tuple[str, str]: (紧急程度, 颜色标识)
                - overdue/red: 已超期
                - urgent/yellow: 即将超期（≤72小时）
                - normal/green: 正常（>72小时）
        """
        remaining_hours = TaskAggregator._calculate_remaining(deadline)
        
        if remaining_hours < 0:
            return ("overdue", "red")
        elif remaining_hours <= 72:
            return ("urgent", "yellow")
        else:
            return ("normal", "green")
    
    @staticmethod
    async def get_user_tasks(
        db: AsyncSession,
        user_id: int
    ) -> List[TaskItem]:
        """
        获取用户所有待办任务
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            
        Returns:
            List[TaskItem]: 待办任务列表（按紧急程度排序）
        """
        tasks: List[TaskItem] = []
        
        # 遍历所有业务表配置
        for config in TaskAggregator.BUSINESS_TABLES:
            # 跳过未启用的表
            if not config.get("enabled", False):
                continue
            
            try:
                # 动态构建查询 SQL
                # 注：使用参数化查询防止 SQL 注入
                query = text(f"""
                    SELECT 
                        id,
                        {config['number_field']} as task_number,
                        {config['deadline_field']} as deadline,
                        {config.get('description_field', 'NULL')} as description
                    FROM {config['table']}
                    WHERE {config['handler_field']} = :user_id
                    AND status NOT IN ('closed', 'completed', 'cancelled')
                    ORDER BY {config['deadline_field']} ASC
                """)
                
                result = await db.execute(query, {"user_id": user_id})
                rows = result.fetchall()
                
                # 处理查询结果
                for row in rows:
                    task_id = row.id
                    task_number = row.task_number
                    deadline = row.deadline
                    description = row.description if hasattr(row, 'description') else None
                    
                    # 计算紧急程度和剩余时间
                    remaining_hours = TaskAggregator._calculate_remaining(deadline)
                    urgency, color = TaskAggregator._calculate_urgency(deadline)
                    
                    # 生成跳转链接
                    link = config['link_pattern'].format(id=task_id)
                    
                    # 创建任务项
                    task_item = TaskItem(
                        task_type=config['task_type'],
                        task_id=task_id,
                        task_number=task_number,
                        deadline=deadline,
                        urgency=urgency,
                        color=color,
                        remaining_hours=remaining_hours,
                        link=link,
                        description=description
                    )
                    
                    tasks.append(task_item)
                    
            except Exception as e:
                # 记录错误但不中断整个聚合流程
                # 某个业务表查询失败不应影响其他表的任务聚合
                print(f"警告：从表 {config['table']} 聚合任务失败: {str(e)}")
                continue
        
        # 按剩余时间排序（最紧急的在前）
        tasks.sort(key=lambda x: x.remaining_hours)
        
        return tasks
    
    @staticmethod
    async def get_task_statistics(
        db: AsyncSession,
        user_id: int
    ) -> Dict[str, Any]:
        """
        获取用户任务统计信息
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            
        Returns:
            Dict[str, Any]: 统计信息
                - total: 总任务数
                - overdue: 已超期任务数
                - urgent: 紧急任务数
                - normal: 正常任务数
        """
        tasks = await TaskAggregator.get_user_tasks(db, user_id)
        
        total = len(tasks)
        overdue = sum(1 for task in tasks if task.urgency == "overdue")
        urgent = sum(1 for task in tasks if task.urgency == "urgent")
        normal = sum(1 for task in tasks if task.urgency == "normal")
        
        return {
            "total": total,
            "overdue": overdue,
            "urgent": urgent,
            "normal": normal
        }


# 创建全局任务聚合器实例
task_aggregator = TaskAggregator()

