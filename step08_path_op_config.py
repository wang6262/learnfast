# ==============================================
# 文件名：step08_path_op_config.py
# 基础功能：学习 FastAPI 路径操作配置：标签、文档描述、废弃标记、OpenAPI 元数据
# 核心学习知识点：
#   1. tags 标签 — 在 /docs 中分组显示接口，改善文档可读性
#   2. summary + description — 为接口添加简短标题和详细说明
#   3. response_description — 自定义不同状态码的文档描述
#   4. deprecated — 标记废弃接口，文档自动灰色 + 警告
#   5. include_in_schema=False — 隐藏内部接口，不出现在 OpenAPI 文档中
#   6. status_code — 显式声明非 200 的成功状态码
#   7. OpenAPI 元数据 — title/description/version/summary/contact/license 等
#   8. 响应额外信息 — responses 参数添加多状态码的文档描述
# 适用场景：完善 API 文档、API 版本演进、内部管理接口隐藏、文档分组
# 使用方法：
#   终端运行：uv run python step08_path_op_config.py
#   浏览器访问：
#     http://127.0.0.1:8000/docs      — Swagger UI 查看分组、标签、废弃标记
#     http://127.0.0.1:8000/redoc     — ReDoc 风格文档
#     http://127.0.0.1:8000/openapi.json — 原始 OpenAPI Schema
# 进阶说明：
#   1. OpenAPI 规范（3.1.x）是 API 文档的行业标准，不依赖 Swagger 也可以被其他工具消费
#   2. 良好的文档可以减少 80% 的沟通成本（开发者直接看文档，无需频繁问接口格式）
#   3. include_in_schema=False 不会影响接口功能，只是在文档中隐藏
#   4. 使用 OpenAPI 的 callbacks 可以定义 webhook 回调格式
# 常用配套函数：
#   @app.get(tags=["标签"])                — 接口分组
#   @app.get(summary="标题")               — 简短标题（Swagger 列表显示）
#   @app.get(description="详细说明")       — 长描述（Markdown 支持）
#   @app.get(deprecated=True)              — 标记已废弃
#   @app.get(include_in_schema=False)      — 从文档中隐藏
#   @app.get(response_description="描述")  — 响应说明
#   @app.get(responses={404:{...}})        — 多状态码的文档描述
#   @app.get(status_code=201)              — 自定义成功状态码
# ==============================================
import uvicorn

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


# ==============================================
# 应用实例 — 添加更多 OpenAPI 元数据
# 【基础】FastAPI() 的额外参数会显示在文档头部
# 【进阶】完整的 OpenAPI 元数据字段：
#   title — 应用标题（/docs 页面顶部）
#   description — 应用描述（支持 Markdown）
#   version — API 版本（建议用语义化版本 semver）
#   summary — 简短摘要（OpenAPI 3.1+）
#   terms_of_service — 服务条款 URL
#   contact={...} — 联系人信息（name, url, email）
#   license_info={...} — 许可证信息（name, url）
#   openapi_tags=[...] — 预定义标签列表（含描述和外部文档链接）
#   servers=[...] — 指定服务器列表（开发/生产环境 URL）
# 这些元数据出现在 /openapi.json 中，并被 /docs /redoc 消费
# ==============================================
app = FastAPI(
    title="LearnFast API — 路径操作配置",
    description="""
FastAPI 学习 Step08：路径操作配置与 OpenAPI 文档自定义。

## 本步骤学习内容
- **tags** — 接口分组标签
- **summary / description** — 接口标题和说明
- **deprecated** — 废弃接口标记
- **include_in_schema** — 隐藏接口
- **OpenAPI 元数据** — API 全局元信息

## Markdown 支持
OpenAPI description 字段支持 **Markdown** 语法，可以添加：
- 标题、列表
- 代码块
- 链接 [FastAPI 官方文档](https://fastapi.tiangolo.com)
""",
    version="0.1.0",
    summary="学习型 FastAPI 路径操作配置示例",
    contact={
        "name": "LearnFast 学习项目",
        "url": "https://github.com/learnfast",
    },
    license_info={
        "name": "MIT",
    },
    # 【基础】预定义标签列表，在 /docs 中按 tags 参数分组显示
    # 【进阶】openapi_tags 可以让 Swagger UI 按标签顺序排列，每个标签可加描述
    openapi_tags=[
        {
            "name": "users",
            "description": "用户管理相关接口 — 包含查询、创建、更新、删除操作",
            # externalDocs 给标签添加外部文档链接（如详细使用指南）
            "externalDocs": {
                "description": "用户管理详细文档",
                "url": "https://example.com/docs/users",
            },
        },
        {"name": "items", "description": "商品管理相关接口 — 商品 CRUD 操作"},
        {"name": "legacy", "description": "已废弃的旧版接口 — 请尽快迁移到新版"},
        {"name": "internal", "description": "内部管理接口 — 不在文档中显示"},
    ],
)


# ==============================================
# 模型定义
# ==============================================
class UserResponse(BaseModel):
    """用户输出模型"""
    id: int
    username: str
    email: str
    role: str = "user"


class ItemResponse(BaseModel):
    """商品输出模型"""
    id: int
    name: str
    price: float
    in_stock: bool


# ==============================================
# 模拟数据库
# ==============================================
fake_users = {
    1: {"id": 1, "username": "admin", "email": "admin@test.com", "role": "admin"},
    2: {"id": 2, "username": "user1", "email": "user1@test.com", "role": "user"},
}

fake_items = {
    1: {"id": 1, "name": "机械键盘", "price": 299.0, "in_stock": True},
    2: {"id": 2, "name": "无线鼠标", "price": 149.0, "in_stock": False},
}


# ==============================================
# 用户管理接口 — tags=["users"]
# 【基础】tags 参数将接口归类到 "users" 标签下，/docs 中分组显示
#         同一个标签的接口显示在同一个分组里
#         标签名建议用英文复数（users/items/orders），或中文业务名
# 【进阶】tags 值是 str 列表，一个接口可以属于多个标签
#   如 tags=["users", "v2"] 表示该接口同时出现在 users 和 v2 分组中
# ==============================================


@app.get(
    "/users/",
    tags=["users"],
    summary="获取用户列表",
    description="返回所有注册用户的列表。支持按角色筛选（后续版本将支持分页参数）。",
    response_description="成功返回用户列表，包含 id、username、email、role 字段",
    response_model=list[UserResponse],
)
async def list_users():
    """
    【基础功能】获取所有用户列表
    【学习知识点】
        1. summary — 接口简短标题，显示在 Swagger 列表左侧
        2. description — 接口详细描述，展开后可见，支持 Markdown
        3. response_description — 响应数据的文字说明
        4. response_model=list[Model] — 文档中标注返回值为模型数组
    调用示例：curl http://127.0.0.1:8000/users/
    """
    return list(fake_users.values())


@app.get(
    "/users/{user_id}",
    tags=["users"],
    summary="获取单个用户详情",
    description="根据用户 ID 获取用户详细信息。**user_id 必须为整数**。",
    response_description="成功返回单个用户的完整信息",
    # 【基础】responses 参数定义不同状态码的文档描述
    #   让使用者预先知道 404 时返回什么格式
    # 【进阶】每个状态码的 description 支持 Markdown
    #   model 参数可以在文档中展示错误响应体的 JSON Schema
    responses={
        200: {"description": "成功返回用户信息"},
        404: {"description": "用户不存在", "content": {"application/json": {"example": {"detail": "用户 999 不存在"}}}},
    },
    status_code=200,
)
async def get_user_detail(user_id: int):
    """获取用户详情"""
    user = fake_users.get(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail=f"用户 {user_id} 不存在")
    return user


# ==============================================
# 商品管理接口 — tags=["items"]
# ==============================================


@app.get(
    "/items/",
    tags=["items"],
    summary="获取商品列表",
    description="返回所有商品。商品信息包括名称、价格、库存状态。",
    response_description="商品对象数组",
)
async def list_items():
    """获取商品列表"""
    return list(fake_items.values())


@app.get(
    "/items/{item_id}",
    tags=["items"],
    summary="获取单个商品",
    description="根据商品 ID 获取详细信息（暂不支持查询参数筛选）。",
    responses={
        404: {"description": "商品不存在"},
    },
)
async def get_item(item_id: int):
    """获取单个商品"""
    item = fake_items.get(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail=f"商品 {item_id} 不存在")
    return item


# ==============================================
# 旧版接口 — tags=["legacy"] + deprecated=True
# 【基础】deprecated=True 让接口在 /docs 中显示灰色 + 删除线 + 警告图标
#         使用者一眼就知道这个接口即将下线，应迁移到新版
# 【进阶】API 生命周期管理：
#   1. 发布新接口（v2_users），新旧并存
#   2. 标记旧接口 deprecated=True，文档警告
#   3. 设置下线日期（可配合 HTTP Sunet 头）
#   4. 观察旧接口调用量降至零后移除
#   5. 如果旧接口仍有调用，联系使用方做迁移
# 这是一种渐进式废弃策略，给客户端留出迁移时间
# ==============================================


@app.get(
    "/v1/users/",
    tags=["legacy"],
    summary="[已废弃] 旧版用户列表",
    description="""
> ⚠️ **此接口已废弃，请使用新版 `/users/`**

旧版接口将于下个版本移除。新版接口返回结构有所简化，
使用 `response_model` 过滤了敏感字段。
""",
    deprecated=True,  # ← Swagger 灰色 + 删除线 + 警告
)
async def legacy_list_users():
    """【已废弃】旧版用户列表，请迁移到 GET /users/"""
    return {"data": list(fake_users.values()), "version": "v1", "warning": "此接口已废弃，请使用 /users/"}


# ==============================================
# 内部接口 — include_in_schema=False
# 【基础】include_in_schema=False 让接口不出现在 OpenAPI 文档中
#         接口函数正常可用，但 /docs 和 /redoc 中看不到
#         适合内部管理接口、调试接口、健康检查等不需要对外暴露文档的场景
# 【进阶】隐藏接口的安全考量：
#   1. 隐藏 ≠ 安全，接口仍然可通过 URL 直接访问
#   2. 隐藏只是减少表面积，真正的安全需要鉴权
#   3. 可用于内部调试接口（如 dump 缓存、查看配置），这些接口对外无意义
#   4. 生产环境中可以设置 docs_url=None 完全关闭文档
# 注意：隐藏接口仍可通过 openapi.json 看到？不会 — include_in_schema=False
#   意味着不会添加到 OpenAPI Schema 中，openapi.json 也看不到
# ==============================================


@app.get(
    "/internal/stats/",
    tags=["internal"],
    summary="内部统计接口（不在文档中显示）",
    include_in_schema=False,  # ← 从 OpenAPI Schema 中排除
)
async def internal_stats():
    """
    【基础功能】内部调试用统计接口，仅限开发/运维使用
    【学习知识点】
        1. include_in_schema=False — 隐藏接口，不暴露在文档中
        2. 内部接口的最佳实践 — 隐藏文档 + 鉴权保护
    """
    return {
        "total_users": len(fake_users),
        "total_items": len(fake_items),
        "server_status": "running",
        "note": "内部统计接口，不对外公开",
    }


# ==============================================
# 程序入口
# ==============================================
if __name__ == "__main__":
    uvicorn.run(
        "step08_path_op_config:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )
