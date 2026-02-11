# QMS 质量管理系统 (Quality Management System)

企业级质量管理系统，专为汽车电子制造行业设计，实现供应商质量管理、过程质量控制、客户质量追溯的全流程数字化。

## 项目概述

本系统采用 **Monorepo + Docker Compose** 架构，实现 **Preview（预览环境）与 Stable（正式环境）双轨并行运行**，共享同一 PostgreSQL 数据库底座。

### 核心特性

- **统一认证入口**：支持内部员工（账号密码/LDAP）和外部供应商（账号密码+验证码）的统一登录
- **细粒度权限控制**：基于"功能模块-操作类型"的二维权限矩阵
- **千人千面工作台**：根据用户角色动态渲染个性化看板和待办任务聚合
- **移动端响应式**：跨设备适配，支持现场扫码和离线暂存
- **双轨发布机制**：新功能在预览环境验证后平滑发布到正式环境
- **IMS 系统集成**：自动同步物料入库、生产数据，实时计算质量指标

## 技术栈

### 后端
- **语言**: Python 3.10+
- **框架**: FastAPI (高性能异步 Web 框架)
- **数据库**: PostgreSQL 15+ (主数据库) + Redis 7+ (缓存/队列)
- **ORM**: SQLAlchemy 2.0+ (Async)
- **任务队列**: Celery + Redis
- **认证**: Python-Jose (JWT) + LDAP3 (预留)
- **数据校验**: Pydantic V2

### 前端
- **框架**: Vue 3 (Composition API) + Vite
- **UI 组件**: Element Plus (桌面端) + Tailwind CSS (移动端)
- **状态管理**: Pinia
- **图表**: ECharts
- **HTTP 客户端**: Axios

### 基础设施
- **容器编排**: Docker Compose
- **网关**: Nginx (反向代理 + 路由分发)
- **数据库迁移**: Alembic

## 双轨发布架构

系统通过 Nginx 基于域名的路由规则，将请求分发到不同的容器实例：

```
用户访问
  ├── qms.company.com (正式环境)
  │   ├── 前端: frontend-stable
  │   └── 后端: backend-stable
  │
  └── preview.company.com (预览环境)
      ├── 前端: frontend-preview
      └── 后端: backend-preview
      
共享数据底座
  ├── PostgreSQL (主数据库)
  └── Redis (缓存/队列)
```

### 架构优势

1. **零停机发布**：新功能在预览环境验证，不影响正式环境用户
2. **数据一致性**：两个环境共享数据库，确保数据实时互通
3. **灰度测试**：通过功能开关控制新功能的发布范围
4. **快速回滚**：发现问题可立即切换回稳定版本

### 数据库兼容性原则

为确保双轨环境稳定运行，数据库迁移必须遵循**非破坏性原则**：

✅ **允许的操作**：
- 新增表
- 新增字段（必须设置为 `nullable=True` 或带有 `server_default`）
- 新增索引

❌ **禁止的操作**：
- 删除字段 (`op.drop_column()`)
- 删除表 (`op.drop_table()`)
- 修改字段类型 (`ALTER COLUMN`)
- 重命名字段/表

## 快速开始

### 环境要求

- Docker 20.10+
- Docker Compose 2.0+
- Python 3.10+ (本地开发)
- Node.js 18+ (本地开发)

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd QMS
```

2. **配置环境变量**
```bash
cp .env.example .env
# 编辑 .env 文件，填写实际的密码和配置
```

3. **启动所有服务**
```bash
# 构建并启动所有容器（后台运行）
docker compose up -d --build

# 查看服务状态
docker compose ps

# 查看日志
docker compose logs -f backend-stable
docker compose logs -f frontend-stable
```

4. **执行数据库迁移**
```bash
# 正式环境
docker compose exec backend-stable alembic upgrade head

# 预览环境
docker compose exec backend-preview alembic upgrade head
```

5. **访问系统**
- 正式环境: http://localhost (或配置的域名)
- 预览环境: http://localhost:8081 (或配置的预览域名)
- API 文档: http://localhost/api/docs

### 本地开发

#### 后端开发
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

#### 前端开发
```bash
cd frontend
npm install
npm run dev
```

## 项目结构

```
QMS/
├── backend/                 # 后端应用
│   ├── app/
│   │   ├── api/            # API 路由
│   │   │   └── v1/         # API 版本 1
│   │   ├── core/           # 核心配置（认证、权限、配置）
│   │   ├── models/         # SQLAlchemy 数据模型
│   │   ├── schemas/        # Pydantic 数据校验模型
│   │   ├── services/       # 业务逻辑层
│   │   └── main.py         # 应用入口
│   ├── alembic/            # 数据库迁移脚本
│   ├── tests/              # 测试用例
│   ├── requirements.txt    # Python 依赖
│   └── Dockerfile          # 后端容器构建文件
│
├── frontend/               # 前端应用
│   ├── src/
│   │   ├── api/           # API 调用封装
│   │   ├── assets/        # 静态资源
│   │   ├── components/    # 公共组件
│   │   ├── layouts/       # 页面布局
│   │   ├── stores/        # Pinia 状态管理
│   │   ├── views/         # 页面视图
│   │   ├── router/        # 路由配置
│   │   └── main.ts        # 前端入口
│   ├── package.json       # Node.js 依赖
│   └── Dockerfile         # 前端容器构建文件
│
├── deployment/            # 部署配置
│   └── nginx/
│       └── nginx.conf     # Nginx 配置文件
│
├── docker-compose.yml     # 容器编排配置
├── .env.example           # 环境变量模板
├── .gitignore            # Git 忽略文件
└── README.md             # 项目说明文档
```

## 常用命令

### Docker 操作
```bash
# 启动所有服务
docker compose up -d

# 停止所有服务
docker compose down

# 重启特定服务
docker compose restart backend-stable

# 查看日志
docker compose logs -f backend-stable
docker compose logs -f frontend-preview

# 进入容器
docker compose exec backend-stable bash
docker compose exec postgres psql -U qms_user -d qms_db
```

### 数据库操作
```bash
# 创建新的迁移脚本
docker compose exec backend-stable alembic revision --autogenerate -m "描述"

# 执行迁移
docker compose exec backend-stable alembic upgrade head

# 回滚迁移
docker compose exec backend-stable alembic downgrade -1

# 查看迁移历史
docker compose exec backend-stable alembic history
```

### 测试
```bash
# 后端测试
docker compose exec backend-stable pytest

# 前端测试
docker compose exec frontend-stable npm run test
```

## 功能模块

### 已实现模块
- ✅ 用户注册与审核
- ✅ 统一登录与身份认证
- ✅ 细粒度权限控制
- ✅ 操作日志审计
- ✅ 个人中心与工作台
- ✅ 待办任务聚合
- ✅ 站内信通知
- ✅ 公告管理
- ✅ 功能特性开关

### 开发中模块
- 🚧 供应商质量管理
- 🚧 过程质量管理
- 🚧 客户质量管理
- 🚧 新品质量管理
- 🚧 审核管理

### 预留模块
- ⏸️ 仪器与量具管理
- ⏸️ 质量成本管理

## 部署说明

### 生产环境部署

1. **配置 SSL 证书**
```bash
# 将证书文件放置到 deployment/nginx/certs/
deployment/nginx/certs/
├── qms.company.com.crt
├── qms.company.com.key
├── preview.company.com.crt
└── preview.company.com.key
```

2. **配置域名解析**
- qms.company.com → 服务器 IP
- preview.company.com → 服务器 IP

3. **启动生产环境**
```bash
docker compose -f docker-compose.prod.yml up -d --build
```

### 网络配置

系统部署在 DMZ 区，需要配置双网卡：
- **外网网卡**：响应前端用户请求
- **内网网卡**：访问 IMS 系统获取生产数据

## 安全注意事项

1. **密码策略**：强制密码复杂度（大写、小写、数字、特殊字符中至少三种，长度>8位）
2. **登录保护**：连续 5 次错误锁定账号 30 分钟
3. **定期修改**：密码 90 天强制修改
4. **数据隔离**：供应商用户仅能查看关联到其自身的数据
5. **操作审计**：所有关键操作记录日志

## 贡献指南

请参考 [CONTRIBUTING.md](CONTRIBUTING.md)

## 许可证

[待定]

## 联系方式

- 项目负责人: [待填写]
- 技术支持: [待填写]
- 问题反馈: [待填写]
