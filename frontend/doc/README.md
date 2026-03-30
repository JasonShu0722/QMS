# Frontend README

`frontend` 是 QMS 的 Vue 3 前端应用，负责：

- 登录与注册界面
- 工作台与业务页面
- 权限驱动路由
- 调用后端 API

## 技术栈

- Vue 3
- Vite
- TypeScript
- Element Plus
- Pinia
- Vue Router
- Axios
- Vitest

## 目录结构

```text
frontend/
├─ src/
│  ├─ api/
│  ├─ components/
│  ├─ layouts/
│  ├─ router/
│  ├─ stores/
│  ├─ test/
│  ├─ types/
│  ├─ utils/
│  ├─ views/
│  ├─ App.vue
│  └─ main.ts
├─ doc/
├─ package.json
├─ vite.config.ts
└─ .env.development
```

## 推荐启动方式

推荐配合本地后端一起启动：

1. 根目录启动 `postgres` 和 `redis`
2. 本地启动后端 `8000`
3. 本地启动前端 `5173`

## 本地启动

### 1. 安装依赖

```bash
cd frontend
npm install
```

### 2. 检查开发环境变量

开发环境配置文件：

```text
frontend/.env.development
```

当前推荐配置：

```env
VITE_API_BASE_URL=/api
VITE_ENVIRONMENT=stable
```

这里必须使用 `/api`，让浏览器通过 Vite 代理访问后端，避免本地开发时直接跨域请求 `http://localhost:8000`。

这里的 `stable` 表示“本地前端默认按正式版语义运行”，不是说本地不能调预览版。项目里的预览版 / 正式版仍然由登录请求中的 `environment` 和双环境服务来控制。

### 3. 启动前端

```bash
cd frontend
npm run dev
```

启动后访问：

```text
http://localhost:5173
```

## 本地调试说明

当前 `vite.config.ts` 已配置代理：

- `/api` -> `http://localhost:8000`

所以本地调试时应保证：

- 后端运行在 `http://localhost:8000`
- 前端运行在 `http://localhost:5173`

## 常用命令

### 启动开发服务器

```bash
npm run dev
```

### 构建

```bash
npm run build
```

### 本地预览构建结果

```bash
npm run preview
```

### 运行测试

```bash
npm run test
```

## 登录调试

如果登录页出现：

- “网络连接失败”
- “登录失败，请检查用户名和密码”

优先检查：

1. 后端是否启动在 `8000`
2. `frontend/.env.development` 是否为 `VITE_API_BASE_URL=/api`
3. Vite 是否已重启并加载最新环境变量

## 开发建议

- 页面入口主要在 `src/views`
- 公共逻辑优先看 `src/components`、`src/composables`
- 请求封装在 `src/utils/request.ts`
- 登录态和权限逻辑在 `src/stores/auth.ts` 与 `src/router/index.ts`
- 测试目录已统一为：
  - `src/test`
  - `src/components/test`
  - `src/views/test`
