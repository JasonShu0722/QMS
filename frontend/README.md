# QMS Frontend

质量管理系统前端应用，基于 Vue 3 + Vite + TypeScript 构建。

## 技术栈

- **框架**: Vue 3 (Composition API)
- **构建工具**: Vite
- **UI 组件库**: Element Plus (桌面端) + Tailwind CSS (移动端)
- **状态管理**: Pinia
- **路由**: Vue Router
- **HTTP 客户端**: Axios
- **图表**: ECharts
- **语言**: TypeScript

## 开发环境

### 安装依赖

```bash
npm install
```

### 启动开发服务器

```bash
npm run dev
```

访问 http://localhost:5173

### 构建生产版本

```bash
npm run build
```

### 预览生产构建

```bash
npm run preview
```

## 项目结构

```
frontend/
├── src/
│   ├── api/              # API 接口封装
│   ├── assets/           # 静态资源
│   ├── components/       # 公共组件
│   ├── layouts/          # 布局组件
│   │   ├── MainLayout.vue      # 桌面端主布局
│   │   └── MobileLayout.vue    # 移动端布局
│   ├── router/           # 路由配置
│   ├── stores/           # Pinia 状态管理
│   ├── views/            # 页面视图
│   ├── App.vue           # 根组件
│   ├── main.ts           # 入口文件
│   └── style.css         # 全局样式
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
└── Dockerfile
```

## 响应式设计

系统采用响应式设计，支持桌面端和移动端访问：

- **桌面端** (≥768px): 使用 Element Plus 组件库
- **移动端** (<768px): 使用 Tailwind CSS 响应式布局

断点配置：
- sm: 640px (手机)
- md: 768px (平板)
- lg: 1024px (桌面)

## 双轨环境

系统支持预览环境和正式环境双轨运行：

- **正式环境**: qms.company.com
- **预览环境**: preview.company.com

用户可以在界面上实时切换环境。

## Docker 部署

### 构建镜像

```bash
docker build -t qms-frontend:latest .
```

### 运行容器

```bash
docker run -p 80:80 qms-frontend:latest
```

## 环境变量

在 `.env.development` 或 `.env.production` 中配置：

- `VITE_API_BASE_URL`: 后端 API 地址
- `VITE_ENVIRONMENT`: 环境标识 (stable/preview)
