# ==============================================
# 文件名：step21_background_tasks.py
# 基础功能：学习 FastAPI 后台任务和生命周期事件
# 核心学习知识点：
#   1. BackgroundTasks — 请求返回后继续执行的后台任务
#   2. @app.on_event("startup") / @app.on_event("shutdown") — 生命周期事件
#   3. lifespan 上下文管理器 — Python 3.8+ 推荐的启动/关闭方式
#   4. asyncio.create_task() — 创建异步后台任务
#   5. 后台任务的适用场景 — 发邮件/推送通知/写日志，不阻塞 HTTP 响应
# 适用场景：发送确认邮件、数据统计、缓存预热、连接池初始化
# 运行方式：uv run python step21_background_tasks.py
# ==============================================
import uvicorn
import asyncio
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, BackgroundTasks, Request


# ==============================================
# Lifespan 上下文管理器（推荐的启动/关闭方式）
# 【基础】lifespan 替代旧的 @app.on_event("startup"/"shutdown")
#         yield 之前 = 启动时执行（startup）
#         yield 之后 = 关闭时执行（shutdown）
#         这里放初始化代码：连接数据库、预热缓存等
# 【进阶】@asynccontextmanager 是 Python 3.7+ 的标准库装饰器
#   能把 async generator 函数转成异步上下文管理器
#   lifespan 方式比 on_event 更灵活：
#   1. 状态可以存在变量中（通过 yield 传递）
#   2. 支持 async 初始化操作（on_event 的 async def 支持不完整）
#   3. 能作为应用状态传递给路由函数
# ==============================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """替代 @app.on_event 的 lifespan 模式"""
    # --- Startup ---
    print("应用启动中...")
    # 模拟：预热连接池
    await asyncio.sleep(0.1)
    print("应用已就绪")

    # yield 把控制权交给 FastAPI（开始接收请求）
    yield

    # --- Shutdown ---
    print("应用关闭中...")
    # 模拟：关闭数据库连接
    await asyncio.sleep(0.1)
    print("应用已安全关闭")


app = FastAPI(
    title="LearnFast API — 后台任务",
    description="FastAPI 学习 Step21：BackgroundTasks、生命周期事件",
    version="0.1.0",
    lifespan=lifespan,  # 注册 lifespan 管理器
)


# ==============================================
# 模拟的后台任务函数
# 【基础】这些函数会在请求返回之后继续运行，不会阻塞客户端等待
# 【进阶】BackgroundTasks 的局限性（需要知道）：
#   1. 和主请求在同进程内运行（服务器重启 → 任务丢失）
#   2. 不适合长时间任务（> 几分钟）或需要重试的任务
#   3. 无法跨进程（如果有多个 worker，任务只在当前 worker 运行）
#   对于"重型"后台任务，应使用 Celery + Redis（Step23+ 可拓展学习）
# ==============================================


def send_welcome_email(email: str, username: str):
    """
    模拟发送欢迎邮件（同步函数）。
    真实项目使用 aiosmtplib 或第三方邮件服务（SendGrid/AWS SES）。
    """
    # 模拟耗时操作
    time.sleep(2)
    print(f"[后台任务完成] 欢迎邮件已发送给 {username} ({email})")


def write_audit_log(user: str, action: str):
    """模拟写入审计日志"""
    with open("audit.log", "a", encoding="utf-8") as f:
        f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {user} 执行了 {action}\n")
    print(f"[后台任务完成] 审计日志已记录")


async def async_background_task(task_id: str, duration: int = 3):
    """
    模拟异步后台任务。
    【学习知识点】BackgroundTasks 也支持 async 函数。
    """
    await asyncio.sleep(duration)
    print(f"[异步后台任务完成] 任务 {task_id} 耗时 {duration}s")


# ==============================================
# 路由：使用 BackgroundTasks
# ==============================================


@app.post("/users/register", tags=["users"])
async def register_user(
    username: str,
    email: str,
    background_tasks: BackgroundTasks,  # FastAPI 自动注入
):
    """
    【基础功能】注册用户（立即返回），后台发送欢迎邮件
    【学习知识点】
        1. BackgroundTasks 作为参数 → FastAPI 自动注入
        2. background_tasks.add_task(func, *args) → 添加后台任务
        3. 请求立即返回 201，邮件在后台 2 秒后"发送"
        4. 这是 fire-and-forget 模式（发后即忘，不关心结果）
    调用示例：
        curl -X POST "http://127.0.0.1:8000/users/register?username=alice&email=a@t.com"
        立即返回 201，2 秒后控制台打印邮件发送完成
    """
    # 【基础】注册逻辑（立即完成）
    # ...

    # 【基础】把发邮件放入后台任务队列（不阻塞响应）
    background_tasks.add_task(send_welcome_email, email, username)

    return {
        "message": f"用户 {username} 注册成功！欢迎邮件将在后台发送",
        "user": username,
    }


@app.post("/items/create", tags=["items"])
async def create_item(
    name: str,
    user: str = "admin",
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    """
    【基础功能】创建商品 + 后台写审计日志
    演示多个后台任务的场景
    """
    # 同时添加多个后台任务（它们会顺序执行还是并发执行取决于任务池）
    background_tasks.add_task(write_audit_log, user, f"创建商品: {name}")
    background_tasks.add_task(async_background_task, task_id=f"item-{name}", duration=2)

    return {"message": f"商品 {name} 创建成功", "background_tasks": 2}


@app.get("/demo/background", tags=["demo"])
async def demo_background(background_tasks: BackgroundTasks):
    """
    演示异步后台任务。
    """
    background_tasks.add_task(async_background_task, task_id="demo-task", duration=5)
    return {"message": "后台任务已启动（5秒后完成），但响应已返回"}


# ==============================================
# 程序入口
# ==============================================
if __name__ == "__main__":
    uvicorn.run("step21_background_tasks:app", host="127.0.0.1", port=8000, reload=True)
