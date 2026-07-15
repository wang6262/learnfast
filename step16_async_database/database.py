# ==============================================
# 文件名：step16_async_database/database.py
# 基础功能：异步 SQLAlchemy 引擎 + asyncpg 驱动 + 异步会话管理
# 核心学习知识点：
#   1. create_async_engine() — 异步引擎（vs 同步 create_engine）
#   2. async_sessionmaker() — 异步会话工厂
#   3. AsyncSession — 异步数据库会话类
#   4. asyncpg — PostgreSQL 的高性能异步驱动（纯 Python，asyncio 原生）
#   5. async get_db() — 异步 yield 依赖
#   6. async with — 异步上下文管理器
# ==============================================
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base

# 【基础】异步连接字符串：postgresql+asyncpg://（驱动改为 asyncpg）
# 【进阶】asyncpg vs psycopg2 对比：
#   asyncpg — 纯 Python asyncio 驱动，性能极高（准备语句缓存、二进制协议）
#   psycopg2 — C 扩展同步驱动，Python 生态最成熟
#   选择：异步路由（async def）用 asyncpg，同步路由用 psycopg2
DATABASE_URL = "postgresql+asyncpg://postgres:123456@localhost:5432/learnfast"

# 【基础】create_async_engine 创建异步引擎
# 【进阶】async engine 内部使用 asyncio 连接池，不用传统的 QueuePool
engine = create_async_engine(
    DATABASE_URL,
    echo=True,        # 打印 SQL（学习用）
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
)

# 【基础】async_sessionmaker 创建异步会话工厂
# 【进阶】expire_on_commit=False → commit 后不使 ORM 对象过期（异步环境常用）
#   否则 commit 后访问对象属性会触发隐式查询（异步中不安全）
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()


# 【基础】异步版 get_db() — async def + async yield
# 【进阶】异步 yield 依赖的使用：
#   路由函数声明 async def，必须用 AsyncSession（不能混用 sync Session）
#   await db.execute() 替代 db.query()（SQLAlchemy 2.0 推荐写法）
async def get_db():
    """异步数据库会话的 FastAPI 依赖"""
    async with AsyncSessionLocal() as db:
        try:
            yield db
        finally:
            await db.close()  # 异步关闭连接
