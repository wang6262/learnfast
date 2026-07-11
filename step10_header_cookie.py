# ==============================================
# 文件名：step10_header_cookie.py
# 基础功能：学习 FastAPI Header() 和 Cookie() 参数的读取与设置
# 核心学习知识点：
#   1. Header() — 读取 HTTP 请求头中的值
#   2. Cookie() — 读取浏览器 Cookie 中的值
#   3. 响应 Cookie 设置 — 通过 Response.set_cookie() 在客户端存储数据
#   4. convert_underscores=True（默认）— 自动将 _ 转为 -，适配 HTTP 头命名
#   5. Cookie 安全属性 — HttpOnly/ Secure / SameSite / Max-Age
#   6. 多个 Header 值 — 同名 header 可传多次
#   7. User-Agent 检测 — 读取客户端浏览器/系统信息
#   8. 无状态的 Web — HTTP 本身无状态，Cookie 是实现"记住我是谁"的机制
# 适用场景：客户端识别、语言偏好、主题设置、AB 测试分组、认证 token 传递
# 使用方法：
#   终端运行：uv run python step10_header_cookie.py
#   浏览器访问 http://127.0.0.1:8000/docs 交互式测试
# 进阶说明：
#   1. HTTP 是"无状态协议"——服务器不记得你上次请求了什么
#      Cookie 是浏览器端的存储，每次请求自动带上，绕过 HTTP 无状态限制
#   2. Cookie 在跨域（CORS）场景需要额外配置 credentials 和 withCredentials
#   3. 生产环境避免在 Cookie 中存敏感数据（密码等），应只存 session ID 或 token
#   4. FastAPI 底层没有 Session 机制（不像 Django/Flask），需自行或第三方实现
# 常用配套函数：
#   Header(default=, convert_underscores=) — 读取请求头
#   Cookie(default=)                        — 读取 Cookie
#   Response.set_cookie(key, value, ...)    — 设置 Cookie（在响应中）
#   Response.delete_cookie(key)             — 删除客户端 Cookie
#   Request.cookies                         — 获取所有 Cookie 的字典
#   Request.headers                         — 获取所有 Header 的字典
# ==============================================
import uvicorn

from datetime import datetime, timedelta
from fastapi import FastAPI, Header, Cookie, Request, Response, HTTPException

app = FastAPI(
    title="LearnFast API — Headers & Cookies",
    description="FastAPI 学习 Step10：请求头读取、Cookie 读写、客户端识别",
    version="0.1.0",
)


# ==============================================
# 例1：读取请求头 — GET /whoami
# 【基础】Header() 读取请求的 HTTP 头信息
#         User-Agent 告诉服务器客户端是什么（浏览器/curl/Python 等）
#         Accept-Language 告诉服务器用户偏好什么语言（中文/英文等）
# 【进阶】convert_underscores 参数：
#   默认 convert_underscores=True → user_agent 自动映射到 User-Agent 头
#   如果 convert_underscores=False → user_agent 精确匹配小写头名
#   这种自动转换是 FastAPI 的特色，省去手动拼 HTTP 头名
# HTTP 头规范：头名字大小写不敏感（User-Agent = user-agent = USER-AGENT）
#   但 FastAPI 推荐用 Python snake_case（下划线），框架自动处理转换
# ==============================================
@app.get("/whoami", tags=["headers"])
async def whoami(
    # 【基础】user_agent → FastAPI 自动匹配 User-Agent 请求头
    #   这个头包含了浏览器名、版本、操作系统信息
    user_agent: str | None = Header(default=None),
    # 【基础】accept_language → 匹配 Accept-Language 头
    #   例如 en-US,en;q=0.9,zh-CN;q=0.8
    accept_language: str | None = Header(default=None),
    # 【基础】x_custom → 匹配 X-Custom 头（自定义头，X- 前缀非标准但惯用）
    x_custom: str | None = Header(default=None, alias="X-Custom"),
):
    """
    【基础功能】读取客户端的 HTTP 请求头，识别用户代理和语言偏好
    【学习知识点】
        1. Header() — 从请求头提取值
        2. convert_underscores — _ 自动转 - 匹配 HTTP 头
        3. alias — 当 Python 名和 HTTP 头名不同时的映射
    调用示例：
        curl -H "X-Custom:hello" http://127.0.0.1:8000/whoami
        curl -H "Accept-Language:zh-CN" http://127.0.0.1:8000/whoami
    """
    # 【基础】根据 User-Agent 判断客户端类型
    client_type = "未知"
    if user_agent:
        if "curl" in user_agent.lower():
            client_type = "命令行 curl"
        elif "python" in user_agent.lower():
            client_type = "Python 程序"
        elif "mozilla" in user_agent.lower() or "chrome" in user_agent.lower():
            client_type = "浏览器"
        elif "postman" in user_agent.lower():
            client_type = "Postman 调试工具"

    return {
        "client_type": client_type,
        "user_agent": user_agent,
        "accept_language": accept_language,
        "x_custom": x_custom,
    }


# ==============================================
# 例2：读取 Cookie — GET /read-cookie
# 【基础】Cookie() 读取浏览器发来的 Cookie 值
#         Cookie 是浏览器按域名存储的小段数据，每次请求自动发送
#         和 Header 的区别：Cookie 是持久化的（用户不主动清除一直存在）
# 【进阶】Cookie 的工作机制（关键理解）：
#   1. 服务器通过 Set-Cookie 响应头告诉浏览器"记住这个值"
#   2. 浏览器存储 Cookie（按域名隔离，每个域名有自己的 Cookie 空间）
#   3. 之后每次请求同域名，浏览器自动在 Cookie 请求头中附带
#   4. 服务器通过 Cookie() 或 Request.cookies 读取
#   5. Cookie 有过期时间（Expires/Max-Age），过期后浏览器自动删除
# ==============================================
@app.get("/read-cookie", tags=["cookies"])
async def read_cookie(
    # 【基础】读取名为 session_id 的 Cookie，默认 None（未设置时）
    session_id: str | None = Cookie(default=None),
    # 【基础】读取名为 theme 的 Cookie
    theme: str | None = Cookie(default="light"),
):
    """
    【基础功能】读取浏览器发送的 Cookie 值（theme 和 session_id）
    【学习知识点】
        1. Cookie() — 从请求 Cookie 中提取值
        2. Cookie 默认值 — 未设置时使用 default 值
        3. Cookie 和 Header 的区别 — 存储机制、生命周期、安全属性
    调用示例：
        curl -b "theme=dark" http://127.0.0.1:8000/read-cookie
    """
    return {
        "session_id": session_id,
        "theme": theme,
        "has_session": session_id is not None,
        "message": "使用 /set-theme 接口设置 Cookie 后再来访问",
    }


# ==============================================
# 例3：设置响应 Cookie — GET /set-theme/{theme_name}
# 【基础】Response.set_cookie() 告诉浏览器"把这个值存起来"
#         key → Cookie 名称
#         value → Cookie 值
#         max_age → 多少秒后过期（None 或 0 表示"会话 Cookie"，关闭浏览器即消失）
#         httponly → True 表示 JavaScript 无法读取（防 XSS 攻击）
#         secure → True 表示只在 HTTPS 连接下发送
#         samesite → 控制跨站请求时是否发送 Cookie（lax/strict/none）
# 【进阶】Cookie 安全属性详解（生产必知）：
#   HttpOnly=True
#     → JavaScript 的 document.cookie 无法读取，只能通过 HTTP 传输
#     → 防御 XSS 攻击窃取 Cookie（攻击者注入的 JS 脚本读不到 cookie）
#     → 几乎所有的 session cookie 都应设为 HttpOnly
#   Secure=True
#     → Cookie 只在 HTTPS（加密连接）下传输，HTTP 明文不发送
#     → 防御中间人攻击（MITM）窃听 Cookie
#     → 生产环境必须设置
#   SameSite=Lax（推荐默认值）
#     → 大多数跨站请求不发送 Cookie（阻止 CSRF 攻击）
#     → 但允许从外部链接跳转时发送（用户体验不受影响）
#     → Lax 是 Chrome 80+ 的默认行为
#   SameSite=Strict
#     → 所有跨站请求都不发送 Cookie（包括外部链接跳转）
#     → 最安全，但用户体验较差（从邮件链接打开需要重新登录）
#   SameSite=None（配合 Secure）
#     → 允许跨站发送（用于第三方嵌入场景）
#     → 必须同时设置 Secure=True，否则浏览器拒绝
# ==============================================
@app.get("/set-theme/{theme_name}", tags=["cookies"])
async def set_theme(
    theme_name: str,
    response: Response,  # 【基础】声明 Response 参数，FastAPI 注入响应对象
):
    """
    【基础功能】设置名为 theme 的 Cookie，保存用户主题偏好
    【学习知识点】
        1. Response 参数注入 — FastAPI 自动识别 Response 类型并传入空响应对象
        2. response.set_cookie() — 设置 Cookie 的核心 API
        3. Cookie 安全属性 — max_age / httponly / samesite
    参数：
        theme_name: 【基础释义：主题名称（light/dark 等）】
        response:   【基础释义：FastAPI 自动注入的 Response 对象，用于设置响应属性】
    调用示例：
        curl -c cookies.txt http://127.0.0.1:8000/set-theme/dark （保存 Cookie 到文件）
        curl -b cookies.txt http://127.0.0.1:8000/read-cookie（用保存的 Cookie 读取）
        或浏览器访问：http://127.0.0.1:8000/set-theme/dark 然后访问 /read-cookie
    同场景常用替代函数：
        1. JSONResponse 直接返回 — 无法设置 Cookie，需要用 Response 或其子类
        2. RedirectResponse — 可同时设置 Cookie + 重定向
        3. 前端 localStorage — 不经过 HTTP 的纯浏览器存储，更灵活但不利于 SSR
    注意事项：
        1. Secure=True 在本地开发（localhost HTTP）时 Cookie 不会生效
        2. SameSite=Lax 是 2026 年的行业标准默认值
    """
    # 【基础】只允许法律的主题值
    if theme_name not in ("light", "dark", "auto"):
        raise HTTPException(status_code=400, detail="主题只能是 light、dark 或 auto")

    # 【基础】设置 Cookie，有效期 30 天
    # 【进阶】max_age 单位为秒：30 * 24 * 60 * 60 = 30 天
    response.set_cookie(
        key="theme",
        value=theme_name,
        max_age=30 * 24 * 60 * 60,  # 30 天（秒）
        httponly=False,  # 允许 JS 读取（前端主题切换需要）
        samesite="lax",  # 跨站链接跳转时仍然发送
        secure=False,    # 开发环境不强制 HTTPS
    )

    return {
        "message": f"主题已设置为 {theme_name}",
        "theme": theme_name,
        "expires_in": "30天",
        "tip": "访问 /read-cookie 查看设置的 Cookie",
    }


# ==============================================
# 例4：设置会话 Cookie + HttpOnly — GET /login-simple/{username}
# 【基础】HttpOnly=True 的 Cookie JavaScript 读不到，更安全
#         用于存储 session ID 或 auth token（敏感信息）
#         浏览器会发送但不能被脚本读取（防 XSS 窃取）
# 【进阶】虽然叫"会话 Cookie"，但 max_age 为 0 或 None 才是真正的会话 Cookie
#   本例故意设置 1 小时过期（max_age=3600），演示"有期限的认证 Cookie"
#   短期认证 token 的最佳实践：过期时间越短越安全（通常 15-60 分钟）
#   同时提供一个长期 refresh token（7 天）来换取新的短期 token（Step11 详解）
# ==============================================
@app.get("/login-simple/{username}", tags=["cookies"])
async def simple_login(username: str, response: Response):
    """
    【基础功能】模拟简单登录，设置 HttpOnly 的安全 Session Cookie
    【学习知识点】
        1. HttpOnly Cookie — 防止 JavaScript 访问，防御 XSS
        2. 认证 Cookie 设计模式 — 浏览器自动带 token，无需手动管理
        3. 短期 token — 1 小时过期，降低 token 泄露的风险窗口
    调用示例：
        浏览器访问 http://127.0.0.1:8000/login-simple/admin
        然后访问 /read-cookie 查看 session_id（由于 HttpOnly，JS 读不到，但 curl 可以）
    """
    # 【基础】模拟生成一个 session token（真实项目用 JWT 或随机字符串）
    import hashlib
    session_token = hashlib.sha256(f"{username}:{datetime.now().isoformat()}".encode()).hexdigest()[:32]

    # 【基础】设置 HttpOnly Session Cookie，1 小时过期
    response.set_cookie(
        key="session_id",
        value=session_token,
        max_age=3600,  # 1 小时（秒）
        httponly=True,  # JS 无法读取，防 XSS
        samesite="lax",
        secure=False,   # 开发环境
    )

    return {
        "message": f"用户 {username} 登录成功",
        "session_token": session_token,  # 仅演示返回，生产环境不应返回 token
        "expires_in": "1小时",
        "security_note": "此 Cookie 设为 HttpOnly，JavaScript 的 document.cookie 无法读取",
    }


# ==============================================
# 例5：删除 Cookie — GET /logout
# 【基础】response.delete_cookie() 发送一个立即过期的 Set-Cookie
#         浏览器收到后删除本地存储的指定 Cookie
#         本质上也是一个 Set-Cookie，只是 max-age=0 或 expires 为过去时间
# 【进阶】删除 Cookie 的关键参数要和设置时完全一致：
#   同样的 key → Cookie 名称
#   同样的 path → 路径匹配（通常 "/"，表示根路径）
#   同样的 domain → 域名匹配
#   同样的 samesite/secure → 安全属性匹配
#   如果不一致，浏览器可能不会删除！（浏览器 Cookie 按 (name, domain, path) 三元组索引）
# ==============================================
@app.get("/logout", tags=["cookies"])
async def logout(response: Response):
    """
    【基础功能】清除 session_id Cookie，实现简单登出
    【学习知识点】
        1. response.delete_cookie() — 删除客户端 Cookie
        2. Cookie 删除原理 — 发送过期的 Set-Cookie 让浏览器清除
        3. 登出后 Cookie 仍可被重放 — 无状态 token 的真正无效化需要黑名单机制
    调用示例：
        curl -c cookies.txt http://127.0.0.1:8000/login-simple/test
        curl -b cookies.txt http://127.0.0.1:8000/logout
        curl -b cookies.txt http://127.0.0.1:8000/read-cookie（session_id 已被清除）
    注意事项：
        无状态 JWT 的真正登出需要服务端维护黑名单或缩短 token 有效期。
        单纯删除客户端 Cookie 只阻止了浏览器自动发送 token，
        如果 token 本身被截获，攻击者仍可手动拼 HTTP 头发送。
    """
    # 【基础】删除 session_id Cookie
    response.delete_cookie(
        key="session_id",
        path="/",  # 路径必须和设置时一致
    )
    return {"message": "已登出", "cleared_cookies": ["session_id"]}


# ==============================================
# 例6：语言偏好 Cookie + 国际化模拟 — GET /lang/{lang}
# 【基础】结合 Cookie 和 Header 做多语言支持
#         Accept-Language 头 = 浏览器默认语言
#         lang Cookie = 用户手动选择的语言（优先级高于浏览器默认）
#         常见模式：先检查 Cookie，没有再看 Header，都没有用默认值
# 【进阶】国际化（i18n）的推荐实现方式：
#   1. URL 路径 → /zh/users/ 和 /en/users/（对 SEO 友好）
#   2. Cookie → 用户手动切换后记住偏好
#   3. Accept-Language 头 → 首次访问时根据浏览器语言自动适配
#   4. 优先级：URL > Cookie > Header > 默认值（本示例展示的是 Cookie 优先模式）
# ==============================================
@app.get("/lang/{lang}", tags=["cookies"])
async def set_language(
    lang: str,
    response: Response,
    accept_language: str | None = Header(default=None),
):
    """
    【基础功能】设置语言偏好 Cookie，同时返回浏览器默认语言
    【学习知识点】
        1. Cookie + Header 组合 — 用户偏好（Cookie）vs 浏览器默认（Accept-Language）
        2. 多来源数据融合 — Cookie > Header > 默认值 的优先级链
        3. 国际化基础 — 优先级决定最终使用哪种语言
    """
    if lang not in ("zh", "en", "ja", "ko"):
        raise HTTPException(status_code=400, detail="支持的语言：zh/en/ja/ko")

    response.set_cookie(
        key="lang",
        value=lang,
        max_age=365 * 24 * 60 * 60,  # 1 年
        samesite="lax",
    )

    # 【基础】语言名称映射表
    lang_names = {"zh": "中文", "en": "English", "ja": "日本語", "ko": "한국어"}

    return {
        "language_set": lang,
        "language_name": lang_names.get(lang, lang),
        "browser_default": accept_language,
        "priority": "用户选择（Cookie）> 浏览器默认（Accept-Language）",
    }


# ==============================================
# 程序入口
# ==============================================
if __name__ == "__main__":
    uvicorn.run(
        "step10_header_cookie:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )
