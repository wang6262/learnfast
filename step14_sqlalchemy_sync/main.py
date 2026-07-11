# ==============================================
# 文件名：step14_sqlalchemy_sync/main.py
# 基础功能：SQLAlchemy 同步引擎 + PostgreSQL — 建表、增删改查完整示例
# 核心学习知识点：
#   1. Base.metadata.create_all() — 根据 ORM 模型自动建表
#   2. Session 增删改查 — add/delete/commit/query/refresh
#   3. filter()/filter_by() — 条件查询
#   4. 事务管理 — commit/rollback
#   5. relationship 级联操作 — 删除用户时自动删除关联商品
#   6. FastAPI 路由 + SQLAlchemy 集成模式
# 使用前准备：
#   1. 确保 PostgreSQL 正在运行
#   2. 创建数据库：createdb learnfast（或在 psql 中 CREATE DATABASE learnfast;）
#   3. 修改 database.py 中的连接字符串（用户名/密码）匹配你的本地配置
# 运行方式：uv run python -m step14_sqlalchemy_sync.main
# 验证：启动后访问 http://127.0.0.1:8000/docs 测试 CRUD 接口
# ==============================================
import uvicorn

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

from .database import engine, Base, SessionLocal, get_db
from .models import User, Item


# ==============================================
# 应用实例
# ==============================================
app = FastAPI(
    title="LearnFast API — SQLAlchemy 同步",
    description="FastAPI 学习 Step14：SQLAlchemy ORM + PostgreSQL CRUD",
    version="0.1.0",
)


# ==============================================
# 启动事件：自动建表
# 【基础】应用启动时，根据 ORM 模型自动创建数据库表
#   如果表已存在，不会重复创建（不会覆盖已有数据）
# 【进阶】Base.metadata.create_all() 的工作原理：
#   1. 扫描所有继承 Base 的类
#   2. 读取 Column 定义，生成对应的 CREATE TABLE SQL
#   3. 按外键依赖顺序执行（users 先于 items 创建）
#   4. 如果表已存在则跳过（不覆盖数据，只创建缺失的表）
#   这种方式适合开发环境，生产环境用 Alembic 迁移（Step17）
# ==============================================
@app.on_event("startup")
def on_startup():
    """应用启动时创建数据库表"""
    Base.metadata.create_all(bind=engine)
    print("数据库表已就绪（users, items）")


# ==============================================
# 路由：用户 CRUD
# ==============================================


@app.post("/users/", tags=["users"])
def create_user(
    username: str,
    email: str,
    full_name: str | None = None,
    password: str = "default123",
    db: Session = Depends(get_db),
):
    """
    【基础功能】创建用户，写入 PostgreSQL 数据库
    【学习知识点】
        1. db.add(obj) → 标记对象为"待插入"（不立即写入）
        2. db.commit() → 提交事务（真正写入数据库）
        3. db.refresh(obj) → 从数据库重新读取（获取自增 ID、默认值等）
        4. ORM 对象状态：transient → pending → persistent → detached
    调用示例：
        curl -X POST "http://127.0.0.1:8000/users/?username=alice&email=alice@test.com&full_name=Alice"
    """
    # 【基础】创建 ORM 对象（此时还不在数据库中）
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    user = User(
        username=username,
        email=email,
        full_name=full_name,
        hashed_password=pwd_context.hash(password),
    )
    # 【基础】添加到会话（标记为待插入）
    db.add(user)
    # 【基础】提交事务（执行 SQL INSERT）
    db.commit()
    # 【基础】刷新对象（获取数据库生成的 id、created_at 等）
    db.refresh(user)

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "created_at": str(user.created_at),
    }


@app.get("/users/", tags=["users"])
def list_users(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    """
    【基础功能】分页查询所有用户
    【学习知识点】
        1. db.query(Model) → 创建查询对象（Query）
        2. .offset(skip).limit(limit) → 分页
        3. .all() → 执行查询，返回所有结果列表
        4. Query 是惰性的（方法链只是构建 SQL，调用 .all() 才真正执行）
    """
    users = db.query(User).offset(skip).limit(limit).all()
    return {
        "users": [
            {"id": u.id, "username": u.username, "email": u.email, "role": u.role}
            for u in users
        ],
        "count": len(users),
    }


@app.get("/users/{user_id}", tags=["users"])
def get_user(user_id: int, db: Session = Depends(get_db)):
    """
    【基础功能】查询单个用户（含关联商品）
    【学习知识点】
        1. db.query(Model).filter(条件).first() → 查询单条
        2. .first() 返回 None（如果没找到）→ 需判空
        3. user.items → relationship 自动加载关联的商品列表
    """
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "items": [
            {"id": item.id, "name": item.name, "price": item.price}
            for item in user.items
        ],
    }


# ==============================================
# 路由：商品 CRUD
# ==============================================


@app.post("/items/", tags=["items"])
def create_item(
    name: str,
    owner_id: int,
    price: float = 0.0,
    stock: int = 0,
    db: Session = Depends(get_db),
):
    """
    【基础功能】为用户创建商品（需要用户存在）
    【学习知识点】
        1. ForeignKey 的校验 — 如果 owner_id 不存在，commit 时会抛 IntegrityError
        2. 级联操作 — 删除用户时自动删除其商品（models.py 中 cascade="all, delete-orphan"）
    """
    # 先验证用户存在
    user = db.query(User).filter(User.id == owner_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail=f"用户 {owner_id} 不存在")

    item = Item(name=name, price=price, stock=stock, owner_id=owner_id)
    db.add(item)
    db.commit()
    db.refresh(item)

    return {"id": item.id, "name": item.name, "price": item.price, "owner": user.username}


@app.get("/items/", tags=["items"])
def list_items(
    min_price: float | None = None,
    max_price: float | None = None,
    db: Session = Depends(get_db),
):
    """
    【基础功能】分页查询商品，支持价格范围过滤
    【学习知识点】
        1. filter() 动态组合条件 — 逐步添加过滤条件
        2. Query 方法链的不可变性 — 每次 filter() 返回新的 Query 对象
    """
    query = db.query(Item)

    # 【基础】动态添加价格过滤条件
    if min_price is not None:
        query = query.filter(Item.price >= min_price)
    if max_price is not None:
        query = query.filter(Item.price <= max_price)

    items = query.all()
    return {
        "items": [{"id": i.id, "name": i.name, "price": i.price, "stock": i.stock} for i in items],
        "count": len(items),
    }


@app.delete("/users/{user_id}", tags=["users"])
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """
    【基础功能】删除用户（级联删除关联商品）
    【学习知识点】
        1. db.delete(obj) → 标记为待删除
        2. 级联删除 — cascade="all, delete-orphan" 自动删除关联商品
        3. 不可逆操作 — 生产环境建议软删除（is_deleted=True）
    """
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")

    db.delete(user)
    db.commit()
    return {"message": f"用户 {user.username} 及其所有商品已删除"}


# ==============================================
# 程序入口
# ==============================================
if __name__ == "__main__":
    uvicorn.run(
        "step14_sqlalchemy_sync.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )
