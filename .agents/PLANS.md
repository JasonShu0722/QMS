# ExecPlan 模板（QMS）

> 这是一份活文档。创建任务计划后，必须随着执行持续更新：
> `进度`、`意外发现`、`决策日志`、`验证证据`、`回顾`。
>
> 使用前先阅读：
> - [`AGENTS.md`](/E:/WorkSpace/QMS/AGENTS.md)
> - [`doc/PROJECT_DEVELOPMENT_HANDOFF.md`](/E:/WorkSpace/QMS/doc/PROJECT_DEVELOPMENT_HANDOFF.md)

---

## 任务名称
[在这里填写任务名称]

## 任务元信息
- 模块：
- 需求来源：
- 关联文档：
- 风险等级：
- 是否涉及双环境 / feature flag：
- 是否需要更新需求面板：
- 是否需要回写 `.kiro` 源文档：

---

## 目的 / 用户可观察结果

[描述这个变更完成后，用户能获得什么。]
[只写用户可感知的结果，不写底层实现细节。]
[尽量给出输入 / 输出或页面 / 接口可观察行为。]

---

## 非目标

- [明确这次不做什么]
- [防止执行过程中范围漂移]

---

## 前置阅读

- [`doc/PROJECT_DEVELOPMENT_HANDOFF.md`](/E:/WorkSpace/QMS/doc/PROJECT_DEVELOPMENT_HANDOFF.md)
- [按任务补充具体文档]
- [按模块补充 `.kiro/specs/`、`backend/doc/`、`frontend/doc/`]

---

## 里程碑与验证

- [ ] 步骤 1：确认范围、依赖和现状
  - 验证：列出已确认的需求项、边界、风险与现状判断
- [ ] 步骤 2：完成后端实现或契约调整
  - 验证：`& '.\\.venv\\Scripts\\python.exe' -m pytest backend/test/[相关测试文件]`
- [ ] 步骤 3：完成前端实现或交互收口
  - 验证：`Set-Location frontend; npm run build`
- [ ] 步骤 4：补齐最小自动化验证
  - 验证：`Set-Location frontend; npm run test:foundation` / `& '.\\.venv\\Scripts\\python.exe' backend/scripts/run_foundation_smoke.py`
- [ ] 步骤 5：联调双环境或部署链路（如适用）
  - 验证：`docker compose config`
- [ ] 步骤 6：更新需求面板 / 专题文档 / 交付记录
  - 验证：记录本次变更影响的需求项、状态与验证口径
- [ ] 步骤 7：如有需求或设计升级，同步回写 `.kiro` 源文档
  - 验证：确认 `.kiro/steering/product.md`、`.kiro/steering/structure.md`、`.kiro/specs/qms-foundation-and-auth/requirements.md`、`.kiro/specs/qms-foundation-and-auth/design.md` 中受影响内容已更新

---

## 进度

- [ ] 待开始
- [ ] 进行中
- [ ] 已完成

> 每次停止前都要更新这一节，确保它反映真实当前状态。

---

## 意外发现 & 新发现

- [记录执行过程中发现的旧实现缺口、历史假设错误、联调阻塞、环境问题]

---

## 决策日志

| 日期 | 决策 | 理由 |
|------|------|------|
| | | |

---

## 验证证据

- 构建：
- 测试：
- 联调：
- 截图 / 接口返回：

---

## 回退思路

- [如果这次改动存在风险，写清楚最小回退路径]

---

## 完成回顾

- 做对了什么：
- 还欠什么：
- 下次应提前规避什么：

---

## 完成检查清单

- [ ] 页面或接口具备真实闭环，不只是骨架存在
- [ ] 权限、状态流转、环境差异已确认
- [ ] 自动化验证已补齐或明确说明缺口
- [ ] 需求面板 / 文档已同步
- [ ] 如果任务升级了需求或设计，相关 `.kiro` 源文档已同步
- [ ] 最终说明包含结果、验证、剩余风险
