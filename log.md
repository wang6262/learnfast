# 学习项目变更日志

> 每次修改/新增代码文件必须在此文件末尾追加标准修改日志。
> 禁止覆盖、删除旧日志，只允许尾部追加，保证项目迭代可追溯。

---

## 日志模板

```
## YYYY-MM-DD
### 文件名：xxx.py
- **修改目的**：简要说明本次修改的原因和目标
- **改动内容**：
  | 参数/函数 | 修改前 | 修改后 | 说明 |
- **数据依据**：如有数据支撑的改动，列出来源和依据
```

---

## 2026-07-06

### 项目初始化
- **修改目的**：初始化 FastAPI 从零到企业级学习项目
- **改动内容**：
  | 文件 | 操作 | 说明 |
  |------|------|------|
  | `main.py` | 重命名为 `main.py.bak` | 临时草稿代码，保留作参考 |
  | `test.py` | 重命名为 `test.py.bak` | 临时草稿代码，保留作参考 |
  | `log.md` | 新建 | 项目变更日志 |
  | `README.md` | 重写 | 学习路径导航 + 快速启动指南 |
- **数据依据**：按 CLAUDE.md 学习型代码规范重建项目结构

### Batch 1：Steps 01-08 — FastAPI 核心（8 个单文件）
- **改动内容**：step01_hello_fastapi ~ step08_path_op_config（开始、路径参数、查询参数、请求体、响应模型、表单文件、异常处理、路径配置）
- **状态**：所有文件通过 Python 语法检查

### Batch 2：Steps 09-13 — 依赖注入 & 认证（5 个单文件）
- **改动内容**：step09_dependency_injection ~ step13_rbac（Depends、Header/Cookie、JWT、OAuth2 Scopes、RBAC）
- **依赖添加**：python-jose[cryptography], passlib[bcrypt]
- **pyproject.toml**：追加 JWT/认证依赖，更新 entrypoint 为 step01_hello_fastapi:app

### Batch 3：Steps 14-18 — 数据库集成（5 个目录）
- **改动内容**：step14_sqlalchemy_sync ~ step18_repository_uow（同步 SQLAlchemy+PG、CRUD API、异步 asyncpg、Alembic、Repository/UoW）
- **依赖添加**：sqlalchemy, psycopg2-binary, asyncpg, alembic

### Batch 4：Steps 19-24 — 高级特性（4 单文件 + 2 目录）
- **改动内容**：step19_middleware ~ step24_streaming（中间件、CORS/安全、后台任务、WebSocket、聊天室、SSE/流式）
- **无新增依赖**

### Batch 5：Steps 25-27 — 测试（3 目录）
- **改动内容**：step25_testing ~ step27_integration_tests（TestClient+pytest、异步测试+dependency_overrides、集成测试+覆盖率）
- **依赖添加**：pytest, pytest-asyncio, pytest-cov, httpx

### Batch 6：Steps 28-30 — 企业级（3 目录）
- **改动内容**：step28_configuration ~ step30_enterprise（pydantic-settings 配置管理、structlog 结构化日志、完整企业架构+Docker）
- **依赖添加**：pydantic-settings, structlog
- **Step 30 架构**：api/v1+v2 → services → repositories → models → core（config/database/deps）+ middleware + Dockerfile + docker-compose.yml

### 总计
- **30 个学习步骤**：13 个单文件 + 17 个目录模块
- **78 个 Python 文件**，覆盖从 Hello World 到企业级分层架构
- **7 批次依赖**，从 fastapi 逐步扩展到 14 个包
- **后端数据库**：PostgreSQL（本地），同步 psycopg2 + 异步 asyncpg 双驱动

---

## 2026-07-07

### Batch 7：React 前端学习模块（react-frontend/ + react-backend.py）

- **修改目的**：新增 React 前端学习模块，从零到实战，配套 FastAPI 后端
- **改动内容**：

  | 文件 | 操作 | 说明 |
  |------|------|------|
  | `react-frontend/` | 新建目录 | Vite + React 18 前端项目 |
  | `react-frontend/package.json` | 新建 | React 18 + Vite 5 + @vitejs/plugin-react |
  | `react-frontend/vite.config.js` | 新建 | 代理 /api → localhost:8000（解决跨域） |
  | `react-frontend/index.html` | 新建 | React 应用入口 HTML |
  | `react-frontend/src/main.jsx` | 新建 | React 18 createRoot 入口，渲染 App |
  | `react-frontend/src/App.jsx` | 新建 | 步骤导航 + 标签页切换 |
  | `react-frontend/src/App.css` | 新建 | 全局样式（CSS 变量 + Flexbox + 响应式） |
  | `react-frontend/src/api.js` | 新建 | 封装 fetch（统一错误处理、GET/POST/PUT/PATCH/DELETE） |
  | `react-frontend/src/components/Step01_JSX.jsx` | 新建 | JSX 语法、组件嵌套、列表渲染、条件渲染 |
  | `react-frontend/src/components/Step02_State.jsx` | 新建 | useState、不可变更新、计数器/Todo 实战 |
  | `react-frontend/src/components/Step03_Props.jsx` | 新建 | Props 传递、children、透传、状态提升 |
  | `react-frontend/src/components/Step04_Events.jsx` | 新建 | 事件处理、受控表单、useRef、键盘事件 |
  | `react-frontend/src/components/Step05_Effects.jsx` | 新建 | useEffect、依赖数组、清理函数、定时器/窗口监听 |
  | `react-frontend/src/components/Step06_Fetch.jsx` | 新建 | HTTP 请求构造器、三态管理、CORS 原理、自定义 Hook |
  | `react-frontend/src/components/Step07_CRUD.jsx` | 新建 | 用户管理系统 CRUD、乐观更新、前端校验、错误回滚 |
  | `react-backend.py` | 新建 | 配套演示 API（内存 CRUD），端口 8000 运行 |
  | `.gitignore` | 更新 | 追加 node_modules/ 和 react-frontend/dist/ |

- **React 学习阶段设计**：

  | 步骤 | 主题 | 核心知识点 |
  |------|------|-----------|
  | Step 1 | JSX 基础 | 表达式、列表渲染、条件渲染、组件嵌套 |
  | Step 2 | useState | 状态管理、不可变更新、Todo 实战 |
  | Step 3 | Props | 父传子、children、透传、状态提升 |
  | Step 4 | 事件 & 表单 | onClick/onChange、受控组件、useRef |
  | Step 5 | useEffect | 副作用、依赖数组、清理函数 |
  | Step 6 | API 调用 | fetch、三态管理、CORS/Vite Proxy |
  | Step 7 | CRUD 实战 | 前后端协作、乐观更新、表单校验 |

- **运行方式**：
  1. 后端：`uv run python react-backend.py`
  2. 前端：`cd react-frontend && npm run dev`
  3. 浏览器访问 `http://localhost:3000`

- **技术栈**：React 18.3 + Vite 5 + CSS 原生（无 UI 库依赖），遵循 CLAUDE.md 学习型注释规范
- **数据依据**：用户选择 React 作为前端学习方向，所有代码适配 Python 开发者入门 JSX
