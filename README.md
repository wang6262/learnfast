# LearnFast — FastAPI 从零基础到企业级

本项目通过 **30 个渐进式学习步骤**，带你从零开始系统掌握 FastAPI，直到能搭建企业级后端架构。

## 快速启动

```bash
# 1. 确保 Python 3.12+ 已安装
python --version

# 2. 安装 uv 包管理器（如未安装）
pip install uv

# 3. 同步依赖
uv sync

# 4. 运行任意步骤
uv run python step01_hello_fastapi.py
# 然后访问 http://127.0.0.1:8000/docs 查看交互式 API 文档
```

## 学习路径

### 阶段 1：FastAPI 核心（Step 01-08）

| 步骤 | 文件 | 学习内容 |
|------|------|---------|
| 01 | `step01_hello_fastapi.py` | 第一个 FastAPI 应用、ASGI 概念、自动文档 |
| 02 | `step02_path_params.py` | 路径参数、类型提示、Enum 约束 |
| 03 | `step03_query_params.py` | 查询参数、Query() 校验、可选参数 |
| 04 | `step04_request_body.py` | 请求体、Pydantic BaseModel、嵌套模型 |
| 05 | `step05_response_models.py` | 响应模型、状态码、数据过滤 |
| 06 | `step06_form_and_file.py` | 表单数据、文件上传、静态文件服务 |
| 07 | `step07_error_handling.py` | 异常处理、全局异常捕获、校验错误自定义 |
| 08 | `step08_path_op_config.py` | 路径操作配置、标签、文档分组、OpenAPI 元数据 |

### 阶段 2：依赖注入 & 认证（Step 09-13）

| 步骤 | 文件 | 学习内容 |
|------|------|---------|
| 09 | `step09_dependency_injection.py` | Depends()、yield 依赖、子依赖 |
| 10 | `step10_header_cookie.py` | Header/Cookie 参数、响应 Cookie |
| 11 | `step11_jwt_auth.py` | JWT 令牌、密码哈希、OAuth2 密码流 |
| 12 | `step12_oauth2_scopes.py` | Security()、OAuth2 作用域、权限颗粒度 |
| 13 | `step13_rbac.py` | 基于角色的访问控制（RBAC） |

### 阶段 3：数据库集成（Step 14-18）

| 步骤 | 目录 | 学习内容 |
|------|------|---------|
| 14 | `step14_sqlalchemy_sync/` | SQLAlchemy 同步引擎、ORM 模型、PostgreSQL |
| 15 | `step15_crud_api/` | 完整 CRUD RESTful API、Schema 分层 |
| 16 | `step16_async_database/` | 异步 SQLAlchemy、asyncpg 驱动 |
| 17 | `step17_alembic/` | Alembic 数据库迁移、版本管理 |
| 18 | `step18_repository_uow/` | Repository 模式、Unit of Work |

### 阶段 4：高级特性（Step 19-24）

| 步骤 | 文件/目录 | 学习内容 |
|------|----------|---------|
| 19 | `step19_middleware/` | 自定义中间件、请求计时、Request ID |
| 20 | `step20_cors_security.py` | CORS、安全头、TrustedHost |
| 21 | `step21_background_tasks.py` | 后台任务、lifespan 事件 |
| 22 | `step22_websocket.py` | WebSocket 基础、实时双向通信 |
| 23 | `step23_websocket_chat/` | WebSocket 聊天室、连接管理、广播 |
| 24 | `step24_streaming.py` | StreamingResponse、SSE 事件流 |

### 阶段 5：测试 & 企业级（Step 25-30）

| 步骤 | 目录 | 学习内容 |
|------|------|---------|
| 25 | `step25_testing/` | TestClient、pytest、单元测试 |
| 26 | `step26_async_testing/` | 异步测试、依赖覆盖、测试数据库 |
| 27 | `step27_integration_tests/` | 集成测试、覆盖率、事务回滚 |
| 28 | `step28_configuration/` | pydantic-settings、环境配置管理 |
| 29 | `step29_logging/` | 结构化日志、关联 ID、健康检查 |
| 30 | `step30_enterprise/` | 完整企业架构、Docker、API 版本化 |

## 前置要求

- Python 3.12+
- PostgreSQL（Step 14 起需要本地运行）
- 每个步骤独立可运行，建议按顺序学习

## 项目规范

本项目遵循 `CLAUDE.md` 中定义的学习型代码规范，所有代码均包含：
- 零基础可读的基础注释
- 进阶学习者专属的原理拆解
- 每个函数附带调用示例和同类函数对比
