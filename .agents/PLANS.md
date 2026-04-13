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
