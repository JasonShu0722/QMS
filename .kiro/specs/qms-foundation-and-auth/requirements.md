# Requirements Document

## 文档说明

本文档定义质量管理系统（QMS）的**基础架构与认证授权模块**的功能需求（对应 product.md 的 2.1-2.3 和 2.12 章节）。

### 文档覆盖范围

**本文档涵盖：**
- 系统基础与门户管理（2.1）
- 个人中心（2.2）
- 系统管理与全局配置（2.3）
- 版本与发布管理（2.12）
- 预留功能接口（2.10-2.11）

**业务模块需求（2.4-2.9）请参考：**
- **详细业务需求文档**：`.kiro/steering/product.md`
  - 2.4 质量数据面板
  - 2.5 供应商质量管理
  - 2.6 过程质量管理
  - 2.7 客户质量管理
  - 2.8 新品质量管理
  - 2.9 审核管理
- **实施任务清单**：`tasks.md` 任务组 9-16

本文档与 product.md 共同构成 QMS 系统的完整需求规格说明。

## Introduction

本文档定义质量管理系统（QMS）的基础架构与认证授权模块的功能需求。该模块是整个 QMS 系统的核心底座，负责用户身份认证、权限管理、系统配置、个人工作台、通知机制以及双轨发布架构。系统采用 Monorepo 结构，通过 Docker Compose 编排，支持 Preview（预览环境）与 Stable（正式环境）双轨并行运行，共享同一数据库底座。

本模块需支持内部员工与外部供应商的统一登录入口，实现细粒度的"功能-操作"权限控制体系，并提供千人千面的动态工作台。同时需预留仪器量具管理、质量成本管理等功能接口，为后续扩展奠定基础。

## Glossary

- **QMS_System**: 质量管理系统，本文档所描述的整体应用系统
- **User**: 系统用户，包含内部员工（Internal_User）和外部供应商（Supplier_User）
- **Internal_User**: 公司内部员工用户
- **Supplier_User**: 外部供应商用户
- **Permission_Matrix**: 权限矩阵，基于"功能模块-操作类型"的二维权限配置表
- **Operation_Type**: 操作类型，包括录入、查阅、修改、删除、导出五种基本操作
- **Feature_Module**: 功能模块，系统的一级/二级/三级菜单功能点
- **Audit_Log**: 操作日志，记录用户关键操作的审计记录
- **Workbench**: 动态工作台，用户登录后的首页，展示个性化看板和待办任务
- **Todo_Task**: 待办任务，需要当前用户处理的业务单据或审批事项
- **Notification**: 站内信通知，系统推送给用户的消息
- **Announcement**: 公告，系统级或质量预警类的全员通知
- **Feature_Flag**: 功能特性开关，用于灰度发布和功能控制的配置项
- **Preview_Environment**: 预览环境，用于新功能验证的隔离环境
- **Stable_Environment**: 正式环境，面向全体用户的生产环境
- **Shared_Database**: 共享数据库，Preview 和 Stable 环境共用的 PostgreSQL 数据库
- **IMS_System**: 内部管理系统，提供物料入库、生产数据等基础数据的源系统
- **LDAP_Auth**: LDAP 认证，基于公司 AD/LDAP 的单点登录认证方式（预留功能）
- **Local_Auth**: 本地认证，基于账号密码的常规登录认证方式
- **JWT_Token**: JSON Web Token，用于用户会话管理的令牌
- **Password_Policy**: 密码策略，强制密码复杂度和定期修改的安全规则
- **Electronic_Signature**: 电子签名，用户上传的手写签名图片，用于审批流程
- **System_Config**: 系统配置，全局性的系统参数配置
- **Notification_Rule**: 通知规则，基于业务触发器的消息推送配置
- **SMTP_Server**: 邮件服务器，用于发送邮件通知的配置
- **Webhook**: Webhook 地址，用于企业微信/钉钉/飞书集成的回调地址
- **Responsive_Layout**: 响应式布局，适配桌面端和移动端的界面设计
- **PWA_Mode**: Progressive Web App 模式，无需原生 APP 的移动端访问方式
- **DMZ_Zone**: 非军事区，系统部署的网络区域，可同时访问外网和内网
- **Alembic_Migration**: Alembic 数据库迁移，遵循非破坏性原则的数据库版本管理
- **Reserved_Feature**: 预留功能接口，当前阶段不实现但需预留扩展槽位的功能

## Requirements

### Requirement 1: 用户注册与审核

**User Story:** 作为系统管理员，我希望能够审核新用户的注册申请，以确保只有合法用户能够访问系统。

#### Acceptance Criteria

1. WHEN 公司用户提交注册申请 THEN THE QMS_System SHALL 记录用户名、姓名、电话、邮箱、部门、职位信息
2. WHEN 供应商用户提交注册申请 THEN THE QMS_System SHALL 记录用户名、姓名、电话、邮箱、供应商名称、职位信息
3. WHEN 供应商用户输入供应商名称 THEN THE QMS_System SHALL 调用 API 模糊搜索系统内的供应商名录并返回匹配结果
4. WHEN 供应商用户选择供应商名称 THEN THE QMS_System SHALL 仅允许从现存的供应商名录中选择
5. WHEN 用户提交注册申请 THEN THE QMS_System SHALL 将用户状态设置为"待审核"
6. WHEN 管理员审核通过注册申请 THEN THE QMS_System SHALL 将用户状态更新为"已激活"并允许用户登录
7. WHEN 管理员驳回注册申请 THEN THE QMS_System SHALL 将用户状态更新为"已驳回"并记录驳回原因

### Requirement 2: 统一登录与身份认证

**User Story:** 作为用户，我希望通过统一入口登录系统，根据我的身份类型选择合适的认证方式，以便安全地访问系统。

#### Acceptance Criteria

1. WHEN 用户访问系统登录页面 THEN THE QMS_System SHALL 展示统一的登录入口界面
2. WHEN 内部员工选择员工登录 THEN THE QMS_System SHALL 提供账号密码登录选项
3. WHEN 供应商选择供应商登录 THEN THE QMS_System SHALL 提供账号密码加图形验证码的登录选项
4. WHEN 用户输入错误密码连续 5 次 THEN THE QMS_System SHALL 锁定账号 30 分钟
5. WHEN 用户首次登录或密码超过 90 天 THEN THE QMS_System SHALL 强制用户修改密码
6. WHEN 用户设置新密码 THEN THE QMS_System SHALL 验证密码包含大写、小写、数字、特殊字符中至少三种且长度大于 8 位
7. WHEN 用户登录成功 THEN THE QMS_System SHALL 生成 JWT_Token 并返回给客户端
8. WHERE LDAP_Auth 功能启用 WHEN 内部员工选择 SSO 登录 THEN THE QMS_System SHALL 调用 LDAP 接口进行身份验证（预留功能）

### Requirement 3: 细粒度权限控制

**User Story:** 作为系统管理员，我希望能够为每个用户配置细粒度的权限，精确控制其对不同功能模块的操作能力，以实现灵活的权限管理。

#### Acceptance Criteria

1. WHEN 管理员访问权限配置界面 THEN THE QMS_System SHALL 展示网格化的权限矩阵配置界面
2. WHEN 管理员选择用户 THEN THE QMS_System SHALL 展示该用户当前的权限配置状态
3. WHEN 管理员为用户配置功能模块权限 THEN THE QMS_System SHALL 支持配置一级、二级、三级菜单的访问权限
4. WHEN 管理员为用户配置操作权限 THEN THE QMS_System SHALL 支持独立配置录入、查阅、修改、删除、导出五种操作权限
5. WHEN 供应商用户查阅数据 THEN THE QMS_System SHALL 仅返回关联到该供应商名称的数据记录
6. WHEN 管理员保存权限配置 THEN THE QMS_System SHALL 立即生效无需重启后端服务
7. WHEN 用户访问功能模块 THEN THE QMS_System SHALL 根据权限配置动态渲染可用的操作按钮
8. WHEN 用户尝试执行无权限的操作 THEN THE QMS_System SHALL 拒绝请求并返回权限不足提示

### Requirement 4: 操作日志审计

**User Story:** 作为系统管理员，我希望能够查阅所有用户的关键操作日志，以便进行安全审计和问题追溯。

#### Acceptance Criteria

1. WHEN 用户执行提交操作 THEN THE QMS_System SHALL 记录操作人、操作时间、操作类型、操作对象到 Audit_Log
2. WHEN 用户执行删除操作 THEN THE QMS_System SHALL 记录操作人、操作时间、操作类型、被删除对象标识到 Audit_Log
3. WHEN 用户执行修改操作 THEN THE QMS_System SHALL 记录操作人、操作时间、操作类型、修改前后的数据快照到 Audit_Log
4. WHEN 管理员访问操作日志界面 THEN THE QMS_System SHALL 展示所有操作日志记录
5. WHEN 管理员筛选操作日志 THEN THE QMS_System SHALL 支持按用户、时间范围、操作类型进行筛选
6. WHEN 管理员导出操作日志 THEN THE QMS_System SHALL 生成 Excel 文件包含所有筛选结果

### Requirement 5: 个人中心与基本信息管理

**User Story:** 作为用户，我希望能够查看和管理我的个人信息，包括修改密码和上传电子签名，以便个性化使用系统。

#### Acceptance Criteria

1. WHEN 用户访问个人中心 THEN THE QMS_System SHALL 展示用户头像、姓名、部门、职位信息
2. WHEN 用户修改密码 THEN THE QMS_System SHALL 验证旧密码正确性并应用 Password_Policy 规则
3. WHEN 用户上传电子签名图片 THEN THE QMS_System SHALL 自动实现图片背景透明化处理
4. WHEN 用户保存电子签名 THEN THE QMS_System SHALL 存储签名图片路径并关联到用户账号
5. WHEN 系统需要用户签名 THEN THE QMS_System SHALL 调用用户的 Electronic_Signature 生成电子签章

### Requirement 6: 动态工作台

**User Story:** 作为用户，我希望登录后看到个性化的工作台，根据我的角色展示相关的指标监控和待办任务，以便快速了解工作状态。

#### Acceptance Criteria

1. WHEN 用户登录系统 THEN THE QMS_System SHALL 将动态工作台设置为默认首页
2. WHEN 内部员工访问工作台 THEN THE QMS_System SHALL 展示基于角色定义的指标全景监控图表
3. WHEN 内部员工访问工作台 THEN THE QMS_System SHALL 聚合展示跨模块的待办任务清单
4. WHEN 供应商访问工作台 THEN THE QMS_System SHALL 展示其当前绩效等级和本月扣分情况
5. WHEN 供应商访问工作台 THEN THE QMS_System SHALL 仅展示需要其行动的任务卡片
6. WHEN 用户点击待办任务 THEN THE QMS_System SHALL 跳转到对应模块的具体单据详情页

### Requirement 7: 待办任务聚合

**User Story:** 作为用户，我希望在一个地方看到所有需要我处理的任务，并能够快速识别紧急和逾期任务，以便合理安排工作优先级。

#### Acceptance Criteria

1. WHEN 系统加载待办任务 THEN THE QMS_System SHALL 遍历所有业务表筛选当前处理人等于当前用户的记录
2. WHEN 系统展示待办任务 THEN THE QMS_System SHALL 显示任务类型、单据编号、紧急程度、剩余处理时间
3. WHEN 任务剩余时间小于 0 THEN THE QMS_System SHALL 标记为红色已超期状态
4. WHEN 任务剩余时间小于等于 72 小时 THEN THE QMS_System SHALL 标记为黄色即将超期状态
5. WHEN 任务剩余时间大于 72 小时 THEN THE QMS_System SHALL 标记为绿色正常状态
6. WHEN 用户点击待办任务 THEN THE QMS_System SHALL 直接跳转到对应单据详情页进行处理

### Requirement 8: 站内信通知

**User Story:** 作为用户，我希望能够接收系统推送的通知消息，并能够管理已读未读状态，以便及时了解重要信息。

#### Acceptance Criteria

1. WHEN 系统触发流程异常 THEN THE QMS_System SHALL 向相关用户发送站内信通知
2. WHEN 系统生成定期报告 THEN THE QMS_System SHALL 向相关用户发送系统提醒通知
3. WHEN 系统检测到预警条件 THEN THE QMS_System SHALL 向相关用户发送预警通知
4. WHEN 用户访问通知中心 THEN THE QMS_System SHALL 展示所有通知消息并标识已读未读状态
5. WHEN 用户标记通知为已读 THEN THE QMS_System SHALL 更新通知状态并移除未读标识
6. WHEN 用户有未读消息 THEN THE QMS_System SHALL 在右上角铃铛图标显示红点数字

### Requirement 9: 公告管理

**User Story:** 作为系统管理员，我希望能够发布系统公告和质量预警，并强制重要公告的阅读确认，以确保信息有效传达。

#### Acceptance Criteria

1. WHEN 管理员发布公告 THEN THE QMS_System SHALL 记录公告标题、内容、类型、重要程度、发布时间
2. WHEN 公告标记为重要 THEN THE QMS_System SHALL 在用户登录后弹窗提醒点击查阅
3. WHEN 用户查阅重要公告 THEN THE QMS_System SHALL 记录阅读时间和阅读人 ID
4. WHEN 用户未读重要公告 THEN THE QMS_System SHALL 在公告栏置顶并高亮显示
5. WHEN 用户访问公告栏 THEN THE QMS_System SHALL 按发布时间倒序展示所有公告

### Requirement 10: 全局任务统计与监控

**User Story:** 作为系统管理员，我希望能够监控团队整体的工作负载和流程瓶颈，并能够批量转派任务，以便优化资源分配。

#### Acceptance Criteria

1. WHEN 管理员访问任务统计界面 THEN THE QMS_System SHALL 展示按部门或人员统计的待办任务数量分布图
2. WHEN 管理员查看逾期分析 THEN THE QMS_System SHALL 列出所有已逾期单据清单并支持按逾期时长排序
3. WHEN 管理员选择批量转派 THEN THE QMS_System SHALL 支持将指定用户名下的所有待办任务转移给另一用户
4. WHEN 管理员执行批量转派 THEN THE QMS_System SHALL 更新所有相关单据的当前处理人字段并发送通知

### Requirement 11: 消息通知机制配置

**User Story:** 作为系统管理员，我希望能够配置业务触发规则和通知渠道，实现自动化的消息推送和升级策略，以提高流程效率。

#### Acceptance Criteria

1. WHEN 管理员配置触发规则 THEN THE QMS_System SHALL 支持选择业务对象、触发条件、执行动作
2. WHEN 管理员配置升级策略 THEN THE QMS_System SHALL 支持定义超时时长和升级抄送对象
3. WHEN 业务单据满足触发条件 THEN THE QMS_System SHALL 自动执行配置的通知动作
4. WHEN 单据在当前节点停留超过设定时长 THEN THE QMS_System SHALL 自动触发升级通知
5. WHEN 管理员配置邮件通道 THEN THE QMS_System SHALL 记录 SMTP_Server 参数并验证连接有效性
6. WHEN 管理员配置企业通讯工具 THEN THE QMS_System SHALL 记录 Webhook 地址并验证可达性

### Requirement 12: 用户信息与权限管理

**User Story:** 作为系统管理员，我希望能够管理用户账号的生命周期，包括审批注册、重置密码、冻结账号和配置权限，以维护系统安全。

#### Acceptance Criteria

1. WHEN 管理员查看待审核用户 THEN THE QMS_System SHALL 展示所有状态为"待审核"的注册申请
2. WHEN 管理员审批注册申请 THEN THE QMS_System SHALL 支持通过或驳回操作并记录审批意见
3. WHEN 管理员重置用户密码 THEN THE QMS_System SHALL 生成临时密码并强制用户下次登录修改
4. WHEN 管理员冻结用户账号 THEN THE QMS_System SHALL 将用户状态设置为"已冻结"并阻止其登录
5. WHEN 管理员解冻用户账号 THEN THE QMS_System SHALL 将用户状态恢复为"已激活"并允许其登录
6. WHEN 管理员配置用户权限 THEN THE QMS_System SHALL 展示 Permission_Matrix 配置界面并支持实时保存

### Requirement 13: 移动端响应式适配

**User Story:** 作为移动端用户，我希望能够在手机或平板上流畅访问系统，界面自动适配屏幕尺寸，以便在现场作业时使用系统。

#### Acceptance Criteria

1. WHEN 用户通过移动设备访问系统 THEN THE QMS_System SHALL 自动应用响应式布局
2. WHEN 移动端加载页面 THEN THE QMS_System SHALL 自动折叠左侧菜单栏并放大操作按钮和输入框
3. WHEN 用户在移动端访问扫码页面 THEN THE QMS_System SHALL 全屏显示扫描框并隐藏顶部导航和底部版权信息
4. WHEN 移动端用户在无网络环境下操作 THEN THE QMS_System SHALL 支持将数据暂存本地
5. WHEN 移动端网络恢复 THEN THE QMS_System SHALL 自动同步提交暂存的本地数据

### Requirement 14: 双轨发布架构

**User Story:** 作为系统管理员，我希望能够在预览环境验证新功能，确认无误后再发布到正式环境，同时两个环境共享数据库，以实现平滑的版本升级。

#### Acceptance Criteria

1. WHEN 系统部署 THEN THE QMS_System SHALL 同时运行 Preview_Environment 和 Stable_Environment 两个容器实例
2. WHEN 用户访问预览域名 THEN THE QMS_System SHALL 路由请求到 Preview_Environment 容器
3. WHEN 用户访问正式域名 THEN THE QMS_System SHALL 路由请求到 Stable_Environment 容器
4. WHEN 任一环境写入数据 THEN THE QMS_System SHALL 将数据存储到 Shared_Database
5. WHEN 任一环境读取数据 THEN THE QMS_System SHALL 从 Shared_Database 查询数据
6. WHEN 预览环境和正式环境同时访问 THEN THE QMS_System SHALL 在环境入口提供实时切换按钮

### Requirement 15: 数据库兼容性管理

**User Story:** 作为开发人员，我希望预览环境的数据库变更不会破坏正式环境的运行，以确保系统稳定性。

#### Acceptance Criteria

1. WHEN 预览环境新增数据表 THEN THE QMS_System SHALL 允许该操作且不影响正式环境
2. WHEN 预览环境新增字段 THEN THE QMS_System SHALL 要求字段设置为 Nullable 或带有 Default Value
3. WHEN 预览环境尝试删除字段 THEN THE QMS_System SHALL 阻止该操作直到正式环境代码同步更新
4. WHEN 预览环境尝试重命名字段 THEN THE QMS_System SHALL 阻止该操作直到正式环境代码同步更新
5. WHEN 预览环境执行 Alembic_Migration THEN THE QMS_System SHALL 验证迁移脚本符合非破坏性原则
6. WHEN 正式环境读取新增字段 THEN THE QMS_System SHALL 对空值进行判空处理避免报错

### Requirement 16: 功能特性开关

**User Story:** 作为系统管理员，我希望能够通过功能开关控制新功能的发布范围，实现灰度测试和白名单机制，以降低发布风险。

#### Acceptance Criteria

1. WHEN 管理员访问功能控制台 THEN THE QMS_System SHALL 展示所有可配置的 Feature_Flag 列表
2. WHEN 管理员启用功能开关 THEN THE QMS_System SHALL 立即对指定范围的用户生效
3. WHEN 管理员禁用功能开关 THEN THE QMS_System SHALL 立即对所有用户隐藏该功能
4. WHEN 管理员配置白名单 THEN THE QMS_System SHALL 支持按用户 ID 或供应商代码指定可见范围
5. WHEN 用户访问功能模块 THEN THE QMS_System SHALL 根据 Feature_Flag 配置动态判断功能可见性
6. WHEN 白名单用户访问新功能 THEN THE QMS_System SHALL 展示新版界面
7. WHEN 非白名单用户访问 THEN THE QMS_System SHALL 展示旧版界面

### Requirement 17: 系统全局配置

**User Story:** 作为系统管理员，我希望能够集中管理系统的全局配置参数，包括业务规则、超时时长、文件大小限制等，以便灵活调整系统行为。

#### Acceptance Criteria

1. WHEN 管理员访问系统配置界面 THEN THE QMS_System SHALL 展示所有可配置的 System_Config 参数
2. WHEN 管理员修改配置参数 THEN THE QMS_System SHALL 验证参数格式和取值范围的合法性
3. WHEN 管理员保存配置 THEN THE QMS_System SHALL 立即生效无需重启服务
4. WHEN 系统执行业务逻辑 THEN THE QMS_System SHALL 从 System_Config 读取最新配置值
5. WHEN 配置参数缺失 THEN THE QMS_System SHALL 使用预设的默认值并记录警告日志

### Requirement 18: 预留功能接口 - 仪器与量具管理

**User Story:** 作为系统架构师，我希望为仪器与量具管理功能预留数据库表结构和 API 接口，以便后续快速扩展该功能。

#### Acceptance Criteria

1. WHEN 系统初始化数据库 THEN THE QMS_System SHALL 创建仪器量具相关的预留表结构
2. WHEN 预留表包含字段 THEN THE QMS_System SHALL 将所有字段设置为 Nullable
3. WHEN 后端 API 设计 THEN THE QMS_System SHALL 预留仪器量具管理的 RESTful 接口路由
4. WHEN 前端菜单设计 THEN THE QMS_System SHALL 预留仪器量具管理的菜单入口但默认隐藏

### Requirement 19: 预留功能接口 - 质量成本管理

**User Story:** 作为系统架构师，我希望为质量成本管理功能预留数据库表结构和 API 接口，以便后续快速扩展该功能。

#### Acceptance Criteria

1. WHEN 系统初始化数据库 THEN THE QMS_System SHALL 创建质量成本相关的预留表结构
2. WHEN 预留表包含字段 THEN THE QMS_System SHALL 将所有字段设置为 Nullable
3. WHEN 后端 API 设计 THEN THE QMS_System SHALL 预留质量成本管理的 RESTful 接口路由
4. WHEN 前端菜单设计 THEN THE QMS_System SHALL 预留质量成本管理的菜单入口但默认隐藏

### Requirement 20: DMZ 网络部署

**User Story:** 作为系统运维人员，我希望系统能够部署在 DMZ 区，同时访问外网（响应前端）和内网（请求 IMS），以满足安全和业务需求。

#### Acceptance Criteria

1. WHEN 系统部署到 DMZ_Zone THEN THE QMS_System SHALL 配置双网卡分别连接外网和内网
2. WHEN 前端用户访问系统 THEN THE QMS_System SHALL 通过外网网卡响应 HTTP 请求
3. WHEN 后端需要同步 IMS 数据 THEN THE QMS_System SHALL 通过内网网卡访问 IMS_System
4. WHEN 网络配置完成 THEN THE QMS_System SHALL 验证外网和内网连接均正常
