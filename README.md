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

## 推荐启动方式：本地调试

这是当前最适合开发和排查问题的方式。

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

## 容器模式启动

如果你想整套服务都在容器中运行，可以在根目录执行：

```bash
docker compose up -d --build
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
