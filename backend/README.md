# QMS Backend - 质量管理系统后端

## 项目结构

```
backend/
├── app/
│   ├── api/              # API 路由层
│   │   └── v1/           # API 版本 1
│   ├── core/             # 核心配置
│   │   └── config.py     # 环境变量配置
│   ├── models/           # SQLAlchemy 数据库模型
│   ├── schemas/          # Pydantic 数据校验模型
│   ├── services/         # 业务逻辑层
│   └── main.py           # FastAPI 应用入口
├── alembic/              # 数据库迁移脚本
├── requirements.txt      # Python 依赖包
├── Dockerfile            # 容器构建文件
└── .env.example          # 环境变量模板
```

## 技术栈

- **Web 框架**: FastAPI + Uvicorn (ASGI)
- **数据库**: PostgreSQL 15+ (通过 SQLAlchemy 2.0 Async ORM)
- **数据迁移**: Alembic
- **数据校验**: Pydantic V2
- **认证**: Python-Jose (JWT) + Passlib (密码哈希)
- **任务队列**: Celery + Redis
- **HTTP 客户端**: HTTPX (用于 IMS 集成)
- **邮件**: aiosmtplib

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并修改配置：

```bash
cp .env.example .env
```

### 3. 初始化数据库迁移

```bash
alembic upgrade head
```

### 4. 启动开发服务器

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

访问 API 文档：http://localhost:8000/api/docs

## Docker 部署

### 构建镜像

```bash
docker build -t qms-backend:latest .
```

### 运行容器

```bash
docker run -d \
  --name qms-backend \
  -p 8000:8000 \
  --env-file .env \
  qms-backend:latest
```

## 数据库迁移

### 创建新迁移

```bash
alembic revision --autogenerate -m "描述变更内容"
```

### 执行迁移

```bash
alembic upgrade head
```

### 回滚迁移

```bash
alembic downgrade -1
```

## 双轨发布注意事项

本系统采用 Preview 和 Stable 双轨发布架构，共享同一数据库。

**数据库迁移规范**：
- ✅ 允许：新增表、新增字段（必须 nullable=True 或有 server_default）
- ❌ 禁止：删除字段、重命名字段、修改字段类型

## 开发规范

- 遵循 **Clean Architecture** 分层原则
- 所有数据库操作使用 **async/await**
- 业务逻辑放在 `services/` 层，不要写在路由中
- 使用 `snake_case` 命名文件和函数
- 使用 `PascalCase` 命名类

## API 文档

启动服务后访问：
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc
