# ExecPlan（QMS）

> 这是一份活文档。创建任务计划后，必须随着执行持续更新：
> `进度`、`意外发现`、`决策日志`、`验证证据`、`回顾`
> 使用前先阅读：
>
> - [`AGENTS.md`](/E:/WorkSpace/QMS/AGENTS.md)
> - [`doc/PROJECT_DEVELOPMENT_HANDOFF.md`](/E:/WorkSpace/QMS/doc/PROJECT_DEVELOPMENT_HANDOFF.md)

***

## 任务名称

系统管理底座升级：角色标签权限管理 + 用户审批/用户清单拆分

## 任务元信息

- 模块：系统管理 / 用户管理 / 权限管理
- 需求来源：
  - 用户最新策划：按角色标签统一授权，由管理员配置角色标签权限并为账户分配角色标签
  - 当前系统管理板块开发收口
- 关联文档：
  - [`doc/PROJECT_DEVELOPMENT_HANDOFF.md`](/E:/WorkSpace/QMS/doc/PROJECT_DEVELOPMENT_HANDOFF.md)
  - [`doc/QMS_ROLE_FUNCTION_MAPPING.md`](/E:/WorkSpace/QMS/doc/QMS_ROLE_FUNCTION_MAPPING.md)
  - [`.kiro/steering/product.md`](/E:/WorkSpace/QMS/.kiro/steering/product.md)
  - [`.kiro/specs/qms-foundation-and-auth/requirements.md`](/E:/WorkSpace/QMS/.kiro/specs/qms-foundation-and-auth/requirements.md)
  - [`.kiro/specs/qms-foundation-and-auth/design.md`](/E:/WorkSpace/QMS/.kiro/specs/qms-foundation-and-auth/design.md)
- 风险等级：高
- 是否涉及双环境 / feature flag：否
- 是否需要更新需求面板：是
- 是否需要回写 `.kiro` 源文档：是

***

## 目的 / 用户可观察结果

- 管理员在“权限管理”中不再按单个用户逐项勾权限，而是按“角色标签”统一维护模块权限。
- 管理员在“用户管理”中可以区分“用户审批”和“用户清单管理”两个子版块。
- 用户清单管理支持按姓名、部门、岗位等字段搜索筛选，并支持基本信息维护、角色分配、冻结/解冻、删除、密码重置等操作。
- 角色标签的权限变更会直接影响对应账户的实际访问权限，保持角色级统一治理。

***

## 非目标

- 不在本次范围内实现完整的组织架构树、部门层级主数据中心。
- 不在本次范围内实现业务管理员与超级管理员的彻底拆权，只保留当前 super admin bootstrap 入口。
- 不在本次范围内重构操作日志、任务监控、通知规则、系统配置页面。

***

## 前置阅读

- [`doc/PROJECT_DEVELOPMENT_HANDOFF.md`](/E:/WorkSpace/QMS/doc/PROJECT_DEVELOPMENT_HANDOFF.md)
- [`doc/QMS_ROLE_FUNCTION_MAPPING.md`](/E:/WorkSpace/QMS/doc/QMS_ROLE_FUNCTION_MAPPING.md)
- [`.kiro/steering/product.md`](/E:/WorkSpace/QMS/.kiro/steering/product.md)
- [`.kiro/specs/qms-foundation-and-auth/requirements.md`](/E:/WorkSpace/QMS/.kiro/specs/qms-foundation-and-auth/requirements.md)
- [`.kiro/specs/qms-foundation-and-auth/design.md`](/E:/WorkSpace/QMS/.kiro/specs/qms-foundation-and-auth/design.md)

***

## 里程碑与验证

- [x] 步骤 1：确认范围、依赖和现状
  - 验证：已确认当前权限模型仍为“按用户授予”，用户管理仅有待审核列表，需新增角色标签与用户清单治理能力
- [x] 步骤 2：完成后端实现或契约调整
  - 验证：`& '.\.venv\Scripts\python.exe' -m pytest backend/test/test_admin_users_api.py backend/test/test_admin_permissions_api.py backend/test/test_permissions.py`
- [x] 步骤 3：完成前端实现或交互收口
  - 验证：`Set-Location frontend; npm run test:foundation`
- [x] 步骤 4：补齐最小自动化验证
  - 验证：`Set-Location frontend; npm run build`
- [x] 步骤 5：联调底座 smoke
  - 验证：`& '.\.venv\Scripts\python.exe' backend/scripts/run_foundation_smoke.py`
- [x] 步骤 6：更新需求面板 / 专题文档 / 交付记录
  - 验证：已同步 `frontend/src/features/requirements-panel/catalog.ts`、`doc/QMS_ROLE_FUNCTION_MAPPING.md`、`doc/PROJECT_DEVELOPMENT_HANDOFF.md`
- [x] 步骤 7：同步回写 `.kiro` 源文档
  - 验证：已同步 `.kiro/steering/product.md`、`.kiro/specs/qms-foundation-and-auth/requirements.md`、`.kiro/specs/qms-foundation-and-auth/design.md`

***

## 进度

- [ ] 待开始
- [ ] 进行中
- [x] 已完成

> 角色标签化权限治理、用户审批/用户清单拆分、验证回归与文档同步已经全部完成。

***

## 意外发现 & 新发现

- 当前权限矩阵接口和页面仍按“用户”为行维度，不符合角色模板化治理目标。
- 当前用户管理接口只有待审核、冻结、解冻、重置密码，缺少用户列表、编辑、角色分配、删除。
- 当前 `is_platform_admin` 仍是用户名白名单 bootstrap 机制，不是结构化系统角色字段。

***

## 决策日志

| 日期         | 决策                          | 理由                      |
| ---------- | --------------------------- | ----------------------- |
| 2026-04-12 | 引入角色标签、角色权限、用户角色关联三张新表      | 最小代价实现“按角色授权 + 按账户分配角色” |
| 2026-04-12 | 保留现有用户直授权限模型并在权限检查时与角色权限做并集 | 保持兼容，避免一次性破坏现有权限能力      |
| 2026-04-12 | 用户管理页面拆成“用户审批 / 用户清单管理”两块   | 与管理动作类型一致，降低页面认知负担      |

***

## 验证证据

- 后端测试：
  - `& '.\.venv\Scripts\python.exe' -m pytest backend/test/test_admin_users_api.py backend/test/test_admin_permissions_api.py backend/test/test_permissions.py`
  - 结果：29 passed
  - `& '.\.venv\Scripts\python.exe' -m pytest backend/test/test_admin_users_api.py -q`
  - 结果：15 passed
- 前端测试：
  - `Set-Location frontend; npm run test:foundation`
  - 结果：通过
- 前端构建：
  - `Set-Location frontend; npm run build`
  - 结果：通过
- 底座 smoke：
  - `& '.\.venv\Scripts\python.exe' backend/scripts/run_foundation_smoke.py`
  - 结果：67 passed
- 契约补充：
  - `backend/test/test_foundation_milestone_api.py::test_permission_matrix_contract_and_mutations`
  - 已同步改为角色标签矩阵口径

***

## 回退思路

- 如角色标签模型上线后出现问题，可先保留用户直授权限通路，前端回退到旧权限矩阵页面；数据库新增表不会破坏现有用户和权限数据。

***

## 完成回顾

- 做对了什么：把“角色标签统一授权 + 账户分配角色”完整落到了模型、接口、页面、测试和文档，且保留了用户直连授权的兼容路径。
- 还缺什么：`sys.business_admin` 仍未独立建模；操作日志、任务监控、通知规则、系统配置仍待后续继续闭环。
- 下次应提前规避什么：系统级契约改造后，要同步检查 foundation smoke 和需求面板口径，避免最后阶段再补测试漂移。

***

## 完成检查清单

- [x] 页面或接口具备真实闭环，不只是骨架存在
- [x] 权限、状态流转、环境差异已确认
- [x] 自动化验证已补齐或明确说明缺口
- [x] 需求面板 / 文档已同步
- [x] 如果任务升级了需求或设计，相关 `.kiro` 源文档已同步
- [x] 最终说明包含结果、验证、剩余风险

***

## Task: Subpage Layout Compaction And Surface Cleanup (2026-04-12)

- Goal:
  - remove the extra blank band left after moving subpage titles into the top bar
  - collapse redundant outer padding and shell borders on titled subpages
  - keep actions inside the single business surface when a page only has one main card
- Non-goals:
  - no API or data-contract changes
  - no redesign of business tables or workflows
- Planned verification:
  - `Set-Location frontend; npm run test:foundation`
  - `Set-Location frontend; npm run build`
- Risks / rollback:
  - the global stage compaction may affect legacy pages with custom spacing
  - rollback point is `frontend/src/layouts/MainLayout.vue`, `frontend/src/style.css`, and the affected admin views

## Task: Admin User Creation Entry And Bulk Provisioning (2026-04-13)

- Goal:
  - add a clear `创建用户` action in the user directory header
  - support single-user creation for internal and supplier accounts
  - support bulk user creation from pasted multi-line text with shared batch rules
  - return temporary passwords / creation results so admins can complete handoff immediately
- Non-goals:
  - no redesign of registration workflow
  - no organization tree / department master-data refactor
  - no supplier lifecycle changes beyond resolving an existing supplier when creating supplier users
- Planned verification:
  - `Set-Location backend; & '..\.venv\Scripts\python.exe' -m pytest test\test_admin_users_api.py`
  - `Set-Location frontend; npm run test:foundation`
  - `Set-Location frontend; npm run build`
- Risks / rollback:
  - batch parsing may reject malformed rows unexpectedly if validation messaging is unclear
  - supplier account creation depends on existing supplier master data
  - rollback point is `backend/app/api/v1/admin/users.py`, `backend/app/schemas/admin.py`, `frontend/src/views/admin/UserApproval.vue`, and related API/type files

## Task: Registration Policy Tightening And Supplier Master Planning (2026-04-15)

- Goal:
  - contract public registration to internal employees only
  - remove supplier self-registration and shift supplier account provisioning fully into admin user management
  - introduce supplier master-data maintenance planning so supplier accounts are created against a governed supplier directory
  - align registration policy, supplier master data, and supplier-account linkage into one closed design
- Non-goals:
  - no immediate implementation of full supplier-quality business workflows
  - no one-shot refactor of all existing supplier-related modules
  - no physical deletion strategy for supplier master records in this phase
- Planned sequence:
  - Phase 1: remove supplier self-registration from public register flow and contract `/auth/register` to internal-only
  - Phase 2: add internal registration gate for corporate email suffix with non-revealing validation messaging
  - Phase 3: design and land a minimal admin-only supplier master module with `supplier_code` and `supplier_name` as the primary reference pair
  - Phase 4: adapt admin supplier-account creation to depend on supplier master records and inherited supplier attributes
- Planned verification:
  - `Set-Location backend; & '..\.venv\Scripts\python.exe' -m pytest test\test_auth_api.py test\test_admin_users_api.py`
  - `Set-Location frontend; npm run test -- src/views/test/login.spec.ts src/views/test/register.spec.ts`
  - `Set-Location frontend; npm run test:foundation`
  - `Set-Location frontend; npm run build`
- Risks / rollback:
  - public registration policy changes require synchronized updates across frontend, backend schema, and source requirements docs
  - supplier master maintenance is shared reference data and may affect downstream modules that already rely on `supplier_id`
  - rollback point is `frontend/src/views/Register.vue`, `backend/app/api/v1/auth.py`, `backend/app/schemas/user.py`, plus the future supplier-master admin surfaces

- Status:
  - completed on 2026-04-18
- Delivered:

## Task: Cross-Module Problem Management Unification (2026-04-20)

- Goal:
  - 梳理供应商质量、制程质量、客户质量、新品质量、审核管理五个板块的问题管理共性与差异
  - 在现有权限、待办、通知和供应商数据隔离底座上，设计一套可渐进落地的统一问题管理抽象
  - 优先收敛第一批最小闭环，为后续编码阶段确定主表/子表、状态机、角色权限和页面/API 顺序
- Non-goals:
  - 本轮不一次性重构所有现有业务表到统一模型
  - 本轮不追求把通知中心、全局任务监控、操作日志全部做成完全体
  - 本轮不直接覆盖供应商绩效、PPAP、索赔、变更等非问题主链路能力
- Planned sequence:
  - Phase 1: 盘点现有问题类模型、页面、接口、权限与待办基础，识别真实可复用部分和契约漂移
  - Phase 2: 定义统一问题主模型边界，明确共性字段、状态、动作、附件、应答、SLA、待办、通知抽象
  - Phase 3: 定义模块差异扩展层，区分供应商SCAR/8D、制程问题、客诉8D、试产问题、审核NC/客户审核问题
  - Phase 4: 锁定第一批最小闭环并按后端模型/API、权限范围、前端列表/详情/应答页顺序实施
- Planned verification:
  - `& '.\\.venv\\Scripts\\python.exe' -m pytest backend/test/test_scar_api.py backend/test/test_process_quality_module.py backend/test/test_customer_quality_comprehensive.py backend/test/test_new_product_comprehensive.py backend/test/test_audit_management_module.py`
  - `& '.\\.venv\\Scripts\\python.exe' -m pytest backend/test/test_permissions.py backend/test/test_notifications.py backend/test/test_task_aggregator.py`
  - `Set-Location frontend; npm run test:foundation`
  - `Set-Location frontend; npm run build`
- Risks / rollback:
  - 现有多个模块已存在各自问题单模型、状态值和前端文案，统一抽象时容易引入契约不兼容
  - 当前任务聚合、通知发送、权限校验在业务模块内落地深度不一致，不能假设已有底座已天然可复用
  - 若统一主模型改造跨度过大，应回退为“统一问题中心 + 模块扩展子表”的渐进方案，避免一次性替换全部现有表
- Status:
  - in progress
- Notes:
  - 分析阶段先输出现状梳理、统一设计建议、角色权限矩阵和最小闭环范围；讨论确认后再进入代码落地。
  - 问题回复形式增加分级：简单/单点问题可走“问题简报”，复杂/重大问题走“8D报告”；发起时可选择，跟进责任人和管理角色可在流程中即时调整，并保留切换审计轨迹。
  - 问题主单号需要按问题分类编码，编码结构参考既定 8D 报告规则；统一编号生成器需支持主问题单号与 8D 报告号分离，并共享分类码、子类码、年月和流水规则。
  - 编号格式定稿：分类码与子类码拼成一个分段，不额外增加连接符；示例：`ZXQ-CQ1-2604-003`、`ZX8D-AQ3-2604-001`。
  - 分类码定稿：
    - `CQ`: `0`=0km，`1`=售后
    - `PQ`: `0`=PCBA段，`1`=组装测试段
    - `IQ`: `0`=结构料，`1`=电子料
    - `DQ`: `0`=厂内试产/调试问题，`1`=客诉问题
  - `AQ`: `0`=体系审核NC，`1`=过程审核NC，`2`=产品审核NC，`3`=客户审核问题
  - 实现假设：`CQ` 默认承载量产后客户质量问题；`DQ-1` 作为量产前/新品阶段来自客户侧的问题编码，后续在主表通过来源类型与业务模块进一步区分。
  - 已补后端共享能力：`backend/app/core/problem_management.py`、`backend/app/api/v1/problem_management.py`、`backend/app/schemas/problem_management.py`，对外提供统一分类字典、回复形式、处理分级和编号规则元数据接口。
  - 已补前端共享接入层：`frontend/src/types/problem-management.ts`、`frontend/src/api/problem-management.ts`、`frontend/src/stores/problemManagement.ts`，并在登录/刷新用户信息后预加载共享字典，避免后续问题页继续散落硬编码。
  - public registration was contracted to internal employees only
  - supplier self-registration and public supplier search were removed
  - internal registration now enforces the corporate email policy with outward-generic validation messaging
  - supplier login now depends on an existing active supplier master record
  - system management now includes supplier master maintenance with list/search/create/bulk-edit/status controls
  - admin supplier-account creation and batch creation now resolve against supplier master data only
- Documentation synced:
  - `.kiro/steering/product.md`
  - `.kiro/specs/qms-foundation-and-auth/requirements.md`
  - `.kiro/specs/qms-foundation-and-auth/design.md`
  - `doc/QMS_ROLE_FUNCTION_MAPPING.md`
  - `frontend/src/features/requirements-panel/catalog.ts`
- Verification evidence:
  - `& '.\.venv\Scripts\python.exe' -m pytest backend/test/test_problem_management.py backend/test/test_problem_management_api.py`
  - `Set-Location frontend; npm run test -- src/stores/test/problemManagement.spec.ts src/stores/test/auth.spec.ts`
  - `Set-Location frontend; npm run build`
  - `Set-Location frontend; npm run test:foundation`
  - `& '.\.venv\Scripts\python.exe' -m pytest backend/test/test_user_registration.py backend/test/test_login.py backend/test/test_admin_suppliers_api.py backend/test/test_admin_users_api.py backend/test/test_foundation_milestone_api.py backend/test/test_profile_api.py`
  - `& '.\.venv\Scripts\python.exe' backend/scripts/run_foundation_smoke.py`
- Residual notes:
  - backend still emits existing `datetime.utcnow()` / Pydantic deprecation warnings during test runs
  - frontend build still emits the existing Sass legacy API and large chunk warnings

## Task: Permission-Driven Surface Visibility And Supplier Quality Panel Access (2026-04-18)

- Goal:
  - make major sections and subpages disappear from navigation when the current account lacks the corresponding permissions
  - keep route-level blocking as the second line of defense, but move menu / quick-entry visibility to permission-aware rendering
  - allow supplier accounts with the correct role tag to access the quality data panel and only view trend data scoped to their own supplier
- Non-goals:
  - no redesign of the permission matrix UI
  - no expansion into full cross-module supplier self-service analytics beyond the quality data panel
  - no rewrite of the entire workbench information architecture
- Planned implementation:
  - add a current-user permission-tree endpoint under auth APIs
  - let the frontend auth store cache the current user permission tree for local visibility checks
  - refactor sidebar and workbench quick actions to render only accessible major/minor entries
  - unify quality data panel API permission checks to the `quality.data_panel` module and restrict supplier views to self-scoped trend access
- Planned verification:
  - `& '.\.venv\Scripts\python.exe' -m pytest backend/test/test_login.py backend/test/test_admin_permissions_api.py backend/test/test_foundation_milestone_api.py`
  - `Set-Location frontend; npm run test:foundation`
  - `Set-Location frontend; npm run build`
- Risks / rollback:
  - menu visibility may drift from route guarding if permission metadata is duplicated instead of centralized
  - supplier analytics access must not leak peer-supplier rankings or unrelated internal analysis tabs
  - rollback points are `frontend/src/layouts/MainLayout.vue`, `frontend/src/views/Workbench.vue`, `frontend/src/stores/auth.ts`, `frontend/src/router/index.ts`, `frontend/src/views/QualityDashboard.vue`, `backend/app/api/v1/auth.py`, and `backend/app/api/v1/quality_metrics.py`
