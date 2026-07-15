# ==============================================
# 文件名：step12_oauth2_scopes.py
# 基础功能：学习 OAuth2 作用域（Scopes）机制 — Security()、细粒度权限控制
# 核心学习知识点：
#   1. Security() vs Depends() — Security 继承自 Depends，额外支持 scopes
#   2. OAuth2 scopes 概念 — "读权限"、"写权限"等细粒度授权
#   3. SecurityRequirement — OpenAPI 文档中自动标记哪些接口需要哪些权限
#   4. Security() 的 scopes 参数 — 声明此依赖需要的作用域
#   5. 权限检查依赖链 — 认证 + 作用域验证的组合守卫
#   6. OAuth2PasswordRequestForm.scopes — 客户端请求的权限范围
#   7. /docs 中的 OAuth2 授权弹窗 — 可视化选权限、获取 token
# 适用场景：第三方 API 授权（"允许访问相册但禁止发帖"）、微服务权限体系
# 使用方法：
#   终端运行：uv run python step12_oauth2_scopes.py
#   浏览器访问 http://127.0.0.1:8000/docs — 点锁图标选择 scopes 后登录测试
# 进阶说明：
#   1. OAuth2 Scopes 是 OAuth2 规范（RFC 6749）的标准概念，不是 FastAPI 独有的
#   2. 在 Google/微信/GitHub 等第三方登录中，"scopes" 就是用户同意的权限范围
#   3. 本步骤的 scopes 是"功能作用域"（读用户/写用户/删除），Step13 的 RBAC 是"角色作用域"
#   4. Scopes 和 Roles 的关系：Scopes = 原子操作权限，Roles = 一组 scopes 的集合
#      e.g. admin 角色 = [read, write, delete] 全部 scopes
# 常用配套函数：
#   Security(Depends(func), scopes=["..."])) — 声明作用域依赖
#   OAuth2PasswordRequestForm(scopes={})      — 客户端请求的作用域列表
#   OAuth2PasswordBearer + scopes             — Bearer token + 作用域绑定
#   Depends(get_current_user)                 — 基础认证（无作用域检查）
#   Security(get_current_user, scopes=[...])  — 认证 + 作用域检查（组合）
# ==============================================
import uvicorn
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, Depends, HTTPException, status, Security
from fastapi.security import (
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm,
    SecurityScopes,
)
from jose import JWTError, jwt
import bcrypt
from pydantic import BaseModel


app = FastAPI(
    title="LearnFast API — OAuth2 Scopes",
    description="FastAPI 学习 Step12：Security() 作用域、细粒度权限、OAuth2 授权弹窗",
    version="0.1.0",
)


# ==============================================
# 配置区
# ==============================================
SECRET_KEY = "learnfast-demo-secret-key-change-in-production-2026"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# 【进阶】使用 bcrypt 直接操作，不再通过 passlib（passlib 与新版 bcrypt 不兼容）
#   bcrypt.hashpw(明文.encode(), bcrypt.gensalt()).decode() → 生成哈希密码
#   bcrypt.checkpw(明文.encode(), 哈希.encode()) → 校验密码是否正确

# 【基础】定义本应用支持的 OAuth2 作用域
#   key=权限代码，value=权限说明
#   /docs 的 OAuth2 弹窗中会以复选框显示这些作用域
# 【进阶】Scopes 设计原则：
#   1. 命名规范：用动词+资源，如 "items:read"（替代简单的 "read"）
#   2. 粒度适中：太大没用（只有一个 "all"），太小繁琐（每个字段一个 scope）
#   3. 层级命名：如 "users:read" / "users:write" / "users:delete"
#   4. 虽然 scopes 可以任意定义，但必须和服务器端校验逻辑一致
SCOPES = {
    "users:read": "查看用户信息",
    "users:write": "修改用户信息",
    "users:delete": "删除用户",
    "items:read": "查看商品信息",
    "items:write": "创建/修改商品",
    "admin": "管理员全部权限",
}

# 【基础】OAuth2PasswordBearer 的 scopes 参数匹配上面定义的 SCOPES dict
#   auto_error=False → token 缺失时不自动抛 401，由下游的 Security scopes 检查处理
#   auto_error=True（默认）→ token 缺失立即 401，作用域检查还没执行
# 【进阶】auto_error=False 的使用场景：
#   - 需要区分"没 token"和"有 token 但权限不够"（前者提示登录，后者提示无权限）
#   - 可选认证的接口（登录可见更多，未登录也可见基础内容）
#   auto_error=True → 简单直接，适用大多数场景
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/token",
    scopes=SCOPES,  # 定义了可用的作用域列表
)


# ==============================================
# 模拟用户数据库 — 每个用户有不同的 scopes
# ==============================================
fake_users_db = {
    "admin": {
        "username": "admin",
        "full_name": "管理员",
        "hashed_password": bcrypt.hashpw("secret".encode(), bcrypt.gensalt()).decode(),
        # 【基础】admin 拥有全部 scopes
        "scopes": ["users:read", "users:write", "users:delete", "items:read", "items:write", "admin"],
        "disabled": False,
    },
    "editor": {
        "username": "editor",
        "full_name": "编辑者",
        "hashed_password": bcrypt.hashpw("editor123".encode(), bcrypt.gensalt()).decode(),
        # 【基础】editor 有读写权限，但不能删除
        "scopes": ["users:read", "items:read", "items:write"],
        "disabled": False,
    },
    "viewer": {
        "username": "viewer",
        "full_name": "只读用户",
        "hashed_password": bcrypt.hashpw("viewer123".encode(), bcrypt.gensalt()).decode(),
        # 【基础】viewer 只有查看权限
        "scopes": ["users:read", "items:read"],
        "disabled": False,
    },
}


# ==============================================
# 模型
# ==============================================
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    scopes: list[str]  # 返回给客户端当前 token 携带的 scopes


class TokenData(BaseModel):
    username: str | None = None
    scopes: list[str] = []


class User(BaseModel):
    username: str
    full_name: str | None = None
    disabled: bool
    scopes: list[str]


class UserInDB(User):
    hashed_password: str


# ==============================================
# 工具函数
# ==============================================


def get_user(username: str) -> UserInDB | None:
    if username in fake_users_db:
        return UserInDB(**fake_users_db[username])
    return None


def verify_password(plain_password, hashed_password):
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def authenticate_user(username: str, password: str) -> UserInDB | None:
    user = get_user(username)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# ==============================================
# 认证依赖（带作用域检查）
# ==============================================


async def get_current_user(
    security_scopes: SecurityScopes,  # 【基础】SecurityScopes 包含路由需要的作用域列表
    token: str = Depends(oauth2_scheme),
) -> User:
    """
    【基础功能】认证依赖 + 作用域校验
    验证 token 有效 → 检查 token 中的 scopes 是否覆盖路由要求的作用域
    【学习知识点】
        1. SecurityScopes — FastAPI 注入，包含当前路由要求的 scopes 列表
        2. token scopes vs route scopes — 用户的权限 vs 路由所需的权限
        3. scope 检查逻辑 — 路由要求的所有 scope 用户都必须拥有

    参数：
        security_scopes: 【基础释义：路由所需的作用域列表（由 Security(scopes=[]) 指定）】
        token: 【基础释义：Bearer token 字符串】
    """
    if security_scopes.scopes:
        # 【基础】路由要求至少一个 scope 时，拼出 "Bearer scope=..." 的认证头
        #   这是 OAuth2 RFC 的要求：401 响应需指明需要哪些 scopes
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = "Bearer"

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭证",
        headers={"WWW-Authenticate": authenticate_value},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_scopes: list[str] = payload.get("scopes", [])
        token_data = TokenData(username=username, scopes=token_scopes)
    except JWTError:
        raise credentials_exception

    user = get_user(token_data.username)
    if user is None:
        raise credentials_exception

    # 【基础】核心：检查 token 中的 scopes 是否包含路由要求的所有 scopes
    #   security_scopes.scopes = 路由 Security(scopes=["items:write"]) 中声明的 ["items:write"]
    #   token_scopes = 签发时放入 JWT 的用户拥有的 scopes
    #   set(token_scopes) >= set(security_scopes.scopes) → 用户拥有的权限 ≥ 路由需要的权限
    for scope in security_scopes.scopes:
        if scope not in token_data.scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"权限不足，需要作用域: {scope}",
                headers={"WWW-Authenticate": authenticate_value},
            )

    return User(
        username=user.username,
        full_name=user.full_name,
        disabled=user.disabled,
        scopes=user.scopes,
    )


# ==============================================
# 路由
# ==============================================


@app.post("/token", response_model=Token, tags=["auth"])
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    """
    【基础功能】OAuth2 密码模式登录，签发带 scopes 的 JWT
    【学习知识点】
        1. form_data.scopes → 客户端请求的权限范围（用户在 /docs 弹窗中勾选的 scopes）
        2. 实际签发 = 用户拥有的 scopes ∩ 请求的 scopes（取交集，防越权）
        3. 如果用户没请求 scope，默认给用户拥有的全部 scopes
    【Swagger 测试步骤】
        1. 访问 /docs → 点击右上角锁图标（Authorize）
        2. 勾选 1-2 个 scopes → 用 admin/secret 登录
        3. 登录后尝试访问不同权限等级的路由
    """
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    # 【基础】确定要签发的 scopes：用户请求的 ∩ 用户实际拥有的
    if form_data.scopes:
        # 取交集：只给用户请求的 AND 用户实际拥有的
        granted_scopes = [s for s in form_data.scopes if s in user.scopes]
    else:
        # 用户没指定 scopes → 给全部权限
        granted_scopes = user.scopes

    access_token = create_access_token(
        data={"sub": user.username, "scopes": granted_scopes}
    )

    return Token(access_token=access_token, token_type="bearer", scopes=granted_scopes)


# --- 不同权限等级的受保护路由 ---


@app.get("/users/", tags=["users"])
async def list_users(
    current_user: User = Security(  # Security() 替代 Depends() 并声明 scopes
        get_current_user,
        scopes=["users:read"],  # ← 这个路由需要 users:read 权限
    ),
):
    """
    【基础功能】查看所有用户（需要 users:read 权限）
    viewer 用户可以访问，因为没有更高级的 scope 要求
    """
    return {
        "users": [
            {"username": u["username"], "full_name": u["full_name"], "scopes": u["scopes"]}
            for u in fake_users_db.values()
        ],
        "accessed_by": current_user.username,
    }


@app.put("/users/{username}", tags=["users"])
async def update_user(
    username: str,
    current_user: User = Security(
        get_current_user,
        scopes=["users:write"],  # ← 需要 users:write 权限
    ),
):
    """
    【基础功能】修改用户信息（需要 users:write 权限）
    viewer 用户访问 → 403 Forbidden
    editor/admin 用户可以访问
    """
    return {
        "message": f"用户 {username} 信息已更新",
        "updated_by": current_user.username,
    }


@app.delete("/users/{username}", tags=["users"])
async def delete_user(
    username: str,
    current_user: User = Security(
        get_current_user,
        scopes=["users:delete"],  # ← 需要 users:delete 权限
    ),
):
    """
    【基础功能】删除用户（需要 users:delete 权限）
    只有 admin 用户可以访问
    """
    return {
        "message": f"用户 {username} 已删除",
        "deleted_by": current_user.username,
    }


@app.get("/items/", tags=["items"])
async def list_items(
    current_user: User = Security(get_current_user, scopes=["items:read"]),
):
    """查看商品列表（需要 items:read 权限，所有用户都有）"""
    return {
        "items": [{"id": 1, "name": "键盘"}, {"id": 2, "name": "鼠标"}],
        "viewed_by": current_user.username,
    }


@app.post("/items/", tags=["items"])
async def create_item(
    current_user: User = Security(get_current_user, scopes=["items:write"]),
):
    """
    【基础功能】创建商品（需要 items:write 权限）
    viewer 无此权限 → 403
    """
    return {"message": "商品创建成功", "created_by": current_user.username}


@app.get("/admin/", tags=["admin"])
async def admin_panel(
    current_user: User = Security(get_current_user, scopes=["admin"]),
):
    """
    【基础功能】管理后台（需要 admin 权限）
    只有 admin 可以访问，editor 虽有多个 scope 但没有 admin scope → 403
    """
    return {"message": f"欢迎 {current_user.username} 进入管理后台"}


@app.get("/me/", tags=["users"])
async def read_own_profile(
    current_user: User = Depends(get_current_user),  # 不声明 scopes → 只验证登录
):
    """
    【基础功能】查看自己的信息（只需登录，不需要特定 scope）
    任何有效 token 都可以访问
    """
    return {"user": current_user}


# ==============================================
# 程序入口
# ==============================================
if __name__ == "__main__":
    uvicorn.run(
        "step12_oauth2_scopes:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )
