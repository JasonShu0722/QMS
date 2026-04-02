# AGENTS.md

## 项目概述
- 本文件基于 [`doc/PROJECT_DEVELOPMENT_HANDOFF.md`](/E:/WorkSpace/QMS/doc/PROJECT_DEVELOPMENT_HANDOFF.md) 提炼，作为 QMS 仓库的项目级协作契约。
- QMS 是一个质量管理系统，覆盖系统基础、质量看板、供应商质量、制程质量、客户质量、新品质量、审核管理及预留扩展模块。
- 仓库采用 Monorepo：
  - `backend/`：FastAPI + SQLAlchemy + Alembic
  - `frontend/`：Vue 3 + Vite + Element Plus + Pinia
  - `deployment/`：Nginx / Docker / 双环境部署配置

## 首次进入仓库先做什么
1. 先阅读 [`doc/PROJECT_DEVELOPMENT_HANDOFF.md`](/E:/WorkSpace/QMS/doc/PROJECT_DEVELOPMENT_HANDOFF.md)。
2. 再按任务类型做渐进式发现，不要一开始就通读整个仓库。
3. 开始实现前，先确认需求项属于哪个模块、批次和当前状态。
4. 不要把“页面存在 / 接口存在 / tasks.md 已勾选”直接当成功能已交付。

## 常用命令
- 前端开发：`Set-Location frontend; npm run dev`
- 前端构建：`Set-Location frontend; npm run build`
- 前端底座回归：`Set-Location frontend; npm run test:foundation`
- 后端测试：`& '.\\.venv\\Scripts\\python.exe' -m pytest backend/test`
- 后端底座 smoke：`& '.\\.venv\\Scripts\\python.exe' backend/scripts/run_foundation_smoke.py`
- 数据库迁移：`Set-Location backend; & '..\\.venv\\Scripts\\python.exe' -m alembic upgrade head`
- Compose 校验：`docker compose config`

## 项目结构
- `backend/app/`：后端 API、模型、服务与核心逻辑
- `backend/alembic/versions/`：数据库迁移版本，默认不要改历史文件
- `backend/test/`：后端接口与回归测试
- `backend/scripts/`：验证脚本、初始化脚本与 smoke 工具
- `frontend/src/views/`：页面级视图
- `frontend/src/router/`：前端路由守卫与页面入口
- `frontend/src/stores/`：认证、环境与全局状态
- `frontend/src/features/requirements-panel/`：需求面板实现与状态基线
- `doc/`：交接、规范、联调与专题文档

## 开发原则
- 先打通主链路，再做增强项。底座能力、权限、认证、工作台、通知、账号治理优先于局部页面打磨。
- 完成标准是“页面可操作、接口可联调、数据可闭环、权限可控制、状态可验证”，不是“文件或路由已经存在”。
- 模块排期服从系统依赖，先看是否依赖统一认证、权限矩阵、待办聚合、通知链路、身份隔离。
- 需求面板是编排工具，不是代码事实扫描器。默认对“历史已完成”保持审慎判断。
- 每推进一个模块，至少同步四件事：需求项顺序、优先级判断、开发状态、验证口径。
- 如果需求、规划或设计相较于 `.kiro/steering/product.md`、`.kiro/steering/structure.md`、`.kiro/specs/qms-foundation-and-auth/requirements.md`、`.kiro/specs/qms-foundation-and-auth/design.md` 发生升级，必须同步回写这些源文档，保持代码与文档一致。
- 前端界面文案默认保持克制，遵循 [`doc/FRONTEND_UI_COPY_REQUIREMENTS.md`](/E:/WorkSpace/QMS/doc/FRONTEND_UI_COPY_REQUIREMENTS.md)。

## 代码与变更要求
- 优先做小而可审查的 diff，避免无请求的大扫除式重构。
- 先搜索现有实现，再改动；不要凭空发明 API、配置、路径或数据结构。
- 保持现有架构和风格一致，优先顺着现有目录与模式延伸。
- 行为变更默认补测试；前端至少跑相关 vitest / build，后端至少跑相关 pytest。
- API 契约变更要保证前后端同步，不允许接口形状和页面消费长期脱节。
- 修改前端页面时，优先减少解释性文案，而不是新增副标题和说明段落。

## Git 与安全边界
- 不要回滚、覆盖或清理你没有充分理解的现有修改。
- 不要修改历史迁移文件，除非任务明确要求。
- 不要把密钥、口令、令牌、`.env` 内容写进代码、日志或测试断言。
- 新增生产依赖、外部网络调用、遥测或分析能力前先确认。
- 不要把“能运行”直接说成“可交付”，必须附带验证结果。

## 任务专属文档（渐进式发现）
- 项目全貌：[`doc/PROJECT_DEVELOPMENT_HANDOFF.md`](/E:/WorkSpace/QMS/doc/PROJECT_DEVELOPMENT_HANDOFF.md)
- 产品与结构：[`/.kiro/steering/product.md`](/E:/WorkSpace/QMS/.kiro/steering/product.md)、[`/.kiro/steering/structure.md`](/E:/WorkSpace/QMS/.kiro/steering/structure.md)
- 底座与认证：[`/.kiro/specs/qms-foundation-and-auth/requirements.md`](/E:/WorkSpace/QMS/.kiro/specs/qms-foundation-and-auth/requirements.md)、[`/.kiro/specs/qms-foundation-and-auth/design.md`](/E:/WorkSpace/QMS/.kiro/specs/qms-foundation-and-auth/design.md)
- 需求编排：[`doc/requirements-panel/QMS_FUNCTION_REQUIREMENTS.md`](/E:/WorkSpace/QMS/doc/requirements-panel/QMS_FUNCTION_REQUIREMENTS.md)、[`frontend/src/features/requirements-panel/catalog.ts`](/E:/WorkSpace/QMS/frontend/src/features/requirements-panel/catalog.ts)
- 前端文案约束：[`doc/FRONTEND_UI_COPY_REQUIREMENTS.md`](/E:/WorkSpace/QMS/doc/FRONTEND_UI_COPY_REQUIREMENTS.md)
- 后端专题文档：`backend/doc/`
- 前端专题文档：`frontend/doc/`

## 大型任务规划
- 当任务跨多个模块、持续时间较长、需要联调或可能影响底座时，先使用 [`.agents/PLANS.md`](/E:/WorkSpace/QMS/.agents/PLANS.md) 创建执行计划。
- 计划必须写清楚目标、非目标、验证命令、风险和回退思路，再开始编码。
- 执行过程中持续更新进度、意外发现、决策日志和验证证据。

## 完成前检查
- 相关构建或测试已运行，并记录结果。
- 需求面板或相关文档的状态与验证口径已同步。
- 如果本次变更升级了需求或设计，相关 `.kiro` 源文档已同步更新。
- 交付说明聚焦结果、风险、验证，不写冗长过程复述。
