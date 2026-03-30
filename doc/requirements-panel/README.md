# Requirements Panel README

## 1. 面板定位

需求看板是一个挂载在 QMS 子路径下的独立页面，用于：

- 汇总 QMS 项目的功能需求条目
- 按模块和整体优先级可视化展示开发状态
- 在联调和验收完成后，在线维护功能状态

这套面板**独立于 QMS 主系统账号体系**：

- 不复用 QMS 的内部员工账号
- 不复用 QMS 的供应商账号
- 使用专门的看板账号登录

## 2. 访问入口

当前线上入口如下：

- 正式版入口：[https://qms.bigshuaibee.cn/requirements-panel](https://qms.bigshuaibee.cn/requirements-panel)
- 预览版入口：[https://preview.qms.bigshuaibee.cn/requirements-panel](https://preview.qms.bigshuaibee.cn/requirements-panel)

本地开发入口：

- `/requirements-panel`

## 3. 默认账号

默认独立账号由 [create_requirements_panel_users.py](/E:/WorkSpace/QMS/backend/scripts/create_requirements_panel_users.py) 初始化。

管理员账号：

- 用户名：`requirements_admin`
- 密码：`ReqPanelAdmin@2026`
- 权限：可登录、可在线调整功能状态

普通查阅账号：

- 用户名：`requirements_viewer`
- 密码：`ReqPanelViewer@2026`
- 权限：可登录、仅查阅，不可修改状态

如果后续需要改成正式公司口径账号，可以通过环境变量覆盖：

- `REQ_PANEL_ADMIN_USERNAME`
- `REQ_PANEL_ADMIN_PASSWORD`
- `REQ_PANEL_ADMIN_FULL_NAME`
- `REQ_PANEL_VIEWER_USERNAME`
- `REQ_PANEL_VIEWER_PASSWORD`
- `REQ_PANEL_VIEWER_FULL_NAME`

## 4. 文件结构

### 4.1 文档与静态原型

当前目录 [requirements-panel](/E:/WorkSpace/QMS/doc/requirements-panel) 下文件说明：

- [README.md](/E:/WorkSpace/QMS/doc/requirements-panel/README.md)
  这份总说明文档
- [QMS_FUNCTION_REQUIREMENTS.md](/E:/WorkSpace/QMS/doc/requirements-panel/QMS_FUNCTION_REQUIREMENTS.md)
  需求条目与优先级梳理文档
- [qms-requirements-data.js](/E:/WorkSpace/QMS/doc/requirements-panel/qms-requirements-data.js)
  静态数据源
- [qms-requirements-panel.html](/E:/WorkSpace/QMS/doc/requirements-panel/qms-requirements-panel.html)
  静态可视化原型面板

### 4.2 前端功能代码

前端功能代码统一放在 [frontend/src/features/requirements-panel](/E:/WorkSpace/QMS/frontend/src/features/requirements-panel)：

- [RequirementsPanel.vue](/E:/WorkSpace/QMS/frontend/src/features/requirements-panel/RequirementsPanel.vue)
  页面主视图
- [api.ts](/E:/WorkSpace/QMS/frontend/src/features/requirements-panel/api.ts)
  面板接口封装
- [request.ts](/E:/WorkSpace/QMS/frontend/src/features/requirements-panel/request.ts)
  独立请求客户端与独立登录态存储
- [types.ts](/E:/WorkSpace/QMS/frontend/src/features/requirements-panel/types.ts)
  类型定义
- [catalog.ts](/E:/WorkSpace/QMS/frontend/src/features/requirements-panel/catalog.ts)
  面板目录数据

### 4.3 后端独立认证与状态维护

后端暂时保持现有分层风格，不强行塞进单目录，避免破坏现有项目结构。核心文件如下：

- [requirements_panel.py](/E:/WorkSpace/QMS/backend/app/api/v1/requirements_panel.py)
- [requirements_panel_auth.py](/E:/WorkSpace/QMS/backend/app/api/v1/requirements_panel_auth.py)
- [requirements_panel_auth.py](/E:/WorkSpace/QMS/backend/app/core/requirements_panel_auth.py)
- [requirements_panel_user.py](/E:/WorkSpace/QMS/backend/app/models/requirements_panel_user.py)
- [requirements_panel_status.py](/E:/WorkSpace/QMS/backend/app/models/requirements_panel_status.py)
- [requirements_panel.py](/E:/WorkSpace/QMS/backend/app/schemas/requirements_panel.py)
- [create_requirements_panel_users.py](/E:/WorkSpace/QMS/backend/scripts/create_requirements_panel_users.py)
- [2026_03_30_1730-9c4d8e7a2b11_add_requirements_panel_statuses.py](/E:/WorkSpace/QMS/backend/alembic/versions/2026_03_30_1730-9c4d8e7a2b11_add_requirements_panel_statuses.py)

## 5. 权限规则

看板权限只有两类：

- `admin`
  可查看全部内容，可在线更新需求状态
- `viewer`
  可查看全部内容，不可更新状态

这套权限不进入 QMS 主系统权限矩阵，不依赖 `system.users` 或其他业务模块权限。

## 6. 维护方式

### 6.1 在线维护

联调或验收完成后，管理员可直接登录线上看板，在线调整条目状态。

推荐状态流转：

- `todo` -> `doing`
- `doing` -> `dev-done`
- `dev-done` -> `verified`

### 6.2 数据源维护

如果需要同步更新静态梳理内容或条目定义，优先维护：

- [QMS_FUNCTION_REQUIREMENTS.md](/E:/WorkSpace/QMS/doc/requirements-panel/QMS_FUNCTION_REQUIREMENTS.md)
- [qms-requirements-data.js](/E:/WorkSpace/QMS/doc/requirements-panel/qms-requirements-data.js)

### 6.3 账号初始化

如果服务器需要重新初始化独立账号，执行：

```bash
cd /www/qms/QMS
docker compose --env-file .env.production exec -T backend-stable python -m scripts.create_requirements_panel_users
```

## 7. 当前建议

当前这套组织方式已经比较适合持续维护：

- 文档归口到一个专属目录
- 前端功能代码归口到一个独立 feature 目录
- 后端保持现有分层，不做过度重构

如果后续这个看板继续扩展成完整子系统，再考虑把后端也升级成模块化目录。
