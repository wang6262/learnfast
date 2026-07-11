# ==============================================
# 文件名：step07_error_handling.py
# 基础功能：学习 FastAPI 异常处理体系：HTTPException、全局异常处理器、校验错误自定义
# 核心学习知识点：
#   1. HTTPException — 主动抛出标准 HTTP 错误（404/400/401 等）
#   2. @app.exception_handler() — 注册全局异常处理器，统一错误响应格式
#   3. RequestValidationError — Pydantic 校验失败时自动触发的异常
#   4. 自定义全局校验错误响应 — 把默认 422 错误格式改成自己想要的
#   5. 自定义业务异常 — 继承 Exception 创建领域异常类
#   6. Starlette HTTPException vs FastAPI HTTPException — 两者兼容但 FastAPI 版功能更全
#   7. 异常处理优先级 — 局部处理器 > 全局处理器 > 默认处理器
#   8. ValidationError vs RequestValidationError — 前者来自 Pydantic，后者来自 FastAPI 封装
# 适用场景：统一错误格式（前端好解析）、业务异常透传、Pydantic 校验错误中文化
# 使用方法：
#   终端运行：uv run python step07_error_handling.py
#   浏览器访问 http://127.0.0.1:8000/docs 测试正常请求和故意触发错误的请求
# 进阶说明：
#   1. 异常处理器本质上是一个 ASGI 中间件（ExceptionMiddleware），捕获异常并生成响应
#   2. 多个异常处理器按注册顺序匹配，第一个匹配到的生效
#   3. 异常处理器可以覆盖默认行为（如把 HTML 格式的 422 改回 JSON）
#   4. 生产环境建议统一异常响应格式为 {"error": {...}}，前端开发体验更好
# 常用配套函数：
#   HTTPException(status_code=, detail=)    — 抛出标准 HTTP 错误
#   @app.exception_handler(ExcType)         — 注册全局异常处理器
#   add_exception_handler(ExcType, handler) — 等价的函数式注册方式
#   RequestValidationError                  — FastAPI 封装的校验异常
#   ValidationError                         — Pydantic 原生校验异常
#   StarletteHTTPException                  — Starlette 底层 HTTP 异常基类
#   status.HTTP_404_NOT_FOUND               — HTTP 状态码常量（from starlette import status）
# ==============================================
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field, ValidationError

app = FastAPI(
    title="LearnFast API — 异常处理",
    description="FastAPI 学习 Step07：异常体系、全局处理、校验错误自定义",
    version="0.1.0",
)


# ==============================================
# 模型定义
# ==============================================
class ItemCreate(BaseModel):
    """商品创建模型，用 strict 规则触发校验异常"""
    name: str = Field(min_length=1, max_length=50)
    price: float = Field(gt=0, lt=1000000)
    quantity: int = Field(ge=1, le=9999)


# ==============================================
# 自定义业务异常类
# 【基础】继承 Exception 创建专属异常类型，特定业务场景抛特定异常
#         比如库存不足抛 InsufficientStockError，方便全局异常处理器精准捕获
# 【进阶】自定义异常类的最佳实践：
#   1. 继承 Exception（不是 BaseException，后者涵盖 KeyboardInterrupt 等系统异常）
#   2. 类名以 Error 或 Exception 结尾
#   3. 包含足够的上下文信息（如 product_id、amount），方便日志排查
#   4. 可附加 HTTP 状态码属性，让异常处理器读取动态状态码
# 设计价值：业务代码只需 raise BusinessError(...)，异常处理器统一转换成 HTTP 响应
#   → 业务层无需关心 HTTP 细节，关注点分离
# ==============================================
class BusinessError(Exception):
    """自定义业务异常基类，包含 HTTP 状态码和错误码"""
    def __init__(self, message: str, status_code: int = 400, error_code: str = "BUSINESS_ERROR"):
        self.message = message
        self.status_code = status_code  # HTTP 状态码
        self.error_code = error_code    # 业务错误码（前端可据此做不同处理）
        super().__init__(self.message)


# 具体业务异常
class InsufficientStockError(BusinessError):
    """库存不足异常"""
    def __init__(self, product: str, requested: int, available: int):
        super().__init__(
            message=f"库存不足：{product} 请求 {requested} 件，仅剩 {available} 件",
            status_code=409,  # 409 Conflict — 资源状态冲突
            error_code="INSUFFICIENT_STOCK",
        )
        self.product = product
        self.requested = requested
        self.available = available


class UserNotFoundError(BusinessError):
    """用户不存在异常"""
    def __init__(self, user_id: int):
        super().__init__(
            message=f"用户 {user_id} 不存在",
            status_code=404,
            error_code="USER_NOT_FOUND",
        )
        self.user_id = user_id


# ==============================================
# 全局异常处理器注册区
# 【基础】@app.exception_handler(异常类型) 把异常类型挂到指定的处理函数上
#         当路由函数中抛出该类型异常时，自动调用对应的处理函数
#         无论哪个接口抛出 BusinessError，都会由统一的 business_error_handler 处理
# 【进阶】ASGI 异常处理流程：
#   1. 路由函数抛出异常 → ASGI 服务器捕获
#   2. 传递给 ExceptionMiddleware（FastAPI 内置）
#   3. 遍历已注册的 exception_handlers 字典，匹配异常类型
#   4. 匹配成功 → 调用 handler(request, exc) 生成 Response
#   5. 匹配失败 → 返回默认 500 Internal Server Error
#   匹配规则：按 MRO（方法解析顺序）查找，先精确匹配，再匹配父类
#   所以 BusinessError handler 能捕获 UserNotFoundError（因为它是 BusinessError 的子类）
# ==============================================


# --- 处理器 1：捕获所有 HTTPException ---
# 【基础】当任何接口抛出 HTTPException 时，统一格式化为 {"error": {...}} JSON
#         默认的 HTTPException 响应格式太简单，这里加上了 error_code 和 path
# 【进阶】为什么还要统一 HTTPException 的格式：
#   即使框架已经处理了 HTTPException，默认格式可能不满足前端需求
#   前端可能需要固定的 {"error": {"code": ..., "message": ..., "path": ...}} 来统一解析
#   避免 404 的格式和 422 的格式不一致，前端需要写多套解析逻辑
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    【基础功能】将 HTTPException 统一转换为 {"error": {...}} 格式的 JSON 响应
    【学习知识点】
        1. @app.exception_handler — 注册全局异常处理器
        2. 统一错误响应格式 — 所有 HTTP 错误格式一致，前端好解析
        3. Request 参数 — 可以读取请求路径、方法等信息放进错误响应中
    参数：
        request: 【基础释义：触发异常的原始 HTTP 请求对象】
        exc:     【基础释义：被捕获的 HTTPException 实例，包含 status_code 和 detail】
    返回值：JSONResponse — 统一格式的错误 JSON
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "path": request.url.path,  # 发生错误的请求路径（方便前端定位）
            }
        },
    )


# --- 处理器 2：捕获自定义业务异常 ---
# 【基础】BusinessError 及其子类统一由此处理器捕获，根据异常的 status_code 返回对应 HTTP 错误
#         业务代码里写 raise UserNotFoundError(42) → 自动转换成 404 JSON 响应
#         业务代码里无需 import HTTPException，完全解耦
# 【进阶】业务异常的模式演进路径：
#   Level 1：函数里 return {"error": "xxx"} → 调用方要 if "error" in result 判断
#   Level 2：函数里 raise HTTPException(404, "xxx") → 和 FastAPI 耦合
#   Level 3：定义业务异常基类 + 全局 handler → 解耦、可测试、可复用 ← 当前步骤
#   Level 4：中间件层统一处理 + 错误码映射表 → 大型项目推荐
@app.exception_handler(BusinessError)
async def business_error_handler(request: Request, exc: BusinessError):
    """捕获自定义业务异常，转为统一格式的 HTTP 错误响应"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "path": request.url.path,
            }
        },
    )


# --- 处理器 3：自定义 Pydantic 校验错误的返回格式 ---
# 【背景】FastAPI 默认的 422 校验错误返回英文 + 复杂嵌套格式，对前端不友好
#         这里自定义为中文化 + 简化格式
# 【基础】RequestValidationError 是 FastAPI 封装的异常，包装了 Pydantic 的 ValidationError
#         包含更多请求上下文信息（请求体内容等），专门用于 HTTP 层
# 【进阶】RequestValidationError vs ValidationError：
#   ValidationError（Pydantic）
#     - 纯数据校验层异常，不知道 HTTP 这件事
#     - 包含 errors() 方法返回错误列表
#     - 可以脱离 FastAPI 独立测试
#   RequestValidationError（FastAPI）
#     - 包装了 ValidationError，加了 request body 等 HTTP 上下文
#     - 由 FastAPI 在请求体/参数解析阶段自动触发
#     - 不需要你手动 raise，框架自动处理
#   简单记：ValidationError 是 Pydantic 的，RequestValidationError 是 FastAPI 的
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    【基础功能】把 Pydantic 校验失败的默认英文错误改成中文 + 简化格式
    【学习知识点】
        1. RequestValidationError — FastAPI 自动抛出的校验异常
        2. exc.errors() — 获取 Pydantic 校验错误详情列表
        3. 自定义错误格式 — 中文化 + 路径定位，前端开发体验更好
        4. exc.body — 获取导致错误的原始请求体（调试神器）
    """
    # exc.errors() 返回格式：[{"loc": ["body","name"], "msg": "...", "type": "..."}, ...]
    # 【基础】提取第一个错误的字段和消息，简化为中文
    errors = exc.errors()

    # 【基础】构造简化的错误信息列表
    simplified_errors = []
    for err in errors:
        # 【基础】loc 是一个元组，如 ("body", "name") 或 ("query", "age")
        #   ".".join() 用点连接成 "body.name" 方便阅读
        location = ".".join(str(loc) for loc in err["loc"])
        simplified_errors.append({
            "field": location,
            "error": err["msg"],  # Pydantic 原始错误消息
            "type": err["type"],  # 错误类型（如 "missing"、"type_error"、"less_than_equal"）
        })

    # 【基础】返回中文化、结构化的校验错误
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "输入数据校验失败，请检查请求参数",
                "path": request.url.path,
                "details": simplified_errors,  # 具体哪些字段有问题
            }
        },
    )


# --- 处理器 4：兜底捕获所有未处理的异常 ---
# 【基础】Exception 是所有异常（除了系统退出类）的基类
#         这个处理器捕获前面所有处理器都没匹配到的异常，防止返回丑陋的 HTML 500 页面
#         生产环境的最后防线——让 API 始终返回 JSON，即使是崩溃也返回结构化的错误
# 【进阶】兜底处理器的注意事项：
#   1. 只应返回通用错误信息（"服务器内部错误"），不要暴露异常细节给客户端
#   2. 服务端应该用 logging.exception() 记录完整 traceback 方便排查
#   3. 如果开了 debug 模式（生产环境绝不开），可以返回 traceback
#   4. 一定要记录日志！没有日志 = 不知道线上发生了什么错误
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """
    【基础功能】兜底捕获所有未处理的异常，统一返回 500 JSON（而非默认 HTML 错误页）
    【学习知识点】
        1. Exception 兜底捕获 — 最后的安全网，防止裸奔的异常暴露服务端信息
        2. 生产错误处理原则 — 对外隐藏细节，对内完整记录（logging）
        3. 状态码 500 — 服务器内部错误的标准返回
    """
    # 【进阶】生产环境应记录日志：logging.exception("Unhandled exception")
    #   本步骤为演示简单，使用 print 代替
    print(f"未处理异常: {type(exc).__name__}: {exc}")

    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "服务器内部错误，请稍后重试",
                "path": request.url.path,
            }
        },
    )


# ==============================================
# 路由定义区
# ==============================================


# --- 接口 1：使用 HTTPException 返回 404 ---
@app.get("/items/{item_id}")
async def get_item(item_id: int):
    """
    【基础功能】查找指定 ID 的商品，不存在返回 404
    【学习知识点】
        1. HTTPException 主动抛出 — 函数内部条件判断后抛出
        2. 自定义 detail — 错误描述可以很详细（但生产环境慎防信息泄露）
    调用示例：
        curl http://127.0.0.1:8000/items/1   → 200（存在）
        curl http://127.0.0.1:8000/items/999 → 404（不存在）
    """
    items_db = {1: "手机", 2: "电脑", 3: "键盘"}

    if item_id not in items_db:
        # 【基础】raise HTTPException 立即终止函数，返回错误给客户端
        # 【进阶】HTTPException 的完整参数：status_code, detail, headers
        #   可以附加 WWW-Authenticate 等响应头（如 401 时告知认证方式）
        raise HTTPException(
            status_code=404,
            detail=f"商品 {item_id} 不存在",
        )

    return {"item_id": item_id, "name": items_db[item_id]}


# --- 接口 2：使用自定义业务异常 ---
@app.post("/orders/")
async def create_order(product: str, quantity: int):
    """
    【基础功能】模拟下单，库存不足时抛出自定义 InsufficientStockError
    【学习知识点】
        1. 自定义业务异常 — 脱离 HTTPException 的纯业务错误表达
        2. 全局 handler 自动捕获 — 业务代码不关心 HTTP 细节
    调用示例：
        curl -X POST "http://127.0.0.1:8000/orders/?product=手机&quantity=2"   → 200
        curl -X POST "http://127.0.0.1:8000/orders/?product=手机&quantity=999"  → 409
    """
    # 模拟库存数据
    stock_db = {"手机": 10, "电脑": 5, "键盘": 20}

    available = stock_db.get(product, 0)

    if available <= 0:
        # 【基础】产品不存在 → 抛出业务异常，由全局 handler 转为 HTTP 404
        raise BusinessError(
            message=f"产品 {product} 不存在",
            status_code=404,
            error_code="PRODUCT_NOT_FOUND",
        )

    if quantity > available:
        # 【基础】库存不足 → 抛出更具体的库存异常
        # 【进阶】异常携带了 product, requested, available 上下文
        #   全局 handler 将这些信息暴露给客户端（调试友好）
        raise InsufficientStockError(
            product=product,
            requested=quantity,
            available=available,
        )

    return {
        "message": f"下单成功：{product} x {quantity}",
        "remaining_stock": available - quantity,
    }


# --- 接口 3：用户查询（演示 UserNotFoundError）---
@app.get("/users/{user_id}")
async def get_user_profile(user_id: int):
    """查找用户，不存在抛 UserNotFoundError"""
    users_db = {1: "张三", 2: "李四"}

    if user_id not in users_db:
        # 【基础】直接 raise 业务异常，无需 import HTTPException
        raise UserNotFoundError(user_id=user_id)

    return {"user_id": user_id, "name": users_db[user_id]}


# --- 接口 4：RequestBody 校验示例（触发自定义的 422 handler）---
@app.post("/items/")
async def create_item(item: ItemCreate):
    """
    【基础功能】创建商品，故意传入非法数据测试自定义 422 响应
    【学习知识点】
        1. Pydantic 校验自动触发 RequestValidationError
        2. 自定义的 422 handler 将默认英文错误转为中文
    调用示例：
        curl -X POST http://127.0.0.1:8000/items/ -H "Content-Type: application/json" -d '{"name":"手机","price":99.9,"quantity":5}'
        → 200（数据合法）
        curl -X POST http://127.0.0.1:8000/items/ -H "Content-Type: application/json" -d '{"name":"","price":-1,"quantity":0}'
        → 422（中文错误信息："输入数据校验失败，请检查请求参数"）
    """
    return {
        "message": f"商品 {item.name} 创建成功",
        "price": item.price,
        "quantity": item.quantity,
    }


# ==============================================
# 程序入口
# ==============================================
if __name__ == "__main__":
    uvicorn.run(
        "step07_error_handling:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )
