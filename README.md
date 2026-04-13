# QMS

质量管理系统（Quality Management System）单仓库项目，包含：

- `backend`：FastAPI 后端
- `frontend`：Vue 3 + Vite 前端
- `deployment`：Docker / Nginx / 部署脚本

当前仓库适合两种启动方式：

- 本地调试模式：`PostgreSQL + Redis` 用 Docker，前后端用本地进程启动
- 容器模式：整套服务全部通过 Docker Compose 启动

## 技术栈

### 后端

- Python 3.10+
- FastAPI
- SQLAlchemy Async
- PostgreSQL
- Redis
- Alembic
- Celery

### 前端

- Vue 3
- Vite
- TypeScript
- Element Plus
- Pinia
- Axios

## 目录结构

```text
QMS/
├─ backend/        # 后端服务
├─ frontend/       # 前端应用
├─ deployment/     # 部署相关文件
├─ docker-compose.yml
└─ README.md
```

## 推荐启动方式：日常开发模式

这是当前最适合开发、联调和排查问题的方式。推荐约定如下：

- 日常开发模式：只保留 `postgres` / `redis` 容器，后端本地运行在 `8000`，前端本地运行在 `5173`
- 容器验收模式：需要验证 `stable / preview` 双环境行为时，再启动或重启 `qms_backend_stable` / `qms_backend_preview`

### 1. 环境要求

- Docker Desktop
- Python 虚拟环境已安装后端依赖
- Node.js 18+
- 前端依赖已安装

### 2. 启动基础设施

在项目根目录执行：

```bash
docker compose up -d postgres redis
```

确认服务状态：

```bash
docker compose ps
```

默认本地端口：

- PostgreSQL：`5432`
- Redis：`6379`

### 3. 启动后端

在 `backend` 目录执行：

```bash
E:\WorkSpace\QMS\backend\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

如果你使用激活虚拟环境的方式，也可以：

```bash
cd backend
.venv\Scripts\activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

后端健康检查：

```text
http://localhost:8000/health
```

后端接口文档：

```text
http://localhost:8000/api/docs
```

### 3.1 本地调试时重启 8000 后端

本地联调统一约定后端固定使用 `8000`，前端开发代理默认也指向这个端口。日常改完后端代码、数据库迁移或系统管理相关设计后，需要把本机 `8000` 切换到“当前工作区最新后端”，不要临时改成其他端口。

如果 `8000` 仍被 Docker 稳定后端占用，请按下面步骤处理：

```powershell
# 1. 释放 8000（只停 stable 后端，保留 postgres / redis / preview）
Set-Location E:\WorkSpace\QMS
docker compose stop backend-stable

# 1.1 如果 8000 已被旧的本地后端占用，先确认 PID 再结束旧进程
Get-NetTCPConnection -LocalPort 8000 -State Listen
Get-Process -Id <PID>
Stop-Process -Id <PID>

# 2. 升级数据库到最新迁移
Set-Location E:\WorkSpace\QMS\backend
.venv\Scripts\python.exe -m alembic upgrade head

# 3. 用 backend/.venv 在 8000 启动当前工作区后端
Start-Process `
  -FilePath E:\WorkSpace\QMS\backend\.venv\Scripts\python.exe `
  -ArgumentList '-m','uvicorn','app.main:app','--host','0.0.0.0','--port','8000','--reload' `
  -WorkingDirectory E:\WorkSpace\QMS\backend `
  -RedirectStandardOutput E:\WorkSpace\QMS\backend-dev-8000.log `
  -RedirectStandardError E:\WorkSpace\QMS\backend-dev-8000.err.log
```

启动后建议立即验证：

```powershell
Invoke-WebRequest http://127.0.0.1:8000/health -UseBasicParsing
Get-NetTCPConnection -LocalPort 8000 -State Listen
```

期望结果：

- `/health` 返回 `{"status":"healthy"}`
- `8000` 监听进程为本地 Python / Uvicorn，而不是 Docker `backend-stable` 端口映射

如果之后要切回容器版稳定后端：

```powershell
Set-Location E:\WorkSpace\QMS
docker compose up -d backend-stable
```

### 4. 启动前端

在 `frontend` 目录执行：

```bash
npm run dev
```

前端默认地址：

```text
http://localhost:5173
```

### 5. 本地调试配置说明

当前开发环境已经按本地调试方式配置：

- 后端本地配置文件：`backend/.env`
- 前端开发配置文件：`frontend/.env.development`

其中前端开发环境使用：

```env
VITE_API_BASE_URL=/api
```

这意味着前端会通过 Vite 代理访问后端，不需要浏览器直接跨域请求 `http://localhost:8000`。

### 6. 本地登录验证

当前本地库中已确认存在管理员账号：

- 用户名：`Admin`
- 用户类型：内部员工

如密码忘记，需要在数据库或脚本中重置，不建议只依赖历史文档中的默认密码。

## 代码变更后的处理规则

当前 `backend-stable` 和 `backend-preview` 共享同一份后端代码挂载、同一个数据库，只是 `ENVIRONMENT` 不同。因此：

- 数据库迁移只需要执行一次，不需要对 stable / preview 各跑一遍
- 后端代码变更后，如果你在用容器验收模式，需要同时让两个后端服务吃到新代码

### 1. 纯 Python / FastAPI 代码改动

- 本地日常开发模式：本地 `uvicorn --reload` 会自动生效，通常不需要手工重启
- 容器验收模式：重启两个后端容器

```bash
docker compose restart backend-stable backend-preview
```

### 2. 数据库模型 / Alembic 迁移改动

- 先执行一次迁移
- 再重启两个后端容器

```bash
cd backend
.venv\Scripts\python.exe -m alembic upgrade head

cd ..
docker compose restart backend-stable backend-preview
```

### 3. 依赖、Dockerfile、镜像层改动

- 仅重启不够，需要重新构建镜像

```bash
docker compose up -d --build backend-stable backend-preview
```

### 4. Celery 任务、通知、定时任务相关改动

- 除后端外，还要同步重启 worker / beat

```bash
docker compose restart backend-stable backend-preview celery-worker celery-beat
```

## 容器模式启动

如果你想整套服务都在容器中运行，可以在根目录执行：

```bash
docker compose up -d --build
```

服务器部署时请显式使用生产环境文件：

```bash
docker compose --env-file .env.production up -d --build
```

查看状态：

```bash
docker compose ps
```

查看日志：

```bash
docker compose logs -f backend-stable
docker compose logs -f frontend-stable
```

## 数据库迁移

### 本地执行

在 `backend` 目录执行：

```bash
E:\WorkSpace\QMS\backend\.venv\Scripts\python.exe -m alembic upgrade head
```

### 容器内执行

```bash
docker compose exec backend-stable alembic upgrade head
```

## 测试

### 后端测试

```bash
cd backend
.venv\Scripts\python.exe -m pytest
```

### 前端测试

```bash
cd frontend
npm run test
```

## 常用命令

### 停止基础设施

```bash
docker compose stop postgres redis
```

### 停止全部容器

```bash
docker compose down
```

### 查看数据库连接

后端本地 `.env` 默认使用：

```env
DATABASE_URL=postgresql+asyncpg://qms_user:qms_dev_password@localhost:5432/qms_db
```

## 当前建议

日常开发建议使用下面这套组合：

1. `docker compose up -d postgres redis`
2. 本地启动 `backend`
3. 本地启动 `frontend`

这样调试速度快，日志清晰，改动即时生效，更适合问题定位和功能优化。
