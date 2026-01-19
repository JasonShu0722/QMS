# Design Document - QMS 质量管理系统

## Overview

本设计文档描述了 QMS 质量管理系统的技术架构、组件设计和实现方案。系统采用现代化的 Monorepo 架构，前后端分离，容器化部署，支持高并发和异步任务处理。

### 核心设计原则

1. **模块化设计**: 各业务模块独立开发，通过统一的权限引擎和任务聚合器协同工作
2. **数据驱动**: 通过 IMS 数据集成实现质量指标的自动计算和实时监控
3. **任务驱动**: 以待办任务为核心，串联各业务流程的闭环管理
4. **AI 增强**: 集成 AI 能力进行异常诊断、报告预审和自然语言查询
5. **安全优先**: 细粒度权限控制、操作日志审计、数据隔离

### 技术栈总览

**后端 (Backend)**:
- 语言: Python 3.10+
- 框架: FastAPI (异步 Web 框架)
- ORM: SQLAlchemy 2.0+ (Async)
- 数据库: PostgreSQL 15+
- 缓存/队列: Redis 7+
- 任务队列: Celery
- 数据校验: Pydantic V2
- 数据库迁移: Alembic

**前端 (Frontend)**:
- 框架: Vue 3 (Composition API)
- 构建工具: Vite
- UI 组件库: Element Plus
- 状态管理: Pinia
- 图表库: ECharts
- HTTP 客户端: Axios

**基础设施 (Infrastructure)**:
- 容器化: Docker + Docker Compose
- 反向代理: Nginx
- 网络: DMZ 部署（双网卡：外网 + 内网）

## Architecture

### 系统拓扑架构

```
┌─────────────────────────────────────────────────────────────┐
│                      外网 (Internet)                         │
│  ┌──────────────┐              ┌──────────────┐            │
│  │ 供应商用户    │              │ 公司领导      │            │
│  └──────────────┘              └──────────────┘            │
└────────────────────┬────────────────────┬───────────────────┘
                     │                    │
                     │   HTTPS (443)      │
                     ▼                    ▼
┌─────────────────────────────────────────────────────────────┐
│                    DMZ 区域 (QMS Server)                     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                  Nginx (反向代理)                      │  │
│  │  - 静态文件服务                                        │  │
│  │  - API 路由转发 (/api -> FastAPI)                    │  │
│  │  - SSL 终止                                           │  │
│  └────────────┬─────────────────────────┬────────────────┘  │
│               │                         │                    │
│               ▼                         ▼                    │
│  ┌─────────────────────┐   ┌──────────────────────────┐    │
│  │  Vue 3 前端容器      │   │  FastAPI 后端容器         │    │
│  │  - Element Plus UI  │   │  - REST API              │    │
│  │  - ECharts 图表     │   │  - 权限引擎               │    │
│  │  - Pinia 状态管理   │   │  - 任务聚合器             │    │
│  └─────────────────────┘   │  - AI 诊断引擎            │    │
│                             └──────────┬────────────────┘    │
│                                        │                     │
│                             ┌──────────▼────────────┐        │
│                             │  Celery Worker 容器   │        │
│                             │  - 定时任务 (IMS 同步) │        │
│                             │  - 异步任务处理        │        │
│                             └──────────┬────────────┘        │
└─────────────────────────────────────────┼───────────────────┘
                                          │
                     ┌────────────────────┼────────────────────┐
                     │                    │                    │
                     ▼                    ▼                    ▼
┌─────────────────────────────────────────────────────────────┐
│                      内网 (Intranet)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ PostgreSQL   │  │    Redis     │  │  IMS 系统     │      │
│  │ (QMS 数据库) │  │ (缓存/队列)   │  │  (数据源)     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```


### 分层架构

系统采用经典的三层架构 + 服务层模式：

```
┌─────────────────────────────────────────────────────────────┐
│                      Presentation Layer                      │
│                         (Vue 3 前端)                          │
│  - 页面组件 (Views)                                           │
│  - 业务组件 (Components)                                      │
│  - 状态管理 (Pinia Stores)                                    │
│  - API 调用封装 (Axios)                                       │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/JSON
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                       API Layer                              │
│                     (FastAPI 路由层)                          │
│  - 路由定义 (app/api/v1/)                                     │
│  - 请求校验 (Pydantic Schemas)                                │
│  - 响应序列化                                                 │
│  - 权限装饰器 (@require_permission)                           │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                     Business Logic Layer                     │
│                       (服务层 Services)                       │
│  - 业务逻辑封装 (app/services/)                               │
│  - IMS 数据集成服务                                           │
│  - 质量指标计算服务                                           │
│  - AI 诊断服务                                                │
│  - 通知服务                                                   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                      Data Access Layer                       │
│                    (数据访问层 Models)                        │
│  - SQLAlchemy ORM 模型 (app/models/)                         │
│  - 数据库会话管理                                             │
│  - 查询构建器                                                 │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                      Database Layer                          │
│                       (PostgreSQL)                           │
└─────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### 1. 认证授权模块 (Auth Module)

**职责**: 用户注册、登录、权限验证、会话管理

**核心组件**:

```python
# backend/app/core/security.py
class SecurityManager:
    """安全管理器"""
    
    def create_access_token(user_id: int) -> str:
        """生成 JWT Token"""
        
    def verify_token(token: str) -> dict:
        """验证 Token 有效性"""
        
    def hash_password(password: str) -> str:
        """密码哈希 (bcrypt)"""
        
    def verify_password(plain: str, hashed: str) -> bool:
        """密码验证"""

# backend/app/api/v1/auth.py
@router.post("/register")
async def register(data: UserRegisterSchema):
    """用户注册接口"""
    
@router.post("/login")
async def login(credentials: LoginSchema):
    """用户登录接口"""
    
@router.get("/me")
async def get_current_user(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
```

**数据流**:
1. 用户提交注册表单 → 前端校验 → 后端创建 User 记录（状态=待审核）
2. 管理员审核 → 更新状态为"已激活" → 发送邮件通知
3. 用户登录 → 验证密码 → 生成 JWT Token → 返回前端
4. 前端存储 Token → 每次请求携带 Token → 后端中间件验证

### 2. 权限引擎 (Permission Engine)

**职责**: 细粒度权限控制、权限矩阵管理、数据隔离

**核心组件**:

```python
# backend/app/core/permissions.py
class PermissionEngine:
    """权限引擎"""
    
    async def check_permission(
        user_id: int,
        module: str,  # 如: "supplier_management"
        operation: str  # 如: "view", "create", "edit", "delete", "export"
    ) -> bool:
        """检查用户是否具有指定权限"""
        
    async def get_user_permissions(user_id: int) -> dict:
        """获取用户的所有权限（用于前端菜单渲染）"""
        
    async def filter_by_supplier(user: User, query):
        """供应商账号数据隔离过滤器"""
        if user.user_type == "supplier":
            return query.filter(Model.supplier_id == user.supplier_id)
        return query

# 权限装饰器
def require_permission(module: str, operation: str):
    """权限检查装饰器"""
    def decorator(func):
        async def wrapper(*args, current_user: User = Depends(get_current_user), **kwargs):
            has_perm = await PermissionEngine.check_permission(
                current_user.id, module, operation
            )
            if not has_perm:
                raise HTTPException(status_code=403, detail="权限不足")
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator

# 使用示例
@router.get("/suppliers")
@require_permission("supplier_management", "view")
async def list_suppliers(current_user: User = Depends(get_current_user)):
    """查询供应商列表（自动应用数据隔离）"""
```

**权限矩阵数据结构**:

```python
# backend/app/models/permission.py
class Permission(Base):
    __tablename__ = "permissions"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    module = Column(String(100))  # 功能模块
    operation = Column(String(20))  # 操作类型
    granted = Column(Boolean, default=False)  # 是否授权
    
    __table_args__ = (
        UniqueConstraint('user_id', 'module', 'operation'),
    )
```


### 3. 任务聚合器 (Task Aggregator)

**职责**: 从各业务模块聚合待办任务、计算剩余时间、任务转派

**核心组件**:

```python
# backend/app/services/task_aggregator.py
class TaskAggregator:
    """任务聚合服务"""
    
    async def get_user_tasks(user_id: int) -> List[TaskItem]:
        """获取用户的所有待办任务"""
        tasks = []
        
        # 从各业务表聚合任务
        # 1. SCAR 单（供应商质量）
        scars = await db.query(SCAR).filter(
            SCAR.current_handler_id == user_id,
            SCAR.status != "closed"
        ).all()
        
        # 2. 8D 报告（客户质量）
        reports_8d = await db.query(Report8D).filter(
            Report8D.current_handler_id == user_id,
            Report8D.status != "archived"
        ).all()
        
        # 3. 审核整改项（审核管理）
        nc_items = await db.query(NCItem).filter(
            NCItem.assignee_id == user_id,
            NCItem.status != "closed"
        ).all()
        
        # ... 其他业务模块
        
        # 统一封装为 TaskItem
        for scar in scars:
            tasks.append(TaskItem(
                task_type="SCAR",
                doc_number=scar.doc_number,
                urgency=self._calculate_urgency(scar.deadline),
                remaining_hours=self._calculate_remaining(scar.deadline),
                link=f"/supplier/scar/{scar.id}"
            ))
        
        return tasks
    
    def _calculate_urgency(self, deadline: datetime) -> str:
        """计算紧急程度"""
        remaining = (deadline - datetime.now()).total_seconds() / 3600
        if remaining < 0:
            return "overdue"  # 已超期
        elif remaining <= 72:
            return "urgent"  # 即将超期
        else:
            return "normal"  # 正常
    
    async def reassign_tasks(
        from_user_id: int,
        to_user_id: int,
        task_ids: List[int]
    ):
        """批量转派任务"""
```

**前端任务卡片组件**:

```vue
<!-- frontend/src/components/TaskCard.vue -->
<template>
  <el-card class="task-card" :class="urgencyClass">
    <div class="task-header">
      <el-tag :type="urgencyTagType">{{ urgencyText }}</el-tag>
      <span class="task-type">{{ task.task_type }}</span>
    </div>
    <div class="task-body">
      <div class="doc-number">{{ task.doc_number }}</div>
      <div class="remaining-time">
        剩余时间: {{ formatRemaining(task.remaining_hours) }}
      </div>
    </div>
    <el-button type="primary" @click="handleTask">处理</el-button>
  </el-card>
</template>

<script setup>
const urgencyClass = computed(() => {
  if (task.urgency === 'overdue') return 'task-overdue'
  if (task.urgency === 'urgent') return 'task-urgent'
  return 'task-normal'
})
</script>
```

### 4. 通知中心 (Notification Hub)

**职责**: 站内信、邮件、企业微信通知的统一管理

**核心组件**:

```python
# backend/app/services/notification.py
class NotificationHub:
    """通知中心服务"""
    
    async def send_notification(
        user_ids: List[int],
        message_type: str,  # "workflow_exception", "system_alert", "warning"
        title: str,
        content: str,
        link: Optional[str] = None
    ):
        """发送站内信"""
        for user_id in user_ids:
            notification = Notification(
                user_id=user_id,
                message_type=message_type,
                title=title,
                content=content,
                link=link,
                is_read=False
            )
            await db.add(notification)
        await db.commit()
    
    async def send_email(
        to_emails: List[str],
        subject: str,
        body: str,
        attachments: Optional[List] = None
    ):
        """发送邮件（通过 SMTP）"""
        # 使用 aiosmtplib 异步发送邮件
        
    async def send_wechat_work(
        user_ids: List[str],
        message: str
    ):
        """发送企业微信消息"""
        # 调用企业微信 API
    
    async def mark_as_read(notification_id: int):
        """标记为已读"""
    
    async def mark_all_as_read(user_id: int):
        """一键标记全部已读"""
```

**通知触发机制**:

```python
# 业务流程中触发通知示例
async def reject_8d_report(report_id: int, reason: str, current_user: User):
    """驳回 8D 报告"""
    report = await db.get(Report8D, report_id)
    report.status = "rejected"
    report.rejection_reason = reason
    await db.commit()
    
    # 触发通知
    await NotificationHub.send_notification(
        user_ids=[report.submitter_id],
        message_type="workflow_exception",
        title="8D 报告被驳回",
        content=f"您提交的 8D 报告 {report.doc_number} 已被驳回。原因：{reason}",
        link=f"/quality/8d/{report.id}"
    )
    
    # 同时发送邮件
    user = await db.get(User, report.submitter_id)
    await NotificationHub.send_email(
        to_emails=[user.email],
        subject="8D 报告被驳回通知",
        body=f"您的 8D 报告 {report.doc_number} 已被驳回..."
    )
```

### 5. IMS 数据集成服务

**职责**: 定时从 IMS 系统同步数据、数据清洗、指标计算

**核心组件**:

```python
# backend/app/services/ims_integration.py
class IMSIntegrationService:
    """IMS 数据集成服务"""
    
    def __init__(self):
        self.ims_client = httpx.AsyncClient(
            base_url=settings.IMS_BASE_URL,
            timeout=30.0
        )
    
    async def sync_incoming_inspection_data(self, date: datetime):
        """同步入库检验数据"""
        # 调用 IMS API 获取数据
        response = await self.ims_client.get(
            "/api/inspection/incoming",
            params={"date": date.strftime("%Y-%m-%d")}
        )
        data = response.json()
        
        # 数据清洗和存储
        for record in data["records"]:
            inspection = IncomingInspection(
                material_code=record["material_code"],
                batch_number=record["batch_number"],
                inspection_result=record["result"],  # "OK" or "NG"
                defect_description=record.get("defect_desc"),
                defect_quantity=record.get("defect_qty", 0),
                inspection_date=date
            )
            await db.add(inspection)
        
        await db.commit()
        
        # 触发自动立案（如果有不合格）
        await self._auto_create_scar(date)
    
    async def _auto_create_scar(self, date: datetime):
        """自动生成 SCAR 单"""
        ng_records = await db.query(IncomingInspection).filter(
            IncomingInspection.inspection_date == date,
            IncomingInspection.inspection_result == "NG"
        ).all()
        
        for record in ng_records:
            scar = SCAR(
                doc_number=self._generate_doc_number(),
                supplier_id=record.supplier_id,
                material_code=record.material_code,
                defect_description=record.defect_description,
                status="pending_supplier_response",
                current_handler_id=record.supplier_contact_id
            )
            await db.add(scar)
            
            # 发送通知给供应商
            await NotificationHub.send_notification(...)
        
        await db.commit()

# Celery 定时任务
@celery_app.task
def sync_ims_data_daily():
    """每日凌晨 2:00 同步 IMS 数据"""
    asyncio.run(IMSIntegrationService().sync_incoming_inspection_data(
        date=datetime.now() - timedelta(days=1)
    ))
```


### 6. 质量指标计算服务

**职责**: 自动计算各类质量指标（PPM、合格率等）

**核心组件**:

```python
# backend/app/services/quality_metrics.py
class QualityMetricsCalculator:
    """质量指标计算服务"""
    
    async def calculate_incoming_pass_rate(
        supplier_id: Optional[int] = None,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> float:
        """计算来料批次合格率"""
        query = db.query(IncomingInspection).filter(
            IncomingInspection.inspection_date.between(start_date, end_date)
        )
        
        if supplier_id:
            query = query.filter(IncomingInspection.supplier_id == supplier_id)
        
        total_batches = await query.count()
        ng_batches = await query.filter(
            IncomingInspection.inspection_result == "NG"
        ).count()
        
        if total_batches == 0:
            return 0.0
        
        pass_rate = ((total_batches - ng_batches) / total_batches) * 100
        return round(pass_rate, 2)
    
    async def calculate_online_defect_ppm(
        supplier_id: Optional[int] = None,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> float:
        """计算物料上线不良 PPM"""
        # 获取物料入库总数量（分母）
        total_qty = await db.query(
            func.sum(IncomingInspection.quantity)
        ).filter(
            IncomingInspection.inspection_date.between(start_date, end_date)
        ).scalar() or 0
        
        # 获取物料上线不良数（分子）
        defect_qty = await db.query(
            func.sum(ProcessDefect.quantity)
        ).filter(
            ProcessDefect.defect_date.between(start_date, end_date),
            ProcessDefect.responsibility_type == "material_defect"
        ).scalar() or 0
        
        if total_qty == 0:
            return 0.0
        
        ppm = (defect_qty / total_qty) * 1000000
        return round(ppm, 2)
    
    async def calculate_0km_ppm(
        product_type: Optional[str] = None,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> float:
        """计算 0KM 不良 PPM"""
        # 获取成品出库总量（分母）
        total_shipment = await db.query(
            func.sum(Shipment.quantity)
        ).filter(
            Shipment.shipment_date.between(start_date, end_date)
        ).scalar() or 0
        
        # 获取 0KM 客诉数（分子）
        complaint_count = await db.query(Complaint).filter(
            Complaint.complaint_type == "0KM",
            Complaint.complaint_date.between(start_date, end_date)
        ).count()
        
        if total_shipment == 0:
            return 0.0
        
        ppm = (complaint_count / total_shipment) * 1000000
        return round(ppm, 2)
    
    async def calculate_rolling_mis_ppm(
        months: int,  # 3 or 12
        product_type: Optional[str] = None,
        end_date: datetime = None
    ) -> float:
        """计算滚动 MIS PPM"""
        start_date = end_date - timedelta(days=months * 30)
        
        # 获取滚动出货量
        rolling_shipment = await db.query(
            func.sum(Shipment.quantity)
        ).filter(
            Shipment.shipment_date.between(start_date, end_date)
        ).scalar() or 0
        
        # 获取 MIS 客诉数
        mis_count = await db.query(Complaint).filter(
            Complaint.complaint_type == f"{months}MIS",
            Complaint.complaint_date.between(start_date, end_date)
        ).count()
        
        if rolling_shipment == 0:
            return 0.0
        
        ppm = (mis_count / rolling_shipment) * 1000000
        return round(ppm, 2)

# Celery 定时任务：每日计算并缓存指标
@celery_app.task
def calculate_daily_metrics():
    """每日计算质量指标"""
    calculator = QualityMetricsCalculator()
    today = datetime.now().date()
    
    # 计算各类指标并存储到 Redis 缓存
    metrics = {
        "incoming_pass_rate": asyncio.run(calculator.calculate_incoming_pass_rate()),
        "online_defect_ppm": asyncio.run(calculator.calculate_online_defect_ppm()),
        "0km_ppm": asyncio.run(calculator.calculate_0km_ppm()),
        "3mis_ppm": asyncio.run(calculator.calculate_rolling_mis_ppm(3)),
        "12mis_ppm": asyncio.run(calculator.calculate_rolling_mis_ppm(12)),
    }
    
    # 存储到 Redis（24小时过期）
    redis_client.setex(
        f"metrics:daily:{today}",
        86400,
        json.dumps(metrics)
    )
```

### 7. AI 诊断引擎

**职责**: 异常归因分析、8D 报告预审、自然语言查询

**核心组件**:

```python
# backend/app/services/ai_diagnostic.py
from openai import AsyncOpenAI

class AIDiagnosticEngine:
    """AI 诊断引擎"""
    
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL  # 支持 DeepSeek 等兼容 API
        )
    
    async def analyze_anomaly(
        metric_name: str,
        current_value: float,
        historical_data: List[dict]
    ) -> str:
        """异常归因分析"""
        prompt = f"""
        质量指标 {metric_name} 出现异常飙升：
        - 当前值: {current_value}
        - 历史数据: {json.dumps(historical_data)}
        
        请分析可能的原因，并提供诊断报告。
        """
        
        response = await self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "你是一个汽车电子行业的质量管理专家。"},
                {"role": "user", "content": prompt}
            ]
        )
        
        return response.choices[0].message.content
    
    async def review_8d_report(self, report_content: dict) -> dict:
        """8D 报告预审"""
        # 检查空洞词汇
        empty_phrases = ["加强培训", "加强管理", "提高意识"]
        issues = []
        
        for step, content in report_content.items():
            for phrase in empty_phrases:
                if phrase in content:
                    issues.append({
                        "step": step,
                        "issue": f"措施不具体，包含空洞词汇：{phrase}",
                        "suggestion": "请补充具体的作业指导书变更证据或培训记录"
                    })
        
        # 调用 AI 进行深度分析
        prompt = f"""
        请审核以下 8D 报告的质量：
        {json.dumps(report_content, ensure_ascii=False)}
        
        重点检查：
        1. 根本原因分析是否深入（5Why 是否到位）
        2. 纠正措施是否具体可执行
        3. 预防措施是否有效
        """
        
        response = await self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "你是一个质量管理专家，擅长审核 8D 报告。"},
                {"role": "user", "content": prompt}
            ]
        )
        
        ai_feedback = response.choices[0].message.content
        
        return {
            "auto_issues": issues,
            "ai_feedback": ai_feedback,
            "approved": len(issues) == 0
        }
    
    async def natural_language_query(self, question: str) -> dict:
        """自然语言查询"""
        # 使用 AI 将自然语言转换为 SQL
        prompt = f"""
        用户问题：{question}
        
        数据库表结构：
        - incoming_inspection: 入库检验记录
        - process_defect: 制程不合格品
        - complaint: 客诉记录
        - shipment: 出货记录
        
        请生成对应的 SQL 查询语句。
        """
        
        response = await self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "你是一个 SQL 专家。"},
                {"role": "user", "content": prompt}
            ]
        )
        
        sql_query = response.choices[0].message.content
        
        # 执行 SQL 查询（需要安全校验）
        result = await db.execute(text(sql_query))
        data = result.fetchall()
        
        # 生成可视化图表配置
        chart_config = self._generate_chart_config(data)
        
        return {
            "sql": sql_query,
            "data": data,
            "chart": chart_config
        }
```


## Data Models

### 核心数据模型 ER 图

```
┌─────────────────┐         ┌─────────────────┐
│     User        │         │   Permission    │
├─────────────────┤         ├─────────────────┤
│ id (PK)         │────────<│ user_id (FK)    │
│ username        │         │ module          │
│ password_hash   │         │ operation       │
│ email           │         │ granted         │
│ user_type       │         └─────────────────┘
│ supplier_id (FK)│
│ status          │         ┌─────────────────┐
│ digital_sign    │         │  Notification   │
└─────────────────┘         ├─────────────────┤
         │                  │ id (PK)         │
         └─────────────────>│ user_id (FK)    │
                            │ message_type    │
                            │ title           │
                            │ content         │
                            │ is_read         │
                            │ created_at      │
                            └─────────────────┘

┌─────────────────┐         ┌─────────────────┐
│   Supplier      │         │      SCAR       │
├─────────────────┤         ├─────────────────┤
│ id (PK)         │────────<│ supplier_id (FK)│
│ name            │         │ doc_number      │
│ code            │         │ material_code   │
│ contact_person  │         │ defect_desc     │
│ contact_email   │         │ status          │
│ status          │         │ current_handler │
└─────────────────┘         │ deadline        │
                            └─────────────────┘
                                     │
                                     │ 1:1
                                     ▼
                            ┌─────────────────┐
                            │   Report8D      │
                            ├─────────────────┤
                            │ id (PK)         │
                            │ scar_id (FK)    │
                            │ d0_team         │
                            │ d1_problem_desc │
                            │ d2_containment  │
                            │ d3_root_cause   │
                            │ d4_corrective   │
                            │ d5_verification │
                            │ d6_preventive   │
                            │ d7_standardize  │
                            │ d8_lessons      │
                            │ status          │
                            │ ai_review_result│
                            └─────────────────┘

┌─────────────────┐         ┌─────────────────┐
│ IncomingInsp    │         │ ProcessDefect   │
├─────────────────┤         ├─────────────────┤
│ id (PK)         │         │ id (PK)         │
│ material_code   │         │ work_order      │
│ batch_number    │         │ defect_type     │
│ supplier_id (FK)│         │ responsibility  │
│ inspection_date │         │ quantity        │
│ result (OK/NG)  │         │ defect_date     │
│ defect_qty      │         └─────────────────┘
└─────────────────┘

┌─────────────────┐         ┌─────────────────┐
│   Shipment      │         │   Complaint     │
├─────────────────┤         ├─────────────────┤
│ id (PK)         │         │ id (PK)         │
│ product_type    │         │ complaint_type  │
│ customer_code   │         │ (0KM/3MIS/12MIS)│
│ quantity        │         │ product_type    │
│ shipment_date   │         │ vin_code        │
└─────────────────┘         │ defect_level    │
                            │ complaint_date  │
                            └─────────────────┘

┌─────────────────┐         ┌─────────────────┐
│     Audit       │         │     NCItem      │
├─────────────────┤         ├─────────────────┤
│ id (PK)         │────────<│ audit_id (FK)   │
│ audit_type      │         │ clause_number   │
│ audit_date      │         │ finding         │
│ auditor_id (FK) │         │ assignee_id (FK)│
│ auditee_id (FK) │         │ root_cause      │
│ score           │         │ corrective_act  │
│ grade (A/B/C)   │         │ status          │
└─────────────────┘         │ deadline        │
                            └─────────────────┘

┌─────────────────┐
│  OperationLog   │
├─────────────────┤
│ id (PK)         │
│ user_id (FK)    │
│ operation_type  │
│ target_module   │
│ target_id       │
│ before_data     │
│ after_data      │
│ ip_address      │
│ created_at      │
└─────────────────┘
```

### 详细数据模型定义

```python
# backend/app/models/user.py
from sqlalchemy import Column, Integer, String, Enum, DateTime, Text
from sqlalchemy.orm import relationship

class User(Base):
    """用户模型"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(100), nullable=False)
    phone = Column(String(20))
    full_name = Column(String(100))
    
    # 用户类型：company（公司用户）/ supplier（供应商用户）
    user_type = Column(Enum("company", "supplier"), nullable=False)
    
    # 公司用户字段
    department = Column(String(100))  # 部门
    position = Column(String(100))  # 职位
    
    # 供应商用户字段
    supplier_id = Column(Integer, ForeignKey("suppliers.id"))
    supplier = relationship("Supplier", back_populates="users")
    
    # 账号状态：pending（待审核）/ active（已激活）/ rejected（已拒绝）/ frozen（已冻结）
    status = Column(Enum("pending", "active", "rejected", "frozen"), default="pending")
    rejection_reason = Column(Text)
    
    # 电子签名（图片路径）
    digital_signature = Column(String(255))
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    permissions = relationship("Permission", back_populates="user")
    notifications = relationship("Notification", back_populates="user")
    operation_logs = relationship("OperationLog", back_populates="user")

# backend/app/models/permission.py
class Permission(Base):
    """权限模型"""
    __tablename__ = "permissions"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 功能模块（如：supplier_management, quality_dashboard）
    module = Column(String(100), nullable=False)
    
    # 操作类型：view, create, edit, delete, export
    operation = Column(Enum("view", "create", "edit", "delete", "export"), nullable=False)
    
    # 是否授权
    granted = Column(Boolean, default=False)
    
    # 关系
    user = relationship("User", back_populates="permissions")
    
    __table_args__ = (
        UniqueConstraint('user_id', 'module', 'operation'),
    )

# backend/app/models/supplier.py
class Supplier(Base):
    """供应商模型"""
    __tablename__ = "suppliers"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    code = Column(String(50), unique=True)
    
    # 联系信息
    contact_person = Column(String(100))
    contact_phone = Column(String(20))
    contact_email = Column(String(100))
    
    # 资质文件
    iso9001_cert = Column(String(255))  # 证书文件路径
    iso9001_expiry = Column(Date)  # 有效期
    iatf16949_cert = Column(String(255))
    iatf16949_expiry = Column(Date)
    business_license = Column(String(255))
    
    # 供应商状态：pending（待审核）/ active（已激活）/ suspended（已暂停）
    status = Column(Enum("pending", "active", "suspended"), default="pending")
    
    # 关系
    users = relationship("User", back_populates="supplier")
    scars = relationship("SCAR", back_populates="supplier")
    quality_targets = relationship("SupplierQualityTarget", back_populates="supplier")
    performance_scores = relationship("SupplierPerformance", back_populates="supplier")

# backend/app/models/scar.py
class SCAR(Base):
    """供应商纠正措施请求单"""
    __tablename__ = "scars"
    
    id = Column(Integer, primary_key=True)
    doc_number = Column(String(50), unique=True, nullable=False)  # 单据编号
    
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    material_code = Column(String(50))
    batch_number = Column(String(50))
    
    defect_description = Column(Text)
    defect_quantity = Column(Integer)
    
    # 状态：pending_supplier_response（待供应商响应）/ 
    #      pending_sqe_review（待 SQE 审核）/ closed（已关闭）
    status = Column(String(50), default="pending_supplier_response")
    
    # 当前处理人
    current_handler_id = Column(Integer, ForeignKey("users.id"))
    
    # 截止时间
    deadline = Column(DateTime)
    
    # 关系
    supplier = relationship("Supplier", back_populates="scars")
    report_8d = relationship("Report8D", back_populates="scar", uselist=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# backend/app/models/report_8d.py
class Report8D(Base):
    """8D 报告模型"""
    __tablename__ = "reports_8d"
    
    id = Column(Integer, primary_key=True)
    scar_id = Column(Integer, ForeignKey("scars.id"), unique=True)
    
    # D0: 组建团队
    d0_team_members = Column(Text)
    
    # D1: 问题描述（5W2H）
    d1_problem_description = Column(Text)
    
    # D2: 围堵措施
    d2_containment_actions = Column(Text)
    d2_in_transit_covered = Column(Boolean, default=False)
    d2_inventory_covered = Column(Boolean, default=False)
    d2_customer_covered = Column(Boolean, default=False)
    
    # D3: 根本原因
    d3_root_cause = Column(Text)
    d3_analysis_method = Column(String(50))  # 5Why, FTA, Fishbone
    d3_analysis_attachment = Column(String(255))
    
    # D4: 纠正措施
    d4_corrective_actions = Column(Text)
    
    # D5: 验证
    d5_verification_method = Column(Text)
    d5_verification_report = Column(String(255))
    
    # D6: 预防措施
    d6_preventive_actions = Column(Text)
    d6_document_updated = Column(Boolean, default=False)
    d6_document_attachment = Column(String(255))
    
    # D7: 标准化
    d7_standardization = Column(Text)
    
    # D8: 水平展开与经验教训
    d8_horizontal_deployment = Column(Text)
    d8_lesson_learned = Column(Text)
    d8_saved_to_library = Column(Boolean, default=False)
    
    # AI 预审结果
    ai_review_result = Column(JSON)
    ai_approved = Column(Boolean, default=False)
    
    # 状态
    status = Column(String(50), default="draft")
    
    # 关系
    scar = relationship("SCAR", back_populates="report_8d")
    
    submitted_at = Column(DateTime)
    approved_at = Column(DateTime)

# backend/app/models/notification.py
class Notification(Base):
    """站内信模型"""
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 消息类型：workflow_exception, system_alert, warning
    message_type = Column(String(50), nullable=False)
    
    title = Column(String(200), nullable=False)
    content = Column(Text)
    link = Column(String(255))  # 跳转链接
    
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    user = relationship("User", back_populates="notifications")

# backend/app/models/operation_log.py
class OperationLog(Base):
    """操作日志模型"""
    __tablename__ = "operation_logs"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 操作类型：create, update, delete, export
    operation_type = Column(String(20), nullable=False)
    
    # 目标模块和对象
    target_module = Column(String(100))
    target_id = Column(Integer)
    
    # 数据快照（JSON 格式）
    before_data = Column(JSON)
    after_data = Column(JSON)
    
    # 请求信息
    ip_address = Column(String(50))
    user_agent = Column(String(255))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    user = relationship("User", back_populates="operation_logs")
```


## Error Handling

### 统一错误处理机制

```python
# backend/app/core/exceptions.py
class QMSException(Exception):
    """QMS 系统基础异常类"""
    def __init__(self, message: str, code: str, status_code: int = 400):
        self.message = message
        self.code = code
        self.status_code = status_code

class PermissionDenied(QMSException):
    """权限不足异常"""
    def __init__(self, message: str = "权限不足"):
        super().__init__(message, "PERMISSION_DENIED", 403)

class ResourceNotFound(QMSException):
    """资源不存在异常"""
    def __init__(self, resource: str):
        super().__init__(f"{resource} 不存在", "RESOURCE_NOT_FOUND", 404)

class ValidationError(QMSException):
    """数据校验异常"""
    def __init__(self, message: str):
        super().__init__(message, "VALIDATION_ERROR", 400)

class IMSIntegrationError(QMSException):
    """IMS 集成异常"""
    def __init__(self, message: str):
        super().__init__(message, "IMS_INTEGRATION_ERROR", 500)

# 全局异常处理器
@app.exception_handler(QMSException)
async def qms_exception_handler(request: Request, exc: QMSException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "code": exc.code,
            "message": exc.message,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    # 记录错误日志
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "code": "INTERNAL_SERVER_ERROR",
            "message": "服务器内部错误",
            "timestamp": datetime.utcnow().isoformat()
        }
    )
```

### 前端错误处理

```typescript
// frontend/src/utils/request.ts
import axios from 'axios'
import { ElMessage } from 'element-plus'

const service = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 30000
})

// 请求拦截器
service.interceptors.request.use(
  config => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
service.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    const { response } = error
    
    if (response) {
      switch (response.status) {
        case 401:
          ElMessage.error('登录已过期，请重新登录')
          // 跳转到登录页
          router.push('/login')
          break
        case 403:
          ElMessage.error(response.data.message || '权限不足')
          break
        case 404:
          ElMessage.error(response.data.message || '资源不存在')
          break
        case 500:
          ElMessage.error('服务器错误，请稍后重试')
          break
        default:
          ElMessage.error(response.data.message || '请求失败')
      }
    } else {
      ElMessage.error('网络错误，请检查网络连接')
    }
    
    return Promise.reject(error)
  }
)

export default service
```

### 数据库事务处理

```python
# backend/app/core/database.py
from contextlib import asynccontextmanager

@asynccontextmanager
async def get_db_session():
    """数据库会话上下文管理器"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database transaction failed: {e}")
            raise
        finally:
            await session.close()

# 使用示例
async def create_scar_with_notification(scar_data: dict, user_id: int):
    """创建 SCAR 单并发送通知（事务）"""
    async with get_db_session() as db:
        # 创建 SCAR
        scar = SCAR(**scar_data)
        db.add(scar)
        await db.flush()  # 获取 scar.id
        
        # 创建通知
        notification = Notification(
            user_id=user_id,
            message_type="workflow_exception",
            title="新的 SCAR 单",
            content=f"SCAR 单 {scar.doc_number} 已创建"
        )
        db.add(notification)
        
        # 提交事务（由上下文管理器自动处理）
```

## Testing Strategy

### 测试金字塔

```
        ┌─────────────┐
        │   E2E Tests │  (少量，关键业务流程)
        │   (Cypress) │
        └─────────────┘
       ┌───────────────┐
       │ Integration   │  (中等数量，API 集成测试)
       │ Tests (Pytest)│
       └───────────────┘
      ┌─────────────────┐
      │   Unit Tests    │  (大量，单元测试)
      │   (Pytest/Jest) │
      └─────────────────┘
```

### 后端测试

```python
# backend/tests/test_auth.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_user_registration(client: AsyncClient):
    """测试用户注册"""
    response = await client.post("/api/v1/auth/register", json={
        "username": "test_user",
        "password": "Test123456",
        "email": "test@example.com",
        "user_type": "company",
        "department": "质量部",
        "position": "SQE"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["status"] == "pending"

@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, test_user):
    """测试登录成功"""
    response = await client.post("/api/v1/auth/login", json={
        "username": "test_user",
        "password": "Test123456"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data["data"]

@pytest.mark.asyncio
async def test_permission_check(client: AsyncClient, authenticated_user):
    """测试权限检查"""
    # 无权限访问
    response = await client.get("/api/v1/suppliers")
    assert response.status_code == 403
    
    # 授予权限后访问
    await grant_permission(authenticated_user.id, "supplier_management", "view")
    response = await client.get("/api/v1/suppliers")
    assert response.status_code == 200

# backend/tests/test_quality_metrics.py
@pytest.mark.asyncio
async def test_calculate_incoming_pass_rate():
    """测试来料合格率计算"""
    calculator = QualityMetricsCalculator()
    
    # 准备测试数据
    await create_test_inspection_data()
    
    pass_rate = await calculator.calculate_incoming_pass_rate(
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 1, 31)
    )
    
    assert pass_rate == 98.5  # 预期值

# backend/tests/test_ims_integration.py
@pytest.mark.asyncio
async def test_sync_ims_data(mock_ims_api):
    """测试 IMS 数据同步"""
    service = IMSIntegrationService()
    
    # Mock IMS API 响应
    mock_ims_api.get("/api/inspection/incoming").mock(
        return_value={"records": [
            {"material_code": "M001", "result": "OK"},
            {"material_code": "M002", "result": "NG"}
        ]}
    )
    
    await service.sync_incoming_inspection_data(datetime.now())
    
    # 验证数据已存储
    count = await db.query(IncomingInspection).count()
    assert count == 2
    
    # 验证自动立案
    scar_count = await db.query(SCAR).count()
    assert scar_count == 1  # 只有 NG 的生成 SCAR
```

### 前端测试

```typescript
// frontend/tests/unit/TaskCard.spec.ts
import { mount } from '@vue/test-utils'
import TaskCard from '@/components/TaskCard.vue'

describe('TaskCard.vue', () => {
  it('renders task information correctly', () => {
    const task = {
      task_type: 'SCAR',
      doc_number: 'SCAR-2024-001',
      urgency: 'urgent',
      remaining_hours: 48
    }
    
    const wrapper = mount(TaskCard, {
      props: { task }
    })
    
    expect(wrapper.text()).toContain('SCAR-2024-001')
    expect(wrapper.find('.task-urgent').exists()).toBe(true)
  })
  
  it('displays correct urgency color', () => {
    const overdueTask = { urgency: 'overdue', remaining_hours: -10 }
    const wrapper = mount(TaskCard, { props: { task: overdueTask } })
    
    expect(wrapper.classes()).toContain('task-overdue')
  })
})

// frontend/tests/e2e/login.spec.ts
describe('Login Flow', () => {
  it('should login successfully with valid credentials', () => {
    cy.visit('/login')
    cy.get('input[name="username"]').type('test_user')
    cy.get('input[name="password"]').type('Test123456')
    cy.get('button[type="submit"]').click()
    
    // 验证跳转到个人中心
    cy.url().should('include', '/personal-center')
    cy.contains('待办事项')
  })
  
  it('should show error with invalid credentials', () => {
    cy.visit('/login')
    cy.get('input[name="username"]').type('wrong_user')
    cy.get('input[name="password"]').type('wrong_pass')
    cy.get('button[type="submit"]').click()
    
    cy.contains('用户名或密码错误')
  })
})
```

### 性能测试

```python
# backend/tests/performance/test_load.py
from locust import HttpUser, task, between

class QMSUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """登录获取 Token"""
        response = self.client.post("/api/v1/auth/login", json={
            "username": "test_user",
            "password": "Test123456"
        })
        self.token = response.json()["data"]["access_token"]
        self.client.headers["Authorization"] = f"Bearer {self.token}"
    
    @task(3)
    def get_tasks(self):
        """获取待办任务（高频操作）"""
        self.client.get("/api/v1/tasks/my-tasks")
    
    @task(2)
    def get_dashboard(self):
        """查看质量数据面板"""
        self.client.get("/api/v1/quality/dashboard")
    
    @task(1)
    def create_scar(self):
        """创建 SCAR 单（低频操作）"""
        self.client.post("/api/v1/scars", json={
            "supplier_id": 1,
            "material_code": "M001",
            "defect_description": "外观不良"
        })

# 运行负载测试
# locust -f test_load.py --host=http://localhost:8000 --users=100 --spawn-rate=10
```

## Deployment

### Docker Compose 配置

```yaml
# docker-compose.yml
version: '3.8'

services:
  # PostgreSQL 数据库
  postgres:
    image: postgres:15-alpine
    container_name: qms_postgres
    environment:
      POSTGRES_DB: qms_db
      POSTGRES_USER: qms_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - qms_network
    restart: unless-stopped

  # Redis 缓存/队列
  redis:
    image: redis:7-alpine
    container_name: qms_redis
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    networks:
      - qms_network
    restart: unless-stopped

  # FastAPI 后端
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: qms_backend
    environment:
      DATABASE_URL: postgresql+asyncpg://qms_user:${DB_PASSWORD}@postgres:5432/qms_db
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379/0
      SECRET_KEY: ${SECRET_KEY}
      IMS_BASE_URL: ${IMS_BASE_URL}
      OPENAI_API_KEY: ${OPENAI_API_KEY}
    depends_on:
      - postgres
      - redis
    networks:
      - qms_network
    restart: unless-stopped

  # Celery Worker
  celery_worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: qms_celery
    command: celery -A app.core.celery worker --loglevel=info
    environment:
      DATABASE_URL: postgresql+asyncpg://qms_user:${DB_PASSWORD}@postgres:5432/qms_db
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379/0
    depends_on:
      - postgres
      - redis
    networks:
      - qms_network
    restart: unless-stopped

  # Celery Beat (定时任务调度器)
  celery_beat:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: qms_celery_beat
    command: celery -A app.core.celery beat --loglevel=info
    environment:
      DATABASE_URL: postgresql+asyncpg://qms_user:${DB_PASSWORD}@postgres:5432/qms_db
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379/0
    depends_on:
      - postgres
      - redis
    networks:
      - qms_network
    restart: unless-stopped

  # Vue 3 前端
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: qms_frontend
    networks:
      - qms_network
    restart: unless-stopped

  # Nginx 反向代理
  nginx:
    image: nginx:alpine
    container_name: qms_nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./deployment/nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./deployment/nginx/ssl:/etc/nginx/ssl
    depends_on:
      - backend
      - frontend
    networks:
      - qms_network
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:

networks:
  qms_network:
    driver: bridge
```

### Nginx 配置

```nginx
# deployment/nginx/nginx.conf
upstream backend {
    server backend:8000;
}

upstream frontend {
    server frontend:3000;
}

server {
    listen 80;
    server_name qms.example.com;
    
    # 重定向到 HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name qms.example.com;
    
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    
    # API 请求转发到后端
    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # 前端静态文件
    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # 文件上传大小限制
    client_max_body_size 50M;
}
```

## Security Considerations

1. **密码安全**: 使用 bcrypt 进行密码哈希，最小长度 8 位，包含大小写字母和数字
2. **JWT Token**: 设置合理的过期时间（如 24 小时），使用 RS256 算法签名
3. **SQL 注入防护**: 使用 SQLAlchemy ORM，避免拼接 SQL
4. **XSS 防护**: 前端对用户输入进行转义，后端返回数据时设置正确的 Content-Type
5. **CSRF 防护**: 使用 SameSite Cookie 属性，API 请求验证 Token
6. **文件上传安全**: 限制文件类型和大小，存储时重命名文件
7. **操作日志**: 记录所有关键操作，保留 3 年以上
8. **数据隔离**: 供应商账号只能查看自己的数据
9. **HTTPS**: 生产环境强制使用 HTTPS
10. **环境变量**: 敏感信息（密码、密钥）通过环境变量配置，不提交到代码库


## Business Module Designs

### 8. 供应商质量管理模块 (Supplier Quality Management)

**职责**: IQC 数据集成、SCAR 闭环、8D 报告协同、供应商审核、绩效评价、PPAP 管理

#### 8.1 IQC 数据集成与自动立案

```python
# backend/app/services/supplier_quality.py
class SupplierQualityService:
    """供应商质量服务"""
    
    async def process_iqc_inspection(self, inspection_data: dict):
        """处理 IQC 检验数据"""
        # 1. 存储检验记录
        inspection = IncomingInspection(**inspection_data)
        await db.add(inspection)
        
        # 2. 如果不合格，自动生成 SCAR
        if inspection.result == "NG":
            scar = await self._auto_create_scar(inspection)
            
            # 3. 通知供应商
            await NotificationHub.send_notification(
                user_ids=[inspection.supplier.contact_user_id],
                message_type="workflow_exception",
                title="新的 SCAR 单",
                content=f"物料 {inspection.material_code} 检验不合格，请填写 8D 报告"
            )
            
            # 4. 发送邮件
            await NotificationHub.send_email(
                to_emails=[inspection.supplier.contact_email],
                subject="SCAR 单通知",
                body=f"SCAR 单号：{scar.doc_number}..."
            )
        
        await db.commit()
        return inspection
    
    async def _auto_create_scar(self, inspection: IncomingInspection) -> SCAR:
        """自动创建 SCAR 单"""
        doc_number = await self._generate_scar_number()
        
        scar = SCAR(
            doc_number=doc_number,
            supplier_id=inspection.supplier_id,
            material_code=inspection.material_code,
            batch_number=inspection.batch_number,
            defect_description=inspection.defect_description,
            defect_quantity=inspection.defect_quantity,
            status="pending_supplier_response",
            current_handler_id=inspection.supplier.contact_user_id,
            deadline=datetime.now() + timedelta(days=7)  # 7 天内响应
        )
        
        await db.add(scar)
        await db.flush()
        return scar
```

#### 8.2 供应商 8D 报告协同

```python
class Report8DService:
    """8D 报告服务"""
    
    async def submit_8d_report(
        self,
        scar_id: int,
        report_data: dict,
        current_user: User
    ) -> dict:
        """供应商提交 8D 报告"""
        # 1. 创建或更新 8D 报告
        report = await db.get(Report8D, scar_id) or Report8D(scar_id=scar_id)
        
        # 更新各步骤数据
        report.d0_team_members = report_data.get("d0_team_members")
        report.d1_problem_description = report_data.get("d1_problem_description")
        # ... 其他步骤
        
        await db.add(report)
        await db.flush()
        
        # 2. AI 预审
        ai_result = await AIDiagnosticEngine().review_8d_report(report_data)
        report.ai_review_result = ai_result
        report.ai_approved = ai_result["approved"]
        
        if not ai_result["approved"]:
            # AI 发现问题，返回给供应商修改
            report.status = "ai_rejected"
            await db.commit()
            return {
                "success": False,
                "message": "AI 预审未通过，请修改后重新提交",
                "issues": ai_result["auto_issues"],
                "ai_feedback": ai_result["ai_feedback"]
            }
        
        # 3. AI 通过，转给 SQE 审核
        report.status = "pending_sqe_review"
        report.submitted_at = datetime.now()
        
        # 更新 SCAR 状态
        scar = await db.get(SCAR, scar_id)
        scar.status = "pending_sqe_review"
        scar.current_handler_id = await self._get_sqe_for_supplier(scar.supplier_id)
        
        await db.commit()
        
        # 4. 通知 SQE
        await NotificationHub.send_notification(
            user_ids=[scar.current_handler_id],
            message_type="workflow_exception",
            title="待审核 8D 报告",
            content=f"SCAR {scar.doc_number} 的 8D 报告已提交，请审核"
        )
        
        return {
            "success": True,
            "message": "8D 报告提交成功，等待 SQE 审核"
        }
    
    async def sqe_review_8d(
        self,
        report_id: int,
        action: str,  # "approve" or "reject"
        comments: str,
        current_user: User
    ):
        """SQE 审核 8D 报告"""
        report = await db.get(Report8D, report_id)
        scar = await db.get(SCAR, report.scar_id)
        
        if action == "approve":
            report.status = "approved"
            report.approved_at = datetime.now()
            report.approved_by_id = current_user.id
            
            # 关闭 SCAR
            scar.status = "closed"
            scar.closed_at = datetime.now()
            
            # 通知供应商
            await NotificationHub.send_notification(
                user_ids=[scar.supplier.contact_user_id],
                message_type="system_alert",
                title="8D 报告已批准",
                content=f"SCAR {scar.doc_number} 的 8D 报告已通过审核"
            )
        else:
            report.status = "rejected"
            report.rejection_reason = comments
            
            # 退回给供应商
            scar.status = "pending_supplier_response"
            scar.current_handler_id = scar.supplier.contact_user_id
            
            # 通知供应商
            await NotificationHub.send_notification(
                user_ids=[scar.supplier.contact_user_id],
                message_type="workflow_exception",
                title="8D 报告被驳回",
                content=f"SCAR {scar.doc_number} 的 8D 报告被驳回。原因：{comments}"
            )
        
        await db.commit()
```

#### 8.3 供应商绩效评价

```python
class SupplierPerformanceService:
    """供应商绩效服务"""
    
    async def calculate_monthly_performance(
        self,
        supplier_id: int,
        year: int,
        month: int
    ) -> dict:
        """计算供应商月度绩效"""
        # 初始分 60 分
        base_score = 60
        deductions = []
        
        # 1. 获取质量目标
        target = await self._get_quality_target(supplier_id, year, month)
        
        # 2. 来料质量扣分
        incoming_deduction = await self._calculate_incoming_deduction(
            supplier_id, year, month, target
        )
        deductions.append({
            "category": "来料质量",
            "deduction": incoming_deduction,
            "details": "..."
        })
        
        # 3. 制程质量扣分（物料上线不良）
        process_deduction = await self._calculate_process_deduction(
            supplier_id, year, month, target
        )
        deductions.append({
            "category": "制程质量",
            "deduction": process_deduction,
            "details": "..."
        })
        
        # 4. 配合度扣分
        cooperation_deduction = await self._get_cooperation_deduction(
            supplier_id, year, month
        )
        deductions.append({
            "category": "配合度",
            "deduction": cooperation_deduction,
            "details": "..."
        })
        
        # 5. 客诉扣分
        complaint_deduction = await self._calculate_complaint_deduction(
            supplier_id, year, month
        )
        deductions.append({
            "category": "客诉质量",
            "deduction": complaint_deduction,
            "details": "..."
        })
        
        # 6. 计算总分（60 分制）
        total_deduction = sum(d["deduction"] for d in deductions)
        score_60 = max(0, base_score - total_deduction)
        
        # 7. 折算为百分制
        score_100 = (score_60 / 60) * 100
        
        # 8. 评定等级
        grade = self._determine_grade(score_100)
        
        # 9. 存储绩效记录
        performance = SupplierPerformance(
            supplier_id=supplier_id,
            year=year,
            month=month,
            base_score=base_score,
            total_deduction=total_deduction,
            score_60=score_60,
            score_100=score_100,
            grade=grade,
            deduction_details=deductions
        )
        await db.add(performance)
        await db.commit()
        
        # 10. 如果是 C/D 级，自动生成改善会议任务
        if grade in ["C", "D"]:
            await self._create_improvement_meeting_task(supplier_id, grade)
        
        return {
            "score_100": score_100,
            "grade": grade,
            "deductions": deductions
        }
    
    async def _calculate_incoming_deduction(
        self,
        supplier_id: int,
        year: int,
        month: int,
        target: SupplierQualityTarget
    ) -> float:
        """计算来料质量扣分"""
        # 计算实际合格率
        actual_rate = await QualityMetricsCalculator().calculate_incoming_pass_rate(
            supplier_id=supplier_id,
            start_date=datetime(year, month, 1),
            end_date=datetime(year, month, 28)  # 简化处理
        )
        
        # 计算差距
        gap = target.incoming_pass_rate_target - actual_rate
        gap_percentage = (gap / target.incoming_pass_rate_target) * 100
        
        # 扣分规则
        if gap_percentage <= 0:
            return 0  # 达标
        elif gap_percentage < 10:
            return 5
        elif gap_percentage < 20:
            return 15
        else:
            return 30
    
    def _determine_grade(self, score: float) -> str:
        """评定等级"""
        if score > 95:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        else:
            return "D"
```

### 9. 过程质量管理模块 (Process Quality Management)

**职责**: 生产数据集成、不合格品管理、问题发单闭环

```python
# backend/app/services/process_quality.py
class ProcessQualityService:
    """过程质量服务"""
    
    async def record_process_defect(
        self,
        defect_data: dict,
        current_user: User
    ) -> ProcessDefect:
        """录入制程不合格品"""
        defect = ProcessDefect(
            work_order=defect_data["work_order"],
            production_line=defect_data["production_line"],
            defect_type=defect_data["defect_type"],
            defect_phenomenon=defect_data["defect_phenomenon"],
            responsibility_type=defect_data["responsibility_type"],  # 物料/作业/设备/工艺/设计
            quantity=defect_data["quantity"],
            defect_date=defect_data["defect_date"],
            recorded_by_id=current_user.id
        )
        
        await db.add(defect)
        await db.commit()
        
        # 如果是物料不良，关联到物料上线不良 PPM 指标
        if defect.responsibility_type == "material_defect":
            await self._update_material_online_ppm(defect)
        
        return defect
    
    async def create_improvement_task(
        self,
        defect_ids: List[int],
        current_user: User
    ) -> ImprovementTask:
        """PQE 发起整改任务"""
        # 1. 创建整改任务
        task = ImprovementTask(
            task_type="process_improvement",
            defect_ids=defect_ids,
            created_by_id=current_user.id,
            status="pending_assignment"
        )
        
        # 2. 根据责任类别推荐责任人
        defects = await db.query(ProcessDefect).filter(
            ProcessDefect.id.in_(defect_ids)
        ).all()
        
        responsibility_type = defects[0].responsibility_type
        recommended_assignee = await self._recommend_assignee(responsibility_type)
        
        task.recommended_assignee_id = recommended_assignee.id
        
        await db.add(task)
        await db.commit()
        
        # 3. 通知推荐责任人
        await NotificationHub.send_notification(
            user_ids=[recommended_assignee.id],
            message_type="workflow_exception",
            title="新的整改任务",
            content=f"PQE {current_user.full_name} 指派了整改任务"
        )
        
        return task
    
    async def submit_improvement_actions(
        self,
        task_id: int,
        actions_data: dict,
        current_user: User
    ):
        """责任板块提交整改措施"""
        task = await db.get(ImprovementTask, task_id)
        
        # 更新整改措施
        task.root_cause_analysis = actions_data["root_cause_analysis"]
        task.containment_actions = actions_data["containment_actions"]
        task.long_term_actions = actions_data["long_term_actions"]
        task.evidence_attachments = actions_data["evidence_attachments"]
        
        # 设置验证期
        task.verification_start_date = datetime.now()
        task.verification_end_date = datetime.now() + timedelta(days=7)
        task.status = "in_verification"
        
        await db.commit()
        
        # 通知 PQE 进入验证期
        await NotificationHub.send_notification(
            user_ids=[task.created_by_id],
            message_type="system_alert",
            title="整改措施已提交",
            content=f"整改任务 {task.id} 已进入验证期"
        )
    
    async def verify_improvement(
        self,
        task_id: int,
        verification_result: bool,
        comments: str,
        current_user: User
    ):
        """PQE 验证整改效果"""
        task = await db.get(ImprovementTask, task_id)
        
        if verification_result:
            task.status = "closed"
            task.closed_at = datetime.now()
            task.verification_comments = comments
        else:
            task.status = "verification_failed"
            task.verification_comments = comments
            # 退回重新整改
        
        await db.commit()
```


### 10. 客户质量管理模块 (Customer Quality Management)

**职责**: 出货数据集成、客诉录入分级、8D 闭环、索赔管理

```python
# backend/app/services/customer_quality.py
class CustomerQualityService:
    """客户质量服务"""
    
    async def create_complaint(
        self,
        complaint_data: dict,
        current_user: User
    ) -> Complaint:
        """CQE 录入客诉"""
        complaint = Complaint(
            complaint_type=complaint_data["complaint_type"],  # 0KM or 3MIS/12MIS
            product_type=complaint_data["product_type"],
            customer_code=complaint_data["customer_code"],
            defect_level=complaint_data["defect_level"],  # A/B/C
            defect_description=complaint_data["defect_description"],
            complaint_date=complaint_data["complaint_date"],
            created_by_id=current_user.id,
            status="pending_d0_d3"  # 待 CQE 完成 D0-D3
        )
        
        # 如果是 MIS 客诉，记录额外信息
        if complaint.complaint_type in ["3MIS", "12MIS"]:
            complaint.vin_code = complaint_data["vin_code"]
            complaint.mileage = complaint_data["mileage"]
            complaint.purchase_date = complaint_data["purchase_date"]
        
        await db.add(complaint)
        await db.flush()
        
        # 自动追溯
        if complaint_data.get("material_code"):
            traceability_data = await self._trace_material(
                complaint_data["material_code"],
                complaint.complaint_date
            )
            complaint.traceability_data = traceability_data
        
        await db.commit()
        return complaint
    
    async def complete_d0_d3(
        self,
        complaint_id: int,
        d0_d3_data: dict,
        current_user: User
    ):
        """CQE 完成一次因解析（D0-D3）"""
        complaint = await db.get(Complaint, complaint_id)
        
        # 更新 D0-D3 数据
        complaint.d0_team = d0_d3_data["d0_team"]
        complaint.d1_problem_desc = d0_d3_data["d1_problem_desc"]
        complaint.d2_containment = d0_d3_data["d2_containment"]
        complaint.d3_preliminary_cause = d0_d3_data["d3_preliminary_cause"]
        
        # 确定责任部门
        complaint.responsible_department = d0_d3_data["responsible_department"]
        
        # 指派给责任板块进行 D4-D8
        responsible_user = await self._get_department_lead(
            complaint.responsible_department
        )
        complaint.current_handler_id = responsible_user.id
        complaint.status = "pending_d4_d8"
        
        # 设置 SLA 时效
        complaint.d4_d8_deadline = datetime.now() + timedelta(days=7)
        
        await db.commit()
        
        # 通知责任板块
        await NotificationHub.send_notification(
            user_ids=[responsible_user.id],
            message_type="workflow_exception",
            title="新的客诉 8D 任务",
            content=f"客诉单 {complaint.doc_number} 已指派给您，请在 7 天内完成 D4-D8"
        )
    
    async def complete_d4_d8(
        self,
        complaint_id: int,
        d4_d8_data: dict,
        current_user: User
    ):
        """责任板块完成 D4-D8"""
        complaint = await db.get(Complaint, complaint_id)
        
        # 更新 D4-D8 数据
        complaint.d4_root_cause = d4_d8_data["d4_root_cause"]
        complaint.d5_corrective_actions = d4_d8_data["d5_corrective_actions"]
        complaint.d6_verification = d4_d8_data["d6_verification"]
        complaint.d6_verification_report = d4_d8_data["d6_verification_report"]
        complaint.d7_preventive_actions = d4_d8_data["d7_preventive_actions"]
        complaint.d7_document_updated = d4_d8_data["d7_document_updated"]
        complaint.d8_horizontal_deployment = d4_d8_data["d8_horizontal_deployment"]
        
        # 检查是否沉淀经验教训
        if d4_d8_data.get("save_to_lesson_learned"):
            await self._save_lesson_learned(complaint, d4_d8_data["lesson_summary"])
        
        # 提交审批
        complaint.status = "pending_approval"
        complaint.submitted_for_approval_at = datetime.now()
        
        # 根据缺陷等级确定审批流
        approvers = await self._get_approvers(complaint.defect_level)
        complaint.approver_ids = [a.id for a in approvers]
        complaint.current_handler_id = approvers[0].id
        
        await db.commit()
        
        # 通知审批人
        await NotificationHub.send_notification(
            user_ids=[approvers[0].id],
            message_type="workflow_exception",
            title="待审批 8D 报告",
            content=f"客诉单 {complaint.doc_number} 的 8D 报告待审批"
        )
    
    async def approve_8d(
        self,
        complaint_id: int,
        approved: bool,
        comments: str,
        current_user: User
    ):
        """审批 8D 报告"""
        complaint = await db.get(Complaint, complaint_id)
        
        if approved:
            # 检查是否所有审批人都已批准
            complaint.approval_records.append({
                "approver_id": current_user.id,
                "approved": True,
                "comments": comments,
                "approved_at": datetime.now().isoformat()
            })
            
            if len(complaint.approval_records) == len(complaint.approver_ids):
                # 所有人都批准，归档
                complaint.status = "archived"
                complaint.archived_at = datetime.now()
                
                # 触发归档检查表
                await self._trigger_archive_checklist(complaint)
            else:
                # 流转到下一个审批人
                next_approver_id = complaint.approver_ids[len(complaint.approval_records)]
                complaint.current_handler_id = next_approver_id
                
                await NotificationHub.send_notification(
                    user_ids=[next_approver_id],
                    message_type="workflow_exception",
                    title="待审批 8D 报告",
                    content=f"客诉单 {complaint.doc_number} 的 8D 报告待审批"
                )
        else:
            # 驳回，退回责任板块
            complaint.status = "pending_d4_d8"
            complaint.current_handler_id = complaint.responsible_user_id
            complaint.rejection_reason = comments
            
            await NotificationHub.send_notification(
                user_ids=[complaint.responsible_user_id],
                message_type="workflow_exception",
                title="8D 报告被驳回",
                content=f"客诉单 {complaint.doc_number} 被驳回。原因：{comments}"
            )
        
        await db.commit()
    
    async def create_claim(
        self,
        complaint_id: int,
        claim_data: dict,
        current_user: User
    ) -> Claim:
        """创建索赔单"""
        complaint = await db.get(Complaint, complaint_id)
        
        claim = Claim(
            claim_type="customer_claim",
            complaint_id=complaint_id,
            customer_code=complaint.customer_code,
            claim_amount=claim_data["claim_amount"],
            claim_details=claim_data["claim_details"],
            created_by_id=current_user.id,
            status="recorded"
        )
        
        await db.add(claim)
        await db.commit()
        
        # 如果根本原因是供应商问题，可以转嫁
        if complaint.d4_root_cause_type == "supplier_material":
            await self._create_supplier_claim(claim, complaint)
        
        return claim
    
    async def _create_supplier_claim(self, customer_claim: Claim, complaint: Complaint):
        """向供应商转嫁索赔"""
        supplier_claim = Claim(
            claim_type="supplier_claim",
            related_customer_claim_id=customer_claim.id,
            supplier_id=complaint.responsible_supplier_id,
            material_code=complaint.material_code,
            claim_amount=customer_claim.claim_amount,
            claim_details=f"转嫁客户索赔：{customer_claim.claim_details}",
            status="pending_supplier_confirmation"
        )
        
        await db.add(supplier_claim)
        await db.commit()
        
        # 通知供应商
        await NotificationHub.send_notification(
            user_ids=[complaint.responsible_supplier.contact_user_id],
            message_type="workflow_exception",
            title="供应商索赔通知",
            content=f"索赔金额：{supplier_claim.claim_amount} 元"
        )
```

### 11. 新品质量管理模块 (New Product Quality Management)


**职责**: 经验教训注入、阶段评审、试产管理、初期流动

```python
# backend/app/services/new_product_quality.py
class NewProductQualityService:
    """新品质量服务"""
    
    async def create_project(
        self,
        project_data: dict,
        current_user: User
    ) -> NewProductProject:
        """创建新品项目"""
        project = NewProductProject(
            project_name=project_data["project_name"],
            product_type=project_data["product_type"],
            project_manager_id=project_data["project_manager_id"],
            quality_engineer_id=current_user.id,
            status="initiated",
            created_at=datetime.now()
        )
        
        await db.add(project)
        await db.flush()
        
        # 自动推送相关经验教训
        lessons = await self._get_relevant_lessons(project.product_type)
        
        for lesson in lessons:
            project_lesson = ProjectLessonCheck(
                project_id=project.id,
                lesson_id=lesson.id,
                status="pending_check",
                assigned_to_id=project.quality_engineer_id
            )
            await db.add(project_lesson)
        
        await db.commit()
        
        # 通知质量工程师
        await NotificationHub.send_notification(
            user_ids=[current_user.id],
            message_type="system_alert",
            title="经验教训点检",
            content=f"项目 {project.project_name} 有 {len(lessons)} 条经验教训需要点检"
        )
        
        return project
    
    async def check_lesson_learned(
        self,
        project_lesson_id: int,
        is_mitigated: bool,
        mitigation_reason: str,
        evidence_attachment: str,
        current_user: User
    ):
        """点检经验教训"""
        project_lesson = await db.get(ProjectLessonCheck, project_lesson_id)
        
        project_lesson.is_mitigated = is_mitigated
        project_lesson.mitigation_reason = mitigation_reason if not is_mitigated else None
        project_lesson.evidence_attachment = evidence_attachment if is_mitigated else None
        project_lesson.checked_at = datetime.now()
        project_lesson.status = "checked"
        
        await db.commit()
    
    async def submit_gate_review(
        self,
        project_id: int,
        gate_name: str,  # "concept", "design", "verification", "production_ready"
        deliverables: dict,
        current_user: User
    ):
        """提交阶段评审"""
        project = await db.get(NewProductProject, project_id)
        
        # 检查必需交付物
        required_deliverables = await self._get_required_deliverables(gate_name)
        missing = []
        
        for req in required_deliverables:
            if req not in deliverables or not deliverables[req]:
                missing.append(req)
        
        if missing:
            raise ValidationError(f"缺少必需交付物：{', '.join(missing)}")
        
        # 检查经验教训是否都已点检
        unchecked_lessons = await db.query(ProjectLessonCheck).filter(
            ProjectLessonCheck.project_id == project_id,
            ProjectLessonCheck.status != "checked"
        ).count()
        
        if unchecked_lessons > 0:
            raise ValidationError(f"还有 {unchecked_lessons} 条经验教训未点检")
        
        # 检查未规避的经验教训是否有证据
        unmitigated_without_evidence = await db.query(ProjectLessonCheck).filter(
            ProjectLessonCheck.project_id == project_id,
            ProjectLessonCheck.is_mitigated == True,
            ProjectLessonCheck.evidence_attachment == None
        ).count()
        
        if unmitigated_without_evidence > 0:
            raise ValidationError("已规避的经验教训需要上传证据")
        
        # 创建评审记录
        gate_review = GateReview(
            project_id=project_id,
            gate_name=gate_name,
            deliverables=deliverables,
            submitted_by_id=current_user.id,
            submitted_at=datetime.now(),
            status="pending_approval"
        )
        
        await db.add(gate_review)
        await db.commit()
        
        # 通知评审人
        reviewers = await self._get_gate_reviewers(gate_name)
        await NotificationHub.send_notification(
            user_ids=[r.id for r in reviewers],
            message_type="workflow_exception",
            title="阶段评审待审批",
            content=f"项目 {project.project_name} 的 {gate_name} 阶段评审待审批"
        )
    
    async def create_trial_production(
        self,
        project_id: int,
        trial_data: dict,
        current_user: User
    ) -> TrialProduction:
        """创建试产记录"""
        trial = TrialProduction(
            project_id=project_id,
            ims_work_order=trial_data["ims_work_order"],
            target_yield_rate=trial_data["target_yield_rate"],
            target_cpk=trial_data["target_cpk"],
            target_dimension_pass_rate=trial_data["target_dimension_pass_rate"],
            created_by_id=current_user.id,
            status="in_progress"
        )
        
        await db.add(trial)
        await db.commit()
        
        return trial
    
    async def sync_trial_production_data(self, trial_id: int):
        """从 IMS 同步试产数据"""
        trial = await db.get(TrialProduction, trial_id)
        
        # 从 IMS 获取工单数据
        ims_data = await IMSIntegrationService().get_work_order_data(
            trial.ims_work_order
        )
        
        # 更新实绩
        trial.actual_input_qty = ims_data["input_qty"]
        trial.actual_output_qty = ims_data["output_qty"]
        trial.actual_first_pass_qty = ims_data["first_pass_qty"]
        trial.actual_defect_qty = ims_data["defect_qty"]
        
        # 计算指标
        trial.actual_yield_rate = (trial.actual_output_qty / trial.actual_input_qty) * 100
        trial.actual_first_pass_rate = (trial.actual_first_pass_qty / trial.actual_input_qty) * 100
        
        await db.commit()
    
    async def generate_trial_summary_report(self, trial_id: int) -> dict:
        """生成试产总结报告"""
        trial = await db.get(TrialProduction, trial_id)
        
        # 对比目标与实绩
        comparison = {
            "yield_rate": {
                "target": trial.target_yield_rate,
                "actual": trial.actual_yield_rate,
                "achieved": trial.actual_yield_rate >= trial.target_yield_rate,
                "color": "green" if trial.actual_yield_rate >= trial.target_yield_rate else "red"
            },
            "cpk": {
                "target": trial.target_cpk,
                "actual": trial.actual_cpk,
                "achieved": trial.actual_cpk >= trial.target_cpk,
                "color": "green" if trial.actual_cpk >= trial.target_cpk else "red"
            },
            # ... 其他指标
        }
        
        # 生成 Excel/PDF 报告
        report_path = await self._generate_report_file(trial, comparison)
        
        return {
            "comparison": comparison,
            "report_path": report_path
        }
```


### 12. 审核管理模块 (Audit Management)

**职责**: 审核计划、数字化检查表、问题整改闭环、二方审核

```python
# backend/app/services/audit_management.py
class AuditManagementService:
    """审核管理服务"""
    
    async def create_annual_audit_plan(
        self,
        plan_data: dict,
        current_user: User
    ) -> AuditPlan:
        """创建年度审核计划"""
        plan = AuditPlan(
            year=plan_data["year"],
            audit_type=plan_data["audit_type"],  # system, process, product, second_party
            planned_audits=plan_data["planned_audits"],  # List of planned audit items
            created_by_id=current_user.id,
            status="active"
        )
        
        await db.add(plan)
        await db.flush()
        
        # 为每个计划项创建提醒任务
        for audit_item in plan_data["planned_audits"]:
            reminder = AuditReminder(
                audit_plan_id=plan.id,
                audit_date=audit_item["planned_date"],
                auditor_id=audit_item["auditor_id"],
                auditee_id=audit_item["auditee_id"],
                reminder_days_before=7,
                status="pending"
            )
            await db.add(reminder)
        
        await db.commit()
        return plan
    
    async def start_audit(
        self,
        audit_plan_item_id: int,
        checklist_template_id: int,
        current_user: User
    ) -> Audit:
        """开始审核"""
        # 创建审核记录
        audit = Audit(
            audit_plan_item_id=audit_plan_item_id,
            auditor_id=current_user.id,
            audit_date=datetime.now().date(),
            checklist_template_id=checklist_template_id,
            status="in_progress"
        )
        
        await db.add(audit)
        await db.flush()
        
        # 加载检查表模板
        template = await db.get(ChecklistTemplate, checklist_template_id)
        
        # 为每个检查项创建记录
        for clause in template.clauses:
            check_item = AuditCheckItem(
                audit_id=audit.id,
                clause_number=clause["number"],
                clause_description=clause["description"],
                result=None,  # 待填写
                evidence_photos=[],
                comments=""
            )
            await db.add(check_item)
        
        await db.commit()
        return audit
    
    async def record_check_item(
        self,
        check_item_id: int,
        result: str,  # "OK" or "NG"
        evidence_photos: List[str],
        comments: str,
        current_user: User
    ):
        """现场录入检查项结果（支持移动端）"""
        check_item = await db.get(AuditCheckItem, check_item_id)
        
        check_item.result = result
        check_item.evidence_photos = evidence_photos
        check_item.comments = comments
        check_item.checked_at = datetime.now()
        
        await db.commit()
    
    async def complete_audit(
        self,
        audit_id: int,
        current_user: User
    ) -> dict:
        """完成审核并自动评分"""
        audit = await db.get(Audit, audit_id)
        
        # 获取所有检查项
        check_items = await db.query(AuditCheckItem).filter(
            AuditCheckItem.audit_id == audit_id
        ).all()
        
        # 计算得分（根据 VDA 6.3 规则）
        score_result = await self._calculate_audit_score(check_items, audit.audit_type)
        
        audit.score = score_result["score"]
        audit.grade = score_result["grade"]  # A/B/C
        audit.status = "completed"
        audit.completed_at = datetime.now()
        
        await db.commit()
        
        # 自动生成不符合项（NC）
        ng_items = [item for item in check_items if item.result == "NG"]
        nc_items = []
        
        for ng_item in ng_items:
            nc = NCItem(
                audit_id=audit_id,
                clause_number=ng_item.clause_number,
                finding=ng_item.comments,
                severity=self._determine_nc_severity(ng_item),
                status="pending_assignment",
                deadline=datetime.now() + timedelta(days=30 if severity == "minor" else 7)
            )
            await db.add(nc)
            nc_items.append(nc)
        
        await db.commit()
        
        # 生成审核报告 PDF
        report_path = await self._generate_audit_report(audit, check_items, score_result)
        
        return {
            "score": audit.score,
            "grade": audit.grade,
            "nc_count": len(nc_items),
            "report_path": report_path
        }
    
    async def _calculate_audit_score(
        self,
        check_items: List[AuditCheckItem],
        audit_type: str
    ) -> dict:
        """计算审核得分"""
        if audit_type == "VDA_6_3":
            # VDA 6.3 评分规则
            total_items = len(check_items)
            ok_items = len([item for item in check_items if item.result == "OK"])
            
            # 基础得分
            base_score = (ok_items / total_items) * 100
            
            # 检查单项 0 分降级规则
            critical_ng = any(
                item.result == "NG" and item.is_critical
                for item in check_items
            )
            
            if critical_ng:
                # 单项 0 分，强制降级
                grade = "C"
                score = min(base_score, 69)
            else:
                if base_score >= 90:
                    grade = "A"
                elif base_score >= 75:
                    grade = "B"
                else:
                    grade = "C"
                score = base_score
            
            return {
                "score": round(score, 1),
                "grade": grade,
                "total_items": total_items,
                "ok_items": ok_items,
                "ng_items": total_items - ok_items
            }
        else:
            # 其他审核类型的评分逻辑
            pass
    
    async def assign_nc_item(
        self,
        nc_item_id: int,
        assignee_id: int,
        current_user: User
    ):
        """指派不符合项"""
        nc_item = await db.get(NCItem, nc_item_id)
        
        nc_item.assignee_id = assignee_id
        nc_item.assigned_at = datetime.now()
        nc_item.status = "assigned"
        
        await db.commit()
        
        # 通知责任人
        await NotificationHub.send_notification(
            user_ids=[assignee_id],
            message_type="workflow_exception",
            title="新的审核整改项",
            content=f"审核不符合项 {nc_item.clause_number} 已指派给您"
        )
    
    async def submit_nc_corrective_action(
        self,
        nc_item_id: int,
        corrective_data: dict,
        current_user: User
    ):
        """提交整改措施"""
        nc_item = await db.get(NCItem, nc_item_id)
        
        nc_item.root_cause = corrective_data["root_cause"]
        nc_item.corrective_actions = corrective_data["corrective_actions"]
        nc_item.evidence_attachments = corrective_data["evidence_attachments"]
        nc_item.submitted_at = datetime.now()
        nc_item.status = "pending_verification"
        
        await db.commit()
        
        # 通知审核员验证
        audit = await db.get(Audit, nc_item.audit_id)
        await NotificationHub.send_notification(
            user_ids=[audit.auditor_id],
            message_type="workflow_exception",
            title="整改措施待验证",
            content=f"不符合项 {nc_item.clause_number} 的整改措施已提交"
        )
    
    async def verify_nc_item(
        self,
        nc_item_id: int,
        verification_result: bool,
        comments: str,
        current_user: User
    ):
        """验证整改效果"""
        nc_item = await db.get(NCItem, nc_item_id)
        
        if verification_result:
            nc_item.status = "closed"
            nc_item.closed_at = datetime.now()
            nc_item.verification_comments = comments
        else:
            nc_item.status = "verification_failed"
            nc_item.verification_comments = comments
            # 退回重新整改
        
        await db.commit()
    
    async def create_second_party_audit(
        self,
        audit_data: dict,
        current_user: User
    ) -> SecondPartyAudit:
        """创建二方审核（客户来厂审核）"""
        audit = SecondPartyAudit(
            customer_name=audit_data["customer_name"],
            audit_type=audit_data["audit_type"],
            audit_date=audit_data["audit_date"],
            customer_auditors=audit_data["customer_auditors"],
            internal_coordinator_id=current_user.id,
            status="scheduled"
        )
        
        await db.add(audit)
        await db.commit()
        
        return audit
    
    async def upload_customer_nc_list(
        self,
        audit_id: int,
        nc_list_file: str,
        current_user: User
    ):
        """上传客户指定的问题整改清单"""
        audit = await db.get(SecondPartyAudit, audit_id)
        
        audit.customer_nc_list_file = nc_list_file
        
        # 解析 Excel 文件，创建内部跟踪任务
        nc_items = await self._parse_customer_nc_list(nc_list_file)
        
        for nc_data in nc_items:
            nc = CustomerNCItem(
                second_party_audit_id=audit_id,
                nc_number=nc_data["nc_number"],
                finding=nc_data["finding"],
                required_action=nc_data["required_action"],
                deadline=nc_data["deadline"],
                status="pending_assignment"
            )
            await db.add(nc)
        
        await db.commit()
        
        # 通知相关责任人
        responsible_user_ids = [nc.assignee_id for nc in nc_items if nc.assignee_id]
        if responsible_user_ids:
            await NotificationHub.send_notification(
                user_ids=responsible_user_ids,
                message_type="workflow_exception",
                title="客户审核整改项",
                content=f"客户审核 {audit.customer_name} 的整改项已分配，请及时处理"
            )
```

## Frontend Component Designs

### 质量数据面板组件

```vue
<!-- frontend/src/views/QualityDashboard.vue -->
<template>
  <div class="quality-dashboard">
    <!-- 指标卡片 -->
    <el-row :gutter="20">
      <el-col :span="6" v-for="metric in metrics" :key="metric.name">
        <MetricCard
          :name="metric.name"
          :value="metric.value"
          :target="metric.target"
          :trend="metric.trend"
          :status="metric.status"
          @click="handleMetricClick(metric)"
        />
      </el-col>
    </el-row>
    
    <!-- 图表区域 -->
    <el-row :gutter="20" class="chart-section">
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>来料批次合格率趋势</span>
              <el-date-picker
                v-model="dateRange"
                type="daterange"
                @change="handleDateChange"
              />
            </div>
          </template>
          <LineChart :data="incomingPassRateData" :options="chartOptions" />
        </el-card>
      </el-col>
      
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>Top5 不良供应商</span>
          </template>
          <BarChart :data="top5SuppliersData" />
        </el-card>
      </el-col>
    </el-row>
    
    <!-- AI 对话框 -->
    <el-button
      class="ai-chat-trigger"
      type="primary"
      circle
      @click="showAIChat = true"
    >
      <el-icon><ChatDotRound /></el-icon>
    </el-button>
    
    <AIChatDialog v-model="showAIChat" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getQualityMetrics } from '@/api/quality'
import MetricCard from '@/components/MetricCard.vue'
import LineChart from '@/components/charts/LineChart.vue'
import BarChart from '@/components/charts/BarChart.vue'
import AIChatDialog from '@/components/AIChatDialog.vue'

const metrics = ref([])
const dateRange = ref([])
const showAIChat = ref(false)

onMounted(async () => {
  await loadMetrics()
})

const loadMetrics = async () => {
  const data = await getQualityMetrics()
  metrics.value = data.metrics
}

const handleMetricClick = (metric) => {
  // 跳转到问题清单页面
  router.push({
    name: 'ProblemList',
    query: { metric: metric.name }
  })
}
</script>
```

### 8D 报告填写组件

```vue
<!-- frontend/src/views/Report8D.vue -->
<template>
  <div class="report-8d">
    <el-steps :active="currentStep" finish-status="success">
      <el-step title="D0 组建团队" />
      <el-step title="D1 问题描述" />
      <el-step title="D2 围堵措施" />
      <el-step title="D3 根本原因" />
      <el-step title="D4 纠正措施" />
      <el-step title="D5 验证" />
      <el-step title="D6 预防措施" />
      <el-step title="D7 标准化" />
      <el-step title="D8 水平展开" />
    </el-steps>
    
    <el-form :model="formData" ref="formRef" :rules="rules">
      <!-- D0 -->
      <div v-show="currentStep === 0">
        <el-form-item label="团队成员" prop="d0_team_members">
          <el-input
            v-model="formData.d0_team_members"
            type="textarea"
            :rows="4"
            placeholder="请输入团队成员姓名和职责"
          />
        </el-form-item>
      </div>
      
      <!-- D1 -->
      <div v-show="currentStep === 1">
        <el-form-item label="问题描述（5W2H）" prop="d1_problem_description">
          <el-input
            v-model="formData.d1_problem_description"
            type="textarea"
            :rows="6"
            placeholder="What, When, Where, Who, Why, How, How Many"
          />
        </el-form-item>
      </div>
      
      <!-- D2 -->
      <div v-show="currentStep === 2">
        <el-form-item label="围堵措施" prop="d2_containment_actions">
          <el-input
            v-model="formData.d2_containment_actions"
            type="textarea"
            :rows="4"
          />
        </el-form-item>
        
        <el-form-item label="覆盖范围">
          <el-checkbox-group v-model="formData.d2_coverage">
            <el-checkbox label="in_transit">在途品</el-checkbox>
            <el-checkbox label="inventory">库存品</el-checkbox>
            <el-checkbox label="customer">客户端库存</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
      </div>
      
      <!-- ... 其他步骤 -->
      
      <!-- D8 -->
      <div v-show="currentStep === 8">
        <el-form-item label="水平展开" prop="d8_horizontal_deployment">
          <el-input
            v-model="formData.d8_horizontal_deployment"
            type="textarea"
            :rows="4"
          />
        </el-form-item>
        
        <el-form-item label="经验教训">
          <el-checkbox v-model="formData.d8_save_to_library">
            沉淀到经验教训库
          </el-checkbox>
          
          <el-input
            v-if="formData.d8_save_to_library"
            v-model="formData.d8_lesson_summary"
            type="textarea"
            :rows="3"
            placeholder="请总结经验教训"
          />
        </el-form-item>
      </div>
    </el-form>
    
    <div class="form-actions">
      <el-button @click="prevStep" v-if="currentStep > 0">上一步</el-button>
      <el-button type="primary" @click="nextStep" v-if="currentStep < 8">
        下一步
      </el-button>
      <el-button type="success" @click="submitReport" v-if="currentStep === 8">
        提交报告
      </el-button>
    </div>
    
    <!-- AI 预审结果对话框 -->
    <el-dialog v-model="showAIReview" title="AI 预审结果">
      <el-alert
        v-if="!aiReviewResult.approved"
        type="warning"
        title="AI 发现以下问题"
        :closable="false"
      />
      
      <div v-for="issue in aiReviewResult.auto_issues" :key="issue.step">
        <p><strong>{{ issue.step }}:</strong> {{ issue.issue }}</p>
        <p class="suggestion">建议：{{ issue.suggestion }}</p>
      </div>
      
      <div class="ai-feedback">
        <h4>AI 综合评价：</h4>
        <p>{{ aiReviewResult.ai_feedback }}</p>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { submit8DReport } from '@/api/supplier'
import { ElMessage } from 'element-plus'

const currentStep = ref(0)
const formData = ref({})
const showAIReview = ref(false)
const aiReviewResult = ref({})

const submitReport = async () => {
  const result = await submit8DReport(formData.value)
  
  if (!result.success) {
    // AI 预审未通过
    aiReviewResult.value = result
    showAIReview.value = true
  } else {
    ElMessage.success('8D 报告提交成功，等待 SQE 审核')
    router.push('/supplier/scars')
  }
}
</script>
```

## Summary

本设计文档详细描述了 QMS 质量管理系统的技术架构和实现方案，涵盖：

1. **系统架构**: DMZ 部署、分层架构、容器化方案
2. **核心组件**: 12 个核心组件的详细设计，包括基础设施和业务模块
3. **数据模型**: 完整的数据库设计和 ER 关系
4. **业务流程**: 供应商质量、过程质量、客户质量、新品质量、审核管理的完整流程
5. **前端组件**: 关键页面的组件设计
6. **错误处理**: 统一的异常处理机制
7. **测试策略**: 单元测试、集成测试、E2E 测试
8. **部署方案**: Docker Compose 配置
9. **安全措施**: 10 项安全考虑

系统采用现代化的技术栈，支持高并发、异步任务处理、AI 增强，能够满足汽车电子制造行业的质量管理需求。

