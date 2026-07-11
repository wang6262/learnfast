# ==============================================
# 文件名：step23_websocket_chat/main.py
# 基础功能：WebSocket 聊天室 — 房间管理、用户昵称、在线列表
# 核心学习知识点：
#   1. ConnectionManager 进阶 — 房间/频道分组管理
#   2. WebSocket 鉴权 — 握手时通过 query param 传递 token
#   3. 用户状态管理 — 昵称 → WebSocket 映射
#   4. 在线列表推送 — 新用户加入/离开时广播在线列表
#   5. 多房间隔离 — 不同频道的消息互不干扰
# 运行方式：uv run python -m step23_websocket_chat.main
# ==============================================
import uvicorn
import asyncio

from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import HTMLResponse


app = FastAPI(
    title="LearnFast API — WebSocket 聊天室",
    description="FastAPI 学习 Step23：聊天室、房间管理、在线列表",
    version="0.1.0",
)


# ==============================================
# 进阶连接管理器（支持房间隔离）
# 【基础】每个房间（room）有独立的连接集合
#         同一房间内消息广播，不同房间互不可见
#         相当于：微信群聊 vs 私聊的概念
# 【进阶】内存字典存储 → 单进程有效
#   多进程/多服务器部署时，需要 Redis Pub/Sub 做跨实例广播
#   Redis 方案（简述）：
#     每个服务器实例订阅 Redis 频道
#     收到 WebSocket 消息 → publish 到 Redis → 所有服务器实例收到 → 推送给各自的连接
#     这是分布式 WebSocket 的标准解法
# ==============================================


class ChatRoom:
    """单个聊天房间"""

    def __init__(self, room_id: str):
        self.room_id = room_id
        self.connections: dict[str, WebSocket] = {}  # username → WebSocket
        self.message_history: list[dict] = []  # 最近的消息记录

    async def join(self, username: str, websocket: WebSocket):
        """用户加入房间"""
        await websocket.accept()
        self.connections[username] = websocket
        # 发送最近 10 条历史消息
        if self.message_history:
            await websocket.send_json({
                "type": "history",
                "messages": self.message_history[-10:],
            })
        await self.broadcast({"type": "system", "message": f"{username} 加入了房间", "online": self.online_users})

    def leave(self, username: str):
        """用户离开房间"""
        self.connections.pop(username, None)

    async def broadcast(self, message: dict, exclude: str = None):
        """广播消息给房间所有人（可选排除某人）"""
        for uname, ws in list(self.connections.items()):
            if uname != exclude:
                try:
                    await ws.send_json(message)
                except Exception:
                    self.leave(uname)

    async def send_message(self, username: str, text: str):
        """用户发送消息 → 广播给所有人"""
        msg = {
            "type": "message",
            "username": username,
            "text": text,
            "time": datetime.now().strftime("%H:%M:%S"),
        }
        self.message_history.append(msg)
        # 只保留最近 100 条
        if len(self.message_history) > 100:
            self.message_history = self.message_history[-100:]
        await self.broadcast(msg)

    @property
    def online_users(self) -> list[str]:
        return list(self.connections.keys())

    @property
    def online_count(self) -> int:
        return len(self.connections)


class RoomManager:
    """全局房间管理器"""

    def __init__(self):
        self.rooms: dict[str, ChatRoom] = {}

    def get_or_create(self, room_id: str) -> ChatRoom:
        if room_id not in self.rooms:
            self.rooms[room_id] = ChatRoom(room_id)
        return self.rooms[room_id]

    def get_room_list(self) -> list[dict]:
        """获取所有房间的信息"""
        return [
            {"id": rid, "online": room.online_count, "users": room.online_users}
            for rid, room in self.rooms.items()
        ]


room_manager = RoomManager()


# ==============================================
# WebSocket 端点：加入聊天室
# 【基础】ws://host:port/ws/chat/{room_id}?username=你的昵称
#         同一 room_id 的用户在同一个房间里
#         不同 room_id 的用户看不到彼此的消息（房间隔离）
# 【进阶】鉴权方式：
#   1. Query Param：ws://host/ws?token=xxx（本示例使用，简单直接）
#   2. 第一条消息鉴权：连接后先发 {"type":"auth","token":"xxx"}
#   3. Cookie 鉴权：浏览器 WebSocket 自动携带同域 Cookie
#   4. 子协议（Sec-WebSocket-Protocol）：握手时传递鉴权信息
#   推荐方式 3（Cookie）+ 方式 1（Query Param for token）组合
# ==============================================


@app.websocket("/ws/chat/{room_id}")
async def chat_room(
    websocket: WebSocket,
    room_id: str,
    username: str = Query(default="游客"),
):
    """
    聊天室 WebSocket。
    参数：
        room_id: 房间号（路径参数），如 "general"、"tech"、"random"
        username: 用户昵称（查询参数），如 ?username=张三
    """
    # 清理用户名（限制长度，防止注入）
    clean_username = username[:20] or "游客"

    room = room_manager.get_or_create(room_id)

    try:
        await room.join(clean_username, websocket)

        while True:
            # 接收客户端消息
            data = await websocket.receive_json()
            msg_type = data.get("type", "message")

            if msg_type == "message":
                text = data.get("text", "")[:500]  # 限制消息长度
                if text.strip():
                    await room.send_message(clean_username, text)

            elif msg_type == "ping":
                # 心跳响应
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        pass
    finally:
        room.leave(clean_username)
        await room.broadcast({
            "type": "system",
            "message": f"{clean_username} 离开了房间",
            "online": room.online_users,
        })


# ==============================================
# REST 端点：房间列表
# ==============================================


@app.get("/rooms/", tags=["rooms"])
async def list_rooms():
    """获取所有活跃房间的信息"""
    return {"rooms": room_manager.get_room_list()}


# ==============================================
# 聊天室 HTML 测试页面
# ==============================================


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def chat_page():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8"><title>聊天室</title>
        <style>
            body { font-family: sans-serif; max-width: 600px; margin: 20px auto; }
            #messages { border: 1px solid #ccc; height: 300px; overflow-y: auto; padding: 10px;
              background: #fafafa; margin: 10px 0; }
            .system { color: #999; font-style: italic; }
            .message { margin: 5px 0; }
            input, select, button { padding: 6px; margin: 3px; }
            #input-row { display: flex; gap: 5px; }
            #msg-input { flex: 1; }
        </style>
    </head>
    <body>
        <h2>FastAPI 聊天室学习示例</h2>
        <div>
            <label>房间：<input id="room-input" value="general" size="10"></label>
            <label>昵称：<input id="name-input" value="学习者" size="10"></label>
            <button onclick="connect()">加入房间</button>
            <span id="status" style="color:gray;">未连接</span>
        </div>
        <div id="messages"></div>
        <div id="input-row">
            <input id="msg-input" placeholder="输入消息..." disabled onkeydown="if(event.key==='Enter')send()">
            <button onclick="send()" id="send-btn" disabled>发送</button>
        </div>
        <script>
            let ws = null;
            function log(msg, cls) {
                const div = document.createElement("div");
                div.className = cls || "message";
                div.textContent = msg;
                document.getElementById("messages").appendChild(div);
                document.getElementById("messages").scrollTop = document.getElementById("messages").scrollHeight;
            }
            function connect() {
                if (ws) ws.close();
                const room = document.getElementById("room-input").value || "general";
                const name = document.getElementById("name-input").value || "游客";
                ws = new WebSocket(`ws://127.0.0.1:8000/ws/chat/${room}?username=${encodeURIComponent(name)}`);
                ws.onopen = () => {
                    document.getElementById("status").textContent = `已连接 (${room})`;
                    document.getElementById("status").style.color = "green";
                    document.getElementById("msg-input").disabled = false;
                    document.getElementById("send-btn").disabled = false;
                };
                ws.onmessage = e => {
                    const d = JSON.parse(e.data);
                    if (d.type === "system") log(d.message + ` (在线: ${d.online ? d.online.join(", ") : ""})`, "system");
                    else if (d.type === "message") log(`[${d.time}] ${d.username}: ${d.text}`, "message");
                    else if (d.type === "history") d.messages.forEach(m => log(`[${m.time}] ${m.username}: ${m.text}`));
                };
                ws.onclose = () => {
                    document.getElementById("status").textContent = "已断开";
                    document.getElementById("status").style.color = "red";
                    document.getElementById("msg-input").disabled = true;
                    document.getElementById("send-btn").disabled = true;
                };
            }
            function send() {
                const inp = document.getElementById("msg-input");
                if (ws && inp.value.trim()) {
                    ws.send(JSON.stringify({type: "message", text: inp.value}));
                    inp.value = "";
                }
            }
        </script>
    </body>
    </html>
    """


if __name__ == "__main__":
    uvicorn.run("step23_websocket_chat.main:app", host="127.0.0.1", port=8000, reload=True)
