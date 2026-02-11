# Implementation Plan - QMS Foundation & Authentication Module

本实施计划将 QMS 质量管理系统基础架构与认证授权模块的设计转化为可执行的开发任务。任务按照从基础设施到核心功能的顺序组织，分为 Phase 1 (Core) 和 Phase 2 (Reserved) 两个阶段。

## 任务执行说明

- 每个任务都引用了对应的需求编号（Requirements: X.X）
- 标记为 `*` 的子任务为可选任务（如单元测试），可根据项目进度决定是否实施
- Phase 1 为核心功能，必须完成
- Phase 2 为预留功能（仪器量具管理、质量成本管理），当前阶段仅预留数据库表结构和 API 接口
- 建议按顺序执行任务，避免依赖问题

---

## Phase 1: 核心功能实现 (Core Features)

### 1. 项目基础设施搭建

- [x] 1.1 初始化 Monorepo 项目结构
  - 创建根目录结构：backend/, frontend/, deployment/
  - 创建 .env.example 环境变量模板（包含 DB_PASSWORD, REDIS_PASSWORD, SECRET_KEY, IMS_BASE_URL, OPENAI_API_KEY, SMTP_SERVER）
  - 编写 README.md 项目说明文档（包含双轨发布架构说明）
  - 创建 .gitignore 文件
  - _Requirements: 2.1.1, 2.12.1_

- [x] 1.2 配置双轨 Docker Compose 环境
  - 创建 docker-compose.yml，定义以下服务：
    - postgres: PostgreSQL 15+ 数据库（共享数据底座）
    - redis: Redis 7+ 缓存/队列
    - backend-stable: 正式环境后端容器
    - backend-preview: 预览环境后端容器
    - frontend-stable: 正式环境前端容器
    - frontend-preview: 预览环境前端容器
    - nginx: 反向代理网关
    - celery-worker: 异步任务处理
    - celery-beat: 定时任务调度
  - 配置容器间网络连接（qms_network）
  - 配置数据卷持久化（postgres_data, redis_data）
  - _Requirements: 2.12.1, 2.12.2_


- [x] 1.3 配置 Nginx 双轨路由分发
  - 创建 deployment/nginx/nginx.conf 配置文件
  - 配置正式环境路由：qms.company.com -> frontend-stable, /api -> backend-stable
  - 配置预览环境路由：preview.company.com -> frontend-preview, /api -> backend-preview
  - 配置 SSL 证书路径（生产环境）
  - 设置文件上传大小限制（client_max_body_size 50M）
  - 配置静态文件缓存策略
  - _Requirements: 2.12.1, 2.12.2_

- [x] 1.4 配置后端开发环境
  - 初始化 FastAPI 项目结构（app/api/, app/core/, app/models/, app/schemas/, app/services/）
  - 创建 requirements.txt 依赖包：
    - FastAPI, Uvicorn (ASGI 服务器)
    - SQLAlchemy 2.0+ (Async ORM)
    - Alembic (数据库迁移)
    - Pydantic V2 (数据校验)
    - Python-Jose (JWT)
    - Passlib + bcrypt (密码哈希)
    - LDAP3 (预留 SSO 集成)
    - Redis, Celery (任务队列)
    - HTTPX (IMS 集成)
    - aiosmtplib (邮件发送)
  - 创建 backend/Dockerfile 容器构建文件
  - 配置 Alembic 数据库迁移工具（alembic.ini, alembic/env.py）
  - 创建 app/core/config.py 配置管理模块（读取环境变量）
  - _Requirements: 2.1.5, 2.12.2_

- [ ] 1.5 配置前端开发环境
  - 使用 Vite 初始化 Vue 3 项目（Composition API）
  - 安装依赖包：
    - Element Plus (桌面端 UI 组件库)
    - Tailwind CSS (移动端响应式布局)
    - ECharts (图表可视化)
    - Axios (HTTP 客户端)
    - Pinia (状态管理)
    - Vue Router (路由管理)
  - 创建 frontend/Dockerfile 容器构建文件
  - 配置 Vue Router 路由结构（router/index.ts）
  - 创建基础布局组件（layouts/MainLayout.vue, layouts/MobileLayout.vue）
  - 配置 Tailwind CSS（tailwind.config.js）
  - _Requirements: 2.1.7, 2.12.1_


### 2. 数据库设计与核心模型

- [ ] 2.1 设计用户与权限数据模型
  - 创建 backend/app/models/user.py User 模型
    - 字段：id, username, password_hash, email, phone, full_name
    - 用户类型：user_type (internal/supplier)
    - 内部员工字段：department, position
    - 供应商字段：supplier_id (FK)
    - 账号状态：status (pending/active/frozen/rejected)
    - 电子签名：digital_signature (图片路径)
    - 安全字段：failed_login_attempts, locked_until, password_changed_at
    - 审计字段：created_at, updated_at, created_by, updated_by
  - 创建 backend/app/models/permission.py Permission 模型
    - 字段：id, user_id (FK), module_path, operation_type, is_granted
    - 操作类型枚举：create, read, update, delete, export
    - 唯一约束：(user_id, module_path, operation_type)
  - 创建 backend/app/models/supplier.py Supplier 模型
    - 字段：id, name, code, contact_person, contact_email, contact_phone
    - 资质字段：iso9001_cert, iso9001_expiry, iatf16949_cert, iatf16949_expiry
    - 状态：status (pending/active/suspended)
  - _Requirements: 2.1.1, 2.1.3, 2.1.4_

- [ ] 2.2 设计通知与日志数据模型
  - 创建 backend/app/models/notification.py Notification 模型
    - 字段：id, user_id (FK), message_type, title, content, link
    - 状态：is_read, read_at
    - 消息类型枚举：workflow_exception, system_alert, warning
  - 创建 backend/app/models/operation_log.py OperationLog 模型
    - 字段：id, user_id (FK), operation_type, target_module, target_id
    - 数据快照：before_data (JSON), after_data (JSON)
    - 请求信息：ip_address, user_agent, created_at
  - 创建 backend/app/models/announcement.py Announcement 模型
    - 字段：id, title, content, announcement_type, importance
    - 状态：is_active, published_at, expires_at
  - _Requirements: 2.1.4, 2.2.4, 2.2.5_

- [ ] 2.3 设计功能特性开关数据模型
  - 创建 backend/app/models/feature_flag.py FeatureFlag 模型
    - 字段：id, feature_key, feature_name, description
    - 开关状态：is_enabled, scope (global/whitelist)
    - 白名单：whitelist_user_ids (JSON Array), whitelist_supplier_ids (JSON Array)
    - 环境标识：environment (stable/preview)
    - 审计字段：created_at, updated_at, created_by
  - _Requirements: 2.12.3_


- [ ] 2.4 设计系统配置数据模型
  - 创建 backend/app/models/system_config.py SystemConfig 模型
    - 字段：id, config_key, config_value (JSON), config_type, description
    - 配置分类：category (business_rule/timeout/file_limit/notification)
    - 验证规则：validation_rule (JSON Schema)
    - 审计字段：created_at, updated_at, updated_by
  - _Requirements: 2.3.2_

- [ ] 2.5 执行数据库迁移（兼容双轨环境）
  - 使用 Alembic 生成初始迁移脚本：alembic revision --autogenerate -m "Initial schema"
  - 验证迁移脚本符合非破坏性原则：
    - 新增字段必须设置为 Nullable 或带有 Default Value
    - 禁止删除字段、重命名字段、修改字段类型
  - 执行迁移：alembic upgrade head
  - 验证表结构和关系完整性
  - 创建数据库索引优化查询性能
  - _Requirements: 2.12.2_

### 3. 认证授权与权限引擎

- [ ] 3.1 实现可插拔认证策略（Strategy Pattern）
  - 创建 backend/app/core/auth_strategy.py 认证策略接口
    - 定义 AuthStrategy 抽象基类：
      - authenticate(username, password) -> User
      - create_access_token(user_id) -> str
      - verify_token(token) -> dict
  - 实现 LocalAuthStrategy（Phase 1 核心功能）：
    - 使用 Passlib + bcrypt 进行密码哈希
    - 使用 Python-Jose 生成 JWT Token（24 小时有效期）
    - 实现密码复杂度验证（大写、小写、数字、特殊字符中至少三种，长度>8位）
    - 实现登录失败锁定机制（连续 5 次错误锁定 30 分钟）
    - 实现密码定期修改策略（90 天强制修改）
  - 预留 LDAPAuthStrategy（Phase 2 预留）：
    - 创建类结构和接口定义
    - 方法体抛出 NotImplementedError
    - 添加注释说明 LDAP 集成逻辑
  - 创建 AuthService 统一认证服务：
    - 根据用户类型选择认证策略
    - 内部员工：优先使用 LocalAuthStrategy（预留 LDAP 切换逻辑）
    - 供应商：使用 LocalAuthStrategy + 图形验证码
  - _Requirements: 2.1.5_


- [ ] 3.2 实现用户注册与审核 API
  - 创建 backend/app/schemas/user.py Pydantic 数据校验模型
    - UserRegisterSchema: 注册表单校验
    - UserApprovalSchema: 审核操作校验
  - 创建 backend/app/api/v1/auth.py 认证路由
  - 实现 POST /api/v1/auth/register 注册接口：
    - 验证用户名唯一性
    - 供应商用户：验证供应商名称必须从 Supplier 表中选择（模糊搜索 API）
    - 创建状态为 "pending" 的用户记录
    - 密码哈希存储
  - 实现 GET /api/v1/auth/suppliers/search?q={keyword} 供应商模糊搜索接口
  - _Requirements: 2.1.3_

- [ ] 3.3 实现统一登录 API（多入口支持）
  - 实现 POST /api/v1/auth/login 登录接口：
    - 接收参数：username, password, user_type (internal/supplier), captcha (供应商必填)
    - 验证用户名和密码
    - 供应商登录：验证图形验证码
    - 检查账号状态（active/frozen/pending）
    - 检查密码是否需要强制修改（首次登录或超过 90 天）
    - 生成 JWT Token
    - 记录登录日志（last_login_at, ip_address）
  - 实现 GET /api/v1/auth/captcha 图形验证码生成接口
  - 实现 GET /api/v1/auth/me 获取当前用户信息接口
  - 创建 get_current_user 依赖注入函数（从 JWT Token 提取用户）
  - _Requirements: 2.1.5_

- [ ] 3.4 实现权限引擎核心逻辑
  - 创建 backend/app/core/permissions.py 权限引擎
  - 实现 PermissionChecker 类：
    - check_permission(user_id, module_path, operation) -> bool
    - get_user_permissions(user_id) -> dict（用于前端菜单渲染）
    - filter_by_supplier(user, queryset)（供应商数据隔离）
  - 实现 require_permission 装饰器：
    - 集成到 FastAPI 路由依赖注入
    - 权限不足返回 403 错误
  - 实现权限缓存机制（Redis）：
    - 缓存用户权限列表（1 小时过期）
    - 权限更新时清除缓存
  - _Requirements: 2.1.1_


- [ ] 3.5 实现权限配置管理 API
  - 创建 backend/app/api/v1/admin/permissions.py 权限管理路由
  - 实现 GET /api/v1/admin/permissions/matrix 获取权限矩阵：
    - 返回用户列表和功能-操作组合
    - 标识每个用户的权限授予状态
  - 实现 PUT /api/v1/admin/permissions/grant 授予权限：
    - 批量授予权限（支持多个用户、多个权限）
    - 实时生效（清除 Redis 缓存）
  - 实现 PUT /api/v1/admin/permissions/revoke 撤销权限
  - 实现 GET /api/v1/admin/permissions/users/{user_id} 获取用户权限详情
  - _Requirements: 2.1.1_

- [ ] 3.6 实现用户审核管理 API
  - 创建 backend/app/api/v1/admin/users.py 用户管理路由
  - 实现 GET /api/v1/admin/users/pending 获取待审核用户列表
  - 实现 POST /api/v1/admin/users/{id}/approve 批准用户：
    - 更新状态为 "active"
    - 发送激活通知邮件
  - 实现 POST /api/v1/admin/users/{id}/reject 拒绝用户：
    - 更新状态为 "rejected"
    - 记录拒绝原因
  - 实现 POST /api/v1/admin/users/{id}/freeze 冻结账号
  - 实现 POST /api/v1/admin/users/{id}/unfreeze 解冻账号
  - 实现 POST /api/v1/admin/users/{id}/reset-password 重置密码：
    - 生成临时密码
    - 发送邮件通知
    - 强制下次登录修改
  - _Requirements: 2.1.3, 2.3.3_

- [ ] 3.7 实现操作日志审计
  - 创建 backend/app/core/audit_middleware.py 审计中间件
  - 拦截所有 POST/PUT/DELETE 请求：
    - 记录操作人、操作时间、操作类型
    - 记录目标对象（模块、ID）
    - 记录数据快照（before_data, after_data）
    - 记录请求信息（IP、User-Agent）
  - 创建 backend/app/api/v1/admin/operation_logs.py 操作日志路由
  - 实现 GET /api/v1/admin/operation-logs 获取日志列表：
    - 支持按用户、操作类型、时间范围、目标模块筛选
    - 分页查询
  - 实现 GET /api/v1/admin/operation-logs/{id} 获取日志详情：
    - 展示数据变更 diff 对比
  - _Requirements: 2.1.4_


### 4. 个人中心与通知系统

- [ ] 4.1 实现任务聚合服务
  - 创建 backend/app/services/task_aggregator.py 任务聚合服务
  - 实现 TaskAggregator 类：
    - get_user_tasks(user_id) -> List[TaskItem]
    - 从各业务表聚合待办任务（SCAR、8D 报告、审核整改项等）
    - _calculate_urgency(deadline) -> str（overdue/urgent/normal）
    - _calculate_remaining(deadline) -> float（剩余小时数）
  - 配置业务表映射：
    - 定义 BUSINESS_TABLES 配置列表
    - 每个配置包含：table, handler_field, task_type, deadline_field, link_pattern
  - 创建 backend/app/api/v1/tasks.py 任务管理路由
  - 实现 GET /api/v1/tasks/my-tasks 获取当前用户待办任务
  - _Requirements: 2.2.3_

- [ ] 4.2 实现任务转派功能
  - 实现 POST /api/v1/admin/tasks/reassign 批量转派任务：
    - 接收参数：from_user_id, to_user_id, task_ids
    - 更新各业务表的 current_handler_id
    - 发送通知给新的处理人
  - 实现 GET /api/v1/admin/tasks/statistics 任务统计：
    - 按部门统计待办任务数量
    - 按人员统计待办任务数量
    - 统计逾期任务清单
  - _Requirements: 2.3.1_

- [ ] 4.3 实现通知中心服务
  - 创建 backend/app/services/notification.py 通知中心服务
  - 实现 NotificationHub 类：
    - send_notification(user_ids, message_type, title, content, link)
    - send_email(to_emails, subject, body, attachments)（使用 aiosmtplib）
    - send_wechat_work(user_ids, message)（预留企业微信集成）
    - mark_as_read(notification_id)
    - mark_all_as_read(user_id)
    - get_unread_count(user_id) -> int
  - 创建 backend/app/api/v1/notifications.py 通知路由
  - 实现 GET /api/v1/notifications 获取站内信列表：
    - 支持按消息类型筛选
    - 分页查询
  - 实现 GET /api/v1/notifications/unread-count 获取未读消息数量
  - 实现 PUT /api/v1/notifications/{id}/read 标记单条消息为已读
  - 实现 PUT /api/v1/notifications/read-all 一键标记全部已读
  - _Requirements: 2.2.4_


- [ ] 4.4 实现个人信息管理 API
  - 创建 backend/app/api/v1/profile.py 个人信息路由
  - 实现 GET /api/v1/profile 获取个人信息
  - 实现 PUT /api/v1/profile/password 修改密码：
    - 验证旧密码
    - 应用密码策略（复杂度、长度）
    - 更新 password_changed_at
    - 强制重新登录
  - 实现 POST /api/v1/profile/signature 上传电子签名：
    - 接收图片文件（PNG/JPG）
    - 自动处理图片背景透明化（使用 Pillow）
    - 存储到文件系统
    - 更新 digital_signature 字段
  - _Requirements: 2.2.2_

- [ ] 4.5 实现公告栏管理
  - 创建 backend/app/api/v1/announcements.py 公告路由
  - 实现 GET /api/v1/announcements 获取公告列表：
    - 按发布时间倒序
    - 过滤有效期内的公告
  - 实现 POST /api/v1/admin/announcements 创建公告：
    - 设置公告类型（system/quality_warning/document_update）
    - 设置重要性标记（normal/important）
    - 设置有效期
  - 实现 POST /api/v1/announcements/{id}/read 记录阅读：
    - 创建阅读记录（user_id, announcement_id, read_at）
  - 实现 GET /api/v1/admin/announcements/{id}/statistics 查看阅读统计：
    - 已读人数、未读人数
    - 阅读人员清单
  - _Requirements: 2.2.5_

- [ ] 4.6 实现消息通知配置管理
  - 创建 backend/app/models/notification_rule.py NotificationRule 模型
    - 字段：id, rule_name, trigger_object, trigger_condition, action_type
    - 升级策略：timeout_hours, escalation_recipients
    - 通道配置：email_enabled, wechat_enabled
  - 创建 backend/app/api/v1/admin/notification_rules.py 通知规则路由
  - 实现 POST /api/v1/admin/notification-rules 创建通知规则
  - 实现 PUT /api/v1/admin/notification-rules/{id} 更新通知规则
  - 实现 POST /api/v1/admin/notification-rules/test 测试通知规则
  - 实现 POST /api/v1/admin/smtp-config 配置 SMTP 服务器：
    - 验证连接有效性
  - 实现 POST /api/v1/admin/webhook-config 配置企业微信/钉钉 Webhook：
    - 验证可达性
  - _Requirements: 2.3.2_


### 5. 功能特性开关与系统配置

- [ ] 5.1 实现功能特性开关服务
  - 创建 backend/app/services/feature_flag_service.py 功能开关服务
  - 实现 FeatureFlagService 类：
    - is_feature_enabled(feature_key, user_id, supplier_id) -> bool
    - update_feature_flag(feature_key, is_enabled, scope, whitelist)
    - get_all_feature_flags() -> List[FeatureFlag]
  - 实现开关逻辑：
    - 全局开关：所有用户生效
    - 白名单机制：仅指定用户/供应商可见
    - 环境隔离：区分 stable/preview 环境
  - 创建 backend/app/api/v1/admin/feature_flags.py 功能开关路由
  - 实现 GET /api/v1/admin/feature-flags 获取功能开关列表
  - 实现 PUT /api/v1/admin/feature-flags/{id} 更新功能开关
  - 实现 GET /api/v1/feature-flags/my-features 获取当前用户可用功能列表
  - _Requirements: 2.12.3_

- [ ] 5.2 实现系统全局配置管理
  - 创建 backend/app/api/v1/admin/system_config.py 系统配置路由
  - 实现 GET /api/v1/admin/system-config 获取所有配置项
  - 实现 PUT /api/v1/admin/system-config/{key} 更新配置项：
    - 验证参数格式和取值范围（使用 JSON Schema）
    - 立即生效（清除 Redis 缓存）
  - 实现配置分类管理：
    - 业务规则（business_rule）
    - 超时时长（timeout）
    - 文件大小限制（file_limit）
    - 通知配置（notification）
  - 实现配置默认值机制：
    - 配置缺失时使用预设默认值
    - 记录警告日志
  - _Requirements: 2.3.2_

### 6. 前端基础组件开发

- [ ] 6.1 实现前端认证与路由
  - 创建 frontend/src/stores/auth.ts Pinia 状态管理
    - 定义 useAuthStore：token, userInfo, isAuthenticated
    - 实现 login(username, password, userType)
    - 实现 logout()
    - 实现 checkPermission(modulePath, operation)
  - 创建 frontend/src/utils/request.ts Axios 封装
    - 请求拦截器：自动添加 Authorization Header
    - 响应拦截器：统一处理错误（401/403/500）
  - 创建 frontend/src/router/index.ts 路由配置
    - 实现路由守卫：验证 Token 有效性
    - 未登录用户重定向到登录页
    - 根据权限动态渲染菜单
  - _Requirements: 2.1.5_


- [ ] 6.2 实现登录注册页面（多入口支持）
  - 创建 frontend/src/views/Login.vue 登录页面
    - 桌面端布局（Element Plus）：
      - 用户类型选择：员工登录 / 供应商登录
      - 员工登录：账号密码 + SSO 登录按钮（预留，当前禁用）
      - 供应商登录：账号密码 + 图形验证码
      - 记住密码功能
    - 移动端布局（Tailwind CSS）：
      - 响应式表单
      - 大号输入框和按钮
  - 创建 frontend/src/views/Register.vue 注册页面
    - 公司用户注册表单：用户名、姓名、电话、邮箱、部门（下拉）、职位
    - 供应商用户注册表单：用户名、姓名、电话、邮箱、供应商名称（模糊搜索）、职位
    - 实现供应商名称模糊搜索组件（SupplierSearch.vue）
    - 表单校验（用户名、密码、邮箱格式）
  - 调用后端注册和登录 API
  - 存储 JWT Token 到 localStorage
  - _Requirements: 2.1.3, 2.1.5_

- [ ] 6.3 实现个人中心页面（动态工作台）
  - 创建 frontend/src/views/PersonalCenter.vue 个人中心页面
  - 实现个人信息模块：
    - 展示头像、姓名、部门、职位
    - 修改密码对话框
    - 电子签名上传组件（支持拖拽上传）
  - 实现待办任务列表：
    - 创建 frontend/src/components/TaskCard.vue 任务卡片组件
    - 紧急程度颜色标识：红色（已超期）/ 黄色（即将超期）/ 绿色（正常）
    - 剩余时间倒计时显示
    - 点击跳转到对应单据详情页
  - 实现内部员工视图：
    - 指标全景监控（预留接口）
    - 待办任务聚合
  - 实现供应商视图：
    - 绩效红绿灯（预留接口）
    - 需要行动的任务卡片
  - _Requirements: 2.1.6, 2.2.1, 2.2.2, 2.2.3_

- [ ] 6.4 实现站内信通知组件
  - 创建 frontend/src/components/NotificationBell.vue 铃铛图标组件
    - 未读消息数量红点标识
    - 点击展开站内信列表弹窗
  - 创建 frontend/src/components/NotificationList.vue 站内信列表组件
    - 按消息类型筛选（流程异常/系统提醒/预警通知）
    - 已读/未读状态标识
    - 一键标记全部已读功能
    - 点击消息跳转到对应页面
  - _Requirements: 2.2.4_


- [ ] 6.5 实现公告栏组件
  - 创建 frontend/src/components/AnnouncementList.vue 公告列表组件
    - 按发布时间倒序展示
    - 未读公告置顶并高亮显示
  - 创建 frontend/src/components/AnnouncementDialog.vue 重要公告弹窗
    - 登录后自动弹出未读重要公告
    - 强制阅读（点击"我已阅读"后记录）
  - _Requirements: 2.2.5_

- [ ] 6.6 实现系统管理后台页面
  - 创建 frontend/src/views/admin/UserApproval.vue 用户审核页面
    - 待审核用户列表展示
    - 批准/拒绝操作
    - 拒绝原因输入对话框
  - 创建 frontend/src/views/admin/PermissionMatrix.vue 权限矩阵配置页面
    - 网格化权限矩阵展示（行：用户，列：功能-操作）
    - 复选框勾选/取消授予权限
    - 实时保存权限配置
  - 创建 frontend/src/views/admin/TaskMonitor.vue 任务统计页面
    - 待办分布图（柱状图/饼图，使用 ECharts）
    - 逾期任务清单展示
    - 批量转派功能
  - 创建 frontend/src/views/admin/OperationLogs.vue 操作日志页面
    - 日志列表展示和筛选
    - 日志详情对话框（含 diff 对比）
  - 创建 frontend/src/views/admin/FeatureFlags.vue 功能开关管理页面
    - 功能开关列表展示
    - 开关状态切换
    - 白名单配置
  - _Requirements: 2.1.1, 2.1.3, 2.1.4, 2.3.1, 2.3.3, 2.12.3_

- [ ] 6.7 实现移动端响应式适配
  - 配置 Tailwind CSS 断点：
    - sm: 640px（手机）
    - md: 768px（平板）
    - lg: 1024px（桌面）
  - 实现响应式布局组件：
    - 移动端自动折叠左侧菜单栏
    - 放大操作按钮和输入框（适应手指触控）
  - 实现扫码页面全屏模式（预留接口）：
    - 隐藏顶部导航和底部版权信息
    - 全屏显示扫描框
  - 实现离线暂存模式（预留接口）：
    - 使用 localStorage 暂存数据
    - 网络恢复后自动同步
  - _Requirements: 2.1.7_


### 7. 环境切换与版本管理

- [ ] 7.1 实现环境切换功能
  - 在前端顶部导航栏添加环境切换按钮：
    - 正式环境显示"切换到预览版"按钮
    - 预览环境显示"切换到正式版"按钮
  - 实现环境切换逻辑：
    - 切换域名（qms.company.com <-> preview.company.com）
    - 保持登录状态（Token 共享）
  - 添加环境标识：
    - 预览环境顶部显示醒目的"预览版"标识
  - _Requirements: 2.12.1_

- [ ] 7.2 实现数据库兼容性验证
  - 创建 Alembic 迁移脚本验证工具：
    - 检查新增字段是否设置为 Nullable 或带有 Default Value
    - 检测禁止操作（删除字段、重命名字段、修改字段类型）
    - 生成兼容性报告
  - 在 CI/CD 流程中集成验证：
    - 预览环境部署前自动验证迁移脚本
    - 不符合规范的迁移阻止部署
  - _Requirements: 2.12.2_

### 8. 测试与部署

- [ ]* 8.1 编写后端单元测试（可选）
  - 创建 backend/tests/test_auth.py 认证模块测试
    - 测试用户注册、登录、Token 验证
    - 测试密码策略、登录锁定机制
  - 创建 backend/tests/test_permissions.py 权限模块测试
    - 测试权限检查逻辑
    - 测试数据隔离过滤器
  - 创建 backend/tests/test_task_aggregator.py 任务聚合测试
    - 测试待办任务聚合
    - 测试紧急程度计算
  - _Requirements: 2.1.1, 2.1.5, 2.2.3_

- [ ]* 8.2 编写前端单元测试（可选）
  - 创建 frontend/tests/unit/TaskCard.spec.ts 任务卡片组件测试
  - 创建 frontend/tests/unit/NotificationBell.spec.ts 通知组件测试
  - 创建 frontend/tests/e2e/login.spec.ts E2E 登录流程测试
  - _Requirements: 2.1.5, 2.2.3, 2.2.4_


- [ ] 8.3 部署准备与优化
  - 配置生产环境变量：
    - 创建 .env.production 文件
    - 配置数据库连接字符串（PostgreSQL）
    - 配置 Redis 连接字符串
    - 配置 IMS API 地址（内网）
    - 配置 SMTP 邮件服务器
    - 配置 JWT Secret Key
  - 配置 SSL 证书：
    - 申请 SSL 证书（qms.company.com, preview.company.com）
    - 配置 Nginx SSL 证书路径
    - 强制 HTTPS 重定向
  - 配置数据库备份策略：
    - 配置 PostgreSQL 自动备份脚本（每日备份）
    - 设置备份保留策略（至少 30 天）
  - 性能优化：
    - 配置 Redis 缓存策略（权限缓存、配置缓存）
    - 优化数据库查询索引
    - 配置 Nginx 静态文件缓存
  - _Requirements: 2.12.1_

- [ ] 8.4 执行生产环境部署
  - 使用 Docker Compose 启动所有服务：
    - docker-compose up -d --build
  - 验证所有容器正常运行：
    - docker-compose ps
  - 执行数据库迁移：
    - docker-compose exec backend-stable alembic upgrade head
    - docker-compose exec backend-preview alembic upgrade head
  - 验证双轨环境访问：
    - 访问 https://qms.company.com（正式环境）
    - 访问 https://preview.company.com（预览环境）
  - 功能验证测试：
    - 验证用户注册和登录
    - 验证权限控制
    - 验证通知发送
    - 验证环境切换
  - _Requirements: 2.12.1, 2.12.2_

---

## Phase 2: 预留功能接口 (Reserved Features)

### 9. 仪器与量具管理（预留）

- [ ] 9.1 创建仪器量具数据模型（预留表结构）
  - 创建 backend/app/models/instrument.py Instrument 模型
    - 字段：id, instrument_code, instrument_name, instrument_type
    - 校准信息：calibration_date, next_calibration_date, calibration_cert_path
    - 状态：status (active/frozen/expired)
    - 所有字段设置为 Nullable（兼容双轨环境）
  - 创建 backend/app/models/msa_record.py MSARecord 模型
    - 字段：id, instrument_id (FK), msa_type, msa_date, msa_result
    - 报告：msa_report_path
    - 所有字段设置为 Nullable
  - 执行数据库迁移（仅创建表结构，不实现业务逻辑）
  - _Requirements: 2.11（预留功能）_


- [ ] 9.2 预留仪器量具管理 API 接口
  - 创建 backend/app/api/v1/instruments.py 仪器量具路由（空实现）
  - 定义 API 接口签名（不实现业务逻辑）：
    - GET /api/v1/instruments 获取仪器量具列表
    - POST /api/v1/instruments 创建仪器量具
    - PUT /api/v1/instruments/{id} 更新仪器量具
    - POST /api/v1/instruments/{id}/calibration 记录校准
    - POST /api/v1/instruments/{id}/msa 记录 MSA 分析
  - 所有接口返回 501 Not Implemented
  - 添加注释说明预留用途
  - _Requirements: 2.11（预留功能）_

- [ ] 9.3 预留仪器量具管理前端页面
  - 创建 frontend/src/views/Instruments.vue 仪器量具管理页面（空页面）
  - 添加菜单入口（默认隐藏）
  - 通过功能开关控制可见性
  - _Requirements: 2.11（预留功能）_

### 10. 质量成本管理（预留）

- [ ] 10.1 创建质量成本数据模型（预留表结构）
  - 创建 backend/app/models/quality_cost.py QualityCost 模型
    - 字段：id, cost_type, cost_category, amount, currency
    - 关联：related_object_type, related_object_id
    - 时间：cost_date, fiscal_year, fiscal_month
    - 所有字段设置为 Nullable（兼容双轨环境）
  - 创建 backend/app/models/cost_analysis.py CostAnalysis 模型
    - 字段：id, analysis_type, analysis_period, total_cost
    - 分析结果：analysis_result (JSON)
    - 所有字段设置为 Nullable
  - 执行数据库迁移（仅创建表结构，不实现业务逻辑）
  - _Requirements: 2.12（预留功能）_

- [ ] 10.2 预留质量成本管理 API 接口
  - 创建 backend/app/api/v1/quality_costs.py 质量成本路由（空实现）
  - 定义 API 接口签名（不实现业务逻辑）：
    - GET /api/v1/quality-costs 获取质量成本列表
    - POST /api/v1/quality-costs 创建质量成本记录
    - GET /api/v1/quality-costs/analysis 获取成本分析
    - GET /api/v1/quality-costs/trend 获取成本趋势
  - 所有接口返回 501 Not Implemented
  - 添加注释说明预留用途
  - _Requirements: 2.12（预留功能）_

- [ ] 10.3 预留质量成本管理前端页面
  - 创建 frontend/src/views/QualityCosts.vue 质量成本管理页面（空页面）
  - 添加菜单入口（默认隐藏）
  - 通过功能开关控制可见性
  - _Requirements: 2.12（预留功能）_

---

## 总结

本实施计划共包含 **10 个主要任务组**，分为 Phase 1（核心功能）和 Phase 2（预留功能）两个阶段：

### Phase 1: 核心功能实现（必须完成）
1. 项目基础设施搭建（双轨 Docker 环境、Nginx 路由分发）
2. 数据库设计与核心模型（用户、权限、通知、功能开关）
3. 认证授权与权限引擎（可插拔策略、多入口登录、细粒度权限）
4. 个人中心与通知系统（任务聚合、站内信、公告栏）
5. 功能特性开关与系统配置（灰度发布、白名单机制）
6. 前端基础组件开发（登录注册、个人中心、管理后台、移动端适配）
7. 环境切换与版本管理（双轨切换、数据库兼容性验证）
8. 测试与部署（单元测试、生产环境部署）

### Phase 2: 预留功能接口（仅预留表结构和 API）
9. 仪器与量具管理（预留）
10. 质量成本管理（预留）

**预估开发周期**：
- Phase 1（核心功能）：4-6 周
- Phase 2（预留功能）：1 周

**总计**：约 5-7 周

**关键技术要点**：
- 双轨发布架构：Preview & Stable 容器并行运行，共享 PostgreSQL 数据库
- 数据库兼容性：遵循 Alembic 非破坏性迁移原则（Add Column Only）
- 可插拔认证：Strategy Pattern 设计，Phase 1 实现 Local Auth，预留 LDAP Auth
- 移动端适配：Element Plus（桌面）+ Tailwind CSS（移动）响应式策略
- 功能开关：支持灰度发布和白名单机制

**下一步行动**：
开始执行 Phase 1 任务，建议按顺序执行，确保每个步骤都建立在前一步的基础上。
