# Implementation Plan

本实施计划将 QMS 质量管理系统的设计转化为可执行的开发任务。任务按照从基础设施到业务功能的顺序组织，确保每个步骤都建立在前一步的基础上。

## 任务执行说明

- 每个任务都引用了对应的需求编号（Requirements: X.X）
- 标记为 `*` 的子任务为可选任务（如单元测试），可根据项目进度决定是否实施
- 核心实现任务必须完成，以确保系统功能完整性
- 建议按顺序执行任务，避免依赖问题

---

## Phase 1: 项目基础设施搭建

- [ ] 1. 初始化项目结构和开发环境
  - 创建 Monorepo 目录结构（backend/, frontend/, deployment/）
  - 配置 Docker Compose 编排文件，定义 PostgreSQL、Redis、Backend、Frontend、Nginx 服务
  - 创建 .env.example 环境变量模板文件
  - 编写 README.md 项目说明文档
  - _Requirements: 10.1, 10.2, 10.3, 10.4_

- [ ] 2. 配置后端开发环境
  - 初始化 FastAPI 项目结构（app/api/, app/core/, app/models/, app/services/）
  - 配置 requirements.txt 依赖包（FastAPI, SQLAlchemy, Pydantic, Redis, Celery, httpx）
  - 创建 backend/Dockerfile 容器构建文件
  - 配置 Alembic 数据库迁移工具
  - 创建 app/core/config.py 配置管理模块
  - _Requirements: 10.5, 10.6_

- [ ] 3. 配置前端开发环境
  - 使用 Vite 初始化 Vue 3 项目
  - 安装 Element Plus、ECharts、Axios、Pinia 依赖
  - 创建 frontend/Dockerfile 容器构建文件
  - 配置 Vue Router 路由结构
  - 创建基础布局组件（MainLayout.vue）
  - _Requirements: 10.1_


- [ ] 4. 配置 Nginx 反向代理
  - 创建 deployment/nginx/nginx.conf 配置文件
  - 配置 API 路由转发规则（/api -> backend:8000）
  - 配置前端静态文件服务（/ -> frontend:3000）
  - 配置 SSL 证书路径（生产环境）
  - 设置文件上传大小限制（client_max_body_size 50M）
  - _Requirements: 10.4_

---

## Phase 2: 数据库设计与核心模型

- [ ] 5. 设计并实现用户与权限数据模型
- [ ] 5.1 创建 User 模型
  - 实现 backend/app/models/user.py，包含用户基本信息、用户类型、账号状态字段
  - 定义 company 和 supplier 两种用户类型的枚举
  - 添加 digital_signature 电子签名字段
  - 建立与 Supplier 的外键关系
  - _Requirements: 1.1, 1.2, 5.4, 5.5_

- [ ] 5.2 创建 Permission 模型
  - 实现 backend/app/models/permission.py，定义权限矩阵结构
  - 创建 user_id, module, operation, granted 字段
  - 添加唯一约束（user_id + module + operation）
  - _Requirements: 2.1, 2.2_

- [ ] 5.3 创建 Supplier 模型
  - 实现 backend/app/models/supplier.py，包含供应商基本信息和资质文件字段
  - 添加 ISO9001、IATF16949 证书路径和有效期字段
  - 定义供应商状态枚举（pending, active, suspended）
  - _Requirements: 1.3, 16.1, 16.2_

- [ ] 5.4 创建 Notification 和 OperationLog 模型
  - 实现 backend/app/models/notification.py 站内信模型
  - 实现 backend/app/models/operation_log.py 操作日志模型
  - 定义消息类型枚举和操作类型枚举
  - _Requirements: 3.1, 6.1, 6.2_


- [ ] 6. 设计并实现供应商质量管理数据模型
- [ ] 6.1 创建 SCAR 和 Report8D 模型
  - 实现 backend/app/models/scar.py 供应商纠正措施请求单模型
  - 实现 backend/app/models/report_8d.py 8D 报告模型（D0-D8 各步骤字段）
  - 添加 AI 预审结果 JSON 字段
  - 建立 SCAR 与 Report8D 的 1:1 关系
  - _Requirements: 14.2, 15.2, 15.3_

- [ ] 6.2 创建供应商绩效和质量目标模型
  - 实现 backend/app/models/supplier_performance.py 绩效评价模型
  - 实现 backend/app/models/supplier_quality_target.py 质量目标模型
  - 添加扣分明细 JSON 字段
  - _Requirements: 17.8, 17.9, 17.17_

- [ ] 6.3 创建 PPAP 和审核相关模型
  - 实现 backend/app/models/ppap.py PPAP 管理模型
  - 实现 backend/app/models/audit.py 审核计划和记录模型
  - 实现 backend/app/models/nc_item.py 不符合项模型
  - _Requirements: 16.6, 16.8, 29.1, 31.1_

- [ ] 7. 设计并实现质量数据和业务流程模型
- [ ] 7.1 创建质量数据集成模型
  - 实现 backend/app/models/incoming_inspection.py 入库检验模型
  - 实现 backend/app/models/process_defect.py 制程不合格品模型
  - 实现 backend/app/models/shipment.py 出货记录模型
  - 实现 backend/app/models/complaint.py 客诉记录模型
  - _Requirements: 11.1, 19.2, 21.1, 22.1_

- [ ] 7.2 创建新品质量管理模型
  - 实现 backend/app/models/new_product_project.py 新品项目模型
  - 实现 backend/app/models/lesson_learned.py 经验教训库模型
  - 实现 backend/app/models/trial_production.py 试产记录模型
  - _Requirements: 25.1, 27.1, 28.1_

- [ ] 8. 执行数据库迁移
  - 使用 Alembic 生成初始迁移脚本
  - 执行迁移创建所有数据表
  - 验证表结构和关系完整性
  - _Requirements: 10.5_


---

## Phase 3: 认证授权与权限引擎

- [ ] 9. 实现安全管理器和认证模块
- [ ] 9.1 实现密码哈希和 JWT Token 生成
  - 创建 backend/app/core/security.py 安全管理器
  - 实现 hash_password() 使用 bcrypt 进行密码哈希
  - 实现 verify_password() 验证密码
  - 实现 create_access_token() 生成 JWT Token（24 小时有效期）
  - 实现 verify_token() 验证 Token 有效性
  - _Requirements: 1.5, 5.2, 5.3_

- [ ] 9.2 实现用户注册 API
  - 创建 backend/app/schemas/user.py Pydantic 数据校验模型
  - 创建 backend/app/api/v1/auth.py 认证路由
  - 实现 POST /api/v1/auth/register 注册接口
  - 验证供应商名称必须从 Supplier_Registry 中选择
  - 创建状态为"待审核"的用户记录
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [ ] 9.3 实现用户登录 API
  - 实现 POST /api/v1/auth/login 登录接口
  - 验证用户名和密码
  - 检查账号状态（已激活/已冻结）
  - 生成并返回 JWT Token
  - _Requirements: 1.5, 8.2_

- [ ] 9.4 实现当前用户信息 API
  - 实现 GET /api/v1/auth/me 获取当前用户信息接口
  - 创建 get_current_user 依赖注入函数
  - 从 JWT Token 中提取用户 ID 并查询用户信息
  - _Requirements: 5.1_


- [ ] 10. 实现权限引擎
- [ ] 10.1 实现权限检查核心逻辑
  - 创建 backend/app/core/permissions.py 权限引擎
  - 实现 check_permission() 检查用户是否具有指定权限
  - 实现 get_user_permissions() 获取用户所有权限
  - 实现 filter_by_supplier() 供应商数据隔离过滤器
  - _Requirements: 2.4, 2.5, 2.6_

- [ ] 10.2 实现权限装饰器
  - 创建 require_permission() 装饰器函数
  - 集成到 FastAPI 路由中进行权限验证
  - 返回 403 错误当权限不足时
  - _Requirements: 2.4, 2.5_

- [ ] 10.3 实现权限配置 API
  - 创建 backend/app/api/v1/permissions.py 权限管理路由
  - 实现 GET /api/v1/permissions/matrix 获取权限矩阵
  - 实现 PUT /api/v1/permissions/grant 授予权限
  - 实现 PUT /api/v1/permissions/revoke 撤销权限
  - 确保权限配置实时生效
  - _Requirements: 2.2, 2.3, 2.7_

- [ ] 11. 实现用户审核管理
- [ ] 11.1 实现用户审核 API
  - 创建 backend/app/api/v1/admin/users.py 用户管理路由
  - 实现 GET /api/v1/admin/users/pending 获取待审核用户列表
  - 实现 POST /api/v1/admin/users/{id}/approve 批准用户
  - 实现 POST /api/v1/admin/users/{id}/reject 拒绝用户
  - 发送激活通知邮件
  - _Requirements: 1.6, 1.7, 1.8_

- [ ] 11.2 实现账号生命周期管理 API
  - 实现 POST /api/v1/admin/users/{id}/freeze 冻结账号
  - 实现 POST /api/v1/admin/users/{id}/unfreeze 解冻账号
  - 实现 POST /api/v1/admin/users/{id}/reset-password 重置密码
  - _Requirements: 8.1, 8.2, 8.3, 8.4_


- [ ] 12. 实现操作日志审计
- [ ] 12.1 创建操作日志中间件
  - 创建 backend/app/core/audit_middleware.py 审计中间件
  - 拦截所有 POST/PUT/DELETE 请求
  - 记录操作人、操作时间、操作类型、目标对象、数据快照
  - _Requirements: 3.1_

- [ ] 12.2 实现操作日志查询 API
  - 创建 backend/app/api/v1/admin/operation_logs.py 操作日志路由
  - 实现 GET /api/v1/admin/operation-logs 获取操作日志列表
  - 支持按用户、操作类型、时间范围、目标模块筛选
  - 实现 GET /api/v1/admin/operation-logs/{id} 获取日志详情（含 diff 对比）
  - _Requirements: 3.2, 3.3, 3.4_

---

## Phase 4: 个人中心与通知系统

- [ ] 13. 实现任务聚合器
- [ ] 13.1 实现任务聚合服务
  - 创建 backend/app/services/task_aggregator.py 任务聚合服务
  - 实现 get_user_tasks() 从各业务模块聚合待办任务
  - 实现 _calculate_urgency() 计算紧急程度（已超期/即将超期/正常）
  - 实现 _calculate_remaining() 计算剩余处理时间
  - _Requirements: 4.2, 4.3, 4.4, 4.5, 4.6_

- [ ] 13.2 实现任务聚合 API
  - 创建 backend/app/api/v1/tasks.py 任务管理路由
  - 实现 GET /api/v1/tasks/my-tasks 获取当前用户待办任务
  - 返回任务类型、单据编号、紧急程度、剩余时间、跳转链接
  - _Requirements: 4.2, 4.3, 4.7_

- [ ] 13.3 实现任务转派功能
  - 实现 POST /api/v1/admin/tasks/reassign 批量转派任务
  - 更新任务的 Current_Handler_ID
  - 发送通知给新的处理人
  - _Requirements: 9.4, 9.5_


- [ ] 14. 实现通知中心
- [ ] 14.1 实现通知服务
  - 创建 backend/app/services/notification.py 通知中心服务
  - 实现 send_notification() 发送站内信
  - 实现 send_email() 发送邮件（使用 aiosmtplib）
  - 实现 send_wechat_work() 发送企业微信消息
  - 实现 mark_as_read() 标记为已读
  - 实现 mark_all_as_read() 一键标记全部已读
  - _Requirements: 6.1, 6.5, 6.6_

- [ ] 14.2 实现通知 API
  - 创建 backend/app/api/v1/notifications.py 通知路由
  - 实现 GET /api/v1/notifications 获取站内信列表
  - 实现 GET /api/v1/notifications/unread-count 获取未读消息数量
  - 实现 PUT /api/v1/notifications/{id}/read 标记单条消息为已读
  - 实现 PUT /api/v1/notifications/read-all 一键标记全部已读
  - 支持按消息类型筛选
  - _Requirements: 6.2, 6.3, 6.4, 6.5, 6.6_

- [ ] 15. 实现个人信息管理
- [ ] 15.1 实现个人信息 API
  - 创建 backend/app/api/v1/profile.py 个人信息路由
  - 实现 GET /api/v1/profile 获取个人信息
  - 实现 PUT /api/v1/profile/password 修改密码
  - 实现 POST /api/v1/profile/signature 上传电子签名
  - 实现图片背景透明化处理
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ] 16. 实现公告栏管理
- [ ] 16.1 实现公告 API
  - 创建 backend/app/api/v1/announcements.py 公告路由
  - 实现 GET /api/v1/announcements 获取公告列表
  - 实现 POST /api/v1/admin/announcements 创建公告
  - 实现 POST /api/v1/announcements/{id}/read 记录阅读
  - 实现 GET /api/v1/admin/announcements/{id}/statistics 查看阅读统计
  - _Requirements: 7.1, 7.2, 7.4, 7.6_


---

## Phase 5: 前端基础组件开发

- [ ] 17. 实现前端认证与路由
- [ ] 17.1 实现登录注册页面
  - 创建 frontend/src/views/Login.vue 登录页面
  - 创建 frontend/src/views/Register.vue 注册页面
  - 实现表单校验（用户名、密码、邮箱格式）
  - 实现供应商名称模糊搜索组件
  - 调用后端注册和登录 API
  - 存储 JWT Token 到 localStorage
  - _Requirements: 1.1, 1.2, 1.3, 1.5_

- [ ] 17.2 实现路由守卫和权限控制
  - 创建 frontend/src/router/index.ts 路由配置
  - 实现路由守卫验证 Token 有效性
  - 实现权限检查，根据用户权限动态渲染菜单
  - 未登录用户重定向到登录页
  - _Requirements: 2.4, 2.5_

- [ ] 17.3 实现 Axios 请求拦截器
  - 创建 frontend/src/utils/request.ts HTTP 客户端
  - 实现请求拦截器自动添加 Authorization Header
  - 实现响应拦截器统一处理错误（401/403/500）
  - _Requirements: 1.5, 2.5_

- [ ] 18. 实现个人中心页面
- [ ] 18.1 实现个人中心布局
  - 创建 frontend/src/views/PersonalCenter.vue 个人中心页面
  - 实现个人信息展示模块（头像、姓名、部门、职位）
  - 实现修改密码对话框
  - 实现电子签名上传组件
  - _Requirements: 4.1, 5.1, 5.2, 5.4, 5.5_

- [ ] 18.2 实现待办任务列表
  - 创建 frontend/src/components/TaskCard.vue 任务卡片组件
  - 实现紧急程度颜色标识（红色/黄色/绿色）
  - 实现剩余时间倒计时显示
  - 实现点击跳转到对应单据详情页
  - _Requirements: 4.3, 4.4, 4.5, 4.6, 4.7_


- [ ] 18.3 实现站内信通知组件
  - 创建 frontend/src/components/NotificationBell.vue 铃铛图标组件
  - 实现未读消息数量红点标识
  - 实现站内信列表弹窗
  - 实现按消息类型筛选
  - 实现一键标记全部已读功能
  - _Requirements: 6.2, 6.3, 6.4, 6.5, 6.6_

- [ ] 18.4 实现公告栏组件
  - 创建 frontend/src/components/AnnouncementList.vue 公告列表组件
  - 实现重要公告弹窗强制阅读
  - 实现未读公告置顶高亮显示
  - _Requirements: 7.2, 7.3, 7.5_

- [ ] 19. 实现系统管理后台页面
- [ ] 19.1 实现用户审核管理页面
  - 创建 frontend/src/views/admin/UserApproval.vue 用户审核页面
  - 实现待审核用户列表展示
  - 实现批准/拒绝操作
  - 实现拒绝原因输入对话框
  - _Requirements: 1.6, 1.7, 1.8_

- [ ] 19.2 实现权限配置页面
  - 创建 frontend/src/views/admin/PermissionMatrix.vue 权限矩阵配置页面
  - 实现网格化权限矩阵展示（行：用户，列：功能-操作）
  - 实现复选框勾选/取消授予权限
  - 实现实时保存权限配置
  - _Requirements: 2.2, 2.3_

- [ ] 19.3 实现任务统计监控页面
  - 创建 frontend/src/views/admin/TaskMonitor.vue 任务统计页面
  - 实现待办分布图（柱状图/饼图）
  - 实现逾期任务清单展示
  - 实现批量转派功能
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [ ] 19.4 实现操作日志查询页面
  - 创建 frontend/src/views/admin/OperationLogs.vue 操作日志页面
  - 实现日志列表展示和筛选
  - 实现日志详情对话框（含 diff 对比）
  - _Requirements: 3.2, 3.3, 3.4_


---

## Phase 6: IMS 数据集成与质量指标计算

- [ ] 20. 实现 IMS 数据集成服务
- [ ] 20.1 实现 IMS 数据同步服务
  - 创建 backend/app/services/ims_integration.py IMS 集成服务
  - 实现 sync_incoming_inspection_data() 同步入库检验数据
  - 实现 sync_production_data() 同步生产数据
  - 实现 sync_shipment_data() 同步出货数据
  - 实现数据清洗和存储逻辑
  - _Requirements: 11.1, 14.1, 19.1, 21.1_

- [ ] 20.2 实现自动立案逻辑
  - 实现 _auto_create_scar() 自动生成 SCAR 单
  - 监测 IMS 检验结果为"不合格"时触发
  - 发送通知给供应商
  - _Requirements: 14.2, 14.3_

- [ ] 20.3 配置 Celery 定时任务
  - 创建 backend/app/core/celery.py Celery 配置
  - 实现 @celery_app.task 装饰器定义定时任务
  - 配置每日凌晨 02:00 同步 IMS 数据
  - _Requirements: 11.1_

- [ ] 21. 实现质量指标计算服务
- [ ] 21.1 实现指标计算核心逻辑
  - 创建 backend/app/services/quality_metrics.py 质量指标计算服务
  - 实现 calculate_incoming_pass_rate() 计算来料批次合格率
  - 实现 calculate_online_defect_ppm() 计算物料上线不良 PPM
  - 实现 calculate_process_defect_rate() 计算制程不合格率
  - 实现 calculate_0km_ppm() 计算 0KM 不良 PPM
  - 实现 calculate_rolling_mis_ppm() 计算滚动 MIS PPM
  - _Requirements: 11.2, 11.4, 11.6, 11.8, 11.10, 11.12_

- [ ] 21.2 实现多维度统计
  - 支持按供应商、按日、按月、按年度统计
  - 支持按物料类型、按责任类别、按产品类型分类统计
  - _Requirements: 11.3, 11.5, 11.7, 11.9, 11.11, 11.13_

- [ ] 21.3 配置指标计算定时任务
  - 实现 calculate_daily_metrics() 每日计算质量指标
  - 将计算结果存储到 Redis 缓存（24 小时过期）
  - _Requirements: 11.1_


- [ ] 22. 实现质量数据面板 API
- [ ] 22.1 实现质量指标查询 API
  - 创建 backend/app/api/v1/quality.py 质量数据路由
  - 实现 GET /api/v1/quality/metrics 获取质量指标
  - 实现 GET /api/v1/quality/metrics/trend 获取指标趋势数据
  - 实现 GET /api/v1/quality/top5-suppliers 获取 Top5 供应商清单
  - 支持按时间范围、类型筛选
  - _Requirements: 12.1, 12.2, 13.1, 13.2_

- [ ] 22.2 实现专项数据分析 API
  - 实现 GET /api/v1/quality/analysis/supplier 供应商质量数据分析
  - 实现 GET /api/v1/quality/analysis/process 制程质量数据分析
  - 实现 GET /api/v1/quality/analysis/customer 客户质量数据分析
  - _Requirements: 13.3, 13.4_

- [ ] 23. 实现质量数据面板前端页面
- [ ] 23.1 实现质量数据面板布局
  - 创建 frontend/src/views/QualityDashboard.vue 质量数据面板页面
  - 实现指标卡片组件（MetricCard.vue）
  - 实现质量红绿灯显示（达标绿色/未达标红色）
  - 实现点击指标跳转到问题清单
  - _Requirements: 12.1, 12.2, 12.5, 12.6, 12.7_

- [ ] 23.2 实现图表组件
  - 创建 frontend/src/components/charts/LineChart.vue 折线图组件
  - 创建 frontend/src/components/charts/BarChart.vue 柱状图组件
  - 集成 ECharts 库
  - 实现时间调整按钮和类型切换按钮
  - _Requirements: 12.3, 12.4_

- [ ] 23.3 实现 Top5 供应商清单展示
  - 创建 frontend/src/components/Top5Suppliers.vue 组件
  - 实现来料批次合格率 Top5 展示
  - 实现物料上线不良 PPM Top5 展示
  - _Requirements: 13.1, 13.2_


---

## Phase 7: AI 诊断引擎集成

- [ ] 24. 实现 AI 诊断引擎
- [ ] 24.1 实现 AI 服务核心逻辑
  - 创建 backend/app/services/ai_diagnostic.py AI 诊断引擎
  - 配置 OpenAI API 客户端（支持 DeepSeek 等兼容 API）
  - 实现 analyze_anomaly() 异常归因分析
  - 实现 review_8d_report() 8D 报告预审
  - 实现 natural_language_query() 自然语言查询
  - _Requirements: 13.5, 13.6, 15.4, 15.5, 13.8_

- [ ] 24.2 实现 AI 诊断 API
  - 创建 backend/app/api/v1/ai.py AI 诊断路由
  - 实现 POST /api/v1/ai/analyze-anomaly 异常分析接口
  - 实现 POST /api/v1/ai/review-8d 8D 报告预审接口
  - 实现 POST /api/v1/ai/query 自然语言查询接口
  - _Requirements: 13.5, 13.6, 15.4, 15.5, 13.7, 13.8_

- [ ] 24.3 实现 AI 对话框前端组件
  - 创建 frontend/src/components/AIChatDialog.vue AI 对话框组件
  - 实现自然语言输入框
  - 实现查询结果展示（数据表格 + 图表）
  - 集成到质量数据面板页面
  - _Requirements: 13.7, 13.8_

---

## Phase 8: 供应商质量管理模块

- [ ] 25. 实现 SCAR 和 8D 报告管理
- [ ] 25.1 实现 SCAR 管理 API
  - 创建 backend/app/api/v1/scars.py SCAR 管理路由
  - 实现 GET /api/v1/scars 获取 SCAR 单列表（供应商数据隔离）
  - 实现 POST /api/v1/scars 创建 SCAR 单
  - 实现 GET /api/v1/scars/{id} 获取 SCAR 单详情
  - _Requirements: 14.2, 15.1_

- [ ] 25.2 实现 8D 报告提交 API
  - 创建 backend/app/api/v1/reports_8d.py 8D 报告路由
  - 实现 POST /api/v1/reports-8d 提交 8D 报告
  - 集成 AI 预审逻辑
  - 实现 PUT /api/v1/reports-8d/{id} 更新 8D 报告
  - _Requirements: 15.2, 15.3, 15.4, 15.5_

- [ ] 25.3 实现 SQE 审核 8D 报告 API
  - 实现 POST /api/v1/reports-8d/{id}/approve 批准 8D 报告
  - 实现 POST /api/v1/reports-8d/{id}/reject 驳回 8D 报告
  - 更新 SCAR 状态为"已关闭"或退回供应商
  - _Requirements: 15.7, 15.8, 15.9_


- [ ] 25.4 实现 8D 报告填写前端页面
  - 创建 frontend/src/views/Report8D.vue 8D 报告填写页面
  - 实现 D0-D8 步骤表单（使用 el-steps 组件）
  - 实现文件上传组件（改善前后对比图）
  - 实现 AI 预审结果对话框展示
  - _Requirements: 15.2, 15.3, 15.4, 15.5_

- [ ] 25.5 实现 SCAR 列表和详情页面
  - 创建 frontend/src/views/SCARList.vue SCAR 列表页面
  - 创建 frontend/src/views/SCARDetail.vue SCAR 详情页面
  - 实现供应商数据隔离（仅显示关联供应商的 SCAR）
  - 实现 SQE 审核操作（批准/驳回）
  - _Requirements: 15.1, 15.7, 15.8_

- [ ] 26. 实现供应商审核管理
- [ ] 26.1 实现供应商准入审核 API
  - 创建 backend/app/api/v1/suppliers.py 供应商管理路由
  - 实现 POST /api/v1/suppliers 创建供应商（上传资质文件）
  - 实现 POST /api/v1/suppliers/{id}/approve 批准供应商
  - 实现 POST /api/v1/suppliers/{id}/reject 驳回供应商
  - 实现证书有效期自动识别和预警
  - _Requirements: 16.1, 16.2, 16.3, 16.4_

- [ ] 26.2 实现供应商变更管理 API
  - 实现 POST /api/v1/suppliers/{id}/pcn 提交 PCN 变更申请
  - 实现 POST /api/v1/suppliers/{id}/pcn/{pcn_id}/evaluate 评估变更
  - 实现 POST /api/v1/suppliers/{id}/pcn/{pcn_id}/approve 批准变更
  - 要求供应商上传断点信息
  - _Requirements: 16.5, 16.6_

- [ ] 26.3 实现年度审核计划和执行 API
  - 创建 backend/app/api/v1/audits.py 审核管理路由
  - 实现 POST /api/v1/audits/plans 创建年度审核计划
  - 实现 POST /api/v1/audits 开始审核
  - 实现 POST /api/v1/audits/{id}/nc-items 录入不符合项
  - 实现 POST /api/v1/audits/{id}/complete 完成审核
  - 配置每月 1 号自动触发审核流程
  - _Requirements: 16.7, 16.8, 29.1, 29.2_


- [ ] 27. 实现供应商质量目标与绩效评价
- [ ] 27.1 实现质量目标设定 API
  - 创建 backend/app/api/v1/supplier_targets.py 质量目标路由
  - 实现 POST /api/v1/supplier-targets/batch 批量设置质量目标
  - 实现 POST /api/v1/supplier-targets/individual 单独设置质量目标
  - 实现目标优先级逻辑（单独 > 批量 > 全局默认）
  - 实现目标倒退风险提示
  - _Requirements: 17.1, 17.2, 17.3, 17.4, 17.5_

- [ ] 27.2 实现供应商签署质量目标 API
  - 实现 POST /api/v1/supplier-targets/{id}/sign 供应商签署目标
  - 记录签署时间并生效目标版本
  - 创建"待签署质量目标"任务
  - _Requirements: 17.6, 17.7_

- [ ] 27.3 实现绩效评价计算服务
  - 创建 backend/app/services/supplier_performance.py 绩效评价服务
  - 实现 calculate_monthly_performance() 计算月度绩效
  - 实现 60 分制扣分逻辑（来料质量、制程质量、配合度、客诉质量）
  - 实现折算为百分制并评定等级（A/B/C/D）
  - _Requirements: 17.8, 17.9, 17.10, 17.11, 17.12, 17.13, 17.14, 17.17_

- [ ] 27.4 实现绩效评价 API
  - 创建 backend/app/api/v1/supplier_performance.py 绩效评价路由
  - 实现 GET /api/v1/supplier-performance 获取绩效评价列表
  - 实现 POST /api/v1/supplier-performance/{id}/review SQE 复核绩效
  - 实现 PUT /api/v1/supplier-performance/{id}/cooperation SQE 填写配合度评价
  - 配置每月 1 日自动计算绩效
  - _Requirements: 17.15, 17.16, 17.17_

- [ ] 27.5 实现改善会议管理 API
  - 实现 POST /api/v1/supplier-meetings 创建改善会议任务
  - 实现 POST /api/v1/supplier-meetings/{id}/upload-report 供应商上传改善报告
  - 实现 POST /api/v1/supplier-meetings/{id}/record-minutes SQE 录入会议纪要
  - 实现违规处罚逻辑（未参会/未提交报告额外扣分）
  - 当绩效为 C/D 级时自动生成会议任务
  - _Requirements: 18.1, 18.2, 18.3, 18.4, 18.5_


- [ ] 28. 实现 PPAP 管理
- [ ] 28.1 实现 PPAP 提交管理 API
  - 创建 backend/app/api/v1/ppap.py PPAP 管理路由
  - 实现 POST /api/v1/ppap 创建 PPAP 提交任务
  - 实现 POST /api/v1/ppap/{id}/upload 供应商上传 PPAP 文件
  - 实现 POST /api/v1/ppap/{id}/approve SQE 审核 PPAP
  - 实现 POST /api/v1/ppap/{id}/reject SQE 驳回 PPAP
  - 内置标准 18 项 PPAP 文件检查表
  - _Requirements: 18.6, 18.7, 18.8, 18.9, 18.10_

- [ ] 28.2 实现 PPAP 年度再鉴定
  - 监控 PPAP 批准日期，满 1 年自动生成"年度产品审核"任务
  - _Requirements: 18.11_

---

## Phase 9: 过程质量管理模块

- [ ] 29. 实现过程质量数据管理
- [ ] 29.1 实现不合格品录入 API
  - 创建 backend/app/api/v1/process_defects.py 过程质量路由
  - 实现 POST /api/v1/process-defects 录入不合格品数据
  - 实现 GET /api/v1/process-defects 获取不合格品列表
  - 支持按产线、工单号、日期、责任类别筛选
  - _Requirements: 19.2, 19.3, 19.4, 19.7_

- [ ] 29.2 实现制程质量问题发单 API
  - 创建 backend/app/api/v1/improvement_tasks.py 整改任务路由
  - 实现 POST /api/v1/improvement-tasks 发起整改任务
  - 实现 POST /api/v1/improvement-tasks/{id}/submit 提交整改措施
  - 实现 POST /api/v1/improvement-tasks/{id}/verify PQE 验证整改效果
  - 根据责任类别自动推荐责任人
  - _Requirements: 20.1, 20.2, 20.3, 20.4, 20.5, 20.6, 20.7, 20.8_

- [ ] 29.3 实现过程质量前端页面
  - 创建 frontend/src/views/ProcessDefects.vue 不合格品管理页面
  - 创建 frontend/src/views/ImprovementTasks.vue 整改任务页面
  - 实现不合格品录入表单
  - 实现整改任务发起和跟踪
  - _Requirements: 19.3, 20.1, 20.3_


---

## Phase 10: 客户质量管理模块

- [ ] 30. 实现客诉管理
- [ ] 30.1 实现客诉录入 API
  - 创建 backend/app/api/v1/complaints.py 客诉管理路由
  - 实现 POST /api/v1/complaints 录入客诉
  - 实现 GET /api/v1/complaints 获取客诉列表
  - 实现 GET /api/v1/complaints/{id} 获取客诉详情
  - 支持 0KM 和 MIS 客诉类型
  - 实现自动追溯查询 IMS 系统
  - _Requirements: 22.1, 22.2, 22.3, 22.4, 22.6, 22.7_

- [ ] 30.2 实现 8D 闭环管理 API
  - 实现 POST /api/v1/complaints/{id}/d0-d3 CQE 完成 D0-D3
  - 实现 POST /api/v1/complaints/{id}/d4-d8 责任板块完成 D4-D8
  - 实现 POST /api/v1/complaints/{id}/approve 审批 8D 报告
  - 实现 POST /api/v1/complaints/{id}/reject 驳回 8D 报告
  - 实现分级审批流（C 级：科室经理；A/B 级：质量部长 + 责任部门部长）
  - _Requirements: 22.5, 23.1, 23.2, 23.3, 23.4, 23.5, 23.6, 23.7, 23.8, 23.9, 23.10, 23.11, 23.12, 23.13, 23.14, 23.15_

- [ ] 30.3 实现索赔管理 API
  - 创建 backend/app/api/v1/claims.py 索赔管理路由
  - 实现 POST /api/v1/claims 创建客户索赔
  - 实现 POST /api/v1/claims/{id}/transfer-to-supplier 转嫁供应商索赔
  - 实现多选关联客户索赔与问题清单
  - _Requirements: 24.1, 24.2, 24.3, 24.4, 24.5_

- [ ] 30.4 实现客诉管理前端页面
  - 创建 frontend/src/views/Complaints.vue 客诉列表页面
  - 创建 frontend/src/views/ComplaintDetail.vue 客诉详情页面
  - 实现客诉录入表单
  - 实现 8D 报告填写和审批流程
  - 实现索赔管理界面
  - _Requirements: 22.1, 23.1, 24.1_

---

## Phase 11: 新品质量管理模块

- [ ] 31. 实现经验教训管理
- [ ] 31.1 实现经验教训库 API
  - 创建 backend/app/api/v1/lessons_learned.py 经验教训路由
  - 实现 GET /api/v1/lessons-learned 获取经验教训库
  - 实现 POST /api/v1/lessons-learned 新增经验教训
  - 实现 PUT /api/v1/lessons-learned/{id} 更新经验教训
  - 实现 DELETE /api/v1/lessons-learned/{id} 删除经验教训
  - _Requirements: 25.1, 25.2_


- [ ] 31.2 实现经验教训反向注入 API
  - 创建 backend/app/api/v1/new_product_projects.py 新品项目路由
  - 实现 POST /api/v1/new-product-projects 创建新品项目
  - 实现 GET /api/v1/new-product-projects/{id}/lessons 获取推送的经验教训
  - 实现 POST /api/v1/new-product-projects/{id}/lessons/{lesson_id}/check 点检经验教训
  - 要求逐条勾选"是否规避"并上传证据
  - _Requirements: 25.3, 25.4, 25.5, 25.6, 25.7_

- [ ] 32. 实现阶段评审管理
- [ ] 32.1 实现阶段评审 API
  - 实现 POST /api/v1/new-product-projects/{id}/gate-reviews 提交阶段评审
  - 实现 GET /api/v1/new-product-projects/{id}/gate-reviews 获取评审记录
  - 实现 POST /api/v1/new-product-projects/{id}/gate-reviews/{review_id}/approve 批准评审
  - 验证必需交付物和经验教训点检完成情况
  - 锁定项目进度直到交付物齐全
  - _Requirements: 26.1, 26.2, 26.3, 26.4, 26.5_

- [ ] 33. 实现试产管理
- [ ] 33.1 实现试产目标与实绩管理 API
  - 创建 backend/app/api/v1/trial_production.py 试产管理路由
  - 实现 POST /api/v1/trial-production 创建试产记录
  - 实现 POST /api/v1/trial-production/{id}/sync-ims 同步 IMS 工单数据
  - 实现 POST /api/v1/trial-production/{id}/manual-data 手动录入 CPK 等数据
  - 实现 GET /api/v1/trial-production/{id}/summary 生成试产总结报告
  - 自动对比目标值与实绩值（红绿灯显示）
  - _Requirements: 27.1, 27.2, 27.3, 27.4, 27.5, 27.6, 27.7, 27.8, 27.9_

- [ ] 33.2 实现试产问题跟进 API
  - 实现 POST /api/v1/trial-production/{id}/issues 录入试产问题
  - 实现 POST /api/v1/trial-production/{id}/issues/{issue_id}/resolve 关闭问题
  - 实现 POST /api/v1/trial-production/{id}/issues/{issue_id}/escalate 升级为 8D 报告
  - 实现 SOP 节点带病量产特批流程
  - _Requirements: 28.1, 28.2, 28.3, 28.4, 28.5, 28.6_


---

## Phase 12: 审核管理模块

- [ ] 34. 实现审核计划与排程
- [ ] 34.1 实现审核计划管理 API
  - 实现 POST /api/v1/audits/plans 创建年度审核计划
  - 实现 GET /api/v1/audits/plans 获取审核计划列表
  - 实现 POST /api/v1/audits/plans/{id}/delay 提交延期申请
  - 配置提前 7 天邮件提醒
  - _Requirements: 29.1, 29.2, 29.3, 29.4, 29.5_

- [ ] 35. 实现数字化检查表
- [ ] 35.1 实现检查表模板管理 API
  - 创建 backend/app/api/v1/audit_templates.py 检查表模板路由
  - 实现 GET /api/v1/audit-templates 获取模板列表
  - 实现 POST /api/v1/audit-templates 创建自定义模板
  - 预置 VDA_6_3、VDA 6.5、IATF16949 检查条款库
  - _Requirements: 30.1, 30.2_

- [ ] 35.2 实现在线打分 API
  - 实现 POST /api/v1/audits/{id}/start 开始审核
  - 实现 POST /api/v1/audits/{id}/check-items/{item_id} 录入检查项结果
  - 实现 POST /api/v1/audits/{id}/complete 完成审核并自动评分
  - 支持移动端访问
  - 支持现场拍照上传
  - 根据 VDA_6_3 规则自动计算得分和等级
  - 自动生成审核报告 PDF
  - _Requirements: 30.3, 30.4, 30.5, 30.6, 30.7_

- [ ] 36. 实现审核问题整改闭环
- [ ] 36.1 实现不符合项管理 API
  - 实现 POST /api/v1/audits/{id}/nc-items/{nc_id}/assign 指派不符合项
  - 实现 POST /api/v1/audits/{id}/nc-items/{nc_id}/submit 提交整改措施
  - 实现 POST /api/v1/audits/{id}/nc-items/{nc_id}/verify 验证整改效果
  - 自动将 NG 条款转化为 NC_Item 待办任务
  - 设定整改期限并自动跟催
  - _Requirements: 31.1, 31.2, 31.3, 31.4, 31.5, 31.6, 31.7_

- [ ] 37. 实现二方审核管理
- [ ] 37.1 实现二方审核 API
  - 实现 POST /api/v1/audits/second-party 创建二方审核记录
  - 实现 POST /api/v1/audits/second-party/{id}/upload-nc-list 上传客户问题清单
  - 实现解析 Excel 文件并创建内部跟踪任务
  - 建立客户审核台账
  - _Requirements: 32.1, 32.2, 32.3, 32.4, 32.5_


---

## Phase 13: 前端业务模块页面开发

- [ ] 38. 实现供应商质量管理前端页面
- [ ] 38.1 实现供应商绩效评价页面
  - 创建 frontend/src/views/SupplierPerformance.vue 绩效评价页面
  - 实现绩效评价列表展示
  - 实现 SQE 复核和配合度评价功能
  - 实现绩效详情查看（扣分明细）
  - _Requirements: 17.15, 17.16_

- [ ] 38.2 实现供应商质量目标管理页面
  - 创建 frontend/src/views/SupplierTargets.vue 质量目标管理页面
  - 实现批量设置和单独设置目标
  - 实现目标倒退风险提示
  - 实现供应商签署目标功能
  - _Requirements: 17.1, 17.4, 17.5, 17.6_

- [ ] 38.3 实现供应商审核管理页面
  - 创建 frontend/src/views/SupplierAudits.vue 供应商审核页面
  - 实现审核计划管理
  - 实现审核记录查看
  - 实现不符合项跟踪
  - _Requirements: 16.7, 16.8, 16.9, 16.10_

- [ ] 38.4 实现 PPAP 管理页面
  - 创建 frontend/src/views/PPAP.vue PPAP 管理页面
  - 实现 PPAP 提交任务创建
  - 实现文件上传和审核
  - 实现 18 项文件检查表展示
  - _Requirements: 18.6, 18.7, 18.8, 18.9_

- [ ] 39. 实现审核管理前端页面
- [ ] 39.1 实现审核计划管理页面
  - 创建 frontend/src/views/AuditPlans.vue 审核计划页面
  - 实现年度审核计划创建和查看
  - 实现延期申请功能
  - _Requirements: 29.1, 29.3_

- [ ] 39.2 实现数字化检查表页面
  - 创建 frontend/src/views/AuditChecklist.vue 数字化检查表页面
  - 实现移动端适配
  - 实现在线打分和拍照上传
  - 实现自动评分结果展示
  - _Requirements: 30.3, 30.4, 30.5, 30.6_

- [ ] 39.3 实现不符合项管理页面
  - 创建 frontend/src/views/NCItems.vue 不符合项管理页面
  - 实现不符合项列表和详情
  - 实现整改措施提交和验证
  - _Requirements: 31.1, 31.2, 31.3_


- [ ] 40. 实现新品质量管理前端页面
- [ ] 40.1 实现新品项目管理页面
  - 创建 frontend/src/views/NewProductProjects.vue 新品项目页面
  - 实现项目创建和列表展示
  - 实现经验教训点检界面
  - 实现阶段评审提交
  - _Requirements: 25.3, 26.1_

- [ ] 40.2 实现试产管理页面
  - 创建 frontend/src/views/TrialProduction.vue 试产管理页面
  - 实现试产记录创建
  - 实现目标与实绩对比展示（红绿灯）
  - 实现试产总结报告生成
  - 实现试产问题跟进
  - _Requirements: 27.1, 27.6, 27.7, 27.9, 28.1_

---

## Phase 14: 测试与部署

- [ ] 41. 编写后端单元测试（可选）
- [ ]* 41.1 编写认证模块测试
  - 测试用户注册、登录、Token 验证
  - 测试权限检查逻辑
  - _Requirements: 1.1, 1.5, 2.4_

- [ ]* 41.2 编写质量指标计算测试
  - 测试来料合格率计算
  - 测试 PPM 计算
  - 测试滚动 MIS 计算
  - _Requirements: 11.2, 11.4, 11.10_

- [ ]* 41.3 编写业务流程测试
  - 测试 SCAR 自动立案
  - 测试 8D 报告 AI 预审
  - 测试绩效评价计算
  - _Requirements: 14.2, 15.4, 17.8_

- [ ] 42. 编写前端单元测试（可选）
- [ ]* 42.1 编写组件测试
  - 测试 TaskCard 组件
  - 测试 MetricCard 组件
  - 测试 NotificationBell 组件
  - _Requirements: 4.3, 12.2, 6.2_

- [ ]* 42.2 编写 E2E 测试
  - 测试登录流程
  - 测试待办任务查看
  - 测试 8D 报告提交流程
  - _Requirements: 1.5, 4.2, 15.2_


- [ ] 43. 部署准备与优化
- [ ] 43.1 配置生产环境变量
  - 创建 .env.production 文件
  - 配置数据库连接字符串
  - 配置 Redis 连接字符串
  - 配置 IMS API 地址
  - 配置 OpenAI API 密钥
  - 配置 SMTP 邮件服务器
  - _Requirements: 10.7_

- [ ] 43.2 配置 SSL 证书
  - 申请 SSL 证书
  - 配置 Nginx SSL 证书路径
  - 强制 HTTPS 重定向
  - _Requirements: 10.4_

- [ ] 43.3 数据库备份策略
  - 配置 PostgreSQL 自动备份脚本
  - 设置备份保留策略（至少 30 天）
  - _Requirements: 3.5_

- [ ] 43.4 性能优化
  - 配置 Redis 缓存策略
  - 优化数据库查询索引
  - 配置 Nginx 静态文件缓存
  - _Requirements: 10.2_

- [ ] 44. 部署与验证
- [ ] 44.1 执行生产环境部署
  - 使用 Docker Compose 启动所有服务
  - 验证所有容器正常运行
  - 执行数据库迁移
  - _Requirements: 10.3, 10.4_

- [ ] 44.2 功能验证测试
  - 验证用户注册和登录
  - 验证权限控制
  - 验证 IMS 数据同步
  - 验证质量指标计算
  - 验证通知发送
  - _Requirements: 1.1, 2.4, 11.1, 11.2, 6.1_

- [ ] 44.3 性能压力测试
  - 使用 Locust 进行负载测试
  - 验证系统在 100 并发用户下的响应时间
  - 验证数据库连接池配置
  - _Requirements: 10.1_

---

## 总结

本实施计划共包含 **44 个主要任务**，涵盖了从基础设施搭建到业务功能实现的完整开发流程。建议按照 Phase 1-14 的顺序执行，确保每个阶段的任务完成后再进入下一阶段。

**预估开发周期**：
- Phase 1-3（基础设施 + 认证授权）：2-3 周
- Phase 4-5（个人中心 + 前端基础）：2 周
- Phase 6-7（数据集成 + AI 引擎）：2-3 周
- Phase 8-12（业务模块）：6-8 周
- Phase 13（前端页面）：3-4 周
- Phase 14（测试部署）：1-2 周

**总计**：约 16-22 周（4-5.5 个月）

