# ==============================================
# 文件名：step30_enterprise/
# 基础功能：完整企业级 FastAPI 项目结构 — 分层架构 + API 版本化 + Docker
# 核心学习知识点：
#   1. 分层架构 — api → services → repositories → models
#   2. API 版本化 — /api/v1/ + /api/v2/ 共存
#   3. 应用工厂模式 — create_app() 可配置生成多个应用实例
#   4. 组合根 — dependencies.py 作为依赖注入的集中注册点
#   5. Dockerfile — 多阶段构建，镜像瘦身
#   6. docker-compose.yml — 多服务编排（app + db + redis）
# 架构分层：
#   api/         — 表示层（HTTP 路由，薄层）
#   services/    — 业务逻辑层（编排业务流程）
#   repositories/ — 数据访问层（封装数据库操作）
#   models/      — ORM 模型（数据库表映射）
#   schemas/     — Pydantic 请求/响应模型
#   core/        — 配置、安全、日志等基础设施
#   middleware/  — 自定义中间件
# 运行方式：uv run python -m step30_enterprise.main
# ==============================================
