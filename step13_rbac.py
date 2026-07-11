# ==============================================
# 文件名：step13_rbac.py
# 基础功能：学习基于角色的访问控制（RBAC）— 角色枚举、权限装饰器、依赖组合
# 核心学习知识点：
#   1. RBAC 三要素 — 用户（User）→ 角色（Role）→ 权限（Permission）
#   2. Role Enum — Python 枚举定义系统角色层级
#   3. 权限依赖链 — 认证 + 角色检查的多层守卫
#   4. 自定义 PermissionChecker 类 — 面向对象的权限验证
#   5. require_role() 工厂函数 — 动态生成角色守卫依赖
#   6. 函数式 vs 类式权限守卫 — 两种模式的对比
#   7. RBAC vs OAuth2 Scopes — 角色（粗粒度）vs 作用域（细粒度），实际项目两者结合使用
#   8. ABAC（基于属性的访问控制）简介 — 比 RBAC 更灵活的下一代权限模型
# 适用场景：后台管理系统、SaaS 多租户权限、企业级应用的权限体系
# 使用方法：
#   终端运行：uv run python step13_rbac.py
#   浏览器访问 http://127.0.0.1:8000/docs 测试
#   测试账号：admin/secret | editor/edit123 | viewer/view123
# 进阶说明：
#   1. RBAC 是工业界最成熟的权限模型，90% 的应用场景都能覆盖
#   2. Scopes（Step12）= 原子操作权限（read/write/delete），角色 = Scopes 的组合
#      admin 角色 = [read, write, delete] scopes
#      editor 角色 = [read, write] scopes
#      viewer 角色 = [read] scopes
#   3. 权限设计的最佳时机是项目初期，后期改造的成本呈指数增长
#   4. ABAC 模型用"属性条件"代替"角色": "部门=技术部 AND 职级≥P7" → 可编辑配置
#      比 RBAC 灵活但实现更复杂，适合高度动态的权限场景
# 常用配套函数：
#   Depends(require_role("admin"))          — 角色守卫依赖
#   Security(func, scopes=[...])            — Scope + 角色组合
#   functools.wraps(func)                   — 保持被装饰函数的元信息
#   typing.Protocol                         — 定义权限检查器的接口协议（面向接口编程）
#   pydantic.BaseModel + model_validator    — 声明式权限规则校验
# ==============================================
import uvicorn
from enum import Enum

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel


app = FastAPI(
    title="LearnFast API — RBAC 权限系统",
    description="FastAPI 学习 Step13：角色枚举、权限依赖链、RBAC 模式实战",
    version="0.1.0",
)


# ==============================================
# 角色定义
# 【基础】Python Enum 定义系统角色，值越大的权限越高
# 【进阶】角色枚举替代魔法字符串（"admin" vs Role.ADMIN），编译器能帮我们检查错误
#   角色层级由业务决定，这里 admin > editor > viewer
#   层级关系在 compare_roles() 函数中实现，不依赖枚举值的数值大小
# ==============================================


class Role(str, Enum):
    """
    用户角色枚举。
    双重继承 (str, Enum) 确保能直接用于 JSON 序列化和字符串比较。
    """
    ADMIN = "admin"     # 管理员：全部权限
    EDITOR = "editor"   # 编辑者：读写权限
    VIEWER = "viewer"   # 浏览者：只读权限


# 【基础】角色层级：每个角色能操作"自己及以下所有角色"的资源
#   比如：admin 能管理 viewer 的数据，而 viewer 只能看自己的数据
# 【进阶】这种层级设计在组织结构中很常见（上级管理下级的数据）
ROLE_HIERARCHY = {
    Role.ADMIN: 3,   # 最高权限等级
    Role.EDITOR: 2,  # 中等权限等级
    Role.VIEWER: 1,  # 最低权限等级
}


def has_role(user_role: Role, required_role: Role) -> bool:
    """
    【基础功能】检查用户的角色权限等级是否 ≥ 所需等级
    【学习知识点】
        1. 角色层级判断 — 高等级角色自动拥有低等级角色的权限
        2. ROLE_HIERARCHY 字典 — 用数值映射角色等级（比 if-elif 更易扩展）
    """
    return ROLE_HIERARCHY.get(user_role, 0) >= ROLE_HIERARCHY.get(required_role, 0)


# ==============================================
# 配置区
# ==============================================
SECRET_KEY = "learnfast-demo-secret-key-rbac-2026"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")


# ==============================================
# 模拟用户数据库（含角色字段）
# ==============================================
fake_users_db = {
    "admin": {
        "username": "admin",
        "full_name": "系统管理员",
        "role": Role.ADMIN,
        "hashed_password": pwd_context.hash("secret"),
        "disabled": False,
    },
    "editor": {
        "username": "editor",
        "full_name": "内容编辑",
        "role": Role.EDITOR,
        "hashed_password": pwd_context.hash("edit123"),
        "disabled": False,
    },
    "viewer": {
        "username": "viewer",
        "full_name": "访客",
        "role": Role.VIEWER,
        "hashed_password": pwd_context.hash("view123"),
        "disabled": False,
    },
}


# ==============================================
# 模型
# ==============================================
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


class TokenData(BaseModel):
    username: str | None = None
    role: Role | None = None


class User(BaseModel):
    username: str
    full_name: str | None = None
    role: Role
    disabled: bool


class UserInDB(User):
    hashed_password: str


# ==============================================
# JWT 工具
# ==============================================


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_user(username: str):
    if username in fake_users_db:
        return UserInDB(**fake_users_db[username])
    return None


def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user or not pwd_context.verify(password, user.hashed_password):
        return None
    return user


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    【基础功能】认证依赖：验证 token，返回当前用户
    这是"认证层"，只认 token 有效性，不检查权限
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭证",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role_str: str = payload.get("role", "viewer")
        if username is None:
            raise credentials_exception
        role = Role(role_str)  # 字符串转枚举
        token_data = TokenData(username=username, role=role)
    except (JWTError, ValueError):
        raise credentials_exception

    user = get_user(token_data.username)
    if user is None:
        raise credentials_exception
    if user.disabled:
        raise HTTPException(status_code=400, detail="用户已被禁用")
    return User(username=user.username, full_name=user.full_name, role=user.role, disabled=user.disabled)


# ==============================================
# RBAC 权限守卫 — 三种实现方式
# ==============================================


# --- 方式 1：require_role() 工厂函数 ---
# 【基础】require_role("admin") 返回一个专门的依赖函数，检查当前用户是否为 admin
#         这是一个"闭包"（closure）— 函数内返回另一个函数，内层函数访问外层的 required_role
# 【进阶】工厂函数模式（Factory Function Pattern）：
#   外层 require_role(required_role) 接收参数 → 返回内层 _role_checker
#   内层 _role_checker 是一个 Depends 兼容的函数（接收并调用 get_current_user）
#   每次调用 require_role("admin") 都创建一个新的闭包实例
# 优点：声明式、一行搞定、可读性好
# 缺点：每个路由创建一个新闭包（轻微性能开销，但可以忽略）
def require_role(required_role: Role):
    """
    工厂函数：根据要求的角色生成一个 FastAPI 依赖函数。
    用法：@app.get("/admin/", dependencies=[Depends(require_role(Role.ADMIN))])

    参数：
        required_role: 访问此路由所需的最低角色
    返回值：一个 Depends 兼容的依赖函数
    """
    async def role_checker(current_user: User = Depends(get_current_user)):
        """内层函数（闭包）：检查当前用户是否有 required_role 权限"""
        if not has_role(current_user.role, required_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"权限不足：需要 {required_role.value} 或更高角色，当前为 {current_user.role.value}",
            )
        return current_user  # 检查通过，返回用户对象给路由函数
    return role_checker


# --- 方式 2：类式权限检查器 ---
# 【基础】PermissionChecker 是一个可调用的类实例
#         Depends(PermissionChecker(Role.ADMIN)) → 创建实例，框架调用其 __call__ 方法
# 【进阶】Callable 类模式 vs 工厂函数模式：
#   工厂函数 — 轻量，适合简单场景
#   可调用类 — 可扩展（加属性/方法），适合复杂权限校验（多条件、日志、缓存等）
#   本示例中类式还记录了 access_count，演示了类的状态保持能力
class PermissionChecker:
    """
    可调用的权限检查器类。
    实例化时指定最低角色要求，调用时执行权限检查。
    相比工厂函数，类可以携带更多上下文和状态。
    """

    def __init__(self, required_role: Role):
        self.required_role = required_role
        # 【进阶】类可以维护状态——本示例记录检查次数（实际项目可记录审计日志）
        self.access_count = 0

    async def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        """
        当 Depends(PermissionChecker(Role.ADMIN)) 时，
        FastAPI 会调用这个 __call__ 方法，并注入 Depends(get_current_user) 的结果。
        """
        self.access_count += 1
        if not has_role(current_user.role, self.required_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"权限不足：需要 {self.required_role.value} 或更高角色",
            )
        return current_user


# --- 方式 3：路由级别声明（dependencies 参数）---
# 【基础】dependencies=[Depends(require_role(Role.ADMIN))] 在装饰器中声明
#         路径函数不需要接收 current_user 参数
#         适合"只需要校验不需要使用用户信息"的场景
# 【进阶】dependencies 参数不传返回值给路径函数！
#   如果需要 user 对象，还是要在函数签名中声明 Depends(...)
#   dependencies 列表中的依赖纯粹是"门卫"（guard），执行后丢弃返回值


# ==============================================
# 路由区
# ==============================================


@app.post("/token", response_model=Token, tags=["auth"])
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """登录并返回含角色信息的 JWT"""
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误",
                            headers={"WWW-Authenticate": "Bearer"})

    access_token = create_access_token(
        data={"sub": user.username, "role": user.role.value}
    )
    return Token(access_token=access_token, token_type="bearer", role=user.role.value)


@app.get("/me/", tags=["users"])
async def read_own_profile(current_user: User = Depends(get_current_user)):
    """获取个人信息（任何已登录用户）"""
    return {"user": current_user}


# --- 读者接口（viewer+）---
@app.get("/articles/", tags=["articles"])
async def list_articles(
    current_user: User = Depends(require_role(Role.VIEWER)),  # 方式1：工厂函数
):
    """查看文章列表（需要 viewer 及以上角色）"""
    return {
        "articles": [{"id": 1, "title": "FastAPI 入门"}, {"id": 2, "title": "RBAC 权限设计"}],
        "accessed_by": current_user.username,
        "role": current_user.role,
    }


# --- 编辑者接口（editor+）---
@app.post("/articles/", tags=["articles"])
async def create_article(
    current_user: User = Depends(require_role(Role.EDITOR)),
):
    """创建文章（需要 editor 及以上角色）"""
    return {"message": "文章创建成功", "author": current_user.username}


@app.put("/articles/{article_id}", tags=["articles"])
async def update_article(
    article_id: int,
    checker: PermissionChecker = Depends(PermissionChecker(Role.EDITOR)),  # 方式2：类式
):
    """编辑文章（需要 editor 及以上，使用类式权限检查器）"""
    return {
        "message": f"文章 {article_id} 已更新",
        "access_count": checker.access_count,  # 演示类的状态
    }


# --- 管理员接口（admin only）---
@app.delete("/articles/{article_id}", tags=["articles"])
async def delete_article(
    article_id: int,
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    """删除文章（需要 admin 角色）"""
    return {"message": f"文章 {article_id} 已删除", "operator": current_user.username}


# --- 使用 dependencies 参数声明路由级守卫 ---
@app.get(
    "/admin/dashboard/",
    tags=["admin"],
    dependencies=[Depends(require_role(Role.ADMIN))],  # 方式3：路由级声明
)
async def admin_dashboard():
    """
    管理后台统计（仅 admin 可访问）。
    注意：函数签名中没有 current_user，因为 dependencies 守卫不传返回值。
    """
    return {
        "dashboard": "系统管理后台",
        "stats": {
            "total_users": len(fake_users_db),
            "roles": {r.value: sum(1 for u in fake_users_db.values() if u["role"] == r)
                       for r in Role},
        },
    }


# --- 角色感知接口 ---
@app.get("/users/", tags=["users"])
async def list_users(current_user: User = Depends(get_current_user)):
    """
    查看用户列表 — 根据角色返回不同的数据量。
    admin 看全部，editor 看非管理员，viewer 只看自己。
    演示了"同一个接口，不同角色看到不同结果"的 RBAC 模式。
    """
    if current_user.role == Role.ADMIN:
        # admin 看所有用户和完整信息
        users = [
            {"username": u["username"], "full_name": u["full_name"], "role": u["role"].value}
            for u in fake_users_db.values()
        ]
    elif current_user.role == Role.EDITOR:
        # editor 看除 admin 外的用户（但隐藏敏感字段）
        users = [
            {"username": u["username"], "role": u["role"].value}
            for u in fake_users_db.values() if u["role"] != Role.ADMIN
        ]
    else:
        # viewer 只能看到自己
        users = [{"username": current_user.username, "role": current_user.role.value}]

    return {"users": users, "visible_to": current_user.role.value}


# ==============================================
# 程序入口
# ==============================================
if __name__ == "__main__":
    uvicorn.run(
        "step13_rbac:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )
