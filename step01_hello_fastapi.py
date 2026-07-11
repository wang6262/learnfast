# ==============================================
# 文件名：step01_hello_fastapi.py
# 基础功能：创建第一个 FastAPI 应用，理解 ASGI 服务器、路由装饰器、路径操作等核心概念
# 核心学习知识点：
#   1. FastAPI() 应用实例化 — 创建 Web 应用的入口
#   2. @app.get() 路由装饰器 — 装饰器模式，将 URL 路径映射到 Python 函数
#   3. uvicorn.run() ASGI 服务器启动 — 开发环境热重载（reload=True）
#   4. OpenAPI 自动文档生成 — 访问 /docs 查看 Swagger UI
#   5. 路径操作函数（path operation function）— 处理 HTTP 请求的函数定义
#   6. JSON 自动序列化 — FastAPI 自动将 dict 转为 JSON 响应
#   7. async def 异步路径函数 — ASGI 原生异步支持
#   8. 返回类型注解 — Python 类型提示驱动数据校验与文档生成
# 适用场景：FastAPI 入门第一课，任何 Web API 项目的起点，理解框架基本运作方式
# 使用方法：
#   终端运行：uv run python step01_hello_fastapi.py
#   浏览器访问：
#     http://127.0.0.1:8000           — API 响应 JSON
#     http://127.0.0.1:8000/health    — 健康检查端点
#     http://127.0.0.1:8000/hello/小明 — 路径参数示例
#     http://127.0.0.1:8000/docs      — Swagger UI 交互式文档（核心学习工具）
#     http://127.0.0.1:8000/redoc     — ReDoc 备选文档风格
#     http://127.0.0.1:8000/openapi.json — 原始 OpenAPI Schema（机器可读）
# 进阶说明：
#   1. ASGI vs WSGI：ASGI（异步服务器网关接口）原生支持 async/await，处理高并发 I/O 优于传统 WSGI
#   2. uvicorn 基于 uvloop（Linux）提升事件循环性能，Windows 上降级为 asyncio 标准事件循环
#   3. 生产环境不建议使用 reload=True，应使用 gunicorn + uvicorn worker 多进程部署
#   4. FastAPI 的核心驱动力是 Python 类型注解（type hints），路由参数类型自动触发 Pydantic 校验
# 常用配套函数：
#   FastAPI()                     — 创建应用实例，所有 FastAPI 项目的起点
#   uvicorn.run()                 — 启动 ASGI 服务器，开发环境使用，生产环境用 gunicorn + uvicorn
#   app.include_router()          — 挂载子路由，大型项目拆分路由模块用
#   app.mount()                   — 挂载静态文件目录或子应用（如 /static 指向静态资源文件夹）
#   @app.middleware("http")       — 注册 HTTP 中间件，拦截所有请求/响应
#   @app.on_event("startup")      — 应用启动时执行初始化逻辑（如连接数据库）
#   app.add_exception_handler()    — 注册全局异常处理器
# ==============================================
import uvicorn
from fastapi import FastAPI
from fastapi.responses import *
# ==============================================
# 【基础】创建一个 FastAPI 应用实例
# 大白话：app 变量就是你的整个 Web 服务，所有路由、中间件都挂在这个对象上
# 【进阶】FastAPI() 支持多个配置参数：
#   title="应用标题" → 显示在 /docs 页面顶部
#   description="描述" → 显示在 /docs 页面标题下方
#   version="1.0.0" → API 版本号
#   docs_url="/docs" → 自定义 Swagger 文档路径（设为 None 可关闭）
#   openapi_url="/openapi.json" → 自定义 OpenAPI Schema 路径
# 设计原理：FastAPI 继承自 Starlette（ASGI 框架），融合 Pydantic 数据校验，实现了"类型即文档"理念
# ==============================================
app = FastAPI(
    title="LearnFast API",
    description="FastAPI 从零到企业级 — 学习项目 Step01",
    version="0.1.0",
)


# ==============================================
# 路径操作函数 1：根路径 GET /
# 【基础】当浏览器访问 http://127.0.0.1:8000 时，这个函数会被调用
#         返回的字典自动转换为 JSON 格式返回给客户端
# 【进阶】@app.get("/") 是装饰器模式的典型应用：
#   1. @app.get 其实是 FastAPI 实例的 get 方法，接收路径字符串
#   2. 内部将 "/" → hello_world 函数的映射注册到路由器（Router）
#   3. 请求到来时，路由器匹配路径 → 调用对应函数 → 返回结果
#   4. FastAPI 根据类型注解自动校验参数和生成文档
# 装饰器模式通俗理解：@app.get("/") 相当于 app.get("/")(hello_world)
#   第一步 app.get("/") 返回一个装饰器函数
#   第二步 这个装饰器函数接收 hello_world 作为参数
#   第三步 装饰器内部把路径 "/" 和函数 hello_world 注册到路由表
# 同类装饰器：@app.post()、@app.put()、@app.delete()、@app.patch() 等处理不同 HTTP 方法
# ==============================================
@app.get("/")
async def hello_world():
    """
    【基础功能】根路径 GET / 的欢迎接口，返回问候信息和基础使用说明
    【学习知识点】
        1. async def — Python 异步函数定义，FastAPI 原生支持异步
        2. dict 自动 JSON 序列化 — 返回 Python dict，FastAPI 自动转为 JSON
        3. 路径操作装饰器 — @app.get(path) 将 URL 路径绑定到函数
    参数：无
    返回值：
        基础：dict → JSON，包含 message（欢迎语）和 docs（文档地址）
        进阶：FastAPI 框架内部调用 jsonable_encoder() 将 dict 序列化为 JSON 字符串
    调用示例：
        示例1：浏览器直接访问 http://127.0.0.1:8000/
        示例2：curl 命令 → curl http://127.0.0.1:8000/
        示例3：Python httpx 客户端 → httpx.get("http://127.0.0.1:8000/").json()
    同场景常用替代函数：
        1. RedirectResponse(url="/docs") — 直接重定向到文档页，适合 API 根路径
        2. PlainTextResponse(content="OK") — 返回纯文本，适合简单健康检查
        3. HTMLResponse(content=html_str) — 返回 HTML 页面，适合前后端不分离场景
        4. FileResponse(path="index.html") — 返回静态文件，适合单页应用入口
    注意事项：
        1. 生产环境建议重定向到 /docs 或返回简洁的状态 JSON
        2. 根路径通常用于负载均衡器的健康探测，不建议返回大量数据
    """
    # 【基础】构造要返回的数据字典，FastAPI 会自动转成 JSON
    # return {
    #     "message": "欢迎来到 FastAPI 学习之旅！",
    #     "docs": "访问 http://127.0.0.1:8000/docs 查看交互式 API 文档",
    #     "next_step": "运行 step02_path_params.py 学习路径参数",
    # }
    return RedirectResponse(url="/docs")


# ==============================================
# 路径操作函数 2：健康检查 GET /health
# 【基础】生产环境中，负载均衡器（如 nginx、k8s）需要定期探测服务是否存活
#         健康检查端点就是告诉外部："我还活着，可以接收请求"
# 【进阶】健康检查分为两种：
#   1. 存活探针（Liveness Probe）：进程是否存活？只要返回 200 即可
#   2. 就绪探针（Readiness Probe）：能否处理流量？需检查数据库/Redis 等依赖是否就绪
#   本步骤介绍最简单的存活探针，就绪探针在 Step28 详解
# 设计原理：健康检查端点追求极简快响应，不应做复杂计算或外部依赖调用
# ==============================================
@app.get("/health")
def health_check():
    """
    【基础功能】运维健康检查接口，返回服务运行状态
    【学习知识点】
        1. def vs async def — 简单同步函数不需要 async，FastAPI 会自动放到线程池执行
        2. 健康检查设计模式 — 极简响应，便于负载均衡器高频探测
    参数：无
    返回值：{"status": "ok"} — 标准健康检查 JSON 响应
    调用示例：
        示例1：curl http://127.0.0.1:8000/health
        示例2：Docker HEALTHCHECK 指令 → CMD curl -f http://localhost:8000/health || exit 1
    同场景常用替代函数：
        1. 返回 HTTP 204 No Content — 更轻量，无响应体
        2. 返回完整系统状态 — 包含数据库连接、缓存状态、内存使用等（就绪探针）
    注意事项：健康检查端点应避免鉴权，否则负载均衡器无法探测
    """
    # 【基础】返回最简单的状态信息
    # 【进阶】生产环境可用 time.time() 返回运行时长等信息
    return {"status": "ok"}


# ==============================================
# 路径操作函数 3：带路径参数的问候 GET /hello/{name}
# 【基础】{name} 是路径参数（Path Parameter），URL 中的动态部分
#         比如 /hello/小明 中 name 的值就是 "小明"
#         比如 /hello/World 中 name 的值就是 "World"
# 【进阶】路径参数原理：
#   1. FastAPI 解析路由模板 "/hello/{name}" 中的 {name}
#   2. 匹配请求 URL 路径，提取对应位置的值
#   3. 根据函数参数的类型注解（str）自动校验和转换
#   4. 如果类型不匹配（如声明 int 但收到 "abc"），自动返回 422 错误
# 类型注解驱动：name: str 告诉 FastAPI name 必须是字符串，同时自动生成文档
# 简化替代写法：不使用 async def，直接用 def hello(name: str) 也可以运行
# ==============================================
@app.get("/hello/{name}")
async def say_hello(name: str):
    """
    【基础功能】接收 URL 中的名字参数，返回个性化问候
    【学习知识点】
        1. 路径参数定义 — {name} 花括号语法定义 URL 中的动态变量
        2. 类型注解 str — 函数参数类型决定数据校验规则
        3. f-string 格式化 — Python 3.6+ 字符串插值语法 f"{变量}"
    参数：
        name: 【基础释义：字符串，URL 路径中的名字部分】【进阶释义：FastAPI 根据路由模板自动提取，类型注解驱动校验】
    返回值：{"message": f"你好，{name}！"} — 包含个性化问候的 JSON
    调用示例：
        示例1：浏览器访问 http://127.0.0.1:8000/hello/小明
        示例2：curl http://127.0.0.1:8000/hello/LearnFast
        示例3：Python → httpx.get("http://127.0.0.1:8000/hello/测试").json()
    同场景常用替代函数：
        1. re.match() — 用正则表达式手动匹配 URL 参数（传统方式，不如 FastAPI 声明式清晰）
        2. urlparse() — 手动解析 URL 各部分（底层库，FastAPI 内部已封装）
    注意事项：
        1. 路径参数不支持特殊字符（/ 和空格），需要 URL 编码
        2. name 参数没有默认值，请求 URL 必须包含该路径段，否则返回 404
    """
    # 【基础】f"{变量}" 是 Python 的 f-string 语法，用 {} 大括号嵌入变量值
    # 【进阶】f-string 在 Python 3.6 引入，比 % 格式化 和 .format() 更高效、更易读
    #   简化替代写法："你好，" + name + "!"（字符串拼接，可读性不如 f-string）
    return {"message": f"你好，{name}！"}


# ==============================================
# 程序入口：启动 ASGI 服务器
# 【基础】if __name__ == "__main__" 确保只有直接运行本文件时才启动服务器
#         如果被其他文件 import，不会启动服务器（避免重复启动）
# 【进阶】uvicorn.run() 参数详解：
#   app="step01_hello_fastapi:app" → "文件名:FastAPI实例变量名" 格式
#   host="127.0.0.1" → 只监听本机，防止外网访问（开发安全）
#   port=8000 → 默认 FastAPI 端口（HTTP 标准备用端口 8080 也可）
#   reload=True → 文件修改后自动重启服务器（底层用 watchfiles 库监听文件变化）
#   注意：reload=True 仅对开发友好，生产环境禁止使用（会降低性能）
# 简化替代写法：终端直接运行 → uvicorn step01_hello_fastapi:app --reload
# ==============================================
if __name__ == "__main__":
    # 【基础】启动服务器，reload=True 表示代码修改后自动重启
    # 【进阶】uvicorn 默认使用 1 个主进程 + 1 个 worker，reload 模式额外启动 watchfiles 进程
    uvicorn.run(
        "step01_hello_fastapi:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )

