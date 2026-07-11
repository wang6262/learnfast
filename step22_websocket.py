# ==============================================
# 文件名：step22_websocket.py
# 基础功能：学习 FastAPI WebSocket 基础：建立连接、收发消息、连接管理
# 核心学习知识点：
#   1. @app.websocket("/ws") — WebSocket 路由装饰器
#   2. await websocket.accept() — 接受连接（服务器端主动握手确认）
#   3. await websocket.receive_text() — 接收客户端文本消息
#   4. await websocket.send_text() — 发送文本给客户端
#   5. await websocket.receive_json() / send_json() — JSON 格式收发
#   6. WebSocket 连接生命周期 — 建立 → 双向通信 → 断开
#   7. WebSocket vs HTTP 轮询 — 持久连接 vs 请求-响应
#   8. ConnectionManager 模式 — 管理多个 WebSocket 连接
# 适用场景：实时聊天、在线协作编辑、实时股价推送、游戏通信
# 运行方式：uv run python step22_websocket.py
#   访问 http://127.0.0.1:8000/ 查看 WebSocket 测试页面
# ==============================================
import uvicorn
import asyncio

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse


app = FastAPI(
    title="LearnFast API — WebSocket",
    description="FastAPI 学习 Step22：WebSocket 基础、双向通信",
    version="0.1.0",
)


# ==============================================
# 连接管理器
# 【基础】管理所有活跃的 WebSocket 连接：
#   - connect(ws)：新连接加入
#   - disconnect(ws)：连接断开移除
#   - broadcast(msg)：向所有连接发送消息
# 【进阶】ConnectionManager 是 WebSocket 应用的标配模式
#   真实项目需要处理：
#   1. 并发安全（asyncio.Lock 保护 active_connections 列表）
#   2. 断线检测（心跳 ping/pong）
#   3. 连接认证（WebSocket 握手时验证 token）
#   4. 频道/房间管理（按 topic 分组连接）
# ==============================================


class ConnectionManager:
    """WebSocket 连接管理器"""

    def __init__(self):
        # 【基础】存储所有活跃的 WebSocket 连接
        #   List 不是线程安全的，但在 asyncio 单线程事件循环中安全
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """接受新连接"""
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        """移除断开的连接"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str, sender: WebSocket = None):
        """
        向所有连接的客户端广播消息。
        sender 参数允许排除发送者（不自收自消息）。
        """
        for connection in self.active_connections:
            if connection != sender:  # 不发给自己
                try:
                    await connection.send_text(message)
                except Exception:
                    # 发送失败（对方可能已断开），自动清理
                    self.disconnect(connection)

    async def send_personal(self, message: str, websocket: WebSocket):
        """发送消息给特定客户端"""
        await websocket.send_text(message)

    @property
    def online_count(self) -> int:
        return len(self.active_connections)


manager = ConnectionManager()


# ==============================================
# WebSocket 端点 1：简单回显
# 【基础】客户端发什么 → 服务端回什么（echo 模式）
#         用于理解 WebSocket 最基本的收发流程
# 【进阶】WebSocket 握手过程（在 accept() 中完成）：
#   1. 客户端发 HTTP GET，带 Upgrade: websocket 头
#   2. 服务端 accept() 返回 101 Switching Protocols
#   3. TCP 连接升级为 WebSocket（同一连接，协议切换）
#   4. 之后就可以双向发送消息（不像 HTTP 必须一问一答）
# ==============================================


@app.websocket("/ws/echo")
async def websocket_echo(websocket: WebSocket):
    """
    简单回显 WebSocket：客户端发什么，服务端回什么。
    浏览器测试页面：访问 http://127.0.0.1:8000/
    """
    await websocket.accept()
    await websocket.send_text("连接成功！输入任意消息，我会回显。输入 'bye' 断开。")

    try:
        while True:
            # 【基础】等待客户端发消息（阻塞当前协程，不阻塞事件循环）
            data = await websocket.receive_text()

            if data.lower() == "bye":
                await websocket.send_text(f"回显：{data} — 连接即将关闭")
                break

            # 【基础】回显消息给客户端
            await websocket.send_text(f"回显：{data}")
    except WebSocketDisconnect:
        # 客户端主动断开连接或网络中断
        print("客户端已断开连接")
    # finally 中可选做清理工作


# ==============================================
# WebSocket 端点 2：带连接管理的广播聊天
# 【基础】多个客户端连接同一个 /ws/chat 端点
#         每个客户端发消息 → 广播给所有其他客户端
#         同时显示当前在线人数
# 【进阶】广播模式的实际应用场景：
#   - 实时聊天室（微信群聊效果）
#   - 在线人数/状态同步
#   - 实时通知推送（如系统维护公告）
# ==============================================


@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """多人广播聊天 WebSocket"""
    await manager.connect(websocket)

    # 通知所有人有新用户加入
    await manager.broadcast(f"一位新用户加入了聊天室！当前在线：{manager.online_count}人")

    try:
        while True:
            data = await websocket.receive_text()
            # 广播消息给所有其他客户端（不自收）
            await manager.broadcast(f"用户说：{data}", sender=websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"一位用户离开了聊天室。当前在线：{manager.online_count}人")


# ==============================================
# WebSocket 端点 3：定时推送（模拟实时数据）
# 【基础】服务端每 2 秒推送一次数据给客户端
#         模拟场景：股价实时更新、服务器 CPU 使用率推送
# 【进阶】推送 + 接收可以同时进行（全双工）
#   但本示例简化为只推送（服务端→客户端单向）
#   真实应用通常是双向：客户端发送订阅请求，服务端推送对应数据
# ==============================================


@app.websocket("/ws/ticker")
async def websocket_ticker(websocket: WebSocket):
    """每 2 秒推送模拟股票行情"""
    await websocket.accept()
    await websocket.send_text("股票行情推送已启动（每2秒推送一次）")

    import random
    price = 100.0

    try:
        while True:
            # 模拟价格波动
            price += random.uniform(-2, 2)
            price = max(1, round(price, 2))

            await websocket.send_json({
                "symbol": "LEARN",
                "price": price,
                "change": round(price - 100, 2),
            })
            await asyncio.sleep(2)  # 每 2 秒推送
    except WebSocketDisconnect:
        print("行情推送客户端已断开")


# ==============================================
# WebSocket 测试页面
# ==============================================


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def ws_test_page():
    """WebSocket 测试页面（浏览器打开即可测试）"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>WebSocket 测试</title>
        <style>
            body { font-family: monospace; max-width: 800px; margin: 20px auto; }
            .section { border: 1px solid #ddd; padding: 10px; margin: 10px 0; border-radius: 5px; }
            input, button { padding: 5px 10px; margin: 5px; }
            #echo-log, #chat-log, #ticker-log { background: #f5f5f5; padding: 10px; height: 150px;
              overflow-y: auto; white-space: pre-wrap; font-size: 12px; }
        </style>
    </head>
    <body>
        <h2>FastAPI WebSocket 测试</h2>

        <div class="section">
            <h3>1. 回显测试 (Echo)</h3>
            <input id="echo-input" placeholder="输入消息..."><button onclick="echoSend()">发送</button>
            <div id="echo-log"></div>
        </div>

        <div class="section">
            <h3>2. 广播聊天 (Chat)</h3>
            <input id="chat-input" placeholder="输入聊天消息..."><button onclick="chatSend()">发送</button>
            <div id="chat-log"></div>
        </div>

        <div class="section">
            <h3>3. 行情推送 (Ticker)</h3>
            <div id="ticker-log"></div>
        </div>

        <script>
            // Echo WebSocket
            const echoWs = new WebSocket("ws://127.0.0.1:8000/ws/echo");
            echoWs.onmessage = e => { document.getElementById("echo-log").textContent += e.data + "\\n"; };

            function echoSend() {
                const inp = document.getElementById("echo-input");
                echoWs.send(inp.value); inp.value = "";
            }

            // Chat WebSocket
            const chatWs = new WebSocket("ws://127.0.0.1:8000/ws/chat");
            chatWs.onmessage = e => { document.getElementById("chat-log").textContent += e.data + "\\n"; };

            function chatSend() {
                const inp = document.getElementById("chat-input");
                chatWs.send(inp.value); inp.value = "";
            }

            // Ticker WebSocket
            const tickerWs = new WebSocket("ws://127.0.0.1:8000/ws/ticker");
            tickerWs.onmessage = e => { document.getElementById("ticker-log").textContent = e.data + "\\n"; };
        </script>
    </body>
    </html>
    """


if __name__ == "__main__":
    uvicorn.run("step22_websocket:app", host="127.0.0.1", port=8000, reload=True)
