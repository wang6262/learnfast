# ==============================================
# 文件名：step11_jwt_auth.py
# 基础功能：学习 JWT 令牌认证的完整流程：签发、验证、密码哈希、Bearer 提取
# 核心学习知识点：
#   1. JWT 三段式结构 — header.payload.signature，Base64 编码，点分隔
#   2. HS256 对称签名 — 同一密钥签发和验证，适合单服务/内部服务
#   3. python-jose 库 — JWT 签发 jwt.encode()、验证 jwt.decode()
#   4. passlib[bcrypt] — 密码哈希（不可逆）、校验哈希对比
#   5. OAuth2PasswordBearer — 标准化的 Bearer Token 提取器
#   6. access token vs refresh token — 短期 token（15-60分钟）+ 长期 token（7-30天）
#   7. token 过期处理 — exp 声明 + jwt.decode() 自动检查过期时间
#   8. Depends 守卫 — 认证依赖保护路由，未认证自动 401
# 适用场景：用户登录认证、API 鉴权、单点登录（SSO）、微服务间认证
# 使用方法：
#   终端运行：uv run python step11_jwt_auth.py
#   浏览器访问 http://127.0.0.1:8000/docs 交互式测试
#   步骤：1. POST /token 获取 token → 2. 点锁图标粘贴 token → 3. 访问受保护接口
# 进阶说明：
#   1. JWT 是无状态认证方案 — 服务器不存 session，完全靠 token 自身携带信息
#      优点：水平扩展友好（任何服务器都能验证），适合微服务架构
#      缺点：无法主动失效（token 发出后有效期内的风险窗口）
#   2. RS256（非对称签名）比 HS256 更安全：私钥签发、公钥验证，适合多服务
#   3. JWT 的 payload 只是 Base64 编码，不是加密！任何人都可以解码看到内容
#      所以绝不能在 payload 中放密码等敏感信息（可用 JWE 加密，但更复杂）
#   4. 生产环境务必使用强密钥（至少 256 位随机字符串），并定期轮换
# 常用配套函数：
#   jwt.encode(claims, key, algorithm)   — 签发 JWT
#   jwt.decode(token, key, algorithms)   — 验证并解码 JWT
#   passlib.hash(password)              — bcrypt 密码哈希
#   passlib.verify(password, hash)      — 验证密码是否正确
#   OAuth2PasswordBearer(tokenUrl=)     — 从 Authorization 头提取 Bearer token
#   Depends(oauth2_scheme)              — 在依赖中提取 token
#   HTTPException(status_code=401)      — 认证失败的标准响应
#   datetime.utcnow() + timedelta()     — 设置 token 过期时间
# ==============================================
import uvicorn
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt  # JWT 操作库（python-jose）
import bcrypt  # 密码哈希库（直接使用 bcrypt，不再通过 passlib）
from pydantic import BaseModel


app = FastAPI(
    title="LearnFast API — JWT 认证",
    description="FastAPI 学习 Step11：JWT 签发验证、密码哈希、Bearer Token 保护路由、令牌刷新",
    version="0.1.0",
)


# ==============================================
# 配置区：JWT 和密码哈希的全局配置
# 【基础】所有魔法数字和密钥集中在此，方便管理和修改
# 【进阶】生产环境密钥应从环境变量或密钥管理服务（Vault）读取
#   密钥生成方法（终端）：openssl rand -hex 32
#   输出 64 个字符的随机十六进制字符串
# ==============================================

# JWT 签名密钥 — 生产环境必须换成强随机密钥且保密！
SECRET_KEY = "learnfast-demo-secret-key-change-in-production-2026"
ALGORITHM = "HS256"  # 签名算法：HS256 = HMAC-SHA256
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # 访问令牌 30 分钟过期
REFRESH_TOKEN_EXPIRE_DAYS = 7    # 刷新令牌 7 天过期

# 【基础】CryptContext 管理密码哈希策略
#   schemes=["bcrypt"] → 使用 bcrypt 算法
#   deprecated="auto" → 自动处理已废弃的旧哈希（迁移场景）
# 【进阶】bcrypt 原理：对明文密码加盐（salt）后多次哈希运算（成本因子 rounds）
#   每次运行 bcrypt.hash("相同的密码") 会产生不同的结果（因为随机盐）
#   所以密码比对不能用哈希值直接相等判断，必须用 verify() 方法
#   成本因子默认 12（2^12 = 4096 次迭代），平衡安全性和性能
# 【进阶】使用 bcrypt 直接操作，不再通过 passlib（passlib 与新版 bcrypt 不兼容）
#   bcrypt.gensalt() — 生成随机盐（默认 rounds=12，即 2^12 次迭代）
#   bcrypt.hashpw(pwd, salt) — 对密码加盐哈希，返回 bytes
#   bcrypt.checkpw(pwd, hashed) — 验证明文密码与哈希是否匹配

# 【基础】OAuth2PasswordBearer 是标准的 Bearer Token 提取器
#   tokenUrl="/token" → 告诉 Swagger 去哪个接口获取 token
#   当用户在 Swagger 中点击锁图标并登录时，自动调用 /token
# 【进阶】OAuth2PasswordBearer 的工作流程：
#   1. 从请求头提取：Authorization: Bearer <token_value>
#   2. 校验格式：必须以 "Bearer " 开头
#   3. 提取 token 部分返回给依赖函数
#   4. 如果头不存在或格式错误，自动返回 401
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")


# ==============================================
# 模拟用户数据库
# 【基础】真实项目这里连接 PostgreSQL 等数据库
# 【进阶】密码存储的是哈希值，不是明文！即使数据库泄露，密码也相对安全
#   bcrypt 加盐哈希的特性：相同密码 → 不同哈希 → 无法用彩虹表破解
#   但 bcrypt 不能防御暴力破解（如字典攻击），需要配合速率限制
# ==============================================
fake_users_db = {
    "admin": {
        "username": "admin",
        "full_name": "管理员",
        "email": "admin@learnfast.dev",
        # 【基础】"secret" 经 bcrypt 哈希后的结果
        # 【进阶】每次运行 hash("secret") 结果不同，但 verify 都能匹配
        "hashed_password": bcrypt.hashpw("secret".encode(), bcrypt.gensalt()).decode(),
        "role": "admin",
        "disabled": False,
    },
    "user1": {
        "username": "user1",
        "full_name": "普通用户",
        "email": "user1@learnfast.dev",
        "hashed_password": bcrypt.hashpw("password123".encode(), bcrypt.gensalt()).decode(),
        "role": "user",
        "disabled": False,
    },
    # 测试用: 禁用的用户（演示 disabled 字段的用途）
    "banned": {
        "username": "banned",
        "full_name": "被禁用用户",
        "email": "banned@learnfast.dev",
        "hashed_password": bcrypt.hashpw("test".encode(), bcrypt.gensalt()).decode(),
        "role": "user",
        "disabled": True,  # 禁用标记
    },
}


# ==============================================
# 模型定义
# ==============================================
class Token(BaseModel):
    """登录成功后返回的 token 模型"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """从 JWT payload 中解析出的用户数据"""
    username: str | None = None
    role: str | None = None


class User(BaseModel):
    """返回给客户端的用户信息（不含密码）"""
    username: str
    full_name: str | None = None
    email: str | None = None
    role: str
    disabled: bool


class UserInDB(User):
    """数据库内部用户模型（含密码哈希，仅供内部使用）"""
    hashed_password: str


# ==============================================
# 工具函数区
# ==============================================


def get_user(db: dict, username: str) -> UserInDB | None:
    """
    【基础功能】根据用户名从数据库查找用户，返回 UserInDB 或 None
    【学习知识点】
        1. 数据库查询函数 — 封装数据访问逻辑
        2. 类型守卫 — UserInDB | None 给调用者明确的"可能返回 None"的信号
    """
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)
    return None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    【基础功能】验证明文密码是否匹配哈希值
    【学习知识点】
        1. pwd_context.verify() — bcrypt 密码比对，Hash(明文) == 存储的哈希？
        2. 安全设计 — 不能直接用 == 比较密码，因为哈希包含随机盐
        3. 防时序攻击 — verify() 内部使用恒定时间比较法，防止通过响应时间猜测密码
    """
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def authenticate_user(db: dict, username: str, password: str) -> UserInDB | None:
    """
    【基础功能】认证用户：查找用户名 → 校验密码 → 检查禁用状态
    【学习知识点】
        1. 认证三步走 — 查用户 → 验密码 → 查状态（标准流程）
        2. 失败返回 None — 调用方自己判断是否应该 401
        3. 不透露具体失败原因 — 防用户名枚举攻击
    """
    user = get_user(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    【基础功能】签发 JWT access token（访问令牌）
    【学习知识点】
        1. JWT claims（声明）— sub/exp/iat/type 等标准字段
        2. jwt.encode() — 传入 claims + 密钥 + 算法 → 输出 token 字符串
        3. exp 过期时间 — JWT 标准声明，验证时自动检查
        4. timezone.utc — 使用 UTC 时间（国际惯例，避免时区混乱）
    参数：
        data: 【基础释义：要编码到 JWT payload 中的用户数据（sub/role 等）】
        expires_delta: 【基础释义：过期时间间隔，None 使用默认 30 分钟】
    返回值：JWT 字符串（header.payload.signature 三段 Base64 编码）
    调用示例：
        token = create_access_token({"sub": "admin", "role": "admin"})
        # token = "eyJhbGciOi...（三段 Base64，点分隔）"
    """
    to_encode = data.copy()

    # 【基础】设置过期时间
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    # 【基础】向 JWT payload 中添加标准声明
    # sub = subject（主体，通常是用户ID/用户名）
    # exp = expiration（过期时间戳）
    # iat = issued at（签发时间）
    # type = 自定义声明，区分 access_token 和 refresh_token
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access",
    })

    # 【基础】jwt.encode() 三要素：payload + 密钥 + 算法
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """
    【基础功能】签发 JWT refresh token（刷新令牌），有效期比 access token 长
    【学习知识点】
        1. 双令牌模式 — access token（短）+ refresh token（长）
        2. access token 过期后用 refresh token 换新的 access token
        3. type 声明区分 token 类型，防止 access token 用于 refresh 接口
    设计原理：access token 短期有效（30分钟），即使泄露风险窗口也小
        refresh token 长期有效（7天），但只用于刷新接口，暴露面小
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh",
    })
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> TokenData:
    """
    【基础功能】验证并解码 JWT token，返回其中的用户信息
    【学习知识点】
        1. jwt.decode() — 验证签名 + 检查过期 + 解码 payload
        2. JWTError — 签名无效、过期、格式错误都会抛出此异常
        3. 统一异常处理 — 调用方 catch JWTError → 返回 401
    参数：
        token: 【基础释义：JWT 字符串，通常是 Bearer token】
    返回值：TokenData — 从 payload 中提取的 username 和 role
    异常：JWTError — token 无效或过期
    """
    # 【基础】jwt.decode() 验证签名并解码 payload
    #   如果签名不匹配（密钥不同/被篡改）→ 抛 JWTError
    #   如果 exp 已过期 → 抛 ExpiredSignatureError（JWTError 子类）
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

    # 【基础】从 payload 中提取用户信息
    username: str = payload.get("sub")
    role: str = payload.get("role")

    if username is None:
        raise JWTError("Token payload 缺少 sub 声明")

    return TokenData(username=username, role=role)


# ==============================================
# 依赖函数区：认证守卫
# ==============================================


async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserInDB:
    """
    【基础功能】认证守卫依赖 — 从 Bearer token 中解析出当前用户
    任何使用 Depends(get_current_user) 的路由都会先经过此函数的认证检查
    【学习知识点】
        1. 认证依赖模式 — 整个认证逻辑封装在 Depends 中，路由函数干净简洁
        2. 401 错误 — 认证失败的标准 HTTP 状态码
        3. WWW-Authenticate 头 — OAuth2 规范要求 401 响应带此头，告知客户端如何认证
        4. pip install python-multipart — OAuth2PasswordRequestForm 的依赖
    参数：
        token: 【基础释义：OAuth2PasswordBearer 从 Authorization 头提取的 Bearer token】
    返回值：UserInDB — 认证通过的用户对象
    异常：HTTPException(401) — token 无效、过期或用户不存在
    """
    # 凭证异常的统一响应格式
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭证",
        headers={"WWW-Authenticate": "Bearer"},  # OAuth2 规范要求
    )

    try:
        # 【基础】解码 token，提取用户信息
        token_data = decode_token(token)
    except JWTError:
        # 【基础】token 无效或过期 → 401
        raise credentials_exception

    # 【基础】从数据库查找用户
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: UserInDB = Depends(get_current_user),
) -> User:
    """
    【基础功能】在认证基础上额外检查用户是否被禁用
    【学习知识点】
        1. 子依赖链 — get_current_active_user → get_current_user → oauth2_scheme
        2. 多层守卫 — 认证 = 验证身份，授权 = 检查权限+状态
        3. disabled 字段 — 软禁用，保留数据但不允许操作
    """
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="用户已被禁用")
    # 【基础】返回不含密码哈希的 User 模型（安全：密码哈希永不外泄）
    return User(
        username=current_user.username,
        full_name=current_user.full_name,
        email=current_user.email,
        role=current_user.role,
        disabled=current_user.disabled,
    )


async def get_admin_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    【基础功能】管理员权限守卫 — 要求用户角色为 admin
    【学习知识点】
        1. 角色检查 — 在认证依赖基础上叠加权限判断
        2. 403 Forbidden — 已认证但权限不足的标准状态码
        3. 403 vs 401 — 401="你是谁？（未知）"，403="我知道你是谁，但你不配"
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限",
        )
    return current_user


# ==============================================
# 路由定义区
# ==============================================


@app.post("/token", response_model=Token, tags=["auth"])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    【基础功能】用户登录接口，验证用户名密码，返回 access token + refresh token
    此接口对应 oauth2_scheme 中配置的 tokenUrl="/token"
    【学习知识点】
        1. OAuth2PasswordRequestForm — FastAPI 内置的登录表单模型
           - form_data.username → 用户名
           - form_data.password → 密码
           - form_data.scopes → 请求的权限范围（Step12 详解）
        2. 密码验证 → token 签发 → 双令牌返回的标准流程
    参数：
        form_data: 【基础释义：表单中的 username、password、scope 字段】
    返回值：Token — access_token + refresh_token + token_type
    调用示例：
        curl -X POST http://127.0.0.1:8000/token -d "username=admin&password=secret"
        或在 /docs 中点击右上角锁图标，输入 admin/secret 登录
    注意事项：
        OAuth2PasswordRequestForm 要求客户端发送 application/x-www-form-urlencoded 格式
        不能用 JSON 格式发送（和 Form() 参数一样的原因）
    """
    # 【基础】认证用户
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 【基础】签发双令牌
    # 【进阶】access token payload 中放入 sub（用户名）和 role（角色）
    #   这些信息编码在 token 内，无需查数据库就能知道用户是谁
    token_data = {"sub": user.username, "role": user.role}
    access_token = create_access_token(data=token_data)
    refresh_token = create_refresh_token(data=token_data)

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


@app.post("/token/refresh", response_model=Token, tags=["auth"])
async def refresh_access_token(refresh_token: str):
    """
    【基础功能】用 refresh token 换取新的 access token + refresh token（令牌刷新）
    【学习知识点】
        1. 令牌刷新机制 — access token 短期 + 可刷新，兼顾安全性和用户体验
        2. type 声明防御 — 检查 token 类型，防止用 access token 来刷新
    参数：
        refresh_token: 【基础释义：刷新令牌字符串】
    返回值：Token — 新的 access_token + refresh_token 对
    调用示例：
        curl -X POST "http://127.0.0.1:8000/token/refresh?refresh_token=<refresh_token_value>"
    注意事项：
        生产环境的 refresh token 应存储在 HttpOnly Cookie 中（防 XSS），而非 query 参数
    """
    # 【基础】验证 refresh token
    try:
        token_data = decode_token(refresh_token)
    except JWTError:
        raise HTTPException(status_code=401, detail="刷新令牌无效或已过期")

    # 【基础】检查 token type（防止 access token 被用于刷新接口）
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="仅接受 refresh token")
    except JWTError:
        raise HTTPException(status_code=401, detail="刷新令牌无效")

    # 【基础】签发新的令牌对
    new_token_data = {"sub": token_data.username, "role": token_data.role}
    new_access = create_access_token(data=new_token_data)
    new_refresh = create_refresh_token(data=new_token_data)

    return Token(access_token=new_access, refresh_token=new_refresh, token_type="bearer")


# --- 受保护的接口 ---


@app.get("/users/me/", response_model=User, tags=["users"])
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """
    【基础功能】获取当前登录用户的个人信息
    【学习知识点】
        1. Depends(get_current_active_user) 作为路由守卫
        2. 路由函数无需关心认证逻辑，直接使用 current_user
    调用示例：
        curl -H "Authorization: Bearer <access_token>" http://127.0.0.1:8000/users/me/
    """
    return current_user


@app.get("/users/me/items/", tags=["users"])
async def read_own_items(current_user: User = Depends(get_current_active_user)):
    """获取当前用户的专属资源（模拟）"""
    return {
        "owner": current_user.username,
        "items": [
            {"id": 1, "name": f"{current_user.username} 的私人物品1"},
            {"id": 2, "name": f"{current_user.username} 的私人物品2"},
        ],
    }


@app.get("/admin/dashboard/", tags=["admin"])
async def admin_dashboard(admin: User = Depends(get_admin_user)):
    """
    【基础功能】管理员专属接口（需要 admin 角色）
    【学习知识点】
        1. 多层守卫链 — get_admin_user → get_current_active_user → get_current_user
        2. 角色区分 — 普通 user 会得到 403 Forbidden
    调用示例：
        curl -H "Authorization: Bearer <admin_token>" http://127.0.0.1:8000/admin/dashboard/
        curl -H "Authorization: Bearer <user_token>" http://127.0.0.1:8000/admin/dashboard/
        → 403 Forbidden（user1 不是 admin）
    """
    return {
        "dashboard": "管理员控制台",
        "welcome": f"你好，{admin.full_name}（{admin.role}）",
        "stats": {"total_users": len(fake_users_db), "active": True},
    }


# ==============================================
# 程序入口
# ==============================================
if __name__ == "__main__":
    uvicorn.run(
        "step11_jwt_auth:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )
