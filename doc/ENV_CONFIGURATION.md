# 环境配置说明

这份文档专门说明项目里几套环境文件的职责，避免把“本地 / 服务器部署”与“正式版 / 预览版”混在一起。

## 一、先分清两层概念

### 1. 运行位置

- 本地开发
- 云服务器部署

这一层决定你主要使用哪份配置文件。

### 2. 业务环境

- `stable`：正式版
- `preview`：预览版

这一层决定用户登录到哪个业务环境，以及 Docker Compose 启动哪组前后端服务。

`.env` 和 `.env.production` 不是用来在业务上切换 `stable / preview` 的，它们更像是“在哪运行、运行参数是什么”。

## 二、项目里几份环境文件各自做什么

### 1. 根目录 `.env`

文件路径：

```text
.env
```

用途：

- 主要给根目录 `docker-compose.yml` 在本地开发时做变量替换
- 适合本机 Docker 启动基础设施或整套容器时使用

典型内容：

- 数据库密码
- Redis 密码
- 本地域名/CORS
- Nginx 模板注入变量

注意：

- 它服务的是“本地运行方式”
- 它不代表“正式版”或者“预览版”

### 2. 根目录 `.env.production`

文件路径：

```text
.env.production
```

用途：

- 给云服务器上的 `docker compose --env-file .env.production ...` 使用
- 给 `deployment/deploy.sh`、`deployment/verify_deployment.sh` 读取

当前仓库里，这份文件会影响：

- Docker Compose 的变量替换
- 服务器部署脚本
- Nginx 域名模板渲染
- 生产 CORS 配置

注意：

- 它代表“服务器部署参数”
- 它也不是“正式版 / 预览版切换开关”

### 3. `backend/.env`

文件路径：

```text
backend/.env
```

用途：

- 后端本地直接运行时读取
- 由 `backend/app/core/config.py` 中的 `env_file=".env"` 加载

适用场景：

- 你在 `backend` 目录执行 `uvicorn`
- 你在 `backend` 目录执行 `alembic`
- 你在 `backend` 目录执行本地调试脚本

注意：

- 这是“后端本地进程配置”
- 它和根目录 `.env` 不是同一份职责

### 4. `frontend/.env.development`

文件路径：

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

- `VITE_API_BASE_URL=/api`：让 Vite 代理请求到本地后端，避免浏览器跨域
- `VITE_ENVIRONMENT=stable`：本地开发默认按正式版语义启动，但登录页仍然可以切换到预览版登录目标

## 三、正式版 / 预览版到底由什么决定

真正控制 `stable / preview` 的是下面几项：

### 1. Docker Compose 服务拆分

在 [docker-compose.yml](/E:/WorkSpace/QMS/docker-compose.yml) 中已经拆成：

- `backend-stable`
- `backend-preview`
- `frontend-stable`
- `frontend-preview`

其中：

- `backend-stable` 明确注入 `ENVIRONMENT=stable`
- `backend-preview` 明确注入 `ENVIRONMENT=preview`
- 两套前端镜像分别注入 `VITE_ENVIRONMENT=stable` 和 `VITE_ENVIRONMENT=preview`

### 2. 登录请求携带的 `environment`

后端登录接口会读取登录请求里的 `environment` 字段。

相关代码：

- [auth.py](/E:/WorkSpace/QMS/backend/app/api/v1/auth.py)
- [user.py](/E:/WorkSpace/QMS/backend/app/schemas/user.py)

### 3. 用户自身的环境权限

数据库里用户有 `allowed_environments` 字段，用来限制该用户可登录哪些环境。

相关代码：

- [user.py](/E:/WorkSpace/QMS/backend/app/models/user.py)

### 4. 前端本地存储的当前环境

前端登录后会把当前业务环境保存到 `localStorage` 的 `current_environment`。

相关代码：

- [auth.ts](/E:/WorkSpace/QMS/frontend/src/stores/auth.ts)

## 四、推荐使用方式

### 本地开发

- 根目录 `.env`：给 Docker Compose 用
- `backend/.env`：给后端本地进程用
- `frontend/.env.development`：给前端本地开发服务器用

### 云服务器部署

- 根目录 `.env.production`：给 Compose、部署脚本、Nginx 模板统一使用

## 五、当前我们已经对齐的约定

- 本地前端默认使用 `VITE_API_BASE_URL=/api`
- 本地前端默认使用 `VITE_ENVIRONMENT=stable`
- 服务器部署必须显式使用 `docker compose --env-file .env.production`
- 正式版与预览版继续由双服务和登录环境控制，不由 `.env.production` 取代
