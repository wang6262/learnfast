# ==============================================
# 文件名：react-backend.py
# 基础功能：React 前端学习配套的 FastAPI 后端，提供用户 CRUD API
# 核心学习知识点：FastAPI CRUD、内存数据存储、Pydantic 类型校验、前后端对接
# 适用场景：配合 react-frontend 的 Step06/Step07 学习前后端协作
# 使用方法：uv run python react-backend.py
# 进阶说明：生产环境用数据库（SQLAlchemy + PostgreSQL），见 Step14-15
# 常用配套函数：无（独立演示后端）
# ==============================================

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

# ==============================================
# 数据模型
# 【基础】Pydantic 模型定义请求参数和响应结构
# ==============================================

class UserCreate(BaseModel):
    """创建用户的请求体"""
    username: str
    email: str
    full_name: str = ""
    password: str


class UserUpdate(BaseModel):
    """更新用户的请求体（所有字段可选）"""
    username: str | None = None
    email: str | None = None
    full_name: str | None = None
    password: str | None = None


class UserResponse(BaseModel):
    """返回给前端的用户数据（不包含密码）"""
    id: int
    username: str
    email: str
    full_name: str | None = None


# ==============================================
# 内存数据存储（演示用，重启丢失）
# 【基础】用列表模拟数据库，方便学习
# ==============================================
fake_db: list[dict] = [
    {"id": 1, "username": "zhangsan", "email": "zhangsan@mail.com", "full_name": "张三", "password": "123"},
    {"id": 2, "username": "lisi", "email": "lisi@mail.com", "full_name": "李四", "password": "123"},
]
next_id = 3

# ==============================================
# FastAPI 应用
# ==============================================
app = FastAPI(
    title="LearnFast React Demo API",
    description="配套 React 前端学习的简易 CRUD 后端",
    version="1.0.0",
)

# CORS 中间件：允许 React 开发服务器跨域请求
# 【基础】如果不加这个，浏览器会拦截前端对后端的请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React 开发服务器地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==============================================
# CRUD API 路由
# ==============================================

@app.get("/api/users/", response_model=list[UserResponse], tags=["users"])
def list_users():
    """获取所有用户列表"""
    return fake_db


@app.get("/api/users/{user_id}", response_model=UserResponse, tags=["users"])
def get_user(user_id: int):
    """根据 ID 获取单个用户"""
    user = next((u for u in fake_db if u["id"] == user_id), None)
    if not user:
        raise HTTPException(status_code=404, detail=f"用户 {user_id} 不存在")
    return user


@app.post("/api/users/", response_model=UserResponse, status_code=201, tags=["users"])
def create_user(body: UserCreate):
    """创建新用户"""
    global next_id
    new_user = {
        "id": next_id,
        "username": body.username,
        "email": body.email,
        "full_name": body.full_name,
        "password": body.password,
    }
    next_id += 1
    fake_db.append(new_user)
    return new_user


@app.put("/api/users/{user_id}", response_model=UserResponse, tags=["users"])
def update_user(user_id: int, body: UserUpdate):
    """更新用户信息（部分更新）"""
    user = next((u for u in fake_db if u["id"] == user_id), None)
    if not user:
        raise HTTPException(status_code=404, detail=f"用户 {user_id} 不存在")
    # 只更新传入的字段（部分更新）
    if body.username is not None:
        user["username"] = body.username
    if body.email is not None:
        user["email"] = body.email
    if body.full_name is not None:
        user["full_name"] = body.full_name
    if body.password is not None:
        user["password"] = body.password
    return user


@app.delete("/api/users/{user_id}", status_code=204, tags=["users"])
def delete_user(user_id: int):
    """删除用户"""
    global fake_db
    user = next((u for u in fake_db if u["id"] == user_id), None)
    if not user:
        raise HTTPException(status_code=404, detail=f"用户 {user_id} 不存在")
    fake_db = [u for u in fake_db if u["id"] != user_id]
    # 204 No Content：删除成功但不返回内容


@app.get("/api/info", tags=["info"])
def app_info():
    """应用信息（Step 06 预设示例使用）"""
    return {"name": "LearnFast React Demo", "version": "1.0.0", "users_count": len(fake_db)}


if __name__ == "__main__":
    uvicorn.run("react-backend:app", host="127.0.0.1", port=8000, reload=True)
