# ==============================================
# 文件名：step02_path_params.py
# 基础功能：学习 FastAPI 路径参数的各种用法：类型校验、枚举约束、多参数组合
# 核心学习知识点：
#   1. 路径参数 {param} — URL 路径中的动态变量，花括号语法声明
#   2. 类型注解驱动校验 — name: int 让 FastAPI 自动做类型转换和验证
#   3. Enum 枚举约束 — 限制参数只能取预定义的值集合
#   4. 路径参数优先级 — 固定路径优先于动态路径匹配
#   5. int/float 类型自动转换 — URL 中的字符串 "/123" 自动转为整数 123
#   6. 类型匹配错误返回 422 — 传入 "abc" 到 int 参数，FastAPI 自动拒绝
#   7. 多路径参数组合 — 一个路径里可以有多个 {param}
#   8. bool 类型路径参数 — True/false/yes/no/1/0 均可识别
# 适用场景：RESTful API 资源定位（/users/123、/products/456）、分类查询
# 使用方法：
#   终端运行：uv run python step02_path_params.py
#   浏览器访问：
#     http://127.0.0.1:8000/users/42       — int 类型路径参数
#     http://127.0.0.1:8000/users/abc      — 类型错误，返回 422
#     http://127.0.0.1:8000/models/gpt-4   — 枚举约束示例
#     http://127.0.0.1:8000/models/unknown — 枚举不匹配，返回 422
#     http://127.0.0.1:8000/docs           — 交互式文档测试所有接口
# 进阶说明：
#   1. FastAPI 使用 pydantic 的 TypeAdapter 做路径参数类型转换
#   2. 路径参数支持 path 类型（:path），匹配含 / 的完整路径段
#   3. Enum 在 OpenAPI 文档中自动生成下拉选择器
#   4. 路径参数的备选方案：Annotated[type, Path()] 可添加额外校验（详见 step03）
# 常用配套函数：
#   Path(gt=, lt=, title=)      — 路径参数的高级校验（如大于0、标题自定义）
#   Annotated[type, Path()]     — Python 类型注解 + 路径校验的组合写法（推荐）
#   Enum                        — Python 标准库，定义有限选项集合
#   int/float/str               — Python 内置类型，直接用于类型注解驱动转换
# ==============================================
import uvicorn
from enum import Enum  # Python 标准库，用于定义有限选项的枚举类
from fastapi import FastAPI

app = FastAPI(
    title="LearnFast API — 路径参数",
    description="FastAPI 学习 Step02：深入理解路径参数的类型校验与枚举约束",
    version="0.1.0",
)


# ==============================================
# 例1：基本路径参数 — GET /users/{user_id}
# 【基础】URL 中的 {user_id} 是路径参数，函数参数同名且带类型注解
#         访问 /users/42 → user_id = 42（自动从字符串 "42" 转为整数 42）
#         访问 /users/abc → FastAPI 自动返回 422 错误（"abc" 不是整数）
# 【进阶】类型转原理：
#   1. FastAPI 从路由模板 "{user_id}" 提取参数名
#   2. 查看函数签名 user_id: int 得到目标类型
#   3. 调用 Pydantic TypeAdapter(int).validate_python("42") → 成功返回 42
#   4. 如果校验失败，pydantic 抛出 ValidationError → FastAPI 转为 422 响应
# 关键设计思想：框架自动做脏活累活（类型校验），开发者只写业务逻辑
# ==============================================
@app.get("/users/{user_id}")
async def get_user(user_id: int):
    """
    【基础功能】根据用户 ID 返回用户信息，ID 必须是整数
    【学习知识点】
        1. int 类型路径参数 — FastAPI 自动将 URL 字符串转为整数
        2. 自动校验 — 非数字字符串返回 422 Unprocessable Entity
        3. 文档自动生成 — Swagger 中自动标注 user_id 为 integer 类型
    参数：
        user_id: 【基础释义：整数，用户唯一编号】【进阶释义：int 类型注解驱动 Pydantic TypeAdapter 校验，URL 字符串自动转换】
    返回值：{"user_id": 42, "name": "用户42"} — 模拟的用户数据
    调用示例：
        示例1：curl http://127.0.0.1:8000/users/42
        示例2：curl http://127.0.0.1:8000/users/abc（测试 422 错误响应）
    同场景常用替代函数：
        1. str 类型路径参数 — 不做数字转换，保持原始字符串，适合用户名/昵称场景
        2. UUID 类型路径参数 — 自动校验 UUID 格式，防止注入非法字符串
    注意事项：
        1. int 类型只接受十进制数字，不接受 0x1A 等十六进制写法
        2. 超出 Python int 范围的大数字可能溢出，生产环境加范围校验
    """
    # 【基础】模拟从数据库查询用户，返回拼接的数据
    # 【进阶】真实项目中这里会调用数据库查询：db.query(User).filter(User.id == user_id).first()
    return {"user_id": user_id, "name": f"用户{user_id}"}


# ==============================================
# 例2：多个路径参数 — GET /files/{file_path:path}
# 【基础】:path 是 FastAPI 的特殊类型声明，让参数匹配包含 / 的完整路径
#   平时 /files/a/b/c 会被解析为多个路径段
#   加了 :path 后，a/b/c 整个作为 file_path 的值
# 【进阶】:path 底层是 Starlette 的路由转换器（path convertor）
#   Starlette 内置转换器：str（默认）、int、float、uuid、path
#   自定义转换器可注册到 Starlette 路由系统
# 使用场景：文件浏览 API（GET /files/docs/2024/report.pdf）、嵌套资源路径
# 安全注意：始终对路径做安全校验，防止路径穿越攻击（如 ../../../etc/passwd）
# ==============================================
@app.get("/files/{file_path:path}")
async def read_file_path(file_path: str):
    """
    【基础功能】接收任意深度的文件路径参数（可包含 / 斜线）
    【学习知识点】
        1. :path 转换器 — 让路径参数匹配包含 / 的完整路径段
        2. Starlette 路由转换器 — 内置 int/float/uuid/path 等多种类型转换器
    参数：
        file_path: 【基础释义：字符串，可包含 / 的文件完整相对路径】【进阶释义：:path 转换器吞掉剩余所有路径段，不做 / 分割】
    返回值：{"file_path": "..."} — 路径回显
    调用示例：
        示例1：curl "http://127.0.0.1:8000/files/docs/report.pdf"
        示例2：curl "http://127.0.0.1:8000/files/a/b/c/d.txt"（深度嵌套路径）
        示例3：curl "http://127.0.0.1:8000/files/../../etc/passwd"（路径穿越示例，见安全注意）
    同场景常用替代函数：
        1. str 类型路径参数 — 只匹配不包含 / 的单段文件名
        2. 查询参数 ?path=xxx — 用查询参数传路径，写法不同但效果相似
    注意事项：
        1. :path 参数必须是路径模板中的最后一个参数
        2. 生产环境必须对 file_path 做安全校验（如 pathlib.Path().resolve() 防路径穿越）
        3. Windows 路径反斜杠 \ 需要额外处理
    """
    # 【基础】直接返回接收到的路径
    return {"file_path": file_path}


# ==============================================
# 例3：枚举类型路径参数 — GET /models/{model_name}
# 【基础】Enum 限制参数只能取预设的几个值之一，传其他值自动 422
#         例如 /models/gpt-4 ✓，/models/custom-model ✗（不在枚举中）
# 【进阶】Enum 继承自 str 的好处：
#   1. (str, Enum) 双重继承让枚举值同时是字符串和枚举成员
#   2. FastAPI 能正确序列化为 JSON 字符串而非数字
#   3. OpenAPI 文档中自动生成下拉选择列表
#   4. 如果用纯 Enum 而非 (str, Enum)，JSON 序列化可能出错
# 设计原理：限制输入范围是防御性编程的核心原则，减少非法输入的处理成本
# 简化替代写法：用 Literal["gpt-4", "gpt-4o", "qwen-max"] 可替代小枚举（Python 3.8+）
# ==============================================
class ModelName(str, Enum):
    """AI 模型名称枚举，双重继承 str + Enum 确保 JSON 正确序列化"""
    gpt4 = "gpt-4"      # 枚举成员 = "gpt-4"，OpenAPI 中自动显示
    gpt4o = "gpt-4o"    # 枚举成员 = "gpt-4o"
    qwen_max = "qwen-max"  # 枚举成员 = "qwen-max"


@app.get("/models/{model_name}")
async def get_model_info(model_name: ModelName):
    """
    【基础功能】根据模型名称返回模型信息，名称必须是预定义的枚举值之一
    【学习知识点】
        1. (str, Enum) 双重继承 — 同时是字符串和枚举，确保 JSON 正确序列化
        2. 枚举路径参数 — FastAPI 自动校验输入值是否在枚举成员中
        3. Python Enum 基础 — 定义有限选项集合，比魔法字符串更安全
    参数：
        model_name: 【基础释义：ModelName 枚举类型，只能是 gpt-4/gpt-4o/qwen-max 之一】
                   【进阶释义：FastAPI 将 URL 字符串与枚举成员值（.value）逐一匹配，匹配失败直接 422】
    返回值：{"model": "gpt-4", "provider": "OpenAI"} — 模拟的模型信息
    调用示例：
        示例1：curl http://127.0.0.1:8000/models/gpt-4
        示例2：curl http://127.0.0.1:8000/models/qwen-max
        示例3：curl http://127.0.0.1:8000/models/unknown（测试 422）
    同场景常用替代函数：
        1. typing.Literal["a", "b"] — 无需 class 定义，适合少量固定选项
        2. pydantic.Field(pattern=r"...") — 用正则限制参数格式，适合非固定选项
        3. 手动 if/else 判断 — 灵活但无自动文档和校验，不推荐
    注意事项：
        1. 修改枚举值后需要同步更新客户端代码（API 合约变更）
        2. 枚举值对外暴露后不建议随意改名（向下兼容原则）
    """
    # 【基础】用字典存储不同模型的简要信息，演示枚举到业务数据的映射
    # 【进阶】真实项目用 match-case（Python 3.10+）或字典映射做分发，比 if-elif 更优雅
    model_db = {
        ModelName.gpt4: {"model": "gpt-4", "provider": "OpenAI", "type": "GPT 系列"},
        ModelName.gpt4o: {"model": "gpt-4o", "provider": "OpenAI", "type": "多模态 GPT"},
        ModelName.qwen_max: {"model": "qwen-max", "provider": "Alibaba Cloud", "type": "通义千问"},
    }
    return model_db[model_name]


# ==============================================
# 例4：多个不同类型路径参数 — GET /products/{category}/{product_id}
# 【基础】一个路径可以有多个路径参数，类型各自独立
#         例如 /products/electronics/789 → category="electronics", product_id=789
# 【进阶】多参数匹配顺序：
#   1. FastAPI 按路径模板从左到右解析 {category} 和 {product_id}
#   2. 每个参数独立进行类型转换和校验
#   3. 任何一个参数校验失败，整个请求返回 422
#   4. 匹配失败（路径段数量不对）返回 404
# RESTful 设计惯例：/资源/{id}/子资源/{sub_id} 表达层级关系
# ==============================================
@app.get("/products/{category}/{product_id}")
async def get_product(category: str, product_id: int):
    """
    【基础功能】根据商品分类和商品 ID 返回商品信息，演示多路径参数组合
    【学习知识点】
        1. 多路径参数组合 — 一个 URL 模板中多个 {param}
        2. 参数类型独立 — category 是 str，product_id 是 int，各自独立校验
        3. RESTful 层级 URL 设计 — /资源/分类/具体ID 表达层级关系
    参数：
        category: 【基础释义：字符串，商品分类名】【进阶释义：str 不做转换，直接透传 URL 中的值】
        product_id: 【基础释义：整数，商品编号】【进阶释义：int 类型自动校验和转换】
    返回值：{"category": "...", "product_id": ..., "name": "..."} — 模拟商品信息
    调用示例：
        示例1：curl http://127.0.0.1:8000/products/electronics/789
        示例2：curl http://127.0.0.1:8000/products/books/42
        示例3：curl http://127.0.0.1:8000/products/electronics/abc（测试 422）
    同场景常用替代函数：
        1. 查询参数 — GET /products?category=electronics&id=789，更灵活但语义不如路径参数清晰
        2. 嵌套路由 — /categories/{cat_id}/products/{prod_id}，层级更明确
    注意事项：
        1. 路径参数过多（3个以上）时建议改用查询参数或请求体
        2. 路径参数的顺序固定，无法像查询参数那样任意排列
    """
    # 【基础】返回分类和 ID 的组合信息
    return {
        "category": category,
        "product_id": product_id,
        "name": f"{category} 分类下的第 {product_id} 号商品",
    }


# ==============================================
# 例5：bool 类型路径参数 — GET /toggle/{flag}
# 【基础】FastAPI 自动将 "true"/"false"/"yes"/"no"/"1"/"0"/"on"/"off" 转为 Python bool
#         例如 /toggle/true → flag=True  (Python 布尔值)
#         例如 /toggle/1    → flag=True
#         例如 /toggle/no   → flag=False
# 【进阶】FastAPI 使用 pydantic 的 bool 解析器，支持多种常见布尔表达
#   源码位置：pydantic._internal._validators → bool_validator
#   可识别的 True 值：{'true', '1', 'yes', 'on', 't', 'y'}
#   可识别的 False 值：{'false', '0', 'no', 'off', 'f', 'n'}
#   大小写不敏感：True/TRUE/true/True 均可
# 注意：只接受上面列出的值，其他字符串（如 "enabled"）返回 422
# ==============================================
@app.get("/toggle/{flag}")
async def toggle_feature(flag: bool):
    """
    【基础功能】接收布尔类型路径参数，演示 FastAPI 自动布尔值解析
    【学习知识点】
        1. bool 类型路径参数 — FastAPI 自动识别多种布尔表达
        2. 布尔值解析规则 — true/false/yes/no/1/0/on/off 均支持
        3. Python 类型注解与 HTTP 协议 — URL 中一切皆字符串，FastAPI 桥梁转换
    参数：
        flag: 【基础释义：布尔值，控制功能开关】【进阶释义：Pydantic bool_validator 解析 URL 字符串，支持 12 种布尔表达】
    返回值：{"feature_enabled": True/False} — 开关状态
    调用示例：
        示例1：curl http://127.0.0.1:8000/toggle/true → True
        示例2：curl http://127.0.0.1:8000/toggle/yes  → True
        示例3：curl http://127.0.0.1:8000/toggle/0    → False
        示例4：curl http://127.0.0.1:8000/toggle/xyz  → 422 错误
    同场景常用替代函数：
        1. int 类型 0/1 — 传统 API 风格，不如 bool 语义清晰
        2. str 类型 + 手动 if 判断 — 灵活但失去自动校验和文档生成能力
    注意事项：bool 只识别预定义值列表，自定义布尔表达（如 "enabled"）会 422
    """
    # 【基础】根据 flag 值返回不同的消息
    status_msg = "功能已开启" if flag else "功能已关闭"
    return {"feature_enabled": flag, "message": status_msg}


# ==============================================
# 例6：float 类型路径参数 — GET /price/{amount}
# 【基础】float 类型支持小数，自动将 "99.99" 转为 Python float 99.99
#         例如 /price/99.99 → amount=99.99（浮点数）
#         例如 /price/100   → amount=100.0 （自动加 .0）
# 【进阶】浮点数精度问题：
#   Python float 是 IEEE 754 双精度，存在精度损失（如 0.1 + 0.2 != 0.3）
#   财务计算场景建议用 Decimal 类型或整数（分）表示金额
#   但学习路径参数类型时，float 是最直观的演示
# Pydantic 的 float 校验允许整数输入（自动转浮点），科学计数法（1e5 = 100000.0）
# ==============================================
@app.get("/price/{amount}")
async def check_price(amount: float):
    """
    【基础功能】接收浮点类型价格参数，演示小数路径参数处理
    【学习知识点】
        1. float 类型路径参数 — FastAPI 自动转换包含小数点的字符串为浮点数
        2. 整数自动转浮点 — 输入 100 自动转为 100.0
        3. 浮点精度常识 — Python float 基于 IEEE 754，存在精度限制
    参数：
        amount: 【基础释义：浮点数，价格金额】【进阶释义：Pydantic float 校验器，支持整数/小数/科学计数法】
    返回值：{"amount": 99.99, "tax": 12.9987, "total": 112.9887} — 模拟价格计算
    调用示例：
        示例1：curl http://127.0.0.1:8000/price/99.99
        示例2：curl http://127.0.0.1:8000/price/100（整数自动转 100.0）
        示例3：curl http://127.0.0.1:8000/price/abc（测试 422）
    同场景常用替代函数：
        1. Decimal 类型 — 精确十进制运算，适合金融场景（需自定义 Pydantic 类型）
        2. int 类型以"分"为单位 — 9959 表示 99.59 元，根除浮点精度问题
    注意事项：
        1. 浮点运算结果可能带长尾小数（如 99.99 * 1.13 = 112.98869999999999）
        2. 生产环境金额计算使用 Decimal 或整数分，不用 float
    """
    # 【基础】模拟含税价格计算
    tax_rate = 0.13  # 13% 税率
    tax = amount * tax_rate
    total = amount + tax
    return {"amount": amount, "tax_rate": f"{tax_rate*100}%", "tax": tax, "total": total}


# ==============================================
# 程序入口
# ==============================================
if __name__ == "__main__":
    # 【基础】启动服务器，代码修改后自动重启
    uvicorn.run(
        "step02_path_params:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )
