# 环境配置说明

这份文档专门说明项目里几套环境文件的职责，避免把“本地 / 服务器部署”和“正式版 / 预览版”混在一起。

## 一、先分清两层概念

### 1. 运行位置

- 本地开发
- 云服务器部署

这一层决定主要使用哪份配置文件。

### 2. 业务环境

- `stable`：正式版
- `preview`：预览版

这一层决定用户登录到哪个业务环境，以及网关把请求转发到哪套服务。

`.env` 和 `.env.production` 不是拿来切换业务环境本身的。
它们更像是“系统运行参数”和“部署参数”。

## 二、项目里的关键规则

### 1. 双域名入口

当前线上部署按两套域名入口运行：

- 正式版：`qms.bigshuaibee.cn`
- 预览版：`preview.qms.bigshuaibee.cn`

Nginx 会根据域名把请求转发到：

- `frontend-stable` / `backend-stable`
- `frontend-preview` / `backend-preview`

### 2. 页面保留环境切换按钮

这不是和双域名冲突，而是项目定义的一部分。

- 在线上环境中，点击“正式版 / 预览版”按钮，本质上是在两个入口域名之间切换
- 在本地开发中，没有双域名，所以按钮退化为切换本地保存的 `current_environment`

### 3. 登录请求仍显式携带 environment

登录请求依旧会带上：

- `environment=stable`
- `environment=preview`

这样后端可以继续基于用户权限做环境准入校验。

## 三、几份环境文件分别做什么

### 1. 根目录 `.env`

路径：

```text
.env
```

用途：

- 主要给根目录 `docker-compose.yml` 在本地运行时做变量替换
- 适合本机 Docker 启动基础设施或整套容器时使用

典型内容：

- 数据库密码
- Redis 密码
- 本地域名 / CORS
- Nginx 模板变量

说明：

- 它服务的是“本地运行方式”
- 不代表正式版或预览版

### 2. 根目录 `.env.production`

路径：

```text
.env.production
```

用途：

- 给云服务器上的 `docker compose --env-file .env.production ...` 使用
- 给部署脚本和校验脚本读取

当前会影响：

- Docker Compose 变量替换
- 服务器部署脚本
- Nginx 域名模板渲染
- 生产 CORS 配置

说明：

- 它代表“服务器部署参数”
- 不是正式版 / 预览版切换开关

### 3. `backend/.env`

路径：

```text
backend/.env
```

用途：

- 后端本地直接运行时读取
- 由 `backend/app/core/config.py` 中的 `env_file=".env"` 加载

适用场景：

- 在 `backend` 目录执行 `uvicorn`
- 在 `backend` 目录执行 `alembic`
- 在 `backend` 目录执行本地调试脚本

### 4. `frontend/.env.development`

路径：

```text
frontend/.env.development
```

用途：

- 前端本地 `npm run dev` 时读取

当前推荐值：

```env
VITE_API_BASE_URL=/api
VITE_ENVIRONMENT=stable
```

说明：

- `VITE_API_BASE_URL=/api`
  让 Vite 代理请求到本地后端，避免浏览器跨域
- `VITE_ENVIRONMENT=stable`
  只是本地默认语义
  真正线上环境切换仍由双域名入口加按钮行为共同决定

## 四、正式版 / 预览版到底由什么决定

### 1. Docker Compose 服务拆分

在 [docker-compose.yml](/E:/WorkSpace/QMS/docker-compose.yml) 中已拆成：

- `backend-stable`
- `backend-preview`
- `frontend-stable`
- `frontend-preview`

其中：

- `backend-stable` 注入 `ENVIRONMENT=stable`
- `backend-preview` 注入 `ENVIRONMENT=preview`
- 两套前端镜像分别构建正式版和预览版入口

### 2. 网关按域名路由

在 [nginx.conf.template](/E:/WorkSpace/QMS/deployment/nginx/nginx.conf.template) 中：

- `PRIMARY_DOMAIN` 路由到稳定环境
- `PREVIEW_DOMAIN` 路由到预览环境

### 3. 登录请求中的 `environment`

后端登录接口会读取登录请求中的 `environment` 字段。

相关代码：

- [auth.py](/E:/WorkSpace/QMS/backend/app/api/v1/auth.py)
- [user.py](/E:/WorkSpace/QMS/backend/app/schemas/user.py)

### 4. 用户本身的环境权限

数据库用户有 `allowed_environments` 字段，用于控制其可登录的业务环境。

相关代码：

- [user.py](/E:/WorkSpace/QMS/backend/app/models/user.py)
- [create_admin.py](/E:/WorkSpace/QMS/backend/scripts/create_admin.py)

### 5. 前端运行时环境状态

前端当前运行环境统一由以下规则决定：

- 线上：优先看当前域名
- 本地：看 `localStorage.current_environment`

相关代码：

- [useEnvironment.ts](/E:/WorkSpace/QMS/frontend/src/composables/useEnvironment.ts)
- [auth.ts](/E:/WorkSpace/QMS/frontend/src/stores/auth.ts)
- [Login.vue](/E:/WorkSpace/QMS/frontend/src/views/Login.vue)
- [MainLayout.vue](/E:/WorkSpace/QMS/frontend/src/layouts/MainLayout.vue)
- [MobileLayout.vue](/E:/WorkSpace/QMS/frontend/src/layouts/MobileLayout.vue)

## 五、推荐使用方式

### 本地开发

- 根目录 `.env`：给 Docker Compose 用
- `backend/.env`：给后端本地进程用
- `frontend/.env.development`：给前端本地开发服务器用

### 云服务器部署

- 根目录 `.env.production`：给 Compose、部署脚本、Nginx 模板统一使用

## 六、当前已经统一的约定

- 本地前端默认使用 `VITE_API_BASE_URL=/api`
- 本地前端默认使用 `VITE_ENVIRONMENT=stable`
- 服务器部署必须显式使用 `docker compose --env-file .env.production`
- 正式版与预览版在线上由双域名入口加按钮切换共同实现
- 前端登录页、桌面布局、移动布局都复用同一套环境切换逻辑
