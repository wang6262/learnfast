# ==============================================
# 文件名：step24_streaming.py
# 基础功能：学习 StreamingResponse 和 Server-Sent Events (SSE)
# 核心学习知识点：
#   1. StreamingResponse — 流式传输响应（不一次生成所有数据）
#   2. 生成器函数 — yield 逐块发送数据
#   3. Server-Sent Events (SSE) — 服务端单向推送事件流
#   4. 文件流下载 — 避免大文件全部加载到内存
#   5. content-type: text/event-stream — SSE 的标准 MIME 类型
#   6. StreamingResponse vs WebSocket — 单向推送 vs 双向通信的选择
#   7. 进度推送 — 模拟长时间任务的进度报告
# 适用场景：大文件下载、AI 流式输出（ChatGPT 逐字输出）、实时日志、进度条
# 运行方式：uv run python step24_streaming.py
# ==============================================
import uvicorn
import asyncio
import time
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.responses import StreamingResponse, HTMLResponse


app = FastAPI(
    title="LearnFast API — 流式响应",
    description="FastAPI 学习 Step24：StreamingResponse、SSE、文件流下载",
    version="0.1.0",
)


# ==============================================
# 例1：模拟 AI 流式输出（SSE）
# 【基础】ChatGPT 那种"一个字一个字往外蹦"的效果
#         服务端 yield 一块 → 客户端收到 → 立即显示
#         不是等全部生成完再一次性返回
# 【进阶】SSE（Server-Sent Events）协议：
#   1. Content-Type: text/event-stream
#   2. 数据格式：data: <内容>\n\n（必须双换行分隔）
#   3. 可选的 event: 字段用于区分事件类型
#   4. 可选的 id: 字段用于断线重连
#   5. 客户端用 EventSource API 接收（浏览器原生支持）
# SSE vs WebSocket：
#   SSE — 单向（服务端→客户端），HTTP 协议，自动重连，浏览器原生支持
#   WebSocket — 双向，独立协议（ws://），需手动实现重连，灵活但更复杂
#   选择原则：只需要推送 → SSE，需要双向通信 → WebSocket
# ==============================================


async def ai_response_generator(prompt: str) -> AsyncGenerator[str, None]:
    """
    模拟 AI 流式输出：逐词生成并 yield。
    异步生成器（async generator）是 StreamingResponse 的核心。
    """
    # 模拟的 AI 回复内容（真实项目调用 OpenAI/Claude API stream=True）
    response = f"关于「{prompt}」这个问题，我来回答：FastAPI 是一个现代、高性能的 Python Web 框架，它基于 Starlette 和 Pydantic，支持异步处理和自动 API 文档生成。它的核心优势是类型注解驱动的数据校验和 OpenAPI 文档自动生成。"
    words = response.split()

    for word in words:
        # 【基础】SSE 格式：data: <内容>\n\n
        yield f"data: {word}\n\n"
        await asyncio.sleep(0.15)  # 模拟生成延迟


@app.get("/ai/stream", tags=["streaming"])
async def ai_stream(prompt: str = "FastAPI 是什么"):
    """
    模拟 AI 流式输出接口。
    响应类型：text/event-stream（浏览器 EventSource 可自动解析）
    调用示例：curl http://127.0.0.1:8000/ai/stream?prompt=你好
    """
    return StreamingResponse(
        ai_response_generator(prompt),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",  # 禁止缓存（流式内容每次都是新的）
            "Connection": "keep-alive",   # 保持连接
            "X-Accel-Buffering": "no",    # 禁用 nginx 缓冲（生产环境重要！）
        },
    )


# ==============================================
# 例2：任务进度推送
# 【基础】模拟一个需要多步完成的任务（5 步，每步 1 秒）
#         每完成一步，推送给客户端当前进度
#         前端可以据此渲染进度条
# 【进阶】真正的进度推送需要后台任务 + 消息队列
#   这里的 SSE 示例是"同步推进"的：
#   客户端发起请求 → 服务端逐步执行 → 逐步推送进度 → 完成
#   复杂场景（异步任务）应该：
#   客户端 POST 创建任务 → 返回 task_id
#   客户端 GET /task/{id}/progress → SSE 监听进度
#   服务端用 Redis Pub/Sub 或 Celery 事件更新进度
# ==============================================


async def task_progress_generator(task_name: str) -> AsyncGenerator[str, None]:
    """模拟任务进度，逐步推送完成百分比"""
    total_steps = 5
    for step in range(1, total_steps + 1):
        progress = int(step / total_steps * 100)
        # 【基础】推送进度事件
        yield f"data: {progress}\n\n"
        # 【基础】模拟每步耗时
        await asyncio.sleep(1)
    # 完成事件
    yield f"data: DONE\n\n"


@app.get("/task/progress", tags=["streaming"])
async def task_progress(task: str = "数据处理"):
    """模拟任务进度推送（每步 1 秒，共 5 步）"""
    return StreamingResponse(
        task_progress_generator(task),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"},
    )


# ==============================================
# 例3：用 HTML 展示 SSE 效果
# ==============================================


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def sse_demo():
    """SSE 演示页面"""
    return """
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"><title>SSE 流式演示</title>
        <style>
            body { font-family: sans-serif; max-width: 600px; margin: 20px auto; }
            .section { border: 1px solid #ddd; padding: 15px; margin: 15px 0; border-radius: 5px; }
            #ai-output, #progress-output { background: #1a1a2e; color: #e0e0e0; padding: 15px;
              border-radius: 5px; white-space: pre-wrap; min-height: 50px; }
            #progress-bar { width: 0; height: 20px; background: #4caf50; border-radius: 10px;
              transition: width 0.3s; }
            button, input { padding: 5px 10px; }
        </style>
    </head>
    <body>
        <h2>FastAPI Streaming & SSE 演示</h2>

        <div class="section">
            <h3>1. AI 流式输出 (SSE)</h3>
            <input id="ai-prompt" value="FastAPI 是什么" size="30">
            <button onclick="aiStart()">开始生成</button>
            <div id="ai-output"></div>
        </div>

        <div class="section">
            <h3>2. 任务进度推送 (SSE)</h3>
            <button onclick="progressStart()">开始任务</button>
            <div id="progress-bar"></div>
            <div id="progress-output"></div>
        </div>

        <script>
            function aiStart() {
                const prompt = document.getElementById("ai-prompt").value;
                const evtSource = new EventSource(`/ai/stream?prompt=${encodeURIComponent(prompt)}`);
                const output = document.getElementById("ai-output");
                output.textContent = "";
                evtSource.onmessage = e => { output.textContent += e.data + " "; };
                evtSource.onerror = () => evtSource.close();
            }
            function progressStart() {
                const evtSource = new EventSource("/task/progress?task=demo");
                const bar = document.getElementById("progress-bar");
                const output = document.getElementById("progress-output");
                evtSource.onmessage = e => {
                    if (e.data === "DONE") {
                        bar.style.width = "100%";
                        output.textContent = "任务完成！";
                        evtSource.close();
                    } else {
                        bar.style.width = e.data + "%";
                        output.textContent = "进度：" + e.data + "%";
                    }
                };
            }
        </script>
    </body>
    </html>
    """


if __name__ == "__main__":
    uvicorn.run("step24_streaming:app", host="127.0.0.1", port=8000, reload=True)
