# ==============================================
# 文件名：step04_request_body.py
# 基础功能：学习 FastAPI 请求体（Request Body）与 Pydantic BaseModel 的完整用法
# 核心学习知识点：
#   1. Pydantic BaseModel — 定义请求体数据结构，字段类型 = 校验规则
#   2. POST/PUT/PATCH 请求体 — 通过请求体传递复杂 JSON 数据
#   3. Field() 高级校验 — gt/lt/min_length/max_length/regex/example 等
#   4. 嵌套模型 — 模型内嵌其他模型，构建复杂数据结构
#   5. Optional 可选字段 — 请求体中可传可不传的字段
#   6. list[Model] 列表嵌套 — 请求体中传列表数据
#   7. Union/Literal 联合类型 — 字段只能取指定值集合
#   8. model_dump() JSON 序列化 — Pydantic v2 的模型导出方法
# 适用场景：用户注册、订单提交、表单录入、API 数据交互等任何需要传递结构化数据的场景
# 使用方法：
#   终端运行：uv run python step04_request_body.py
#   浏览器访问：
#     http://127.0.0.1:8000/docs                    — Swagger 交互表单测试
#     在 /docs 页面点击 "Try it out" 测试 POST 接口，填写 JSON 数据提交
#   或使用 curl 命令行测试：
#     curl -X POST http://127.0.0.1:8000/users/ -H "Content-Type: application/json" -d '{"name":"张三","email":"zhang@test.com","age":25}'
# 进阶说明：
#   1. Pydantic v2 使用 Rust 核心（pydantic-core），速度比 v1 快 5-50 倍
#   2. BaseModel 的 model_dump() 替代了 v1 的 .dict()，性能更好且支持更多选项
#   3. from_attributes=True 允许从 ORM 对象创建 Pydantic 模型（配合 SQLAlchemy 使用）
#   4. Field() 的 json_schema_extra 可添加自定义 OpenAPI Schema 扩展
# 常用配套函数：
#   BaseModel                   — Pydantic 数据模型基类，所有请求/响应模型的基础
#   Field(default=..., gt=)     — Pydantic 字段级校验器，类比 Query()/Path()
#   model_dump()                — 模型实例导出为 Python dict（Pydantic v2）
#   model_dump_json()           — 模型实例直接导出为 JSON 字符串（Pydantic v2）
#   typing.Optional             — 标记可选字段
#   typing.Union / typing.Literal — 联合类型 / 字面量类型约束
#   pydantic.EmailStr           — 内置邮箱校验类型（需安装 email-validator）
# ==============================================
import uvicorn
from typing import Literal
from fastapi import FastAPI
from pydantic import BaseModel, Field


app = FastAPI(
    title="LearnFast API — 请求体",
    description="FastAPI 学习 Step04：Pydantic 模型、请求体校验、嵌套数据结构",
    version="0.1.0",
)


# ==============================================
# 模型定义区：所有 Pydantic 数据模型集中定义在顶部
# 【基础】Pydantic 模型 = Python class 定义数据结构，字段类型 = 校验规则
# 【进阶】Pydantic 模型在 FastAPI 中的角色：
#   1. 请求体校验 → 自动验证、转换、拒绝非法数据
#   2. 响应体定义 → response_model 控制输出
#   3. OpenAPI Schema 生成 → 自动为 /docs 生成 JSON Schema
#   4. ORM 模式 → from_attributes=True 配合 SQLAlchemy 使用
# ==============================================


# --- 用户基础模型 ---
class UserCreate(BaseModel):
    """
    创建用户的请求体模型。
    每个字段的类型注解既定义了 Python 类型，也定义了校验规则。
    """

    # 【基础】str 类型，必填（没有默认值 = 必填）
    # 【进阶】Field() 内 min_length 由 Pydantic 的 str 校验器执行，失败抛出 ValidationError
    name: str = Field(
        min_length=1,
        max_length=50,
        description="用户名，1-50个字符",
        examples=["张三"],
    )

    # 【基础】str 类型，必填
    # 【进阶】pattern 使用正则校验邮箱格式，pydantic-core 在 Rust 层执行，性能极高
    email: str = Field(
        # pattern 接收正则表达式字符串
        # ^[a-zA-Z0-9_.+-]+    → 用户名部分：字母数字+特殊符号
        # @[a-zA-Z0-9-]+       → @ 域名主体
        # \.[a-zA-Z0-9-.]+$   → . 顶级域名
        pattern=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$",
        description="用户邮箱",
        examples=["zhang@test.com"],
    )

    # 【基础】int 类型，16 ≤ age ≤ 120，必填
    age: int = Field(
        ge=16,  # greater than or equal to ≥ 16
        le=120,  # less than or equal to ≤ 120
        description="年龄，16-120岁",
        examples=[25],
    )

    # 【基础】str | None 表示可以不传，默认 None
    # 【进阶】str | None 等价于 Union[str, None]，表示 str 类型或 None
    #   可选字段通常放在必填字段之后，符合 API 设计惯例
    phone: str | None = Field(
        default=None,
        description="手机号（可选）",
        examples=["13800138000"],
    )


# --- 带标签的用户模型（嵌套练习）---
class Tag(BaseModel):
    """标签子模型，被 UserWithTags 嵌套使用。"""
    key: str = Field(description="标签名")
    value: str = Field(description="标签值")


class UserWithTags(BaseModel):
    """
    包含标签列表的用户模型。
    演示 list[子模型] 嵌套 — 请求体中传对象数组。
    JSON 示例：
    {
        "name": "张三",
        "email": "zhang@test.com",
        "age": 25,
        "tags": [
            {"key": "department", "value": "技术部"},
            {"key": "level", "value": "P6"}
        ]
    }
    """
    name: str = Field(min_length=1, max_length=50)
    email: str = Field(pattern=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
    age: int = Field(ge=16, le=120)
    # 【基础】list[Tag] 表示标签列表，每个元素都是 Tag 模型
    # 【进阶】Pydantic 递归校验列表中的每个元素，任一子元素校验失败整体返回 422
    tags: list[Tag] = Field(default=[], description="用户标签列表")


# --- 订单模型（多嵌套 + 联合类型）---
class OrderItem(BaseModel):
    """订单中的商品条目"""
    product_name: str = Field(min_length=1, description="商品名称")
    quantity: int = Field(gt=0, le=999, description="数量，1-999")
    unit_price: float = Field(gt=0, description="单价（元）")


class OrderCreate(BaseModel):
    """
    创建订单的请求体模型。
    演示多模型嵌套 + Literal 联合类型。
    JSON 示例：
    {
        "user_id": 1,
        "items": [
            {"product_name": "键盘", "quantity": 2, "unit_price": 299.0},
            {"product_name": "鼠标", "quantity": 1, "unit_price": 149.0}
        ],
        "payment_method": "wechat",
        "note": "请尽快发货"
    }
    """
    user_id: int = Field(gt=0, description="用户ID")
    # 【基础】list[OrderItem] 嵌套商品列表，每个元素按 OrderItem 模型校验
    items: list[OrderItem] = Field(min_length=1, description="订单商品列表，至少一个")

    # 【基础】Literal 限定字段只能取指定值之一，否则 422
    # 【进阶】Literal 是 Python 3.8+ 特性，用于限定字段值集合
    #   类似 Enum 但无需定义类，适合少量固定选项
    payment_method: Literal["wechat", "alipay", "bank_card"] = Field(
        description="支付方式：wechat=微信，alipay=支付宝，bank_card=银行卡"
    )

    # 【基础】可选备注字段
    note: str | None = Field(default=None, max_length=200, description="备注，最多200字")


# ==============================================
# 例1：基本请求体 — POST /users/
# 【基础】函数参数 user 是 UserCreate 类型 → FastAPI 自动将 POST 请求的 JSON Body 解析为 UserCreate 对象
#         type(user) → <class 'UserCreate'>（Pydantic 模型实例）
#         user.name → 直接取字段值（带类型提示和 IDE 自动补全）
#         传错的类型/格式自动 422，无需手写 if 判断
# 【进阶】请求体解析流程（非常核心的原理）：
#   1. FastAPI 识别函数签名中的 Pydantic 模型参数 → 标记为"请求体参数"
#   2. 读取 HTTP 请求的 Content-Type 头 → 确认为 application/json
#   3. 读取请求体原始字节 → 调用 json.loads() 解析为 dict
#   4. 将 dict 传入 UserCreate(**data) → Pydantic 根据 Field 定义逐字段校验
#   5. 校验通过 → 返回 Pydantic 模型实例对象，类型安全
#   6. 校验失败 → 抛出 ValidationError，FastAPI 转换为 422 JSON 响应
# 多参数规则：一个函数可以同时有路径参数 + 查询参数 + 请求体
#   路径参数在 URL 中，查询参数在 ? 后，请求体在 POST Body 中 → 各自独立
# ==============================================
@app.post("/users/")
async def create_user(user: UserCreate):
    """
    【基础功能】接收 JSON 请求体创建用户，自动校验所有字段
    【学习知识点】
        1. Pydantic 模型作为请求体参数 — 框架自动解析 JSON → Python 对象
        2. POST 方法 + 请求体 — POST 用于创建资源，数据放在 Body 中而非 URL
        3. Field() 声明的校验规则自动执行 — min_length/ge/le/pattern 全覆盖
    参数：
        user: 【基础释义：UserCreate 模型，JSON 请求体自动解析】【进阶释义：Pydantic 模型在 FastAPI 中触发 Body 解析器】
    返回值：{"message": "用户创建成功", "user": {...}} — 创建成功的用户信息
    调用示例：
        示例1：curl -X POST http://127.0.0.1:8000/users/ -H "Content-Type: application/json" -d '{"name":"张三","email":"zhang@test.com","age":25}'
        示例2：curl -X POST http://127.0.0.1:8000/users/ -H "Content-Type: application/json" -d '{"name":"张三","email":"bad-email","age":10}'（测试 422）
        示例3：在 /docs 中点击 "Try it out" 填写 JSON 表单测试
    同场景常用替代函数：
        1. Form() 表单提交 — 接收 application/x-www-form-urlencoded，适合传统 HTML 表单
        2. dict 直接参数 — 不再自动校验，完全手动处理，不推荐
        3. dataclasses — Python 标准库 @dataclass，Pydantic 也支持，但功能不如 BaseModel 丰富
    注意事项：
        1. 请求体必须设置 Content-Type: application/json，否则 FastAPI 无法正确解析
        2. 虽然 name="张三" 含中文，FastAPI 自动处理 UTF-8 编码，无需手动编码解码
        3. Pydantic v2 的 model_dump() 替代了 v1 的 .dict()，注意版本差异
    """
    # 【基础】user 已经是校验通过的合法 UserCreate 对象
    # 【进阶】model_dump() 把 Pydantic 模型导出为 Python dict，方便后续处理（如存数据库）
    user_dict = user.model_dump()

    # 【基础】模拟保存到数据库并返回结果
    return {
        "message": "用户创建成功",
        "user": user_dict,
    }


# ==============================================
# 例2：嵌套模型请求体 — POST /users/with-tags/
# 【基础】请求体中可以嵌套子模型列表，传 JSON 对象数组
#         tags: list[Tag] → JSON 中传 tags: [{"key":"...", "value":"..."}, ...]
#         Pydantic 递归校验每个 Tag 元素的 key 和 value 字段
# 【进阶】嵌套模型校验原理：
#   1. Pydantic 看到 list[Tag] 注解 → 知道这是 Tag 模型的列表
#   2. 遍历 JSON 数组每个元素 → 逐元素调用 Tag(**element) 校验
#   3. 任一子元素校验失败 → 整个请求 422，并指出哪个元素哪个字段有问题
#   4. 错误信息格式：body.tags.0.key → 精确定位嵌套路径中的错误字段
# 设计原则：复杂数据结构 = 简单模型组合，像搭积木一样
# ==============================================
@app.post("/users/with-tags/")
async def create_user_with_tags(user: UserWithTags):
    """
    【基础功能】创建带标签的用户，演示 list[子模型] 嵌套请求体的处理
    【学习知识点】
        1. 列表嵌套模型 — list[Tag] 让请求体支持对象数组
        2. 递归校验 — 嵌套模型的子模型同样被完整校验
        3. 错误定位 — 嵌套路径中的校验错误精确到字段级别
    参数：
        user: 【基础释义：UserWithTags 模型，包含标签列表】【进阶释义：Pydantic 递归遍历嵌套模型树做全量校验】
    返回值：{"message": "...", "user": {...}, "tags_count": ...} — 创建结果
    调用示例：
        示例1 — curl 发送嵌套 JSON：
        curl -X POST http://127.0.0.1:8000/users/with-tags/ \
          -H "Content-Type: application/json" \
          -d '{"name":"张三","email":"zhang@test.com","age":25,"tags":[{"key":"dept","value":"技术部"}]}'
        示例2：在 /docs 中填写完整 JSON 测试
        示例3：尝试传 tags: [{"key":""}] 测试嵌套校验（key 为空会 422）
    同场景常用替代函数：
        1. list[dict] — 不校验子元素结构，灵活但失去类型安全
        2. list[str] — 简单字符串列表，适合标签不需要 key-value 的场景
    注意事项：
        1. tags 有默认值 []，不传 tags 字段不会报错（默认空列表）
        2. 空列表 [] 是合法的，传 tags: [] 不会触发 min_length 错误（因为没设置 min_length）
    """
    user_dict = user.model_dump()
    return {
        "message": "带标签的用户创建成功",
        "user": user_dict,
        "tags_count": len(user.tags),
    }


# ==============================================
# 例3：联合类型 + 复杂嵌套 — POST /orders/
# 【基础】Literal 限定支付方式只能是 wechat/alipay/bank_card 之一
#         传其他值（如 "cash"）会返回 422 详细错误信息
#         嵌套 list[OrderItem] 让订单可以包含多个商品
# 【进阶】Literal 和 Enum 的选择：
#   Literal["a", "b"] → 适合 2-3 个固定选项，无需定义类
#   (str, Enum)       → 适合多个选项或需要复用，可带注释和额外方法
#   Union[A, B]       → 适合"是A类型或B类型"的场景（Python 3.10+ 推荐用 A | B）
# 使用建议：3 个以内固定字符串 → Literal，超过 3 个或需要复用 → Enum
# ==============================================
@app.post("/orders/")
async def create_order(order: OrderCreate):
    """
    【基础功能】创建包含多商品条目的订单，支付方式用 Literal 约束
    【学习知识点】
        1. Literal 联合类型 — 限定字段只能取指定值集合
        2. 多级嵌套模型 — OrderCreate → list[OrderItem] 二级嵌套
        3. 自动金额计算 — 遍历 items 做业务计算
    参数：
        order: 【基础释义：OrderCreate 模型，包含用户ID、商品列表、支付方式】
               【进阶释义：Pydantic 对嵌套 OrderItem 列表递归校验每个条目的字段】
    返回值：{"order_id": ..., "total_amount": ..., "items_count": ...} — 订单摘要
    调用示例：
        示例1 — curl 发送订单 JSON：
        curl -X POST http://127.0.0.1:8000/orders/ \
          -H "Content-Type: application/json" \
          -d '{"user_id":1,"items":[{"product_name":"键盘","quantity":2,"unit_price":299.0}],"payment_method":"wechat"}'
        示例2：尝试 payment_method: "cash" → 422 错误
        示例3：试试传入空 items: [] → 422（Item 列表至少1个）
    同场景常用替代函数：
        1. str + 手动 if 校验 — 灵活但失去自动文档和校验
        2. (str, Enum) — 多个支付方式或需要方法时更合适
        3. Union[TypeA, TypeB] — 字段可以是两种不同类型之一，更灵活
    注意事项：
        1. Literal 中的值大小写敏感，"Wechat" ≠ "wechat"
        2. 嵌套校验失败的错误路径如 body.order.items.0.quantity
    """
    # 【基础】计算订单总金额 = 每条商品 quantity * unit_price 的累加和
    total = sum(item.quantity * item.unit_price for item in order.items)

    # 【基础】构造返回数据，model_dump() 导出完整订单信息
    return {
        "order_id": f"ORD-{order.user_id}-{hash(order.note or '') % 10000:04d}",
        "user_id": order.user_id,
        "items_count": len(order.items),
        "total_amount": round(total, 2),  # round 保留两位小数，避免浮点长尾
        "payment_method": order.payment_method,
        "note": order.note,
    }


# ==============================================
# 例4：PUT 更新请求 — PUT /users/{user_id}
# 【基础】PUT = 完整更新资源，需要同时传路径参数（user_id）和请求体（UserCreate）
#         路径参数定位是"谁"，请求体告诉"改成什么"
#         RESTful 惯例：PUT /users/123 → 用请求体中的新数据完全替换用户 123
# 【进阶】PUT vs PATCH vs POST 的语义区别：
#   POST   /users       → 创建新用户（ID 由服务端生成）
#   PUT    /users/123   → 完整替换用户 123（不传的字段会被设为默认值）
#   PATCH  /users/123   → 部分更新用户 123（只传要改的字段）
# 本示例用 PUT，PATCH 的半更新模式在 step15_crud_api 中深入讲解
# 注意：URL 中 {user_id} 是路径参数，user 是请求体参数，两者互不影响
# ==============================================
@app.put("/users/{user_id}")
async def update_user(user_id: int, user: UserCreate):
    """
    【基础功能】用 PUT 方法完整更新指定用户的信息
    【学习知识点】
        1. 路径参数 + 请求体组合 — 一个函数同时有路径参数和请求体
        2. PUT 语义 — 完整替换资源，与 PATCH 部分更新区分
        3. 参数识别优先级 — FastAPI 自动区分路径参数 vs 请求体 vs 查询参数
    参数：
        user_id: 【基础释义：整数路径参数，要更新的用户ID】
        user:    【基础释义：UserCreate 请求体，用户的新数据】
    返回值：{"message": "...", "user_id": ..., "updated_data": {...}} — 更新结果
    调用示例：
        示例1：curl -X PUT http://127.0.0.1:8000/users/42 -H "Content-Type: application/json" -d '{"name":"新名字","email":"new@test.com","age":30}'
        示例2：curl -X PUT http://127.0.0.1:8000/users/abc → 422（user_id 必须是 int）
    同场景常用替代函数：
        1. PATCH 方法 — 部分更新，只传要改的字段，不会覆盖未传字段
        2. POST /users/123 — 非标准但有时用于替代 PUT（某些防火墙会拦截 PUT）
        3. @app.api_route(path, methods=["PUT", "PATCH"]) — 同时支持多种 HTTP 方法
    注意事项：
        1. PUT 语义要求传完整数据，不传的可选字段会被设为默认值（None）
        2. 实际项目中 PUT 通常用和 POST 不同的 Schema（更新时有些字段不可修改）
    """
    user_dict = user.model_dump()
    return {
        "message": f"用户 {user_id} 已完整更新",
        "user_id": user_id,
        "updated_data": user_dict,
    }


# ==============================================
# 程序入口
# ==============================================
if __name__ == "__main__":
    uvicorn.run(
        "step04_request_body:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )
