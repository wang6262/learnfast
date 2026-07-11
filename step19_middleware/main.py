# ==============================================
# 文件名：step19_middleware/main.py
# 基础功能：自定义 FastAPI 中间件 — 请求计时、Request ID、日志
# 核心学习知识点：
#   1. @app.middleware("http") — 注册 HTTP 中间件
#   2. 中间件执行顺序 — 先注册的先执行（洋葱模型）
#   3. ASGI 中间件 vs HTTP 中间件 — ASGI 更底层，HTTP 更常用
#   4. BaseHTTPMiddleware — Starlette 提供的中间件基类
#   5. 请求/响应修改 — 中间件可以修改请求和响应
#   6. X-Request-ID — 分布式追踪的请求 ID 模式
#   7. timing 中间件 — 记录请求处理时间
#   8. 中间件 vs 依赖 vs 异常处理器 — 各自的使用场景对比
# 适用场景：请求日志、认证拦截、CORS 处理、请求限流、性能监控
# 运行方式：uv run python -m step19_middleware.main
# ==============================================
import uvicorn
import time
import uuid
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI(
    title="LearnFast API — 中间件",
    description="FastAPI 学习 Step19：自定义中间件、请求计时、Request ID",
    version="0.1.0",
)


# ==============================================
# 中间件 1：Request ID 中间件
# 【基础】每个请求分配一个唯一 ID，放在请求对象和响应头中
#         方便日志追踪和问题排查（"X-Request-ID: abc-123"）
# 【进阶】Request ID 在微服务/分布式系统中非常重要：
#   1. 网关生成 Request ID → 注入请求头 → 传递到所有下游服务
#   2. 所有服务的日志都带同一个 Request ID → 可以串联整个调用链
#   3. 排查问题时，用 Request ID 搜索所有服务的日志
#   4. 生产环境通常用 UUID v4 或 Snowflake ID 生成
# ==============================================
@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    """
    为每个请求添加唯一 Request ID。
    如果客户端传了 X-Request-ID 就用客户端的，否则生成新的。
    """
    # 【基础】优先使用客户端传的 Request ID（方便端到端追踪）
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    # 【基础】把 request_id 存到 request.state，路由函数可以通过 request.state.request_id 获取
    request.state.request_id = request_id

    # 【基础】call_next(request) → 交给下一个中间件或最终的路由函数
    response = await call_next(request)

    # 【基础】在响应头中返回 Request ID，客户端可以记录
    response.headers["X-Request-ID"] = request_id
    return response


# ==============================================
# 中间件 2：请求计时中间件
# 【基础】记录每个请求的处理时间，写入响应头 X-Process-Time
#         性能监控和慢请求排查的基础
# 【进阶】生产环境应把计时数据发给 Prometheus（metrics）或日志系统（ELK）
#        响应头的方式只适合开发调试，生产环境不应暴露内部性能数据
# ==============================================
@app.middleware("http")
async def timing_middleware(request: Request, call_next):
    """记录每个请求的处理时间（毫秒）"""
    # 【基础】time.perf_counter() 高精度计时（比 time.time() 更精确）
    start = time.perf_counter()

    response = await call_next(request)

    # 【基础】计算处理耗时（毫秒）
    process_time = (time.perf_counter() - start) * 1000
    response.headers["X-Process-Time"] = f"{process_time:.2f}ms"
    # 控制台输出（生产环境应使用结构化日志）
    print(f"[{request.method}] {request.url.path} — {process_time:.2f}ms")
    return response


# ==============================================
# 中间件 3：简单限流中间件（基于 IP）
# 【基础】最简单的限流：同一 IP 每秒最多 5 个请求
#         超出限制返回 429 Too Many Requests
# 【进阶】这是一个极简示范，生产环境限流应使用：
#   1. Redis + 滑动窗口算法（精确、分布式友好）
#   2. Token Bucket 算法（允许短时突发流量）
#   3. 专业的 API 网关（Kong/APISIX/Traefik）内置限流
#   4. 按用户/API Key/IP 分级限流
#   本示例仅用内存字典演示中间件可以"拒绝"请求
# ==============================================
rate_limit_store = {}  # IP → [时间戳列表]

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """简单 IP 限流中间件（每秒最多 5 请求）"""
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    window = 1.0  # 时间窗口：1 秒
    max_requests = 5  # 窗口内最多 5 个请求

    # 清理过期的时间戳
    if client_ip in rate_limit_store:
        rate_limit_store[client_ip] = [
            t for t in rate_limit_store[client_ip] if now - t < window
        ]

    # 检查是否超出限制
    if len(rate_limit_store.get(client_ip, [])) >= max_requests:
        return JSONResponse(
            status_code=429,
            content={"detail": "请求过于频繁，请稍后重试", "retry_after": window},
            headers={"Retry-After": str(int(window))},
        )

    # 记录本次请求时间
    rate_limit_store.setdefault(client_ip, []).append(now)

    return await call_next(request)


# ==============================================
# 路由
# ==============================================
@app.get("/")
async def root(request: Request):
    """根路径：返回请求信息（含 Request ID 和处理时间）"""
    return {
        "message": "Welcome",
        "request_id": getattr(request.state, "request_id", None),
        "tip": "查看响应头中的 X-Request-ID 和 X-Process-Time",
    }


@app.get("/fast")
async def fast_endpoint():
    """快速接口（几乎不耗时）"""
    return {"result": "fast"}


@app.get("/slow")
async def slow_endpoint():
    """模拟慢查询接口"""
    time.sleep(0.5)  # 模拟 500ms 数据库查询
    return {"result": "slow (500ms)"}


if __name__ == "__main__":
    uvicorn.run("step19_middleware.main:app", host="127.0.0.1", port=8000, reload=True)
