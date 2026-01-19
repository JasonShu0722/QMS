---
inclusion: always
---

# Project Structure

## Organization

本项目采用 **Monorepo (单体仓库)** 结构，通过 Docker Compose 进行统一编排管理。代码库主要分为三个核心领域：

- **backend/**: Python FastAPI 应用（大脑 - 负责业务逻辑与 IMS 对接）。
- **frontend/**: Vue 3 + Vite 应用（脸面 - 负责用户交互与可视化）。
- **deployment/**: Nginx 配置与 Docker 资源（基础设施 - 负责网关与部署）。

## Folder Conventions

### Root Directory (根目录)
```text
/
├── .kiro/                  # Kiro configuration and steering rules (Kiro 配置与规则)
├── backend/                # Backend Application Code (后端代码主目录)
├── frontend/               # Frontend Application Code (前端代码主目录)
├── deployment/             # Nginx & Production Docker configs (部署配置)
├── docker-compose.yml      # Orchestration for Dev/Prod (容器编排文件)
├── .env.example            # Environment variables template (环境变量模板)
└── README.md

```

### Backend Structure (`/backend`)

遵循标准的 FastAPI 清洁架构 (Clean Architecture)。

```text
backend/
├── app/
│   ├── api/                # API Route Controllers (接口路由层)
│   │   └── v1/             # Versioning (版本控制，如 /api/v1/auth)
│   ├── core/               # Global configs (核心配置：安全、Celery、设置)
│   ├── models/             # SQLAlchemy Database Models (数据库ORM模型)
│   ├── schemas/            # Pydantic Schemas (数据校验与序列化模型)
│   ├── services/           # Business Logic (业务逻辑层：IMS对接、分数计算)
│   └── main.py             # App Entry Point (应用启动入口)
├── alembic/                # Database Migrations (数据库版本迁移脚本)
├── tests/                  # Pytest folder (测试用例)
├── requirements.txt        # Python dependencies (依赖包列表)
└── Dockerfile              # Backend Container Config (后端容器构建文件)

```

### Frontend Structure (`/frontend`)

遵循 Vue 3 + Vite 的标准目录结构。

```text
frontend/
├── src/
│   ├── api/                # Axios wrappers for Backend APIs (后端接口调用封装)
│   ├── assets/             # Static images, styles (静态资源)
│   ├── components/         # Reusable UI widgets (公共组件：表格、图表)
│   ├── layouts/            # Page layouts (页面布局：侧边栏、顶部栏)
│   ├── stores/             # Pinia State Management (状态管理：用户、权限)
│   ├── views/              # Page Views (页面视图：如 SupplierDashboard.vue)
│   ├── router/             # Vue Router configuration (路由配置)
│   └── main.ts             # Entry Point (前端入口)
├── index.html
├── package.json
└── Dockerfile              # Frontend Container Config (前端容器构建文件)

```

## File Naming

* **Python/Backend**: 使用 `snake_case` (蛇形命名法) 命名文件和变量。
* *示例*: `supplier_service.py`, `calculate_ppm()`
* *类名*: 使用 `PascalCase` (大驼峰)，例如 `class SupplierScorecard`


* **Vue/Frontend**:
* *组件/视图*: 使用 `PascalCase` (大驼峰)，例如 `AuditPlan.vue`
* *工具/脚本*: 使用 `camelCase` (小驼峰)，例如 `formatDate.ts`


* **API Endpoints**: URL 中使用 `kebab-case` (短横线命名)。
* *示例*: `GET /api/v1/supplier-scorecards`



## Architecture Patterns

本系统采用 **反向代理模式** 来安全地处理内部/外部网络流量，并作为连接公网供应商与内网 IMS 的桥梁。

### System Topology Diagram (系统拓扑图)

```mermaid
graph TD
    %% Define Styles
    classDef external fill:#f9f,stroke:#333,stroke-width:2px;
    classDef dmz fill:#ff9,stroke:#333,stroke-width:2px;
    classDef internal fill:#9f9,stroke:#333,stroke-width:2px;

    %% 1. External Zone (Internet)
    subgraph Internet [公网 / Internet]
        Supplier[供应商 PC / 手机]:::external
        Manager[公司领导 (外网访问)]:::external
    end

    %% 2. DMZ / Server Zone (Your QMS Server)
    subgraph QMS_Server [QMS 服务器 (DMZ区域)]
        direction TB
        
        %% Entry Point
        Nginx[Nginx 网关 (Port 80/443)]:::dmz
        
        %% Frontend Container
        Vue[前端容器 (Vue3 + Element Plus)]:::dmz
        
        %% Backend Container
        FastAPI[后端容器 (FastAPI + Python)]:::dmz
        
        %% Async Task Queue
        Celery[Celery 任务队列]:::dmz
    end

    %% 3. Internal Zone (Intranet)
    subgraph Intranet [公司内网 / Intranet]
        %% QMS Data Storage
        Postgres[(QMS 数据库 - PostgreSQL)]:::internal
        Redis[(缓存 - Redis)]:::internal
        
        %% External Systems
        IMS_DB[(IMS 数据库/接口)]:::internal
        OA_System[OA / SAP 系统]:::internal
    end

    %% --- Data Flows ---
    Supplier -->|HTTPS Request| Nginx
    Nginx -->|Reverse Proxy| Vue
    Nginx -->|API Proxy /api| FastAPI

    %% Backend Logic
    FastAPI -->|Read/Write| Postgres
    FastAPI -->|Cache/Queue| Redis
    
    %% IMS Integration (The Bridge)
    FastAPI -->|HTTPX / SQL (Read Only)| IMS_DB
    Celery -->|Scheduled Sync (Nightly)| IMS_DB
