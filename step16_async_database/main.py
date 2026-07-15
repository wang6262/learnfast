# ==============================================
# 文件名：step16_async_database/main.py
# 基础功能：异步 SQLAlchemy + asyncpg — 异步 CRUD 完整示例
# 核心学习知识点：
#   1. async def 路由 + AsyncSession → 真正的异步 I/O
#   2. await db.execute(select(Model)) → SQLAlchemy 2.0 异步查询
#   3. .scalars().all() → 提取查询结果为模型对象列表
#   4. 异步 vs 同步对比 — asyncpg 在高并发 I/O 场景下性能远优于 psycopg2
#   5. asyncio.gather() 并发多个查询（适合无依赖的并行查询）
#   6. lazy="selectin" — 异步环境推荐的 relationship 加载策略
#   7. 异步引擎启动建表 — run_sync() 在异步引擎中执行同步操作
# 运行方式：uv run python -m step16_async_database.main
# 注意：异步路由中所有数据库操作前都要加 await！
# ==============================================
import uvicorn
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import select, func as sqlfunc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload  # 异步环境的预加载策略

from database import engine, Base, get_db
import models


# ==============================================
# 生命周期：异步启动时自动建表
# 【基础】应用启动时用异步引擎创建数据库表
# 【进阶】lifespan + asynccontextmanager 替代 on_event：
#   - yield 之前 = 启动逻辑，yield 之后 = 关闭逻辑
#   - 支持真正的 async/await，比 on_event 更灵活
# engine.begin() + run_sync() 说明：
#   1. engine.begin() 返回异步连接
#   2. run_sync() → 在异步引擎中执行同步的 create_all
#      （Base.metadata.create_all 是同步的，需要 run_sync 桥接）
# ==============================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("异步数据库表已就绪")
    except Exception as e:
        print(f"[启动失败] 数据库连接异常：{e}")
        print("[提示] 请检查：1) PostgreSQL 是否运行  2) database.py 中连接串是否正确")
        raise  # 重新抛出，让应用启动失败（数据库不可用时没有意义继续运行）
    yield  # 应用运行中


app = FastAPI(
    title="LearnFast API — 异步数据库",
    description="FastAPI 学习 Step16：async SQLAlchemy + asyncpg + 异步路由",
    version="0.1.0",
    lifespan=lifespan,
)


# ==============================================
# 异步用户接口
# ==============================================


@app.get("/users/", tags=["users"])
async def list_users(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """
    【基础功能】异步分页查询用户
    【学习知识点】
        1. select(Model) → SQLAlchemy 2.0 推荐查询语法（替代 db.query）
        2. await db.execute(stmt) → 异步执行查询
        3. .scalars().all() → 从 Result 中提取 ORM 模型对象列表
        4. SQLAlchemy 2.0 语法对比：
           旧写法（1.x）：db.query(User).offset(skip).limit(limit).all()
           新写法（2.0）：await db.execute(select(User).offset(skip).limit(limit))
           新写法更接近原生 SQL，类型安全更好
    """
    # 【基础】构建 SELECT 语句
    stmt = select(models.User).offset(skip).limit(limit)
    # 【基础】await 执行（异步等待数据库返回结果）
    result = await db.execute(stmt)
    # 【基础】scalars() 提取每行第一个字段（这里是 User 对象）
    users = result.scalars().all()

    return {
        "users": [{"id": u.id, "username": u.username, "email": u.email} for u in users],
        "count": len(users),
    }


@app.get("/users/{user_id}", tags=["users"])
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    【基础功能】异步查询单个用户 + 关联商品
    【学习知识点】
        1. .where() → SQLAlchemy 2.0 的 filter 等价写法
        2. selectinload(User.items) → 预加载关联数据（异步环境避免懒加载）
        3. 异步环境不能使用 lazy="select"（默认懒加载），会触发隐式 IO
           必须显式预加载：options(selectinload(User.items))
    """
    # 【进阶】selectinload 预加载关联数据
    #   不写这个 → user.items 访问时会触发第二次异步查询（可能失败）
    #   写了这个 → 一条 SQL JOIN 把用户和商品一起查出来
    stmt = (
        select(models.User)
        .where(models.User.id == user_id)
        .options(selectinload(models.User.items))
    )
    result = await db.execute(stmt)
    user = result.scalars().first()

    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "items": [{"id": i.id, "name": i.name, "price": i.price} for i in user.items],
    }


@app.post("/users/", tags=["users"], status_code=201)
async def create_user(
    username: str,
    email: str,
    password: str = "default123",
    db: AsyncSession = Depends(get_db),
):
    """
    【基础功能】异步创建用户
    【学习知识点】
        1. db.add(obj) + await db.commit() → 异步写入
        2. await db.refresh(obj) → 异步刷新（获取自增 ID）
        3. 所有写操作都要 await
    """
    import bcrypt

    user = models.User(
        username=username,
        email=email,
        hashed_password=bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode(),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return {"id": user.id, "username": user.username, "email": user.email}


@app.get("/stats/", tags=["stats"])
async def get_stats(db: AsyncSession = Depends(get_db)):
    """
    【基础功能】异步并发统计查询 — asyncio.gather 同时执行多个查询
    【学习知识点】
        1. asyncio.gather() → 并发执行多个异步查询（并行，不是串行）
        2. 串行 vs 并行：3 个独立的查询串行=3x时间，并行=1x时间
        3. 注意：只有独立的查询才能 gather，有依赖的查询必须顺序执行
    """
    import asyncio

    # 【基础】定义 3 个独立的统计查询
    async def count_users():
        result = await db.execute(select(sqlfunc.count(models.User.id)))
        return result.scalar()

    async def count_items():
        result = await db.execute(select(sqlfunc.count(models.Item.id)))
        return result.scalar()

    async def total_stock():
        result = await db.execute(select(sqlfunc.sum(models.Item.stock)))
        return result.scalar() or 0

    # 【基础】asyncio.gather 并发执行（并行），总耗时 ≈ 最慢的那个查询
    user_count, item_count, stock_sum = await asyncio.gather(
        count_users(), count_items(), total_stock()
    )

    return {
        "total_users": user_count,
        "total_items": item_count,
        "total_stock": stock_sum,
        "note": "这 3 个查询是并行执行的（asyncio.gather）",
    }


if __name__ == "__main__":
    uvicorn.run("step16_async_database.main:app", host="127.0.0.1", port=8000, reload=True)
