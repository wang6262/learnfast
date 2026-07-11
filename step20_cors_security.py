# ==============================================
# 文件名：step20_cors_security.py
# 基础功能：学习 FastAPI 的 CORS 跨域配置和安全中间件
# 核心学习知识点：
#   1. CORSMiddleware — 允许前端跨域调用 API
#   2. CORS 原理 — 浏览器同源策略 + 预检请求（OPTIONS）
#   3. TrustedHostMiddleware — 限制允许的 Host 头（防 DNS 重绑定攻击）
#   4. GZipMiddleware — 压缩响应体（减少带宽）
#   5. HTTPSRedirectMiddleware — 强制 HTTPS 跳转
#   6. allow_origins vs allow_origin_regex — 精确匹配 vs 正则匹配
#   7. allow_credentials — 跨域 Cookie 的开关
#   8. 安全最佳实践 — 生产环境收紧所有配置
# 适用场景：前后端分离项目、第三方 API 授权、CDN 跨域资源
# 运行方式：uv run python step20_cors_security.py
# ==============================================
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

app = FastAPI(
    title="LearnFast API — CORS & 安全",
    description="FastAPI 学习 Step20：CORS 跨域、安全头、压缩、HTTPS 跳转",
    version="0.1.0",
)

# ==============================================
# 1. CORSMiddleware — 跨域资源共享
# 【基础】浏览器有"同源策略"：www.a.com 的 JS 不能请求 api.b.com
#   CORS 就是让 api.b.com 告诉浏览器"我允许 www.a.com 来请求我"
#   如果不配置 CORS，前端 axios/fetch 请求会被浏览器拦截
# 【进阶】CORS 的核心头：
#   Access-Control-Allow-Origin → 允许哪些域名跨域
#   Access-Control-Allow-Methods → 允许哪些 HTTP 方法
#   Access-Control-Allow-Headers → 允许哪些请求头
#   Access-Control-Allow-Credentials → 是否允许携带 Cookie
#   Access-Control-Max-Age → 预检请求缓存时间（秒）
# 预检请求（Preflight Request）：
#   浏览器对"非简单请求"先发 OPTIONS 探测，确认允许后才发真实请求
#   简单请求：GET/HEAD/POST + 标准头（如 Content-Type: form-urlencoded）
#   非简单请求：PUT/DELETE + Content-Type: application/json → 触发 OPTIONS 预检
# ==============================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",    # React 开发服务器
        "http://localhost:5173",    # Vite 开发服务器
        "http://127.0.0.1:5500",   # Live Server
    ],
    allow_origin_regex=r"https://.*\.example\.com",  # 正则匹配子域名（生产用）
    allow_credentials=True,  # 允许跨域携带 Cookie（前后端都需要配置）
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],  # 允许所有请求头（开发环境），生产环境应限制
    expose_headers=["X-Request-ID", "X-Process-Time"],  # 暴露自定义响应头给 JS 读取
    max_age=3600,  # 预检请求缓存 1 小时
)


# ==============================================
# 3. GZipMiddleware — 响应压缩
# 【基础】自动压缩大于 minimum_size 的 JSON 响应
#         压缩后传输体积可减小 60-90%，显著提升加载速度
# 【进阶】默认最小压缩阈值 500 bytes（太小的内容压缩不划算）
#   压缩 vs 不压缩的权衡：
#   - 压缩：CPU 开销 + 服务端延迟 ≈ 1-3ms，省带宽 60-90%
#   - 通常在反向代理层（nginx）做 gzip，应用层可以不做
#   但 FastAPI 内置的 GZipMiddleware 是最简单的压缩方案
# ==============================================
app.add_middleware(GZipMiddleware, minimum_size=500)


# ==============================================
# 2. TrustedHostMiddleware — 限制 Host 头
# 【基础】防止攻击者伪造 Host 头（Host Header Injection）
#         例如攻击者 curl -H "Host: evil.com" 可能绕过某些安全检查
#         这个中间件校验请求的 Host 头必须在白名单中
# 【进阶】生产环境必须配置！all_allowed_hosts 中的域名应包括：
#   - 你的真实域名（api.xxx.com）
#   - 内网地址（如果是内部服务）
#   - 不要放通配符 "*"（安全漏洞）
# ==============================================
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=[
        "localhost",
        "127.0.0.1",
        "*.example.com",  # 通配子域名
    ],
)


# 路由
@app.get("/")
async def root():
    return {"message": "CORS & Security 配置完成", "cors_origins": ["localhost:3000", "localhost:5173"]}


@app.get("/api/data", tags=["api"])
async def get_data():
    """演示接口：前端跨域请求此接口"""
    return {
        "items": [{"id": 1, "name": "商品1"}, {"id": 2, "name": "商品2"}],
        "note": "如果从 localhost:3000 发请求，CORS 头会告诉你允许跨域",
    }


# ==============================================
# CORS 测试用 HTML 页面（嵌入式）
# 【基础】访问 http://127.0.0.1:8000/test-cors 打开测试页面
#         页面从当前页面发 fetch 请求，不会触发跨域（同源）
#         要测试真实的 CORS，需要在 localhost:3000 等其他域名下运行前端
# ==============================================
from fastapi.responses import HTMLResponse


@app.get("/test-cors", response_class=HTMLResponse, include_in_schema=False)
async def test_cors_page():
    """简单的 CORS 测试页面"""
    return """
    <!DOCTYPE html>
    <html>
    <head><title>CORS 测试</title></head>
    <body>
        <h2>CORS 跨域测试</h2>
        <p>当前页面与 API 同源，需在其他域名下测试 CORS。</p>
        <button onclick="fetch('/api/data').then(r=>r.json()).then(d=>{document.getElementById('result').textContent=JSON.stringify(d,null,2)})">调用 /api/data</button>
        <pre id="result"></pre>
        <p>用浏览器 DevTools → Network → 查看响应头中的 Access-Control-Allow-Origin</p>
    </body>
    </html>
    """


if __name__ == "__main__":
    uvicorn.run("step20_cors_security:app", host="127.0.0.1", port=8000, reload=True)
