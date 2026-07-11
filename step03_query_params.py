# ==============================================
# 文件名：step03_query_params.py
# 基础功能：学习 FastAPI 查询参数的完整用法：默认值、校验、可选参数、分页模式
# 核心学习知识点：
#   1. 查询参数 vs 路径参数 — URL ?key=value 的解析机制
#   2. Query() 高级校验器 — min_length、max_length、gt、lt、regex 等
#   3. Optional 可选参数 — 参数可以不传，用 None 做默认值
#   4. Annotated 类型注解写法 — Python 3.9+ 推荐的组合注解方式
#   5. 分页参数模式 — skip + limit 控制返回数据量和偏移
#   6. 必填 vs 可选参数 — ...(Ellipsis) 标记必填参数
#   7. 参数别名 alias — API 对外名称和 Python 内部变量名可以不同
#   8. deprecated 参数标记 — 标记废弃参数，/docs 中自动显示警告
# 适用场景：搜索过滤、分页列表、排序、API 版本兼容、可选参数控制
# 使用方法：
#   终端运行：uv run python step03_query_params.py
#   浏览器访问：
#     http://127.0.0.1:8000/items/?skip=0&limit=10      — 分页查询
#     http://127.0.0.1:8000/search/?q=fastapi&page=1     — 搜索
#     http://127.0.0.1:8000/users/?active=true&role=admin — 多条件过滤
#     http://127.0.0.1:8000/docs                         — Swagger 交互测试
# 进阶说明：
#   1. Query() 内部创建 pydantic.FieldInfo 对象，校验规则最终由 Pydantic 执行
#   2. 查询参数也支持类型转换：?count=5 自动转为 int(5)
#   3. Python 3.10+ 推荐用 T | None 替代 Optional[T]，语义更直接
#   4. 查询参数默认是字符串，FastAPI 的自动类型转换是其核心优势之一
# 常用配套函数：
#   Query(default=..., gt=, lt=, min_length=) — 查询参数校验器
#   Annotated[type, Query()]                   — Python 原生类型注解 + 校验组合
#   type | None                                — 可选参数标记（Python 3.10+ 推荐）
#   type | None                                 — 可选参数标记（Python 3.10+）
#   ellipsis（...）                              — 标记必填参数，区别于 None 默认值
# ==============================================
import uvicorn
# Python 3.9 兼容写法已移除，3.10+ 使用 str | None
from fastapi import FastAPI, Query

app = FastAPI(
    title="LearnFast API — 查询参数",
    description="FastAPI 学习 Step03：查询参数校验、分页、过滤、搜索",
    version="0.1.0",
)


# ==============================================
# 例1：基本查询参数（有默认值）— GET /items/
# 【基础】函数参数 skip 和 limit 不在路径模板中，自动成为查询参数
#         ?skip=0&limit=10 → skip=0, limit=10
#         ?limit=5           → skip 使用默认值 0, limit=5
#         不加任何参数       → skip=0, limit=10（都使用默认值）
# 【进阶】识别规则：
#   不在路径模板中的函数参数 → 自动成为查询参数（Query Parameter）
#   在路径模板中的参数       → 路径参数（Path Parameter）
#   参数声明为 Pydantic 模型 → 请求体（Request Body）
# 这3条规则构成了 FastAPI 参数识别的核心逻辑，无需手动标注
# ==============================================
@app.get("/items/")
async def list_items(skip: int = 0, limit: int = 10):
    """
    【基础功能】分页获取商品列表，skip=跳过条数，limit=每页条数
    【学习知识点】
        1. 查询参数自动识别 — 不在路径中的函数参数自动成为查询参数
        2. 默认值提供可选性 — skip=0, limit=10 指定不传参时的默认值
        3. 分页模式 — skip + limit 是最常见的分页参数组合
    参数：
        skip:  【基础释义：整数，跳过的记录数，默认0（从第一条开始）】
               【进阶释义：OFFSET 语义，对应 SQL 的 OFFSET 或 MongoDB 的 skip()】
        limit: 【基础释义：整数，返回的记录上限，默认10】
               【进阶释义：LIMIT 语义，限制单次查询返回量，防止一次返回过多数据拖垮服务】
    返回值：{"items": [...], "page_info": {...}} — 模拟分页数据
    调用示例：
        示例1：curl "http://127.0.0.1:8000/items/"                    — 第1页（默认）
        示例2：curl "http://127.0.0.1:8000/items/?skip=10&limit=10"    — 第2页
        示例3：curl "http://127.0.0.1:8000/items/?limit=5"             — 只取5条
    同场景常用替代函数：
        1. page + page_size 分页 — 用页码代替 skip，用户更友好，后端需换算 skip = (page-1) * page_size
        2. cursor 游标分页 — 用上一页最后一条 ID 做偏移，适合大数据集的稳定翻页
    注意事项：
        1. skip + limit 模式下新增/删除数据会导致翻页漂移（"第2页看到第1页的数据"）
        2. limit 需要设置上限（如 max=100），防止客户端请求过多数据
    """
    # 【基础】模拟一个数据源（真实项目中从数据库查）
    all_items = [{"id": i, "name": f"商品{i}", "price": i * 10} for i in range(1, 101)]
    # 【进阶】列表切片 [skip:skip+limit] 实现内存级分页，大数据量应在数据库层做 LIMIT+OFFSET
    page_items = all_items[skip : skip + limit]
    return {
        "items": page_items,
        "page_info": {
            "skip": skip,
            "limit": limit,
            "total": len(all_items),
            "returned": len(page_items),
        },
    }


# ==============================================
# 例2：Query() 校验器 — GET /search/
# 【基础】Query() 给查询参数附加校验规则，输入不合法自动返回 422
#         min_length=1     → 至少1个字符
#         max_length=50    → 最多50个字符
#         default=None     → 不传时为 None（可选参数）
# 【进阶】Query() 的完整参数列表（常用）：
#   default=...                → ... (Ellipsis) 表示必填
#   default=None               → 可选，不传为 None
#   alias="q"                  → API 参数名和函数参数名不同
#   title="搜索关键词"          → OpenAPI 文档中的显示标题
#   description="..."           → 参数说明文字
#   min_length / max_length    → 字符串长度校验
#   gt / ge / lt / le          → 数值大于/大于等于/小于/小于等于
#   regex=r"..."               → 正则匹配校验
#   deprecated=True             → 标记已废弃
#   include_in_schema=False    → 不显示在 OpenAPI 文档中
# ==============================================
@app.get("/search/")
async def search_items(
    q: str | None = Query(
        default=None,  # 默认值，Optional 表示可以不传
        min_length=1,  # 最小长度 1
        max_length=50,  # 最大长度 50
        title="搜索关键词",
        description="在商品名称和描述中搜索",
    ),
    page: int = Query(
        default=1,  # 默认第1页
        ge=1,  # greater than or equal to 1 → 页码最小为1
        title="页码",
    ),
):
    """
    【基础功能】按关键词搜索商品，支持分页，输入值都有严格校验
    【学习知识点】
        1. Query() 校验器 — 声明式校验规则，框架自动执行
        2. Optional + default=None — 可选参数的组合写法
        3. ge=1 数值下限校验 — 防止页码 ≤ 0 的非法输入
        4. min_length / max_length — 字符串长度校验
    参数：
        q:    【基础释义：可选字符串，搜索关键词，1到50个字符】
              【进阶释义：str | None = Query(default=None) — 三重语义：
               1. Optional 表示可传可不传
               2. str 类型注解驱动字符串校验
               3. Query() 附加长度限制】
        page: 【基础释义：整数页码，最小为1，默认第1页】【进阶释义：ge=1 设置数值下限，Pydantic 校验链执行】
    返回值：{"query": "...", "results": [...], "page": 1} — 搜索结果
    调用示例：
        示例1：curl "http://127.0.0.1:8000/search/?q=fastapi&page=1"
        示例2：curl "http://127.0.0.1:8000/search/?q=手机"（不传 page，默认为 1）
        示例3：curl "http://127.0.0.1:8000/search/"（不传 q，搜索全部）
        示例4：curl "http://127.0.0.1:8000/search/?q=&page=0"（测试 422 校验失败）
    同场景常用替代函数：
        1. 不用 Query() — q: str = None，失去长度校验能力，不推荐
        2. Annotated[str, Query()] — Python 3.9+ 推荐写法，类型注解和校验逻辑分离更清晰
    注意事项：
        1. 可选参数需设 default 值（None 或具体值），否则变成必填参数
        2. min_length=1 意味着传了 q 就不能是空字符串（""），不传则可以
    """
    # 【基础】模拟搜索匹配逻辑
    all_items = [{"id": i, "name": f"商品{i}", "category": f"分类{i%5}"} for i in range(1, 101)]

    # 【基础】如果传了搜索词，按名称匹配过滤
    if q:
        # 【基础】Python 列表推导式 + if 条件过滤
        # 大白话：从 all_items 里选出名字包含搜索词的条目
        results = [item for item in all_items if q.lower() in item["name"].lower()]
    else:
        results = all_items

    return {"query": q, "page": page, "total_results": len(results), "results": results[:10]}


# ==============================================
# 例3：必填查询参数（.../Ellipsis）— GET /required/
# 【基础】... (三个点) 在 Python 中叫 Ellipsis，在 FastAPI 中表示"必填"
#         与 default=None 的区别：... 意味着用户必须提供这个参数
#         ?name=test     ✓
#         ?               ✗ 返回 422（缺少必填参数 name）
# 【进阶】必填参数的设计哲学：
#   查询参数默认可选（因为 ? 本身表示"可选的查询"）
#   但某些场景需要强制用户提供参数（如 API key、必需的过滤条件）
#   Query(default=...) 打破了"查询参数总是可选"的默认惯例
#   注意：用在请求体（Request Body）的 Field() 中也可用同样的 ... 语法
# ==============================================
@app.get("/required/")
async def required_param(
    name: str = Query(default=..., min_length=1, description="必填的用户名"),
    age: int = Query(default=..., ge=1, le=150, description="必填的年龄，范围1-150"),
):
    """
    【基础功能】演示必填查询参数，name 和 age 都必须提供
    【学习知识点】
        1. ... (Ellipsis) — Python 内置常量，FastAPI 中使用它标记必填参数
        2. ge/le 组合 — 同时校验数值上下限（1 ≤ age ≤ 150）
        3. 多个必填查询参数 — 每个参数独立校验，任一失败整体 422
    参数：
        name: 【基础释义：必填字符串，用户名，至少1个字符】【进阶释义：default=... 传递 Ellipsis 给 Query() 内部，标记 required=True】
        age:  【基础释义：必填整数，年龄，范围 1-150】【进阶释义：ge/le 边界值校验，Pydantic 生成对应的 JSON Schema 校验规则】
    返回值：{"name": "...", "age": ..., "message": "..."} — 回显用户信息
    调用示例：
        示例1：curl "http://127.0.0.1:8000/required/?name=张三&age=25"
        示例2：curl "http://127.0.0.1:8000/required/?name=张三"（缺少 age，422）
        示例3：curl "http://127.0.0.1:8000/required/?name=张三&age=999"（age超限，422）
    同场景常用替代函数：
        1. 用请求体（POST + BaseModel）— 必填字段用 ... 标记，适合复杂数据结构
        2. 用路径参数替代 — /required/{name}/{age}，适合资源定位场景
    注意事项：
        1. 必填查询参数在 /docs 页面中会标注红色 * 号
        2. 不要滥用必填查询参数，简单的 GET 请求不应要求过多必填条件
    """
    # 【基础】返回校验通过的用户信息
    return {"name": name, "age": age, "message": f"欢迎，{name}！（{age}岁）"}


# ==============================================
# 例4：参数别名 alias — GET /alias/
# 【基础】alias 让 API 对外参数名和 Python 函数参数名不同
#         比如 API 用 user-id（带连字符），Python 变量用 user_id（下划线）
#         连字符在 Python 变量名中不合法，alias 解决了这个矛盾
#         前端调用：?user-id=123
#         Python 代码中：user_id 取值 123
# 【进阶】alias 的使用场景：
#   1. HTTP 头中常用连字符（如 X-Request-ID），Python 不支持
#   2. OpenAPI 规范推荐 camelCase，但 Python 惯用 snake_case
#   3. 兼容旧 API 参数名，同时保持 Python 代码整洁
#   注意：alias 只影响外部传参方式，不影响 Python 内部使用
# ==============================================
@app.get("/alias/")
async def alias_demo(
    user_name: str = Query(default=..., alias="user-name", description="用连字符传递的用户名"),
    request_id: str = Query(default=..., alias="X-Request-ID", description="请求追踪ID"),
):
    """
    【基础功能】演示参数别名，外部用连字符传参，内部用下划线变量接收
    【学习知识点】
        1. alias="外部名" — API 参数名和 Python 变量名分离
        2. 连字符参数名 — 解决 Python 变量名不支持连字符的问题
        3. HTTP 头命名风格 — X-Request-ID 这种带连字符的标准头命名
    参数：
        user_name:  【基础释义：别名 user-name，外部传参用连字符】【进阶释义：alias 映射到 OpenAPI Schema 的 name 字段】
        request_id: 【基础释义：别名 X-Request-ID，模拟 HTTP 头命名】【进阶释义：大写字母开头+连字符，Python 变量名不支持】
    返回值：{"user_name": "...", "request_id": "..."} — 回显收到的参数值
    调用示例：
        示例1：curl "http://127.0.0.1:8000/alias/?user-name=张三&X-Request-ID=abc-123"
        示例2（错误写法）：curl "http://127.0.0.1:8000/alias/?user_name=张三"（用 Python 变量名传参会 422）
    同场景常用替代函数：
        1. Header() + convert_underscores=True — 自动转换 _ 为 -，如 X_Request_Id → X-Request-Id
        2. 手动在函数内部做参数名映射 — 不如 alias 优雅，失去自动文档映射
    注意事项：
        1. 使用 alias 后，原始 Python 变量名不能用于 URL 传参
        2. 别名应该在 API 文档中清晰标注，避免使用者混淆
    """
    # 【基础】返回收到的参数
    return {"user_name": user_name, "request_id": request_id}


# ==============================================
# 例5：废弃参数 deprecated — GET /legacy/
# 【基础】deprecated=True 标记旧参数不再使用，/docs 中灰色显示+警告图标
#         给 API 使用者缓冲期，逐步迁移到新参数
#         旧参数仍可正常工作，只是文档上警告
# 【进阶】API 版本演进策略：
#   1. 新增参数替代旧参数（v1 用 old_name，v2 用 new_name）
#   2. 在过渡期同时支持两个参数，deprecated 标记旧的
#   3. 一个版本周期后移除旧参数，清理代码
#   4. 配合 HTTP 响应头 Sunset/Deprecation 告知下线时间
# 设计模式：Strangler Fig Pattern — 新功能逐步替代旧功能，而非一次性重写
# ==============================================
@app.get("/legacy/")
async def legacy_endpoint(
    old_param: str | None = Query(
        default=None,
        deprecated=True,  # 标记为已废弃，文档灰色显示
        description="此参数已废弃，请改用 new_param",
    ),
    new_param: str | None = Query(
        default=None,
        description="新参数，替代 old_param",
    ),
):
    """
    【基础功能】演示参数弃用机制，平滑过渡 API 旧参数到新参数
    【学习知识点】
        1. deprecated=True — 标记废弃参数，文档自动显示灰色和警告
        2. API 版本兼容策略 — 新旧参数共存过渡期
        3. 面向使用者的 API 演进 — 文档先行，再移除功能
    参数：
        old_param: 【基础释义：已废弃的旧参数名，建议改用 new_param】【进阶释义：内部仍工作但文档标记废弃，缓冲期后移除此参数】
        new_param: 【基础释义：新的参数名，功能同旧参数】【进阶释义：新参数的名字/校验/行为可能与旧参数不同】
    返回值：{"param_used": "...", "deprecated": True/False} — 使用的参数和是否废弃
    调用示例：
        示例1：curl "http://127.0.0.1:8000/legacy/?old_param=hello"（旧参数仍可用但文档警告）
        示例2：curl "http://127.0.0.1:8000/legacy/?new_param=world"（推荐方式）
        示例3：查看 /docs 对比两个参数的显示差异
    同场景常用替代函数：
        1. HTTP 301 重定向 — 自动将旧 URL 请求转发到新 URL
        2. @app.api_route() 多路径 — 同一函数挂多个路径，旧路径保留兼容
    注意事项：
        1. deprecated 只是文档标记，不影响实际校验和执行
        2. 废弃参数也需要设置合理的 default 值（通常是 None）
    """
    # 【基础】优先使用新参数，兼顾旧参数兼容
    used = new_param or old_param or "未传参"
    # 【基础】old_param 有值但 new_param 没值 = 用户还在使用旧参数
    is_deprecated = bool(old_param and not new_param)
    return {
        "param_used": used,
        "is_deprecated_usage": is_deprecated,
        "hint": "建议改用 new_param 参数" if is_deprecated else "正在使用新参数",
    }


# ==============================================
# 例6：Annotated 推荐写法 — GET /users/
# 【基础】Annotated[type, Query(...)] 是 Python 3.9+ 的类型注解新标准
#         把类型信息和校验逻辑分开写，更清晰
#         对比旧写法：q: str = Query(default=...)  → 变量和默认值混在一起
#         Annotated 写法：q: Annotated[str, Query(default=...)] → 类型在左，校验在右
# 【进阶】Annotated 的优势：
#   1. 类型注解和校验信息物理分离，IDE 静态分析更准确
#   2. 可以叠加多个元数据（如 Annotated[str, Query(), Depends()]）
#   3. Python 官方推荐的注解元数据机制（PEP 593）
#   4. FastAPI 官方从 0.95+ 开始主推 Annotated 写法
# 如果你的团队用 Python 3.9+，建议全面使用 Annotated 风格
# ==============================================
from typing import Annotated  # Python 标准库 typing 模块


@app.get("/users/")
async def list_users(
    role: Annotated[
        str | None,  # 类型：可选的字符串
        Query(           # 校验元数据（默认值用 = 在 Annotated 外面设置）
            description="按角色筛选用户（admin/user/guest）",
            min_length=2,
        ),
    ] = None,  # ← 注意：Annotated 写法的默认值放在最后
    active: Annotated[
        bool | None,
        Query(
            description="按活跃状态筛选（true=活跃，false=禁用）",
        ),
    ] = None,
):
    """
    【基础功能】用 Annotated 写法实现用户列表筛选（按角色和状态）
    【学习知识点】
        1. Annotated[type, Query()] — Python 3.9+ 类型注解 + 校验组合
        2. 默认值放在 Annotated 之后 — 语法：Annotated[T, meta] = default
        3. Annotated 的元数据叠加 — 可以追加多个元数据对象（如 Depends）
        4. bool 查询参数 — FastAPI 自动解析 true/false/1/0 等
    参数：
        role:   【基础释义：可选字符串，角色筛选（admin/user/guest）】
                【进阶释义：Annotated[str | None, Query(...)] — 类型在 Annotated 第一个参数，校验在第二个参数】
        active: 【基础释义：可选布尔值，按活跃状态筛选】【进阶释义：bool 查询参数自动识别多种布尔表达】
    返回值：{"users": [...], "filters": {...}} — 筛选后的用户列表
    调用示例：
        示例1：curl "http://127.0.0.1:8000/users/?role=admin&active=true"
        示例2：curl "http://127.0.0.1:8000/users/?role=user"
        示例3：curl "http://127.0.0.1:8000/users/"（不传筛选条件，返回全部）
    同场景常用替代函数：
        1. 旧式 Query() 写法 — role: str = Query(default=None)，简洁但类型和校验混合
        2. Union[None, str] — str | None 的旧式等价写法，功能等价但不够简洁
    注意事项：
        1. Annotated 在 Python 3.9+ 可用，3.8 及以下不支持
        2. 默认值放在 Annotated[] = 之后，不能放在 Query(default=xxx) 里（冲突）
    """
    # 【基础】模拟用户数据
    users = [
        {"id": 1, "name": "张三", "role": "admin", "active": True},
        {"id": 2, "name": "李四", "role": "user", "active": True},
        {"id": 3, "name": "王五", "role": "guest", "active": False},
        {"id": 4, "name": "赵六", "role": "admin", "active": False},
        {"id": 5, "name": "钱七", "role": "user", "active": True},
    ]

    # 【基础】根据角色和活跃状态做筛选，None 表示不限制
    # 【进阶】列表推导式 + 多条件过滤，每个条件用 or 做"不筛选时跳过"
    result = [
        u
        for u in users
        if (role is None or u["role"] == role)  # role 为 None = 不限制
        and (active is None or u["active"] == active)  # active 为 None = 不限制
    ]

    return {"users": result, "count": len(result), "filters": {"role": role, "active": active}}


# ==============================================
# 程序入口
# ==============================================
if __name__ == "__main__":
    uvicorn.run(
        "step03_query_params:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )
