# ==============================================
# 文件名：step29_logging/app.py
# 基础功能：structlog 结构化日志 + Request ID + 健康检查
# 核心学习知识点：
#   1. structlog — Python 结构化日志库（JSON 格式，机器可读）
#   2. 结构化 vs 非结构化日志 — JSON 可搜索 vs 纯文本 grep
#   3. 关联 ID — 同一个 Request ID 贯穿一个请求的所有日志
#   4. 请求日志中间件 — 自动记录每个请求的 method/path/status/duration
#   5. 健康检查端点 — /health/live（存活）+ /health/ready（就绪）
#   6. 日志级别 — DEBUG/INFO/WARNING/ERROR 的使用场景
#   7. 生产环境日志策略 — 写 stdout 不写文件（容器标准），ELK/Grafana 聚合
# 运行方式：uv run python -m step29_logging.app
# ==============================================
import uvicorn
import time
import uuid
import structlog
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# ==============================================
# 配置 structlog
# 【基础】structlog 输出 JSON 格式的日志（机器可解析）
# 【进阶】structlog.configure() 设置全局日志行为：
#   processors → 日志处理管道（每个 processor 处理一种格式转换）
#   wrapper_class → structlog 的包装类（BoundLogger 支持 .bind() 绑定上下文）
#   context_class → 线程安全的上下文字典
#   logger_factory → 底层日志工厂（这里用标准 logging 模块）
#   cache_logger_on_first_use → 性能优化：首次使用后缓存 logger
# ==============================================

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,        # 按级别过滤（低于配置级别的忽略）
        structlog.stdlib.add_log_level,           # 添加 level 字段
        structlog.stdlib.PositionalArgumentsFormatter(),  # 格式化 %s 占位符
        structlog.processors.TimeStamper(fmt="iso"),      # 添加 timestamp 字段
        structlog.processors.StackInfoRenderer(),          # 异常时添加堆栈信息
        structlog.processors.format_exc_info,              # 格式化异常信息
        structlog.processors.UnicodeDecoder(),              # 处理 Unicode
        structlog.dev.ConsoleRenderer(),                   # 开发环境：彩色控制台输出
        # 生产环境替换为：structlog.processors.JSONRenderer()  # 输出 JSON
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

# 获取 logger 实例
logger = structlog.get_logger()


app = FastAPI(
    title="LearnFast API — 日志与监控",
    description="FastAPI 学习 Step29：结构化日志、请求追踪、健康检查",
    version="0.1.0",
)


# ==============================================
# Request ID 中间件（增强版：带日志绑定）
# 【基础】为每个请求分配唯一 ID，并绑定到 structlog 的上下文中
#         所有该请求的日志都会自动包含这个 request_id
#         排查问题时，用 request_id 串联所有相关日志
# 【进阶】structlog.contextvars.bind_contextvars() → 绑定到上下文变量
#   后续所有 logger.info/error 调用自动带这些 key-value
#   clear_contextvars() → 请求结束后清除绑定（防止泄漏到下一个请求）
# ==============================================


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """请求日志中间件：记录 method/path/status/duration/request_id"""
    # 生成或提取 Request ID
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

    # 【基础】把 request_id 绑定到 structlog，后续所有日志自动带此字段
    structlog.contextvars.bind_contextvars(request_id=request_id)

    start = time.perf_counter()

    # 请求开始日志
    logger.info(
        "request_started",
        method=request.method,
        path=request.url.path,
        client=request.client.host if request.client else "unknown",
    )

    try:
        response = await call_next(request)
        process_time = time.perf_counter() - start

        # 请求成功日志（结构化：包含状态码、耗时）
        logger.info(
            "request_finished",
            status_code=response.status_code,
            duration_ms=round(process_time * 1000, 2),
        )

        response.headers["X-Request-ID"] = request_id
        return response

    except Exception as exc:
        # 异常日志
        logger.error(
            "request_failed",
            error=str(exc),
            duration_ms=round((time.perf_counter() - start) * 1000, 2),
            exc_info=True,
        )
        raise
    finally:
        # 【基础】清除上下文绑定（防止 request_id 泄漏到下一个请求）
        structlog.contextvars.clear_contextvars()


# ==============================================
# 健康检查端点
# 【基础】Kubernetes/Docker 用健康检查端点判断服务是否存活
#   /health/live — 存活探针（Liveness）：进程是否活着？
#   /health/ready — 就绪探针（Readiness）：能否接收请求？
# 【进阶】两者的区别：
#   存活探针失败 → K8s 重启 Pod（进程挂了/死循环等）
#   就绪探针失败 → K8s 停止向 Pod 发送流量（数据库连接断等）
#   两个探针必须都通过，服务才算"健康"
#   就绪探针可以检查数据库、Redis、消息队列等外部依赖
# ==============================================


@app.get("/health/live", include_in_schema=False)
async def health_live():
    """存活探针：只检查进程是否运行"""
    return {"status": "alive"}


@app.get("/health/ready", include_in_schema=False)
async def health_ready():
    """
    就绪探针：检查服务依赖是否就绪。
    真实项目这里检查数据库连接、Redis 连接等。
    本示例只做简单检查。
    """
    # 模拟：检查关键依赖（数据库连接等）
    try:
        # 真实项目：db.execute("SELECT 1")
        dependencies_ok = True
    except Exception:
        dependencies_ok = False

    if dependencies_ok:
        return {"status": "ready"}
    else:
        return JSONResponse(status_code=503, content={"status": "not ready"})


# ==============================================
# 路由
# ==============================================


@app.get("/")
async def root():
    """根路径：演示不同级别的日志"""
    logger.debug("这是 DEBUG 日志（通常不输出）")
    logger.info("这是 INFO 日志", extra_info="一般信息")
    return {"message": "查看控制台的结构化日志输出"}


@app.get("/users/{user_id}")
async def get_user(user_id: int):
    """查询用户：演示业务日志"""
    if user_id > 100:
        logger.warning("查询的用户ID较大", user_id=user_id, reason="可能不存在")
        return {"error": "用户不存在"}
    logger.info("用户查询成功", user_id=user_id)
    return {"user_id": user_id, "name": f"用户{user_id}"}


if __name__ == "__main__":
    uvicorn.run("step29_logging.app:app", host="127.0.0.1", port=8000, reload=True)
