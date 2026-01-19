# Requirements Document

## Introduction

本文档定义了完整的质量管理系统（QMS）的功能需求。该系统是一个面向汽车电子制造行业的企业级质量管理平台，采用 FastAPI (Python) 后端 + Vue 3 前端的 Monorepo 架构，通过 Docker Compose 进行容器化部署。

系统涵盖以下核心功能模块：
1. 系统权限管理（2.1）- 细粒度权限控制、用户注册审核、操作日志
2. 个人中心（2.2）- 任务聚合、站内信、公告栏、电子签名
3. 系统管理与全局配置（2.3）- 任务统计监控、消息通知配置、权限配置
4. 质量数据面板（2.4）- IMS 数据集成、指标计算、可视化展示、AI 诊断
5. 供应商质量管理（2.5）- IQC 集成、SCAR 闭环、审核管理、绩效评价、PPAP
6. 过程质量管理（2.6）- 生产数据集成、不合格品管理、问题发单闭环
7. 客户质量管理（2.7）- 出货数据集成、客诉分级、8D 闭环、索赔管理
8. 新品质量管理（2.8）- 经验教训注入、阶段评审、试产管理、初期流动
9. 审核管理（2.9）- 审核计划、数字化检查表、问题整改闭环、二方审核

核心目标是建立覆盖质量各板块管控的信息化管理系统，同步衔接现有的 IMS/OA/SAP 系统，实现各版块质量数据智能化统计以及跟进，并接入 AI 实现趋势诊断和问题回复诊断。

## Glossary

- **QMS_System**: 质量管理系统，本文档所描述的整体软件平台
- **Auth_Module**: 认证授权模块，负责用户登录、权限验证的子系统
- **Permission_Engine**: 权限引擎，执行基于功能-操作矩阵的访问控制逻辑的组件
- **User_Account**: 用户账号，包含公司内部员工账号和供应商账号两种类型
- **Supplier_Registry**: 供应商名录，系统中已注册的合格供应商列表
- **Operation_Log**: 操作日志，记录用户关键操作的审计追踪记录
- **Personal_Center**: 个人中心，用户登录后的默认首页和工作台
- **Task_Aggregator**: 任务聚合器，从各业务模块收集待办事项的后台服务
- **Digital_Signature**: 电子签名，用户上传的手写签名图片，用于审批流程
- **Notification_Hub**: 通知中心，管理站内信、邮件、企业微信等多渠道消息的组件
- **Admin_Portal**: 系统管理门户，仅管理员可访问的配置界面
- **IMS_System**: 内部管理系统，公司现有的物料入库和生产管理系统
- **Quality_Dashboard**: 质量数据面板，展示各类质量指标的可视化仪表盘
- **IQC_Module**: 来料检验模块，处理供应商物料入库检验的子系统
- **SCAR**: 供应商纠正措施请求单，Supplier Corrective Action Request
- **8D_Report**: 8D 问题解决报告，包含 D0-D8 八个步骤的质量问题分析文档
- **SQE**: 供应商质量工程师，Supplier Quality Engineer
- **PQE**: 过程质量工程师，Process Quality Engineer
- **CQE**: 客户质量工程师，Customer Quality Engineer
- **PPM**: 百万分之一不良率，Parts Per Million
- **CPK**: 过程能力指数，Process Capability Index
- **0KM_Complaint**: 0 公里客诉，客户产线端发现的质量问题
- **MIS_Complaint**: 售后客诉，终端市场反馈的质量问题（3MIS/12MIS）
- **PPAP**: 生产件批准程序，Production Part Approval Process
- **VDA_6_3**: 德国汽车工业协会过程审核标准
- **NC_Item**: 不符合项，Non-Conformance Item，审核中发现的问题点
- **Lesson_Learned**: 经验教训，从质量问题中沉淀的知识库条目
- **AI_Diagnostic_Engine**: AI 诊断引擎，调用大模型进行异常归因和报告预审的组件

## Requirements

### Requirement 1: 用户注册与审核

**User Story:** 作为一名新员工或供应商联系人，我希望能够在线注册账号并等待审核，以便获得系统访问权限。

#### Acceptance Criteria

1. WHEN 公司用户访问注册页面，THE QMS_System SHALL 显示包含用户名、姓名、电话、邮箱、部门（下拉选择）、职位字段的注册表单
2. WHEN 供应商用户访问注册页面，THE QMS_System SHALL 显示包含用户名、姓名、电话、邮箱、供应商名称（模糊搜索）、职位字段的注册表单
3. WHEN 供应商用户在供应商名称字段输入文本，THE QMS_System SHALL 调用 API 从 Supplier_Registry 进行模糊搜索并返回匹配的供应商列表
4. IF 供应商用户选择的供应商名称不存在于 Supplier_Registry 中，THEN THE QMS_System SHALL 阻止表单提交并显示错误提示
5. WHEN 用户提交注册表单，THE QMS_System SHALL 创建状态为"待审核"的 User_Account 记录并返回成功消息
6. WHEN 管理员访问 Admin_Portal 的用户审核页面，THE QMS_System SHALL 显示所有状态为"待审核"的 User_Account 列表
7. WHEN 管理员批准某个 User_Account，THE QMS_System SHALL 更新账号状态为"已激活"并发送激活通知邮件给用户
8. WHEN 管理员拒绝某个 User_Account，THE QMS_System SHALL 更新账号状态为"已拒绝"并记录拒绝原因

### Requirement 2: 细粒度权限控制

**User Story:** 作为系统管理员，我希望能够为每个用户配置精细的功能和操作权限，以便实现灵活的访问控制策略。

#### Acceptance Criteria

1. THE QMS_System SHALL 维护一个权限矩阵，包含功能模块（一级/二级/三级菜单）和操作类型（录入、查阅、修改、删除、导出）的组合
2. WHEN 管理员访问权限配置界面，THE QMS_System SHALL 显示网格化的权限矩阵，行为用户列表，列为功能-操作组合
3. WHEN 管理员勾选或取消某个权限复选框，THE Permission_Engine SHALL 实时更新数据库中的权限配置记录
4. WHEN 用户登录后访问任意功能页面，THE Permission_Engine SHALL 验证该用户是否具有"查阅"权限，若无则返回 403 错误
5. WHEN 用户尝试执行录入、修改、删除、导出操作，THE Permission_Engine SHALL 验证对应的操作权限，若无则阻止操作并提示权限不足
6. WHERE 用户类型为供应商账号，WHEN 用户查询业务数据，THE QMS_System SHALL 自动过滤仅返回关联到该供应商名称的数据记录
7. THE Permission_Engine SHALL 在权限配置更新后立即生效，无需重启后端服务

### Requirement 3: 操作日志审计

**User Story:** 作为质量经理，我希望能够查看所有用户的关键操作记录，以便进行合规审计和问题追溯。

#### Acceptance Criteria

1. WHEN 用户执行提交、删除、修改等关键操作，THE QMS_System SHALL 在 Operation_Log 中记录操作人 ID、操作时间、操作类型、目标对象、操作前后数据快照
2. WHEN 管理员访问操作日志页面，THE QMS_System SHALL 显示所有 Operation_Log 记录的列表视图
3. THE QMS_System SHALL 提供按用户、操作类型、时间范围、目标模块的筛选功能
4. WHEN 管理员选择某条 Operation_Log 记录，THE QMS_System SHALL 显示该操作的详细信息，包含数据变更的 diff 对比
5. THE Operation_Log SHALL 保留至少 3 年的历史记录，且不允许任何用户（包括管理员）删除或修改

### Requirement 4: 个人中心与任务聚合

**User Story:** 作为质量工程师，我希望登录后能看到所有需要我处理的待办任务，以便高效安排工作优先级。

#### Acceptance Criteria

1. WHEN 用户登录成功，THE QMS_System SHALL 默认跳转到 Personal_Center 页面
2. WHEN Personal_Center 页面加载，THE Task_Aggregator SHALL 从所有业务模块查询 Current_Handler_ID 等于当前用户 ID 的待办记录
3. THE Personal_Center SHALL 显示待办事项列表，包含任务类型、单据编号、紧急程度、剩余处理时间（倒计时）
4. WHEN 剩余处理时间小于 0 小时，THE Personal_Center SHALL 以红色标识该任务为"已超期"
5. WHEN 剩余处理时间小于等于 72 小时且大于 0，THE Personal_Center SHALL 以黄色标识该任务为"即将超期"
6. WHEN 剩余处理时间大于 72 小时，THE Personal_Center SHALL 以绿色标识该任务为"正常"
7. WHEN 用户点击某条待办任务，THE QMS_System SHALL 跳转到对应业务模块的单据详情页面

### Requirement 5: 个人信息与电子签名

**User Story:** 作为 SQE 工程师，我希望能够上传我的手写签名，以便在审批 8D 报告时自动生成电子签章。

#### Acceptance Criteria

1. WHEN 用户访问 Personal_Center 的个人信息模块，THE QMS_System SHALL 显示用户的头像、姓名、部门、职位信息
2. THE Personal_Center SHALL 提供修改密码功能，要求用户输入旧密码、新密码、确认新密码
3. WHEN 用户提交密码修改请求且旧密码验证通过，THE Auth_Module SHALL 更新用户密码并强制用户重新登录
4. THE Personal_Center SHALL 提供上传 Digital_Signature 图片的功能，支持 PNG、JPG 格式
5. WHEN 用户上传 Digital_Signature 图片，THE QMS_System SHALL 自动处理图片背景透明化并存储到用户账号关联的签名字段
6. WHEN 用户在审批流程中点击"签署"按钮，THE QMS_System SHALL 调用该用户的 Digital_Signature 图片生成电子签章并附加到文档

### Requirement 6: 站内信通知系统

**User Story:** 作为系统用户，我希望能够接收流程异常、系统提醒、预警通知等消息，以便及时响应重要事件。

#### Acceptance Criteria

1. WHEN 业务流程触发通知事件（如单据被驳回），THE Notification_Hub SHALL 创建站内信记录并关联到目标用户 ID
2. WHEN 用户登录 Personal_Center，THE QMS_System SHALL 在右上角铃铛图标显示未读消息数量的红点标识
3. WHEN 用户点击铃铛图标，THE QMS_System SHALL 显示站内信列表，包含消息类型、标题、时间、已读/未读状态
4. THE QMS_System SHALL 支持按消息类型（流程异常、系统提醒、预警通知）筛选站内信
5. WHEN 用户点击某条站内信，THE QMS_System SHALL 标记该消息为已读并显示消息详情
6. THE Personal_Center SHALL 提供"一键标记全部已读"功能

### Requirement 7: 公告栏与强制阅读

**User Story:** 作为质量部长，我希望能够发布重要质量预警公告，并确保所有相关人员已阅读，以便落实全员知晓要求。

#### Acceptance Criteria

1. WHEN 管理员在 Admin_Portal 创建公告，THE QMS_System SHALL 允许设置公告类型（系统公告、质量警告、体系文件更新）和重要性标记（普通/重要）
2. WHEN 用户访问 Personal_Center，THE QMS_System SHALL 在公告栏显示所有有效期内的公告列表
3. WHERE 公告被标记为"重要"，WHEN 用户登录系统，THE QMS_System SHALL 弹窗强制显示该公告内容
4. WHEN 用户点击查看重要公告，THE QMS_System SHALL 记录阅读时间和阅读人 ID 到公告阅读记录表
5. THE Personal_Center SHALL 将未读的重要公告置顶并高亮显示
6. WHEN 管理员查看公告详情，THE QMS_System SHALL 显示该公告的阅读统计（已读人数、未读人数、阅读人员清单）

### Requirement 8: 账号生命周期管理

**User Story:** 作为系统管理员，我希望能够冻结离职员工或暂停合作供应商的账号，以便保障系统安全。

#### Acceptance Criteria

1. WHEN 管理员在 Admin_Portal 选择某个 User_Account 并点击"冻结"，THE Auth_Module SHALL 更新账号状态为"已冻结"
2. WHEN 状态为"已冻结"的 User_Account 尝试登录，THE Auth_Module SHALL 拒绝登录并返回"账号已被冻结，请联系管理员"提示
3. WHEN 管理员点击"解冻"按钮，THE Auth_Module SHALL 恢复账号状态为"已激活"
4. THE Admin_Portal SHALL 提供重置用户密码功能，生成临时密码并通过邮件发送给用户
5. WHEN 用户使用临时密码登录，THE QMS_System SHALL 强制用户在首次登录时修改密码

### Requirement 9: 全局任务统计与监控

**User Story:** 作为质量经理，我希望能够查看团队整体的待办任务分布和逾期情况，以便进行工作负载平衡和督办。

#### Acceptance Criteria

1. WHEN 管理员访问 Admin_Portal 的任务统计页面，THE Task_Aggregator SHALL 统计所有待办任务按部门和人员的分布数量
2. THE Admin_Portal SHALL 显示待办分布图（柱状图或饼图），展示各部门或人员的任务积压情况
3. THE Admin_Portal SHALL 显示所有已逾期（剩余时间 < 0）的单据清单，支持按逾期时长排序
4. WHEN 管理员选择某位用户的待办任务，THE Admin_Portal SHALL 提供批量转派功能，允许将任务转移给另一位用户
5. WHEN 管理员执行批量转派操作，THE QMS_System SHALL 更新所有选中任务的 Current_Handler_ID 并发送通知给新的处理人

### Requirement 10: 数据库与基础架构

**User Story:** 作为系统架构师，我希望系统采用容器化部署并支持异步任务处理，以便实现高可用性和可扩展性。

#### Acceptance Criteria

1. THE QMS_System SHALL 使用 PostgreSQL 15+ 作为主数据库存储用户、权限、业务数据
2. THE QMS_System SHALL 使用 Redis 作为缓存层和 Celery 任务队列的消息中间件
3. THE QMS_System SHALL 通过 Docker Compose 编排 FastAPI 后端容器、Vue 3 前端容器、PostgreSQL 容器、Redis 容器
4. THE QMS_System SHALL 使用 Nginx 作为反向代理，处理静态文件服务和 API 路由转发
5. THE QMS_System SHALL 使用 SQLAlchemy (Async) 作为 ORM 框架，支持数据库迁移（Alembic）
6. THE QMS_System SHALL 使用 Pydantic 进行 API 请求和响应的数据校验
7. THE QMS_System SHALL 部署在 DMZ 区域，后端需同时具备访问外网（响应前端）和内网（请求 IMS）的网络权限

### Requirement 11: IMS 数据集成与质量指标计算

**User Story:** 作为质量数据分析员，我希望系统能够自动从 IMS 拉取生产数据并计算质量指标，以便实时监控质量状况。

#### Acceptance Criteria

1. THE QMS_System SHALL 每日凌晨 02:00 通过 Celery 定时任务从 IMS_System 同步物料入库批次数、物料入库不合格批次数、物料入库总数量、成品出库总量数据
2. WHEN IMS 数据同步完成，THE QMS_System SHALL 自动计算来料批次合格率 = ((物料入库批次数 - 物料入库不合格批次数) / 物料入库批次数) * 100%
3. THE QMS_System SHALL 按供应商、按日、按月统计来料批次合格率并合计年度数据
4. THE QMS_System SHALL 自动计算物料上线不良 PPM = (物料上线不良数 / 物料入库总数量) * 1000000
5. THE QMS_System SHALL 按供应商、按物料类型、按日、按月统计物料上线不良 PPM 并合计年度数据
6. THE QMS_System SHALL 自动计算制程不合格率 = (完成制程不合格品数 / 成品产出入库数) * 100%
7. THE QMS_System SHALL 按责任类别、按日、按月统计制程不合格率并合计年度数据
8. THE QMS_System SHALL 自动计算 0KM 不良 PPM = (0KM 客诉数 / 成品出库总量) * 1000000
9. THE QMS_System SHALL 按产品类型、按日、按月滚动推移 0KM 不良 PPM 并合计年度数据
10. THE QMS_System SHALL 自动计算售后不良 PPM(3MIS) = (3MIS 客诉数 / 3 个月滚动出货量) * 1000000
11. THE QMS_System SHALL 按产品类型进行月度滚动推移售后不良 PPM(3MIS)
12. THE QMS_System SHALL 自动计算售后不良 PPM(12MIS) = (12MIS 客诉数 / 12 个月滚动出货量) * 1000000
13. THE QMS_System SHALL 按产品类型进行月度滚动推移售后不良 PPM(12MIS)

### Requirement 12: 质量数据可视化展示

**User Story:** 作为质量工程师，我希望能够通过可视化图表查看质量指标趋势，以便快速识别异常。

#### Acceptance Criteria

1. WHEN 用户访问 Quality_Dashboard，THE QMS_System SHALL 根据用户权限配置显示可查阅的数据图表
2. THE Quality_Dashboard SHALL 提供 0KM 不良 PPM、售后不良 PPM(3MIS)、售后不良 PPM(12MIS)、来料批次合格率、上线不良 PPM 的基础数据图表
3. THE Quality_Dashboard SHALL 提供类型按钮，允许用户切换查看不同类型的指标图表
4. THE Quality_Dashboard SHALL 提供时间调整按钮，允许用户查看不同时间区间的指标图表
5. WHEN 指标达标，THE Quality_Dashboard SHALL 以绿色显示该指标
6. WHEN 指标未达标，THE Quality_Dashboard SHALL 以红色显示该指标
7. WHEN 用户点击某个指标，THE QMS_System SHALL 跳转到该指标对应的问题清单页面，显示当日或当月的相关问题记录

### Requirement 13: 专项数据分析与 AI 诊断

**User Story:** 作为质量经理，我希望系统能够自动生成 Top5 供应商清单并提供 AI 诊断，以便快速定位问题根源。

#### Acceptance Criteria

1. THE QMS_System SHALL 每月自动生成来料批次合格率 Top5 供应商清单（最差的 5 家）
2. THE QMS_System SHALL 每月自动生成物料上线不良 PPM Top5 供应商清单（最差的 5 家）
3. THE QMS_System SHALL 每月自动形成制程不合格率按责任类别的分类统计，并生成月度趋势推移图表
4. THE QMS_System SHALL 每月自动形成客户质量数据（0KM、3MIS、12MIS）按产品类型的分类统计，并生成月度趋势推移图表
5. WHEN 监控到某项指标突发飙升，THE AI_Diagnostic_Engine SHALL 自动触发异常分析
6. WHEN AI 异常分析完成，THE AI_Diagnostic_Engine SHALL 遍历当天的数据，寻找强相关性因子并生成诊断报告
7. THE Quality_Dashboard SHALL 提供 AI 对话框，允许用户用自然语言提问
8. WHEN 用户在 AI 对话框输入自然语言查询，THE AI_Diagnostic_Engine SHALL 转化为 SQL 查询数据库并返回数据详情和图表

### Requirement 14: IQC 数据集成与自动立案

**User Story:** 作为 IQC 检验员，我希望系统能够自动从 IMS 同步检验记录并在发现不合格时自动生成 SCAR 单，以便快速响应质量问题。

#### Acceptance Criteria

1. THE QMS_System SHALL 定时从 IMS_System 读取入库检验记录，包含物料编码、批次号、检验结果（OK/NG）、不良描述、不良数量
2. WHEN IMS_System 出现检验结果为"不合格"的记录，THE IQC_Module SHALL 自动生成 SCAR 单并关联该检验记录
3. WHEN SCAR 单生成，THE Notification_Hub SHALL 发送邮件通知给对应的供应商账号
4. THE IQC_Module SHALL 同步 IMS_System 的特采记录，并标记该批次物料为"特采"状态
5. THE QMS_System SHALL 将 IQC 数据作为 Requirement 11 中质量指标计算的源数据

### Requirement 15: 供应商 8D 报告协同与 AI 预审

**User Story:** 作为供应商质量工程师，我希望供应商能够在线填写 8D 报告并由 AI 预审，以便提高报告质量和审核效率。

#### Acceptance Criteria

1. WHEN 供应商账号登录系统，THE QMS_System SHALL 仅显示关联到该供应商名称的 SCAR 单列表
2. WHEN 供应商点击某个 SCAR 单，THE QMS_System SHALL 显示 8D 报告填写表单，包含 D0-D8 各步骤的输入字段
3. THE 8D_Report 表单 SHALL 要求供应商上传改善前后对比图作为附件
4. WHEN 供应商提交 8D_Report，THE AI_Diagnostic_Engine SHALL 预审报告内容
5. IF AI 检测到报告包含"加强培训"、"加强管理"等空洞词汇，THEN THE AI_Diagnostic_Engine SHALL 提示供应商"措施不具体，请补充作业指导书变更证据"
6. WHEN AI 预审通过，THE QMS_System SHALL 将 8D_Report 状态更新为"待 SQE 审核"并通知 SQE
7. WHEN SQE 审核 8D_Report，THE QMS_System SHALL 提供"批准"和"驳回"按钮
8. IF SQE 点击"驳回"，THEN THE QMS_System SHALL 要求填写具体修改意见并将报告退回给供应商
9. WHEN SQE 点击"批准"，THE QMS_System SHALL 更新 SCAR 单状态为"已关闭"

### Requirement 16: 供应商审核管理

**User Story:** 作为 SQE，我希望能够管理供应商的准入审核、年度审核和变更管理，以便确保供应商质量体系的有效性。

#### Acceptance Criteria

1. WHEN 新供应商注册，THE QMS_System SHALL 要求上传 ISO9001/IATF16949 证书、营业执照等资质文件
2. THE QMS_System SHALL 自动识别证书有效期并在到期前 30 天发送预警通知
3. WHEN 采购工程师或 SQE 审核供应商资质，THE QMS_System SHALL 提供"批准"和"驳回"按钮
4. IF 审核人员点击"驳回"，THEN THE QMS_System SHALL 创建提交任务并通知供应商重新提交
5. WHEN 供应商提交 PCN（变更申请），THE QMS_System SHALL 创建内部评估流程任务并指派给采购工程师或 SQE
6. WHEN 评估通过，THE QMS_System SHALL 通知供应商执行切换并要求上传断点信息
7. THE QMS_System SHALL 每月 1 号自动触发年度审核计划中的审核流程
8. WHEN 审核员录入不符合项（NC），THE QMS_System SHALL 自动转化为任务清单并指派给供应商
9. WHEN 供应商完成整改并上传证据，THE QMS_System SHALL 通知审核员进行验证
10. WHEN 审核员验证通过，THE QMS_System SHALL 允许关闭该 NC_Item

### Requirement 17: 供应商质量目标与绩效评价

**User Story:** 作为 SQE，我希望能够为供应商设定质量目标并自动计算月度绩效评分，以便客观评价供应商表现。

#### Acceptance Criteria

1. THE QMS_System SHALL 支持 SQE 按物料类别或供应商等级批量设置质量目标（来料合格率、PPM 目标）
2. THE QMS_System SHALL 支持针对特定供应商进行差异化目标配置
3. WHEN 系统计算绩效时，THE QMS_System SHALL 优先查询该供应商的单独目标，若无则使用批量目标，最后使用全局默认值
4. WHEN SQE 设定目标时，THE QMS_System SHALL 左右分栏展示拟设定的目标值和该供应商上一年度实际达成值
5. IF 目标值低于历史实际值，THEN THE QMS_System SHALL 高亮提示"目标倒退风险"
6. WHEN 目标书发布，THE QMS_System SHALL 创建"待签署质量目标"任务并通知供应商
7. WHEN 供应商点击"确认/签署"，THE QMS_System SHALL 记录签署时间并生效该目标版本
8. THE QMS_System SHALL 每月 1 日自动计算供应商绩效评分，初始分为 60 分
9. THE QMS_System SHALL 根据来料质量、制程质量、配合度、0 公里/售后质量进行扣分
10. WHEN 来料检验质量合格率达到目标，THE QMS_System SHALL 扣 0 分
11. WHEN 来料检验质量合格率差距小于 10% 目标值，THE QMS_System SHALL 扣 5 分
12. WHEN 来料检验质量合格率差距在 10%-20% 目标值之间，THE QMS_System SHALL 扣 15 分
13. WHEN 来料检验质量合格率差距大于等于 20% 目标值，THE QMS_System SHALL 扣 30 分
14. THE QMS_System SHALL 对制程质量（PPM 超标）、配合度、客诉问题应用类似的扣分规则
15. WHEN SQE 在每月最后一天填写配合度评价，THE QMS_System SHALL 根据评价等级（高/中/低）自动计算配合度扣分
16. THE QMS_System SHALL 允许 SQE 复核系统生成的扣分项并进行核减，要求附上详细说明
17. WHEN 绩效计算完成，THE QMS_System SHALL 按 60 分制扣分后按 100 分满分折算百分制，并评定等级（A/B/C/D）
18. WHEN 月度绩效为 C 级或 D 级，THE QMS_System SHALL 自动生成"供应商月度品质改善会议"任务

### Requirement 18: 供应商改善会议与 PPAP 管理

**User Story:** 作为 SQE，我希望系统能够强制要求低绩效供应商参加改善会议并管理 PPAP 提交，以便推动供应商持续改进。

#### Acceptance Criteria

1. WHEN 供应商月度绩效为 C 级，THE QMS_System SHALL 通知要求供应商副总级参加改善会议
2. WHEN 供应商月度绩效为 D 级，THE QMS_System SHALL 通知要求供应商总经理参加改善会议
3. THE QMS_System SHALL 要求供应商在会议前上传《物料品质问题改善报告》，逾期触发预警
4. WHEN SQE 录入会议纪要，THE QMS_System SHALL 记录实际参会最高级别人员
5. IF SQE 标记为"供应商未参会"或"未提交报告"，THEN THE QMS_System SHALL 在下个月度的绩效评价中强制执行额外扣分
6. WHEN 触发 PPAP 提交场景（新物料导入、变更、模具转移、停产一年后恢复），THE QMS_System SHALL 创建 PPAP 提交任务
7. THE QMS_System SHALL 内置标准 18 项 PPAP 文件检查表（PSW、全尺寸测量报告、控制计划、PFMEA、材质证明等）
8. WHEN SQE 指定各项文件的要求上传日期，THE QMS_System SHALL 通知供应商并创建待办任务
9. WHEN 供应商逐项上传附件，THE QMS_System SHALL 更新文件提交状态
10. WHEN SQE 审核 PPAP 文件包，THE QMS_System SHALL 提供"单项驳回"和"整体批准"功能
11. THE QMS_System SHALL 监控 PPAP 批准日期，满 1 年自动生成"年度产品审核"任务

### Requirement 19: 过程质量数据集成与不合格品管理

**User Story:** 作为过程质量工程师，我希望系统能够集成生产数据并管理不合格品记录，以便准确计算制程不合格率。

#### Acceptance Criteria

1. THE QMS_System SHALL 定时从 IMS_System 拉取生产入库统计数据，包含成品入库数、产线、工单号、日期
2. THE QMS_System SHALL 从 IMS_System 同步各工序自动判定的不良记录
3. THE QMS_System SHALL 提供人工补录界面，允许产线或维修工位录入未被设备捕捉的外观/组装不良
4. WHEN 用户录入不合格品数据，THE QMS_System SHALL 要求选择不良现象和责任类别（物料不良、作业不良、设备不良、工艺不良、设计不良）
5. IF 用户选择责任类别为"物料不良"，THEN THE QMS_System SHALL 自动关联 Requirement 11 的"物料上线不良 PPM"指标
6. THE QMS_System SHALL 使用生产入库数据作为制程不合格率计算的分母
7. THE QMS_System SHALL 支持按产线、工单号、日期、责任类别的多维度钻取分析

### Requirement 20: 制程质量问题发单与闭环

**User Story:** 作为 PQE，我希望能够针对制程异常发起整改任务并跟踪闭环，以便持续改进过程质量。

#### Acceptance Criteria

1. WHEN PQE 在 Quality_Dashboard 或不合格品数据清单中选中数据点，THE QMS_System SHALL 提供"一键发起整改"功能
2. WHEN PQE 发起整改，THE QMS_System SHALL 根据责任类别自动推荐责任板块担当，允许 PQE 修改并指派
3. WHEN 责任板块担当收到任务，THE QMS_System SHALL 要求填写原因分析、围堵措施、长期对策
4. THE QMS_System SHALL 要求责任板块担当上传改善证据（如：作业指导书修订版、设备参数调整记录）
5. WHEN 对策导入后，THE QMS_System SHALL 设定验证期（如：后续 1 周）
6. WHILE 验证期内，THE QMS_System SHALL 监控 Quality_Dashboard 的相关指标是否无超标或不合格品无再发
7. WHEN 验证期结束，THE QMS_System SHALL 通知 PQE 进行验证判定
8. WHEN PQE 判定验证通过，THE QMS_System SHALL 允许关闭该整改任务

### Requirement 21: 客户质量出货数据集成

**User Story:** 作为客户质量工程师，我希望系统能够自动从 ERP/SAP 拉取出货数据，以便准确计算 0KM 和 MIS 指标。

#### Acceptance Criteria

1. THE QMS_System SHALL 每天从 ERP/SAP 或 IMS_System 拉取发货记录，包含客户代码、产品类型、出货日期、出货数量
2. THE QMS_System SHALL 存储并维护过去 24 个月的分月出货数据表
3. THE QMS_System SHALL 使用当期成品出库量计算 0KM PPM
4. THE QMS_System SHALL 使用历史滚动出货量计算 3MIS 和 12MIS 指标
5. THE QMS_System SHALL 支持按客户代码、产品类型、出货日期的多维度查询

### Requirement 22: 客诉录入与分级受理

**User Story:** 作为 CQE，我希望能够录入客诉信息并进行分级管理，以便根据严重程度采取不同的响应策略。

#### Acceptance Criteria

1. WHEN CQE 录入客诉，THE QMS_System SHALL 提供 0KM_Complaint 和 MIS_Complaint 两种类型选择
2. WHERE 客诉类型为 MIS_Complaint，THE QMS_System SHALL 要求录入失效里程、购车日期、VIN 码
3. THE QMS_System SHALL 要求 CQE 选择缺陷等级（具体分级方案待定）
4. THE QMS_System SHALL 根据缺陷等级自动确定升级汇报机制和供应商扣分权重
5. WHEN CQE 完成一次因解析（D0-D3），THE QMS_System SHALL 确定责任部门并将任务流转至责任板块进行 D4-D8 处理
6. WHEN CQE 录入追溯信息，THE QMS_System SHALL 联动 IMS_System 追溯查询系统，自动调取过程记录
7. IF 涉及物料失效，THEN THE QMS_System SHALL 通过输入物料编码实现自动追溯查询

### Requirement 23: 8D 闭环与时效管理

**User Story:** 作为责任板块担当，我希望系统能够提供标准化的 8D 流程并监控时效，以便高效完成问题分析和改善。

#### Acceptance Criteria

1. THE QMS_System SHALL 监控 8D_Report 提交时效，要求 7 个工作日内提交
2. THE QMS_System SHALL 监控 8D_Report 归档时效，要求 10 个工作日内归档
3. WHEN 责任板块担当填写 D0-D3，THE QMS_System SHALL 要求填写问题描述（5W2H）和围堵措施
4. THE QMS_System SHALL 验证围堵措施是否覆盖在途品、库存品、客户端库存
5. WHEN 责任板块担当填写 D4-D7，THE QMS_System SHALL 提供 5Why、鱼骨图、FTA、流程分析等工具模板
6. WHEN 责任板块担当填写 D6，THE QMS_System SHALL 要求上传验证报告或测试数据作为附件
7. WHEN 责任板块担当填写 D7，THE QMS_System SHALL 询问是否涉及文件修改（PFMEA/CP/SOP）
8. IF 涉及文件修改，THEN THE QMS_System SHALL 要求上传修改附件
9. WHEN 责任板块担当填写 D8，THE QMS_System SHALL 提供搜索功能，允许关联类似产品/类似工艺
10. THE QMS_System SHALL 将 D8 对策推送到相关项目组
11. WHEN 责任板块担当提交结案，THE QMS_System SHALL 询问是否沉淀经验教训
12. IF 选择沉淀经验教训，THEN THE QMS_System SHALL 弹出《经验教训总结表》弹窗
13. WHEN 经验教训提交，THE QMS_System SHALL 创建审批任务并指派给责任部门部长
14. WHEN 8D_Report 提交审批，THE QMS_System SHALL 根据缺陷等级确定审批流（C 级：科室经理；A/B 级：质量部长 + 责任部门部长）
15. WHEN 8D_Report 归档，THE QMS_System SHALL 自动触发《8D 报告归档检查表》核对流程

### Requirement 24: 索赔管理与成本转嫁

**User Story:** 作为财务对接人员，我希望系统能够管理客户索赔并支持向供应商转嫁，以便准确核算质量成本。

#### Acceptance Criteria

1. WHEN 用户录入客户索赔，THE QMS_System SHALL 记录扣款金额和明细
2. THE QMS_System SHALL 提供筛选功能，允许将客户索赔与问题清单进行多选关联
3. WHERE 8D_Report 的根本原因判定为"供应商来料问题"，WHEN 用户在客诉单界面点击"生成供应商索赔"，THE QMS_System SHALL 自动提取物料号、供应商、客诉金额信息
4. THE QMS_System SHALL 在供应商质量管理模块生成供应商索赔单
5. THE QMS_System SHALL 通知供应商查看索赔单并要求确认或申诉

### Requirement 25: 新品经验教训反向注入

**User Story:** 作为项目质量工程师，我希望系统能够在新品开发时自动推送历史质量问题，以便规避已知风险。

#### Acceptance Criteria

1. THE QMS_System SHALL 建立 Lesson_Learned 库，调用供应商、制程、客诉模块中所有标记为"已存入经验库"的 8D 结案记录
2. THE QMS_System SHALL 支持手工完善、删减、新增 Lesson_Learned 条目
3. WHEN 新品项目立项，THE QMS_System SHALL 自动推送相关的历史质量问题列表
4. THE QMS_System SHALL 要求责任担当逐条勾选"是否在本项目规避"
5. IF 责任担当选择"否"，THEN THE QMS_System SHALL 要求注明理由
6. WHEN 项目开发至后续阶段，THE QMS_System SHALL 要求上传规避证据（如：设计截图）
7. IF 未上传规避证据，THEN THE QMS_System SHALL 阻止通过对应的阶段评审

### Requirement 26: 新品阶段评审与交付物管理

**User Story:** 作为项目经理，我希望系统能够管理项目质量阀门和交付物，以便确保项目按质量要求推进。

#### Acceptance Criteria

1. THE QMS_System SHALL 支持配置项目关键节点（如：概念、设计、验证、量产准备）
2. THE QMS_System SHALL 内置项目质量需点检交付物清单
3. THE QMS_System SHALL 支持设置其他关键交付物
4. IF 关键交付物缺失，THEN THE QMS_System SHALL 锁定项目进度无法转段
5. WHEN 项目申请转段，THE QMS_System SHALL 验证所有必需交付物已提交

### Requirement 27: 试产目标与实绩管理

**User Story:** 作为质量工程师，我希望系统能够自动生成试产总结报告，以便评估试产质量达成情况。

#### Acceptance Criteria

1. WHEN 试产开始，THE QMS_System SHALL 要求录入 IMS_System 工单号
2. THE QMS_System SHALL 要求设定试产质量目标（如：直通率 > 95%，CPK > 1.33，尺寸合格率 100%）
3. THE QMS_System SHALL 根据关联的工单号，自动从 IMS_System 调取投入数、产出数、一次合格数、不良数
4. THE QMS_System SHALL 自动计算试产合格率和直通率
5. THE QMS_System SHALL 提供在线表格，允许 QE 手动录入 CPK 测算值、破坏性实验结果、外观评审得分
6. THE QMS_System SHALL 自动对比目标值与实绩值
7. WHEN 实绩达标，THE QMS_System SHALL 以绿色显示该指标
8. WHEN 实绩未达标，THE QMS_System SHALL 以红色显示该指标
9. THE QMS_System SHALL 提供一键输出《试产质量总结报告 (Excel/PDF)》功能

### Requirement 28: 试产问题跟进与升级

**User Story:** 作为试产质量工程师，我希望能够快速记录和跟踪试产问题，以便在 SOP 前完成整改。

#### Acceptance Criteria

1. THE QMS_System SHALL 提供试产问题清单录入界面，记录设计、模具、工艺问题
2. WHEN 用户录入问题，THE QMS_System SHALL 指派责任人并创建待办任务
3. WHEN 责任人上传对策，THE QMS_System SHALL 允许问题发起人关闭该问题
4. WHERE 问题复杂，THE QMS_System SHALL 提供"一键升级为 8D 报告"功能
5. WHEN SOP 节点到达且仍有未关闭问题，THE QMS_System SHALL 要求经过"带病量产"特批流程
6. THE QMS_System SHALL 要求特批人签署风险告知书

### Requirement 29: 审核计划与排程管理

**User Story:** 作为审核组长，我希望系统能够管理年度审核计划并自动提醒，以便确保审核按时执行。

#### Acceptance Criteria

1. THE QMS_System SHALL 支持导入或创建年度审核计划，涵盖体系审核、过程审核、产品审核、二方审核
2. THE QMS_System SHALL 根据计划日期，提前 7 天邮件通知审核组长及迎审负责人
3. IF 计划未按期执行，THEN THE QMS_System SHALL 要求提交延期申请并注明理由
4. WHEN 延期申请提交，THE QMS_System SHALL 创建审批任务并指派给质量部长
5. WHEN 质量部长批准延期，THE QMS_System SHALL 允许修改计划时间

### Requirement 30: 数字化检查表与在线打分

**User Story:** 作为审核员，我希望能够使用移动设备进行现场审核并在线打分，以便提高审核效率和数据准确性。

#### Acceptance Criteria

1. THE QMS_System SHALL 预置 VDA_6_3 (P2-P7)、VDA 6.5、IATF16949 检查条款库
2. THE QMS_System SHALL 支持创建自定义审核模板（如：防静电专项审核、异物管理专项审核）
3. THE QMS_System SHALL 支持移动端（手机/平板）访问审核界面
4. WHEN 审核员现场审核，THE QMS_System SHALL 允许逐条录入检查结果（OK/NG）
5. THE QMS_System SHALL 支持现场拍照上传，直接挂载到对应条款下
6. THE QMS_System SHALL 根据 VDA_6_3 规则（如：单项 0 分降级规则）自动计算最终得分和等级（A/B/C）
7. THE QMS_System SHALL 自动生成《审核报告 (PDF)》，包含得分雷达图和问题清单

### Requirement 31: 审核问题整改与闭环

**User Story:** 作为迎审负责人，我希望系统能够自动将审核问题转化为整改任务，以便跟踪闭环进度。

#### Acceptance Criteria

1. WHEN 审核结束提交，THE QMS_System SHALL 将所有判定为 NG 的条款自动生成 NC_Item 待办任务
2. WHEN 审核组长指派 NC_Item，THE QMS_System SHALL 通知责任板块并创建待办任务
3. WHEN 责任人填写根本原因及纠正措施，THE QMS_System SHALL 要求上传整改后的照片或文件
4. WHEN 责任人提交整改证据，THE QMS_System SHALL 通知审核员进行验证
5. WHEN 审核员验证有效，THE QMS_System SHALL 允许关闭该 NC_Item
6. THE QMS_System SHALL 设定整改期限（一般项 30 天，严重项 7 天）
7. WHEN NC_Item 逾期未关闭，THE QMS_System SHALL 自动跟催并升级抄送

### Requirement 32: 二方审核特别管理

**User Story:** 作为客户审核对接人，我希望系统能够管理客户来厂审核的档案和问题跟进，以便满足客户要求。

#### Acceptance Criteria

1. THE QMS_System SHALL 建立客户审核台账，记录客户名称、审核类型、审核日期、最终得分/结果
2. THE QMS_System SHALL 支持以附件形式上传客户指定的问题整改清单（Excel）
3. THE QMS_System SHALL 依据客户指摘问题清单在系统内部创建对应的问题任务条目
4. THE QMS_System SHALL 确保客户提出的每个整改项都有对应的内部跟踪任务
5. WHEN 所有客户整改项关闭，THE QMS_System SHALL 允许归档该客户审核记录
