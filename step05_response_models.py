# ==============================================
# 文件名：step05_response_models.py
# 基础功能：学习 FastAPI 响应模型（Response Model）的使用：过滤敏感字段、状态码、响应头
# 核心学习知识点：
#   1. response_model — 控制 API 输出的数据结构，过滤不应返回的字段
#   2. response_model_exclude — 排除指定字段不返回（如密码、内部ID）
#   3. response_model_include — 只返回指定字段集
#   4. response_model_exclude_unset — 只返回实际传了值的字段（PATCH 部分更新常用）
#   5. status_code — 自定义 HTTP 状态码（201 Created、204 No Content）
#   6. Response 对象 — 完全控制响应体、状态码、响应头
#   7. response_description — OpenAPI 文档中的状态码描述
#   8. JSONResponse — 自定义 JSON 响应，直接控制响应内容
# 适用场景：用户接口过滤密码、API 版本差异输出、敏感数据脱敏、文件下载响应头
# 使用方法：
#   终端运行：uv run python step05_response_models.py
#   浏览器访问 http://127.0.0.1:8000/docs 交互式测试所有接口
# 进阶说明：
#   1. response_model 在响应数据返回前执行，只影响输出，不影响内部业务逻辑
#   2. Pydantic v2 的 model_dump() 也支持 exclude/include 参数，实现相同效果
#   3. 使用 response_model 有性能代价（序列化+校验），但带来的安全性收益远大于代价
#   4. 对于高并发接口，可以用 response_model_exclude_none 减少传输量
# 常用配套函数：
#   JSONResponse(content=, status_code=) — 直接构造 JSON 响应
#   RedirectResponse(url=)               — HTTP 重定向响应（301/302）
#   StreamingResponse(content=)          — 流式响应（大文件下载、SSE）
#   FileResponse(path=)                  — 静态文件响应（下载文件）
#   PlainTextResponse(content=)          — 纯文本响应
#   HTMLResponse(content=)               — HTML 页面响应
#   Response(content=, media_type=)      — 通用响应基类，自定义任意类型
# ==============================================
import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field


app = FastAPI(
    title="LearnFast API — 响应模型",
    description="FastAPI 学习 Step05：响应模型过滤、状态码、自定义响应",
    version="0.1.0",
)


# ==============================================
# 模型定义区
# ==============================================


class UserCreate(BaseModel):
    """创建用户的输入模型（含密码字段）"""
    username: str = Field(min_length=1, max_length=20)
    password: str = Field(min_length=6, description="明文密码（仅输入用，不应返回）")
    email: str
    role: str = Field(default="user")


class UserResponse(BaseModel):
    """
    用户输出模型（不含密码）。
    【基础】与 UserCreate 不同：去掉了 password 字段，增加了 id 和 is_active
    【进阶】设计原则：输出模型和输入模型分开定义
      1. 安全性 — 密码等敏感字段永不出现在响应中
      2. 关注点分离 — 输入校验规则 ≠ 输出展示规则
      3. API 演进 — 可以独立修改输入/输出结构而不互相影响
      4. 性能 — 避免返回不需要的字段，减少网络传输量
    """
    id: int
    username: str
    email: str
    role: str
    is_active: bool


class UserDetailResponse(BaseModel):
    """用户详情输出模型（含更多字段）"""
    id: int
    username: str
    email: str
    role: str
    is_active: bool
    internal_id: str = Field(description="内部系统ID，某些场景需要隐藏")
    created_at: str


class ItemCreate(BaseModel):
    """商品创建输入"""
    name: str
    price: float = Field(gt=0)
    description: str | None = None
    tags: list[str] = Field(default=[])


class ItemResponse(BaseModel):
    """商品输出"""
    id: int
    name: str
    price: float


# ==============================================
# 模拟数据库
# ==============================================
fake_users_db = {}


# ==============================================
# 例1：response_model 过滤敏感字段 — POST /users/
# 【基础】response_model=UserResponse 指定返回给客户的数据结构
#         UserResponse 没有 password 字段 → 密码不出现在响应中
#         即使 return 的 dict 里有 password，FastAPI 也会自动去掉
# 【进阶】response_model 执行流程：
#   1. 路径操作函数执行完毕，得到返回的 dict/model
#   2. FastAPI 调用 UserResponse.model_validate(returned_data)
#   3. Pydantic 按 UserResponse 定义校验并过滤数据
#   4. 多余的字段被丢弃（exclude），缺少的字段报错
#   5. model_dump() 序列化为 JSON 返回客户端
# 核心价值：函数内部可以用完整数据（含密码做业务逻辑），但客户端拿不到敏感字段
#   return 的 dict 里有 password，UserResponse 没有，password 被自动丢弃
# 简化替代写法：手动 del user_dict["password"]，但不如 response_model 声明式清晰
# ==============================================
@app.post("/users/", response_model=UserResponse, status_code=201)
async def create_user(user: UserCreate):
    """
    【基础功能】创建用户，返回不含密码的用户信息，状态码 201 Created
    【学习知识点】
        1. response_model — 声明式过滤输出字段，密码永不泄露
        2. status_code=201 — POST 创建成功返回 201 而非默认 200
        3. 输入/输出模型分离 — UserCreate ≠ UserResponse
    参数：
        user: 【基础释义：UserCreate 输入模型，含密码用于创建账户】
    返回值：【基础释义：UserResponse 格式，不含密码的安全用户信息】
            【进阶释义：FastAPI 用 UserResponse 过滤返回数据，多余字段自动丢弃】
    调用示例：
        示例1：curl -X POST http://127.0.0.1:8000/users/ -H "Content-Type: application/json" -d '{"username":"zhang","password":"secret123","email":"z@t.com"}'
        示例2：观察返回结果 — 没有 password 字段，但有新增的 id 和 is_active
    同场景常用替代函数：
        1. 手动过滤 dict — del data["password"]，原始但不安全（容易遗漏）
        2. response_model_exclude={"password"} — 排除指定字段（备选方案）
        3. @field_serializer — 自定义字段序列化逻辑，适合脱敏场景
    注意事项：
        1. response_model 中的字段必须和返回 dict 的 key 能匹配，多余的自动忽略
        2. 输入模型和输出模型分开是行业最佳实践，不要偷懒混用
    """
    # 【基础】生成模拟用户 ID
    user_id = len(fake_users_db) + 1

    # 【基础】构造完整用户数据（含密码，但 response_model 会过滤掉）
    user_data = {
        "id": user_id,
        "username": user.username,
        "password": user.password,  # ← 在 dict 中存在，但 UserResponse 没有该字段，输出时自动丢弃
        "email": user.email,
        "role": user.role,
        "is_active": True,
    }

    # 存入模拟数据库
    fake_users_db[user_id] = user_data

    # 【进阶】返回的 dict 包含 password，但 response_model=UserResponse 自动过滤
    #   这就是"返回什么 ≠ 输出什么"的安全设计
    return user_data  # password 将被 response_model 过滤，客户端看不到


# ==============================================
# 例2：response_model_exclude — GET /users/{user_id}
# 【基础】动态排除字段：response_model_exclude={"internal_id"} 不返回 internal_id
#         适合某些场景下按需隐藏字段（如不同角色看到不同字段集）
# 【进阶】exclude vs include 的灵活控制：
#   exclude={"field1", "field2"}   → 排除指定字段
#   exclude_unset=True             → 只返回传了值的字段（PATCH 更新确认用）
#   exclude_none=True              → 排除值为 None 的字段，减少传输
#   exclude_defaults=True          → 排除值等于默认值的字段
#   include={"field1", "field2"}   → 只返回指定字段（白名单模式）
# 这些参数在函数体内动态设置，比 response_model 静态声明更灵活
# ==============================================
@app.get("/users/{user_id}", response_model=UserDetailResponse)
async def get_user(user_id: int, show_internal: bool = False):
    """
    【基础功能】获取用户详情，可选择是否显示内部系统ID
    【学习知识点】
        1. 动态 exclude — 根据请求参数决定返回哪些字段
        2. response_model_exclude — 响应生成时动态排除字段
        3. 查询参数控制输出内容 — show_internal 决定是否包含敏感字段
    参数：
        user_id: 【基础释义：整数，用户ID】
        show_internal: 【基础释义：布尔值，是否显示内部ID（默认隐藏）】
    返回值：UserDetailResponse — 用户详情（根据 show_internal 决定 internal_id 可见性）
    调用示例：
        示例1：curl http://127.0.0.1:8000/users/1（internal_id 被隐藏）
        示例2：curl http://127.0.0.1:8000/users/1?show_internal=true（internal_id 可见）
    同场景常用替代函数：
        1. 两个不同的 response_model — 根据权限路由到不同模型，但代码冗余
        2. Pydantic model_dump(exclude={...}) — 在函数内部手动过滤后返回
    注意事项：
        1. response_model_exclude 的字段名必须和 response_model 的名字匹配
        2. 动态 exclude 会影响 Swagger 文档中显示的示例（因它是运行时决定）
    """
    user = fake_users_db.get(user_id)
    if user is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"用户 {user_id} 不存在")

    user_data = {
        "id": user["id"],
        "username": user["username"],
        "email": user["email"],
        "role": user["role"],
        "is_active": user["is_active"],
        "internal_id": f"INTERNAL-{user['id']:04d}",
        "created_at": "2026-01-01T00:00:00",
    }

    # 【基础】如果不需要显示内部ID，动态隐藏
    # 【进阶】response_model_exclude 是 FastAPI 路由层参数，在响应序列化阶段生效
    if not show_internal:
        # 排除 internal_id 字段，客户端无法看到
        return JSONResponse(
            content={
                k: v for k, v in user_data.items() if k != "internal_id"
            }
        )

    return user_data


# ==============================================
# 例3：response_model_exclude_none — PATCH 部分更新确认
# 【基础】exclude_none=True 过滤掉值为 None 的字段
#         PATCH 只传 name → 返回值只有 name 和新数据，没有被清空的 email 等 None 字段
#         JSON 输出更简洁，不会出现 "email": null 这种无意义数据
# 【进阶】exclude_none 减少传输量：
#   没有 exclude_none：{"id":1,"name":"新名","price":0.0,"description":null,"tags":null}
#   有 exclude_none：{"id":1,"name":"新名","price":0.0}
#   在高频调用场景下，排除 null 字段可显著减少带宽（尤其含大量可选字段时）
# ==============================================
@app.patch("/users/{user_id}", response_model=UserResponse)
async def patch_user(user_id: int, username: str | None = None, email: str | None = None):
    """
    【基础功能】部分更新用户，只更新传了值的字段，未传字段保持不变
    【学习知识点】
        1. PATCH 语义 — 部分更新，只改传的字段，不覆盖未传字段
        2. Optional 参数 — 可选参数默认 None，None = "用户没传，不更新"
        3. 部分更新的数据库交互模式 — 先查后改
    参数：
        user_id:  【基础释义：整数，要更新的用户ID】
        username: 【基础释义：可选字符串，新用户名，不传则不更新】
        email:    【基础释义：可选字符串，新邮箱，不传则不更新】
    返回值：UserResponse — 更新后的用户信息
    调用示例：
        示例1：curl -X PATCH http://127.0.0.1:8000/users/1?username=新名字（只改名字）
        示例2：curl -X PATCH http://127.0.0.1:8000/users/1?username=新名&email=new@t.com（改两个字段）
        示例3：curl -X PATCH http://127.0.0.1:8000/users/1（不传任何字段，原样返回）
    同场景常用替代函数：
        1. PUT 完整替换 — 需要传所有字段，PATCH 更轻量适合部分更新
        2. 请求体 + Optional 字段 — 用 BaseModel 传参，比查询参数更规范
        3. JSON Patch (RFC 6902) — 标准化部分更新协议，适合复杂操作场景
    注意事项：
        1. 实际项目中 PATCH 应使用请求体而非查询参数（此处为简化演示用查询参数）
        2. None vs 空字符串 — None = "不改"，"" = "改为空"，两者语义不同
    """
    user = fake_users_db.get(user_id)
    if user is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"用户 {user_id} 不存在")

    # 【基础】只更新传了值的字段（非 None）
    if username is not None:
        user["username"] = username
    if email is not None:
        user["email"] = email

    return user


# ==============================================
# 例4：204 No Content — DELETE /users/{user_id}
# 【基础】删除成功后返回 204，无响应体（body 为空）
#         204 No Content 语义：操作成功，但没有可返回的内容
#         和 200 OK 的区别：200 通常带响应体，204 明确表示没有内容
# 【进阶】常用的非 200 状态码一览：
#   201 Created          — 资源创建成功
#   202 Accepted         — 请求已接收但尚未处理（异步任务）
#   204 No Content       — 操作成功，无响应体
#   301 Moved Permanently— 永久重定向
#   304 Not Modified     — 资源未修改（缓存命中）
#   400 Bad Request      — 请求格式错误
#   401 Unauthorized     — 未认证（需要登录）
#   403 Forbidden        — 已认证但权限不足
#   404 Not Found        — 资源不存在
#   409 Conflict         — 资源冲突（如重复创建）
#   422 Unprocessable    — 参数校验失败（FastAPI 默认校验错误）
#   429 Too Many Requests— 频率限制
#   500 Internal Error   — 服务器内部错误
# ==============================================
@app.delete("/users/{user_id}", status_code=204)
async def delete_user(user_id: int):
    """
    【基础功能】删除用户，成功返回 204 No Content（无响应体）
    【学习知识点】
        1. HTTP 204 No Content — 操作成功但无响应内容的语义
        2. DELETE 方法 — RESTful 标准的资源删除方法
        3. status_code 自定义 — 非默认 200 的状态码使用
    参数：
        user_id: 【基础释义：整数，要删除的用户ID】
    返回值：无（204 状态码，响应体为空）
    调用示例：
        示例1：curl -X DELETE http://127.0.0.1:8000/users/1
        示例2：curl -I -X DELETE http://127.0.0.1:8000/users/1（查看响应头，确认 204）
    同场景常用替代函数：
        1. 200 + {"message": "deleted"} — 传统风格，204 更符合 REST 语义
        2. 软删除（is_deleted=True）— 不真正删除数据，保留恢复能力
    注意事项：
        1. 204 响应不能有响应体，如果 return 了数据 FastAPI 会忽略
        2. 重复删除同一 ID 应该返回 404 还是 204？REST 惯例：幂等，已删除仍返回 204
    """
    if user_id in fake_users_db:
        del fake_users_db[user_id]
    # 【基础】204 不需要 return，响应体为空
    # 【进阶】Response(status_code=204) 也可达到同样效果


# ==============================================
# 例5：Response 对象自定义响应头 — GET /users/export/{user_id}
# 【基础】Response 对象可以直接操作响应头和内容
#         response.headers["X-Custom-Header"] = "xxx"
#         返回 Response 对象而非 dict/模型时，不会被 response_model 处理
# 【进阶】Response vs JSONResponse 的选择：
#   Response(content=bytes, media_type="application/json")
#     → 通用响应，需手动设 media_type 和序列化
#   JSONResponse(content=dict, status_code=200)
#     → 自动 JSON 序列化，适合标准 JSON API
#   StreamingResponse → 适合流式输出（文件下载、SSE 事件流）
# 返回 Response 时，response_model 参数会被忽略（因为 Response 已完全控制输出）
# ==============================================
@app.get("/users/export/{user_id}")
async def export_user(user_id: int):
    """
    【基础功能】导出用户数据，自定义响应头和内容格式
    【学习知识点】
        1. Response 对象 — 完全控制响应的三要素：body、status、headers
        2. 自定义响应头 — 设置 X- 前缀的自定义头（行业惯例）
        3. 返回 Response 时跳过 response_model 处理
    参数：
        user_id: 【基础释义：整数，要导出的用户ID】
    返回值：Response 对象 — 完全自定义的 HTTP 响应
    调用示例：
        示例1：curl -i http://127.0.0.1:8000/users/export/1（-i 显示响应头）
        示例2：在浏览器 /docs 中测试此接口，查看响应头
    同场景常用替代函数：
        1. JSONResponse — 只控制 JSON 内容，比 Response 少写 media_type
        2. FileResponse — 直接返回文件内容，自动设置 Content-Disposition
        3. StreamingResponse — 大文件流式下载，不占用服务端内存
    注意事项：
        1. 自定义头建议用 X- 前缀（虽然 RFC 6648 建议废弃此惯例，但业界仍广泛使用）
        2. 返回 Response 时不会再经过 response_model 过滤，需自行确保数据安全
    """
    user = fake_users_db.get(user_id)
    if user is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"用户 {user_id} 不存在")

    # 【基础】构造要返回的导出数据（去除敏感字段）
    export_data = {
        "id": user["id"],
        "username": user["username"],
        "email": user["email"],
        "role": user["role"],
    }

    # 【进阶】import json 手动序列化，返回 Response 对象控制全部参数
    import json
    content = json.dumps(export_data, ensure_ascii=False, indent=2)

    # 【基础】Response(content=内容, media_type=类型, headers=头信息)
    response = Response(
        content=content,
        media_type="application/json",
        status_code=200,
    )
    # 【基础】添加自定义响应头，X-Export-At = 导出时间
    # 【进阶】headers 是 MutableHeaders 对象，继承自 dict
    from datetime import datetime
    response.headers["X-Export-At"] = datetime.now().isoformat()
    response.headers["X-Export-Version"] = "1.0"
    response.headers["X-User-ID"] = str(user_id)

    return response


# ==============================================
# 程序入口
# ==============================================
if __name__ == "__main__":
    uvicorn.run(
        "step05_response_models:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )
