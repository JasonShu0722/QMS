# QMS 项目开发原则与新线程上下文摘要

## 1. 这份文档是做什么的

给新线程一个最小但够用的入场材料，帮助快速理解：

- 项目要解决什么问题
- 当前开发应遵循什么原则
- 先看哪些文档最有效
- 当前仓库里的“完成度”应该如何解读

## 2. 项目开发原则

1. 先打通主链路，再做增强项。
   当前开发优先保证底座能力和核心业务闭环可运行，再逐步补 AI、移动端、分析增强、预留模块。

2. 功能“能访问”不等于“已交付”。
   已有页面、接口、模型或路由，只能说明骨架可能存在；必须以“页面可操作、接口可联调、数据可闭环、权限可控制、状态可验证”为完成标准。

3. 先保证跨模块共用底座稳定。
   权限、登录、工作台、通知、审计、账号治理等底座能力，会直接影响后续所有业务模块，优先级高于局部页面打磨。

4. 开发顺序服从系统依赖，而不是只看单点页面。
   模块排期优先看是否依赖统一认证、权限矩阵、待办聚合、通知链路、供应商/内部用户身份隔离等基础能力。

5. 需求面板是策划与跟踪工具，不是代码事实识别器。
   面板中的默认开发状态来自配置文件，不是自动扫描代码得出的真实完成度。

6. 对“历史已完成”保持审慎判断。
   历史 `tasks.md`、总结文档、接口实现文档可以帮助理解结构和已有尝试，但新线程需要结合当前代码、页面行为和联调结果重新确认是否真的可用。

7. 每推进一个模块，至少同步四件事。
   需求项顺序、优先级判断、开发状态、验证口径。

## 3. 当前项目上下文摘要

- 项目是一个 QMS 质量管理系统，覆盖系统基础、质量看板、供应商质量、制程质量、客户质量、新品质量、审核管理及预留扩展模块。
- 仓库结构是 Monorepo：
  - `backend/`：FastAPI + SQLAlchemy + Alembic
  - `frontend/`：Vue 3 + Vite + Element Plus + Pinia
  - `deployment/`：Nginx / Docker / 部署配置
- 系统设计目标是支持内部员工与外部供应商统一入口访问，并通过细粒度权限矩阵控制功能和操作权限。
- 需求面板已经承担项目级需求编排职责，当前支持 `总览`、`开发顺序`、`明细` 三类视图。
- 后续无论开发哪个模块，都建议先在需求面板里确认所在批次、优先级和当前状态，再进入具体实现。
- 当前需求状态基线已按保守口径回收：
  - `todo`: 50
  - `reserved`: 4
- 这意味着后续新线程开发时，应默认认为绝大多数需求仍未真正完成；不要把旧的“dev-done / doing”理解成代码已成熟可交付。

## 4. 推荐阅读顺序

### 第一层：先理解项目全貌

1. [`.kiro/steering/product.md`](/E:/WorkSpace/QMS/.kiro/steering/product.md)
   项目最完整的业务需求源头，解释系统为什么存在、有哪些业务模块、每个模块要解决什么问题。

2. [`.kiro/steering/structure.md`](/E:/WorkSpace/QMS/.kiro/steering/structure.md)
   快速理解 Monorepo 结构、前后端分工、部署拓扑和双轨环境设计。

### 第二层：进入系统公共能力或底座开发前重点看

3. [`.kiro/specs/qms-foundation-and-auth/requirements.md`](/E:/WorkSpace/QMS/.kiro/specs/qms-foundation-and-auth/requirements.md)
   底座模块的正式需求定义，覆盖认证、权限、工作台、通知、公告、系统配置、发布管理等。

4. [`.kiro/specs/qms-foundation-and-auth/design.md`](/E:/WorkSpace/QMS/.kiro/specs/qms-foundation-and-auth/design.md)
   底座模块的技术设计，包括双轨发布、共享数据库、认证策略、技术栈与架构约束。

5. [`.kiro/specs/qms-foundation-and-auth/tasks.md`](/E:/WorkSpace/QMS/.kiro/specs/qms-foundation-and-auth/tasks.md)
   可用来理解原始实施拆分，但要注意：
   这里的历史勾选状态不能直接等价为“当前业务能力已完整交付”。

### 第三层：理解需求编排与当前排期口径

6. [`doc/requirements-panel/QMS_FUNCTION_REQUIREMENTS.md`](/E:/WorkSpace/QMS/doc/requirements-panel/QMS_FUNCTION_REQUIREMENTS.md)
   按模块整理的功能条目清单，适合快速建立“模块-条目-优先级-范围”的整体认知。

7. [`frontend/src/features/requirements-panel/catalog.ts`](/E:/WorkSpace/QMS/frontend/src/features/requirements-panel/catalog.ts)
   当前需求目录与默认状态基线所在位置，是需求面板的数据基础。

8. [`frontend/src/features/requirements-panel/RequirementsPanel.vue`](/E:/WorkSpace/QMS/frontend/src/features/requirements-panel/RequirementsPanel.vue)
   当前需求面板实现，已包含总览、开发顺序、明细三种视图，以及开发顺序清单的批次划分逻辑。

### 第四层：按模块下钻时再查

- `backend/doc/`
  查看已实现或曾尝试实现的后端能力总结，适合在进入具体模块时快速定位模型、接口和联调背景。
- `frontend/doc/`
  查看前端页面、交互、环境切换等实现说明，适合进入具体页面开发前补背景。
- `.kiro/specs/` 下的其他规格文档
  如果后续新增模块规格，应优先阅读对应规格，而不是只依赖代码猜测。

## 5. 新线程通用切入方式

如果新线程是做任意功能模块开发，建议按下面顺序切入：

1. 先读 `product.md`，明确模块业务目标和边界。
2. 再读对应规格文档或相关实现文档，理解设计约束和已有方案。
3. 然后核对当前代码是否真正具备：
   - 页面入口
   - 核心数据模型
   - API 闭环
   - 权限控制
   - 状态流转
   - 联调可用性
4. 如果只有接口、模型或页面骨架，不要直接标记为已完成。
5. 开发推进后，再回到需求面板同步优先级判断和开发状态。

## 6. 对新线程最重要的提醒

- 不要把历史“完成总结”直接当成现状结论。
- 不要把接口存在当成功能完成。
- 优先用当前代码、当前页面和联调结果来判断真实完成度。
- 开发完成一个子模块后，记得同步更新需求面板中的开发顺序、优先级判断与状态。
