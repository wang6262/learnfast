# ==============================================
# 文件名：step09_dependency_injection.py
# 基础功能：学习 FastAPI 依赖注入系统 Depends()：函数依赖、类依赖、yield 生命周期、子依赖
# 核心学习知识点：
#   1. Depends() — FastAPI 核心特性，声明式依赖注入，自动调用依赖函数
#   2. 函数依赖 — 用 Depends(普通函数) 注入参数，复用逻辑
#   3. 类依赖 — 用 Depends(类) 实现可配置的依赖（带 __init__ 参数）
#   4. yield 依赖 — 用 yield 分离 setup 和 teardown 逻辑（类似上下文管理器）
#   5. 子依赖（依赖链）— Depends(A) → Depends(B) → Depends(C) 层层嵌套
#   6. 依赖缓存 use_cache — 同一请求中多次调用同一依赖，默认只执行一次
#   7. 依赖参数共享 — 多个路径函数共享同一个依赖函数
#   8. dependency_overrides — 测试时替换真实依赖为模拟对象（Step26 深入）
# 适用场景：数据库连接管理、用户认证提取、权限校验、请求参数预处理、公共校验逻辑
# 使用方法：
#   终端运行：uv run python step09_dependency_injection.py
#   浏览器访问 http://127.0.0.1:8000/docs 交互式测试
# 进阶说明：
#   1. 依赖注入是 FastAPI 的核心设计理念，理解它就理解了 FastAPI 的 50%
#   2. Depends() 背后是 Python 的闭包 + callable 机制，不是魔法——是设计模式
#   3. 依赖的执行顺序 = Python 函数参数求值顺序（从左到右）
#   4. yield 依赖 = 上下文管理器的语法糖角终于——用 yield 替代 __enter__/__exit__
#   5. 依赖函数的参数本身也可以是 Depends()，形成依赖树，框架自动递归解析
# 常用配套函数：
#   Depends(callable)          — 最基础的依赖注入，接收任意可调用对象
#   Depends(Class)             — 类依赖，__init__ 接收参数，__call__ 执行逻辑
#   Security(Depends(...))     — 安全依赖（Step12），本质是 Depends + scope
#   app.dependency_overrides   — 测试时覆盖依赖的字典
#   contextmanager(func)       — 将 generator 函数转为上下文管理器（标准库）
#   asynccontextmanager(func)  — 异步上下文管理器装饰器
# ==============================================


import uvicorn
from fastapi import FastAPI, Depends, Header, HTTPException, Query
from fastapi.responses import JSONResponse

app = FastAPI(
    title="LearnFast API — 依赖注入",
    description="FastAPI 学习 Step09：Depends()、yield 生命周期、类依赖、子依赖",
    version="0.1.0",
)


# ==============================================
# 依赖函数定义区（放在顶部，方便复用）
# 这些函数不是路径操作函数，而是"被注入到"路径函数中的依赖
# ==============================================


# --- 依赖 1：最简单的查询参数预处理 ---
# 【基础】普通函数作为依赖：接收请求参数，返回处理后的值
#         路径函数通过 Depends(common_params) 使用它
#         路径函数参数 = Depends(这个函数) 的返回值
# 【进阶】依赖函数可以有参数（Query/Path/Header 等），框架会自动解析
#   依赖函数本身的参数就是"依赖的依赖"，会先执行
def common_params(
    q: str | None = Query(default=None, description="通用搜索关键词"),
    skip: int = Query(default=0, ge=0, description="跳过条数"),
    limit: int = Query(default=20, ge=1, le=100, description="每页条数"),
):
    """
    通用分页 + 搜索依赖。
    多个路径函数共享同一套查询参数逻辑，避免重复声明。
    返回值：dict 包含 q, skip, limit 三个处理后的参数
    """
    return {"q": q, "skip": skip, "limit": limit}


# --- 依赖 2：模拟"验证用户是否登录"的依赖 ---
# 【基础】这个依赖模拟从请求头中提取 token 并验证身份
#         真实项目中会从数据库查用户、校验 JWT
#         这里简单模拟：有 token 就是登录的，没有就是匿名的
# 【进阶】Header() 的参数 convert_underscores 自动将 _ 转 -
#   X_Auth_Token → X-Auth-Token（HTTP 头标准写法用连字符）
def get_current_user(
    x_auth_token: str | None = Header(
        default=None,
        alias="X-Auth-Token",
        description="认证令牌（模拟）",
    )
):
    """
    模拟认证依赖：从请求头提取 token，返回当前用户信息。
    如果 token 为空，返回匿名用户。
    真实项目中替换为 JWT 验证逻辑（Step11）。
    """
    if x_auth_token:
        # 模拟：有 token 就是已登录用户
        return {"username": "admin", "role": "admin", "authenticated": True}
    # 模拟：无 token 返回匿名用户
    return {"username": "guest", "role": "anonymous", "authenticated": False}


# --- 依赖 3：yield 依赖（数据库会话生命周期模拟）---
# 【基础】yield 之前的代码 = setup（获取资源）
#         yield 之后 的代码 = teardown（释放资源）
#         yield 的值 = 传给路径函数的实际值
#         像是一个"不用写 class 的上下文管理器"
# 【进阶】yield 依赖的执行顺序（非常重要）：
#   1. 请求到达 → FastAPI 调用 get_db()
#   2. 执行 yield 之前的代码（setup：创建会话）
#   3. yield session → session 传给路径操作函数
#   4. 路径操作函数执行（使用 session 做数据库操作）
#   5. 路径函数返回 response → 框架返回到 yield 之后
#   6. 执行 yield 之后的代码（teardown：关闭会话）
#   这种模式确保无论如何退出（异常/正常），资源都会被释放
# yield 依赖内可以获取 Depends 的值，但不能用 raise（yield 之前抛异常使用 try）
def get_db():
    """
    模拟数据库会话生命周期的 yield 依赖。
    yield 前 = 打开连接，yield 后 = 关闭连接。
    真实项目中替换为 SQLAlchemy Session（Step14）。
    """
    # 【基础】setup 阶段：模拟打开数据库连接
    # 真实项目：db = SessionLocal()
    db = {"connection": "fake_db_session", "status": "connected"}
    print(f"[依赖] 数据库连接已打开: {id(db)}")

    try:
        # 【基础】yield 把 db 传给路径函数，路径函数用完后再回到这里
        yield db
    finally:
        # 【基础】teardown 阶段：关闭连接 ← 无论异常与否，这里都会执行
        # 真实项目：db.close()
        db["status"] = "disconnected"
        print(f"[依赖] 数据库连接已关闭: {id(db)}")


# --- 依赖 4：类依赖（可配置的依赖）---
# 【基础】类作为依赖 = Depends(类名) → FastAPI 自动实例化
#         类的 __init__ 参数由 FastAPI 注入（如 Query/Header）
#         实例化后调用 __call__ 方法（如果定义了）
#         或者直接把实例本身作为依赖值返回
# 【进阶】类依赖的两种用法：
#   1. 实例作为依赖值（本示例）：Depends(MyClass) → 返回 MyClass() 实例
#   2. __call__ 作为依赖值：Depends(MyClass) → 返回 MyClass()() 的返回值
#   区别在于类是否定义了 __call__ 方法
class Pagination:
    """
    可配置的分页依赖类。
    实例化后可直接作为依赖值使用，实例属性可复用。
    """
    def __init__(
        self,
        page: int = Query(default=1, ge=1, description="页码"),
        size: int = Query(default=10, ge=1, le=100, description="每页大小"),
    ):
        # 【基础】__init__ 的参数由 FastAPI 自动注入（Query）
        self.page = page
        self.size = size
        # 【基础】计算 SQL 的 offset 值
        # 【进阶】offset = (page - 1) * size 是分页的标准换算公式
        self.offset = (page - 1) * size

    def info(self) -> dict:
        """返回分页元信息的 dict"""
        return {
            "page": self.page,
            "size": self.size,
            "offset": self.offset,
        }


# --- 依赖 5：子依赖（依赖链）---
# 【基础】一个依赖的参数可以本身是 Depends()，形成依赖链
#         A 依赖 B，B 依赖 C，框架自动递归解析执行
# 【进阶】子依赖的解析是递归的：
#   1. FastAPI 扫描 get_paginated_users 的函数签名
#   2. 发现 pagination 是 Depends(get_pagination_context)
#   3. 扫描 get_pagination_context 签名
#   4. 发现 commons 是 Depends(common_params)，p 是 Depends(Pagination)
#   5. 先执行 common_params → 再执行 Pagination → 再执行 get_pagination_context
#   6. 最终返回给 get_paginated_users
# 依赖树的执行顺序 = 深度优先遍历
def get_pagination_context(
    commons: dict = Depends(common_params),  # 子依赖 1：通用参数
    p: Pagination = Depends(Pagination),      # 子依赖 2：分页对象
):
    """
    子依赖示例：组合 common_params 和 Pagination 的结果。
    返回合并后的完整上下文信息。
    """
    return {
        "search": commons["q"],
        "pagination": p.info(),
        "combined_message": f"搜索={commons['q']}, 第{p.page}页, 每页{p.size}条",
    }


# ==============================================
# 路径操作函数区
# ==============================================


# --- 接口 1：使用 common_params 函数依赖 ---
# 【基础】Depends(common_params) 让 FastAPI 自动调用 common_params 函数
#         common_params 的返回值（dict）作为 commons 参数的值
#         `commons: dict = Depends(common_params)` — 声明 + 注入二合一
# 【进阶】对比三种写法（效果相同，推荐 Annotated）：
#   1. commons: dict = Depends(common_params) — 传统写法
#   2. commons: Annotated[dict, Depends(common_params)] — Python 3.9+ 推荐
#   3. 函数内部手动调用 common_params(q, skip, limit) — 没利用框架能力，不推荐
# Depends 让 FastAPI 自动处理依赖的参数解析 + 缓存 + 生命周期，比自己调用强大得多
@app.get("/items/", tags=["items"])
async def list_items(commons: dict = Depends(common_params)):
    """
    【基础功能】获取商品列表，使用 Depends 注入通用分页+搜索参数
    【学习知识点】
        1. Depends(func) — 声明式依赖注入，框架自动调用
        2. 参数复用 — 所有接口共享同一套 common_params 逻辑
        3. 返回值注入 — common_params 的返回值成为 commons 参数的值
    调用示例：
        curl "http://127.0.0.1:8000/items/?q=键盘&skip=0&limit=5"
    """
    return {
        "items": [{"name": f"商品{i}"} for i in range(commons["skip"], commons["skip"] + commons["limit"])],
        "params": commons,
    }


@app.get("/users/", tags=["users"])
async def list_users(commons: dict = Depends(common_params)):
    """
    【基础功能】获取用户列表，复用同一个 common_params 依赖
    【学习知识点】
        1. 同一个依赖多接口复用 — 一份代码，到处使用
        2. DRY 原则 — Don't Repeat Yourself，避免复制粘贴参数声明
    """
    return {"users": [{"name": f"用户{i}"} for i in range(10)], "params": commons}


# --- 接口 2：使用认证依赖 + 数据库依赖 ---
@app.get("/users/me", tags=["users"])
async def read_own_profile(
    current_user: dict = Depends(get_current_user),
    db: dict = Depends(get_db),  # yield 依赖，自动管理生命周期
):
    """
    【基础功能】获取当前登录用户的信息，同时使用认证依赖和数据库依赖
    【学习知识点】
        1. 多个 Depends() — 一个路径函数可以有多个依赖参数
        2. Depends 参数求值与传递 — 依赖返回值通过参数名绑定
        3. yield 依赖 — 请求结束后自动执行 teardown 代码
    调用示例：
        curl http://127.0.0.1:8000/users/me（匿名用户）
        curl -H "X-Auth-Token:secret123" http://127.0.0.1:8000/users/me（登录用户）
    """
    return {
        "user": current_user,
        "db_status": db["status"],
        "message": f"当前用户: {current_user['username']}, 角色: {current_user['role']}",
    }


# --- 接口 3：使用类依赖 ---
@app.get("/products/", tags=["products"])
async def list_products(p: Pagination = Depends(Pagination)):
    """
    【基础功能】用分页类依赖处理商品列表的翻页
    【学习知识点】
        1. Depends(类) — 类做依赖，自动实例化
        2. 实例属性访问 — p.page, p.offset 等可直接使用
        3. 实例方法调用 — p.info() 提供额外功能
    调用示例：
        curl "http://127.0.0.1:8000/products/?page=2&size=5"
    """
    return {
        "products": [{"name": f"产品{i}"} for i in range(p.offset, p.offset + p.size)],
        "pagination": p.info(),
    }


# --- 接口 4：演示依赖链（子依赖）---
@app.get("/advanced/", tags=["advanced"])
async def advanced_query(ctx: dict = Depends(get_pagination_context)):
    """
    【基础功能】演示依赖链：一个依赖使用另一个依赖的结果
    【学习知识点】
        1. 子依赖 — Depends 嵌套，框架自动递归解析
        2. 依赖组合 — 多个底层依赖组合成高层依赖
        3. 依赖树 — common_params → Pagination → get_pagination_context
    调用示例：
        curl "http://127.0.0.1:8000/advanced/?q=fastapi&page=1&size=10"
    """
    return {"context": ctx}


# --- 接口 5：演示 use_cache（依赖缓存）---
# 【基础】shared_commons 和 same_commons 会得到同一个 common_params 返回值
#         因为默认 use_cache=True，同一请求中同名依赖只计算一次
#         这意味着：即使两个参数都用了 Depends(common_params)，只执行一次
# 【进阶】use_cache 的设计原理：
#   use_cache=True（默认）：同一请求生命周期内，如果依赖函数 + 参数完全一致，返回缓存的实例
#   use_cache=False：每次使用该依赖都重新执行，即使参数相同
#   缓存范围：单个请求（per-request cache），不同请求间不共享缓存
#   缓存键：(依赖函数, 参数值元组)
#   使用场景：
#     ✓ use_cache=True → 数据库连接（不要重复开连接）、认证用户（一次请求只需查一次）
#     ~ use_cache=False → 每次需要新值的场景（如生成随机数、取当前时间戳）
@app.get("/cache-demo/", tags=["advanced"])
async def cache_demo(
    shared_commons: dict = Depends(common_params),
    same_commons: dict = Depends(common_params),  # 同一个依赖用两次
):
    """
    【基础功能】演示依赖缓存机制，同一依赖同一请求只执行一次
    【学习知识点】
        1. use_cache=True（默认）— 同请求内同名依赖只执行一次
        2. 实例对比 — shared_commons 和 same_commons 是同一个对象（is 判断为 True）
    调用示例：
        curl "http://127.0.0.1:8000/cache-demo/?q=test"
        观察：两个 dict 的 id 相同（同一个对象引用）
    """
    return {
        "same_object_in_memory": shared_commons is same_commons,  # 是否同一个内存对象
        "shared_id": id(shared_commons),   # Python 对象 id（内存地址标识）
        "same_id": id(same_commons),        # 如果相同，说明被缓存了
        "shared": shared_commons,
        "same": same_commons,
    }


# ==============================================
# 程序入口
# ==============================================
if __name__ == "__main__":
    uvicorn.run(
        "step09_dependency_injection:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )
