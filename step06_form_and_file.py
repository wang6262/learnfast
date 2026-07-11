# ==============================================
# 文件名：step06_form_and_file.py
# 基础功能：学习 FastAPI 表单数据、文件上传、多文件上传、静态文件服务
# 核心学习知识点：
#   1. Form() — 接收 HTML 表单数据（application/x-www-form-urlencoded）
#   2. File() + bytes — 接收小文件上传，全部加载到内存
#   3. UploadFile — 异步大文件上传，写入临时文件或流式处理
#   4. list[UploadFile] — 批量多文件上传
#   5. StaticFiles 挂载 — app.mount() 将本地目录暴露为静态资源 URL
#   6. multipart/form-data — 表单和文件混合提交的编码格式
#   7. UploadFile 对象属性 — filename、content_type、file、size
#   8. 文件安全校验 — 校验文件类型、大小、防止恶意上传
# 适用场景：用户头像上传、文档管理系统、HTML 表单登录、批量文件导入
# 使用方法：
#   终端运行：uv run python step06_form_and_file.py
#   浏览器访问：
#     http://127.0.0.1:8000/docs     — Swagger 上传文件测试
#     http://127.0.0.1:8000/static/  — 静态文件目录浏览
#   创建测试目录：mkdir uploads（文件上传存储目录，程序会自动创建）
# 进阶说明：
#   1. UploadFile 底层使用 Python 的 SpooledTemporaryFile — 小文件存内存，大文件存磁盘
#   2. UploadFile 提供了异步的 read()/write()/seek()/close() 方法
#   3. jsonable_encoder() 无法序列化文件对象，返回文件信息需提取属性
#   4. 生产环境建议用对象存储（S3/MinIO）而非本地磁盘
# 常用配套函数：
#   Form()                    — 接收 URL 编码的表单字段
#   File()                    — 接收纯字节文件（默认小文件，全部在内存中）
#   UploadFile                — 异步文件上传类，支持大文件流式处理
#   StaticFiles               — 静态文件挂载（from fastapi.staticfiles）
#   app.mount()               — 挂载子应用或静态文件目录
#   aiofiles.open()           — 异步文件写入库（需安装 aiofiles）
#   shutil.copyfileobj()      — 内存高效的文件流复制（同步方式）
#   mimetypes.guess_type()    — 猜测文件 MIME 类型
# ==============================================
import os
import shutil
from pathlib import Path

import uvicorn
from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse


app = FastAPI(
    title="LearnFast API — 表单与文件",
    description="FastAPI 学习 Step06：表单数据、文件上传、多文件上传、静态文件",
    version="0.1.0",
)


# ==============================================
# 配置文件上传目录
# 【基础】Path.cwd() 获取当前工作目录，/ "uploads" 拼出上传文件夹路径
# 【进阶】Path.cwd().resolve() 返回绝对路径，消除软链接和相对路径歧义
#   使用 pathlib.Path 而非 os.path 的原因：
#   1. Path 跨平台（/ 在 Windows 上自动转 \\）
#   2. 运算符重载 / 拼接路径比 os.path.join 更直观
#   3. Path.mkdir() 直接创建目录，不用调用 os.makedirs
# ==============================================
UPLOAD_DIR = Path.cwd() / "uploads"
# 【基础】如果上传目录不存在，自动创建（exist_ok=True 不报错即使已存在）
# parents=True 表示如果父级目录也不存在，一同创建（类似 mkdir -p）
UPLOAD_DIR.mkdir(exist_ok=True, parents=True)


# ==============================================
# 静态文件服务挂载
# 【基础】app.mount("/static", ...) 把 UPLOAD_DIR 文件夹映射到 /static URL
#         例如文件 uploads/photo.jpg → 浏览器访问 http://127.0.0.1:8000/static/photo.jpg
#         客户端可以直接通过 URL 查看/下载上传的文件
# 【进阶】mount 的原理：
#   1. mount 实际上是挂载了一个独立的 ASGI 子应用（StaticFiles）
#   2. 请求先经过 FastAPI 路由匹配，不匹配再交给 /static 的 StaticFiles 处理
#   3. StaticFiles 自动处理 MIME 类型、304 Not Modified（ETag/Last-Modified）
#   4. 实际使用：app.mount("/static", StaticFiles(directory="uploads"), name="static")
# 注意：mount 的路径前缀会从 URL 中"消耗掉"再传给子应用
#   URL: /static/photo.jpg → StaticFiles 收到路径: photo.jpg → 在 UPLOAD_DIR 中查找
# ==============================================
app.mount("/static", StaticFiles(directory=str(UPLOAD_DIR)), name="static")


# ==============================================
# 例1：表单登录 — POST /login/
# 【基础】Form() 接收 application/x-www-form-urlencoded 格式的 HTML 表单数据
#         和 JSON 请求体不同，表单数据是 key1=value1&key2=value2 格式
#         常见场景：传统 HTML <form> 提交、OAuth2 密码模式认证
# 【进阶】为什么 OAuth2 登录要用 Form 而非 JSON：
#   1. OAuth2 规范（RFC 6749）要求密码模式使用 form-urlencoded 格式
#   2. 浏览器原生 <form> 只有 GET 和 POST 方法，且默认编码是 urlencoded
#   3. FastAPI 内置的 OAuth2PasswordRequestForm 就基于 Form()
# 对比：JSON Body 使用 BaseModel，Form Body 使用 Form() 逐个声明参数
# ==============================================
@app.post("/login/")
async def login(
    # 【基础】username 来自表单字段，必填
    username: str = Form(description="登录用户名"),
    # 【基础】password 来自表单字段，必填
    password: str = Form(description="登录密码"),
):
    """
    【基础功能】模拟表单登录，接收 HTML 表单格式的账号密码
    【学习知识点】
        1. Form() — 声明表单参数，支持与 Query/Path 相同的校验参数
        2. application/x-www-form-urlencoded — 表单默认编码格式
        3. FastAPI 自动解析 Content-Type → 表单数据
    参数：
        username: 【基础释义：字符串，表单中的登录用户名】【进阶释义：Form() 从请求体 urlencoded 数据中提取字段】
        password: 【基础释义：字符串，登录密码】
    返回值：{"message": "...", "username": "..."} — 登录结果
    调用示例：
        示例1：curl -X POST http://127.0.0.1:8000/login/ -d "username=admin&password=123456"
        示例2：在 /docs 中使用表单输入框测试（Swagger 自动生成表单 UI）
    同场景常用替代函数：
        1. OAuth2PasswordRequestForm — FastAPI 内置，自动解析 grant_type/scope（Step11 详细讲解）
        2. JSON Body (BaseModel) — 适合 SPA/移动端应用，表单格式适合传统 Web 应用
        3. python-multipart — Form 依赖的底层库，处理 multipart 编码
    注意事项：
        1. Form() 不能和 BaseModel 请求体同时使用（技术原因是编码格式不同）
        2. 密码明文传输，生产环境必须用 HTTPS 加密
        3. 表单参数默认是必填的，要设为可选使用 Form(default=None)
    """
    # 【基础】模拟验证（真实项目需哈希比对密码）
    if username == "admin" and password == "123456":
        return {"message": "登录成功", "username": username}
    # 【基础】密码错误抛出 401
    raise HTTPException(status_code=401, detail="用户名或密码错误")


# ==============================================
# 例2：单文件上传（bytes）— POST /upload/bytes/
# 【基础】File() 将上传的文件内容读入内存，适合 <1MB 的小文件
#         file: bytes → 文件内容以二进制字节流存在内存中
#         优点：简单直接，拿到就是 byte[]
#         缺点：文件太大内存扛不住（上传 100MB 文件 → OOM）
# 【进阶】File() vs UploadFile 的选择指南：
#   File() + bytes
#     ✓ 文件小（< 1MB），操作简单
#     ✓ 需要直接操作字节内容（如 MD5 哈希、Base64 编码）
#     ✗ 大文件会撑爆内存
#   UploadFile
#     ✓ 文件大或未知大小
#     ✓ 需要异步处理（不阻塞事件循环）
#     ✓ 生产环境推荐的默认选择
# ==============================================
@app.post("/upload/bytes/")
async def upload_small_file(
    file: bytes = File(description="上传的文件（小文件，字节流）")
):
    """
    【基础功能】上传小文件并保存到磁盘，文件内容以字节流接收
    【学习知识点】
        1. File() + bytes — 内存中接收文件内容的简单方式
        2. 二进制写入 — "wb" 模式写入字节
        3. 文件大小限制 — 小文件适用，大文件须用 UploadFile
    参数：
        file: 【基础释义：bytes 类型，上传文件的二进制内容】
              【进阶释义：File() 底层读取整个文件到内存，由 Starlette 的 MultiPartParser 解析】
    返回值：{"file_size": ..., "message": "..."} — 保存结果
    调用示例：
        示例1：curl -X POST http://127.0.0.1:8000/upload/bytes/ -F "file=@test.txt"
        示例2：在 /docs 中点击文件上传按钮测试
    同场景常用替代函数：
        1. UploadFile — 大文件和异步场景的推荐选择
        2. 直接操作 request.body() — 底层方式，失去了文件元信息
    注意事项：
        1. 没有文件名信息（bytes 不包含文件名），需额外从路径或头部获取
        2. 生产环境限制文件大小：在中间件层或 nginx 层做限制
    """
    # 【基础】保存文件到 uploads 目录，命名为 uploaded_bytes.bin
    # 【进阶】"wb" 模式 = 二进制写入，不经过文本编码转换，保证文件完整性
    save_path = UPLOAD_DIR / "uploaded_bytes.bin"
    save_path.write_bytes(file)

    return {"file_size": len(file), "message": f"文件已保存到 {save_path}"}


# ==============================================
# 例3：单文件上传（UploadFile）— POST /upload/
# 【基础】UploadFile 是异步文件上传的推荐方式，自动处理大文件
#         属性：
#           file.filename    → 原始文件名（客户端上传时的文件名）
#           file.content_type → MIME 类型（如 image/png、application/pdf）
#           file.size        → 文件大小（属性，不是方法）
#           await file.read() → 异步读取全部内容
#           await file.seek(0) → 重置读取位置（多次读取前必须执行）
# 【进阶】UploadFile 内部机制：
#   1. UploadFile 封装了 Python 的 SpooledTemporaryFile
#      - 小文件（< 1MB）：存在内存的 BytesIO 中
#      - 大文件（≥ 1MB）：自动溢出到磁盘临时文件
#   2. 临时文件在请求结束后自动删除（由 GC 回收）
#   3. 异步方法避免文件 I/O 阻塞事件循环
#   4. 文件上传完后必须调用 await file.close() 或让 GC 自动关闭
# ==============================================
@app.post("/upload/")
async def upload_file(file: UploadFile = File(description="上传文件（支持大文件）")):
    """
    【基础功能】上传文件并保存到本地磁盘，返回文件信息
    【学习知识点】
        1. UploadFile — FastAPI 异步文件处理，适合任意大小文件
        2. filename/content_type/size 属性 — 获取文件元信息
        3. 磁盘写入 — 将上传文件流保存到本地目录
        4. 文件安全校验 — 校验 MIME 类型和文件大小
    参数：
        file: 【基础释义：UploadFile 对象，包含文件内容和元信息】【进阶释义：SpooledTemporaryFile 实现自动内存/磁盘切换】
    返回值：{"filename": "...", "content_type": "...", "size": ..., "url": "..."}
    调用示例：
        示例1：curl -X POST http://127.0.0.1:8000/upload/ -F "file=@photo.jpg"
        示例2：在 /docs 中选择文件上传
    同场景常用替代函数：
        1. aiofiles — 异步文件写入库，配合 UploadFile 做高性能 I/O
        2. boto3 S3 client.upload_fileobj() — 直传到云存储，不落磁盘
        3. File() + bytes — 小文件简单场景
    注意事项：
        1. await file.read() 后指针在文件末尾，再次读取前需要 await file.seek(0)
        2. file.content_type 来自客户端声明，不可完全信任（可被伪造）
        3. 生产环境务必校验文件类型（魔数检测，不仅靠 content_type）
    """
    # --- 安全校验：文件类型 ---
    # 【基础】只允许特定类型的文件上传
    # 【进阶】content_type 来自 HTTP 请求头，客户端可伪造
    #   更安全的做法：用 python-magic 或 filetype 库做魔数检测
    ALLOWED_TYPES = {
        "image/jpeg", "image/png", "image/gif", "image/webp",
        "application/pdf",
        "text/plain", "text/markdown",
    }
    if file.content_type and file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型: {file.content_type}。允许的类型: {ALLOWED_TYPES}",
        )

    # --- 安全校验：文件大小（最大 10MB）---
    # 【基础】读取文件内容（会全部加载到内存，大文件慎用）
    contents = await file.read()
    MAX_SIZE = 10 * 1024 * 1024  # 10 MB
    if len(contents) > MAX_SIZE:
        raise HTTPException(status_code=400, detail=f"文件太大，最大允许 {MAX_SIZE//1024//1024}MB")

    # --- 保存文件 ---
    # 【基础】构造安全的保存路径：上传目录 + 原始文件名
    # 【进阶】生产环境需要处理文件名冲突（加时间戳/UUID）、
    #   防止路径穿越（basename 去掉目录部分）、
    #   使用安全的文件名（过滤特殊字符）
    safe_filename = Path(file.filename).name if file.filename else "unknown_file"
    save_path = UPLOAD_DIR / safe_filename
    save_path.write_bytes(contents)

    # 【基础】构造可访问的文件 URL（通过上面挂载的 /static 路径）
    file_url = f"/static/{safe_filename}"

    return {
        "filename": safe_filename,
        "content_type": file.content_type,
        "size": len(contents),
        "url": file_url,
    }


# ==============================================
# 例4：多文件上传 — POST /upload/multiple/
# 【基础】list[UploadFile] 接收多个文件，一次性上传多张图片/文档
#         客户端需使用 multipart/form-data 格式发送
#         所有文件传在同一个字段名（"files"）下
# 【进阶】多文件同时上传的实现：
#   1. 客户端在 multipart body 中为每个文件创建独立的分段（part）
#   2. Starlette MultiPartParser 解析出所有文件
#   3. 每个文件创建独立的 SpooledTemporaryFile
#   4. FastAPI 组装成 Python list 传给函数
#   5. 大文件并发写入可用 asyncio.gather() 提升速度
# curl 示例：-F "files=@a.jpg" -F "files=@b.jpg"（注意同一个字段名多次）
# 单字段名 = "files"，多文件填在这个字段下
# ==============================================
@app.post("/upload/multiple/")
async def upload_multiple_files(
    files: list[UploadFile] = File(description="批量上传的文件列表")
):
    """
    【基础功能】一次性上传多个文件，支持批量操作
    【学习知识点】
        1. list[UploadFile] — 多文件同时上传的参数声明
        2. 批量文件处理 — 遍历列表逐个保存
        3. 异常处理 — 单个文件失败不影响其他文件（容错）
    参数：
        files: 【基础释义：UploadFile 列表，多个待上传文件】【进阶释义：Starlette 解析 multipart 中同一字段名的所有文件分段】
    返回值：{"uploaded": [...], "total": ..., "failed": ...} — 上传统计
    调用示例：
        示例1：curl -X POST http://127.0.0.1:8000/upload/multiple/ -F "files=@a.jpg" -F "files=@b.jpg"
        示例2：在 /docs 中多选文件上传（Ctrl+点击多选）
    同场景常用替代函数：
        1. 逐个调用单文件上传接口 — 简单但多次请求，效率低
        2. 压缩包 (zip) 上传 — 客户端打包上传，服务端解压，减少请求数
        3. 前端分片上传 + 后端合并 — 超大文件（>100MB）的工业级方案
    注意事项：
        1. 同时上传很多大文件可能耗尽服务器内存和磁盘
        2. 生产环境需限制单次上传文件数量（如最多 10 个）
    """
    uploaded_list = []
    failed_list = []

    for file in files:
        try:
            # 【基础】逐个处理文件，try/except 保证单个失败不影响其他
            contents = await file.read()

            # 【基础】安全检查文件名
            safe_name = Path(file.filename).name if file.filename else f"unknown_{len(uploaded_list)}"
            save_path = UPLOAD_DIR / safe_name
            save_path.write_bytes(contents)

            uploaded_list.append({
                "filename": safe_name,
                "size": len(contents),
                "url": f"/static/{safe_name}",
            })
        except Exception as e:
            # 【基础】记录失败文件，继续处理剩余
            failed_list.append({
                "filename": file.filename,
                "error": str(e),
            })

    return {
        "uploaded": uploaded_list,
        "failed": failed_list,
        "total_received": len(files),
        "success_count": len(uploaded_list),
        "failed_count": len(failed_list),
    }


# ==============================================
# 例5：表单 + 文件混合上传 — POST /profile/
# 【基础】同时接收 JSON 数据（Form）和文件（UploadFile）
#         multipart/form-data 编码支持在同一请求中混合文本和文件
#         常见场景：用户注册同时上传头像、商品创建同时上传图片
# 【进阶】multipart 编码原理：
#   Content-Type: multipart/form-data; boundary=----WebKitFormBoundary
#   每个字段（文本或文件）是独立的分段（part），用 boundary 字符串分隔
#   文本字段和文件字段共存于同一个请求体中
#   缺点是比纯 JSON 体积大（boundary + 头部开销），适合文件上传场景
# ==============================================
@app.post("/profile/")
async def create_profile(
    # 【基础】表单文本字段名 "name"
    name: str = Form(description="用户姓名"),
    # 【基础】表单文本字段名 "bio"
    bio: str = Form(default="", description="个人简介"),
    # 【基础】文件字段名 "avatar"，可以不传
    avatar: UploadFile = File(default=None, description="头像文件"),
):
    """
    【基础功能】创建用户档案，同时提交文本信息（Name/Bio）和头像文件
    【学习知识点】
        1. Form + UploadFile 混合 — 同一请求中接收文本和文件
        2. multipart/form-data 编码 — 承载混合数据的 HTTP 编码格式
        3. 可选文件字段 — UploadFile 也可以设置 default=None
    参数：
        name:   【基础释义：字符串，表单中的用户姓名】
        bio:    【基础释义：可选字符串，个人简介，默认空字符串】
        avatar: 【基础释义：可选头像文件，不传则为 None】
    返回值：{"name": "...", "bio": "...", "avatar_url": "..."} — 档案信息
    调用示例：
        示例1（纯文本，无头像）：
          curl -X POST http://127.0.0.1:8000/profile/ -F "name=张三" -F "bio=开发者"
        示例2（文本 + 头像文件）：
          curl -X POST http://127.0.0.1:8000/profile/ -F "name=张三" -F "bio=开发者" -F "avatar=@photo.jpg"
        示例3：在 /docs 中填写表单并选择文件
    同场景常用替代函数：
        1. 两步上传 — 先 POST /users/ 创建用户，再 PATCH /users/1/avatar 上传头像
        2. Base64 内嵌图片 — 把图片转为 Base64 字符串放 JSON 里传输（体积增大 33%，不推荐大文件）
        3. 预签名 URL — 客户端直传 S3，再提交文件 URL 给服务端
    注意事项：
        1. Form + File 混合时必须用 multipart/form-data，不能用 application/json
        2. 文件字段设为可选时（default=None），需要注意 None 值在 UploadFile 方法上的特殊处理
    """
    avatar_info = None

    # 【基础】如果用户上传了头像，保存文件
    if avatar and avatar.filename:
        contents = await avatar.read()
        safe_name = Path(avatar.filename).name
        save_path = UPLOAD_DIR / safe_name
        save_path.write_bytes(contents)
        avatar_info = {
            "filename": safe_name,
            "size": len(contents),
            "url": f"/static/{safe_name}",
        }

    return {
        "name": name,
        "bio": bio,
        "avatar": avatar_info,
        "message": "档案创建成功",
    }


# ==============================================
# 程序入口
# ==============================================
if __name__ == "__main__":
    # 确保上传目录存在
    UPLOAD_DIR.mkdir(exist_ok=True, parents=True)
    uvicorn.run(
        "step06_form_and_file:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )
