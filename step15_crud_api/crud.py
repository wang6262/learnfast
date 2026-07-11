# ==============================================
# 文件名：step15_crud_api/crud.py
# 基础功能：可复用的 CRUD 辅助函数 — 将数据库操作从路由逻辑中抽离
# 核心学习知识点：
#   1. CRUD 函数模式 — 标准化的增删改查函数封装
#   2. 分离关注点 — 路由负责 HTTP，CRUD 负责数据库
#   3. commit/refresh/rollback — 事务生命周期管理
#   4. get_or_404 模式 — 封装"查不到抛异常"逻辑
#   5. 部分更新（PATCH）— 只更新传了值的字段
# ==============================================
from typing import Type, TypeVar
from fastapi import HTTPException
from sqlalchemy.orm import Session

from . import models, schemas
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# TypeVar 用于泛型类型提示
ModelType = TypeVar("ModelType")


# ==============================================
# 用户 CRUD
# ==============================================


def get_user(db: Session, user_id: int) -> models.User | None:
    """
    【基础功能】按 ID 查询用户，不存在返回 None
    【学习知识点】
        1. db.query(Model).filter(条件).first() → 查询单条
        2. first() → 0 或 1 条结果，多条也只取第一条
        3. one() → 要求恰好 1 条，多了少了都抛异常（SQLAlchemy 级别）
    """
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_username(db: Session, username: str) -> models.User | None:
    """按用户名查询用户"""
    return db.query(models.User).filter(models.User.username == username).first()


def get_users(db: Session, skip: int = 0, limit: int = 100) -> list[models.User]:
    """分页查询所有用户"""
    return db.query(models.User).offset(skip).limit(limit).all()


def create_user(db: Session, user_in: schemas.UserCreate) -> models.User:
    """
    【基础功能】创建用户（密码自动哈希）
    【学习知识点】
        1. 密码哈希在 CRUD 层处理 → 路由层不关心密码如何存储
        2. 数据转换：Pydantic Schema → ORM Model
        3. commit + refresh → 写入 + 获取自增 ID
    """
    # Pydantic Schema 转 ORM 对象（手动映射字段，密码单独哈希）
    user = models.User(
        username=user_in.username,
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=pwd_context.hash(user_in.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user(db: Session, user: models.User, user_in: schemas.UserUpdate) -> models.User:
    """
    【基础功能】部分更新用户（PATCH 语义）
    【学习知识点】
        1. model_dump(exclude_unset=True) — 只获取用户实际传了的字段
        2. exclude_unset — PATCH 的核心：未传的字段不出现在 dict 中
        3. setattr(obj, key, value) — 动态更新 ORM 对象的属性
        4. 如果传了新密码，自动哈希后再赋值
    """
    # 【基础】获取用户实际传了的字段（未传的字段不在 update_data 中）
    update_data = user_in.model_dump(exclude_unset=True)

    # 如果更新了密码，先哈希
    if "password" in update_data:
        update_data["hashed_password"] = pwd_context.hash(update_data.pop("password"))

    # 【基础】遍历更新字段，用 setattr 动态设置 ORM 对象属性
    for field, value in update_data.items():
        setattr(user, field, value)

    db.add(user)  # 标记为待更新（SQLAlchemy 跟踪更改，会自动生成 UPDATE）
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user_id: int) -> models.User:
    """删除用户（级联删除关联商品）"""
    user = get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    db.delete(user)
    db.commit()
    return user  # 返回已删除的用户对象（内存中还存在，但已从数据库移除）


# ==============================================
# 商品 CRUD
# ==============================================


def get_item(db: Session, item_id: int) -> models.Item | None:
    return db.query(models.Item).filter(models.Item.id == item_id).first()


def get_items(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    owner_id: int | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
) -> list[models.Item]:
    """分页查询商品，支持按所有者和价格过滤"""
    query = db.query(models.Item)

    if owner_id is not None:
        query = query.filter(models.Item.owner_id == owner_id)
    if min_price is not None:
        query = query.filter(models.Item.price >= min_price)
    if max_price is not None:
        query = query.filter(models.Item.price <= max_price)

    return query.offset(skip).limit(limit).all()


def create_item(db: Session, item_in: schemas.ItemCreate) -> models.Item:
    """创建商品（需验证所有者存在）"""
    # 验证所有者存在
    owner = get_user(db, item_in.owner_id)
    if owner is None:
        raise HTTPException(status_code=404, detail=f"用户 {item_in.owner_id} 不存在")

    item = models.Item(
        name=item_in.name,
        description=item_in.description,
        price=item_in.price,
        stock=item_in.stock,
        owner_id=item_in.owner_id,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def update_item(db: Session, item: models.Item, item_in: schemas.ItemUpdate) -> models.Item:
    """部分更新商品（PATCH 语义）"""
    update_data = item_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(item, field, value)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def delete_item(db: Session, item_id: int) -> models.Item:
    item = get_item(db, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="商品不存在")
    db.delete(item)
    db.commit()
    return item
