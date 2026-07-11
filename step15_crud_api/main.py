# ==============================================
# 文件名：step15_crud_api/main.py
# 基础功能：完整 RESTful CRUD API — 用户和商品的标准化接口
# 核心学习知识点：
#   1. 标准 RESTful 接口 — 每个资源有标准化的 GET/POST/PUT/PATCH/DELETE
#   2. CRUD 模式 — 路由→CRUD函数→数据库的调用链
#   3. response_model 与 ORM — Pydantic Schema 过滤敏感字段
#   4. PATCH 部分更新 — model_dump(exclude_unset=True) 只更新传了的字段
#   5. HTTP 状态码规范 — 201 Created / 204 No Content / 422 Validation Error
#   6. 路由标签分组 — tags=["users"] / tags=["items"] 文档分组
# 运行方式：uv run python -m step15_crud_api.main
# ==============================================
import uvicorn

from fastapi import FastAPI, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from . import crud, models, schemas
from .database import engine, Base, get_db

app = FastAPI(
    title="LearnFast API — CRUD 实战",
    description="FastAPI 学习 Step15：完整 RESTful CRUD API + Schema 分层 + PATCH",
    version="0.1.0",
)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


# ==============================================
# 用户 CRUD 接口
# ==============================================


@app.post("/users/", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED, tags=["users"])
def create_user(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    【基础功能】创建新用户（POST）
    【学习知识点】
        1. 201 Created — 资源创建成功的标准状态码
        2. response_model=UserResponse → 返回不含密码的安全用户对象
        3. Schema → CRUD → ORM → DB 的调用链
    """
    # 检查用户名唯一性
    existing = crud.get_user_by_username(db, user_in.username)
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")
    return crud.create_user(db, user_in)


@app.get("/users/", response_model=list[schemas.UserResponse], tags=["users"])
def list_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """获取用户列表（GET）"""
    return crud.get_users(db, skip=skip, limit=limit)


@app.get("/users/{user_id}", response_model=schemas.UserDetailResponse, tags=["users"])
def get_user(user_id: int, db: Session = Depends(get_db)):
    """获取用户详情 + 关联商品（GET）"""
    user = crud.get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user  # UserDetailResponse 自动序列化 user.items（ORM relationship）


@app.put("/users/{user_id}", response_model=schemas.UserResponse, tags=["users"])
def update_user_full(user_id: int, user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    完整更新用户（PUT 语义 — 所有字段必传）
    【学习知识点】PUT vs PATCH — PUT 要求完整数据，PATCH 只传要更新的字段
    """
    user = crud.get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    # PUT 用 UserCreate（全字段）转换为 UserUpdate（全字段更新）
    update_data = schemas.UserUpdate(**user_in.model_dump())
    update_data.password = user_in.password  # 密码需要特殊处理
    return crud.update_user(db, user, update_data)


@app.patch("/users/{user_id}", response_model=schemas.UserResponse, tags=["users"])
def update_user_partial(user_id: int, user_in: schemas.UserUpdate, db: Session = Depends(get_db)):
    """
    部分更新用户（PATCH 语义 — 只传要改的字段）
    【学习知识点】
        1. PATCH — RESTful 标准的部分更新方法
        2. UserUpdate 所有字段 Optional，不传的不改
        3. 密码哈希在 crud.update_user 中自动处理
    """
    user = crud.get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    return crud.update_user(db, user, user_in)


@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["users"])
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """删除用户（DELETE — 204 No Content）"""
    crud.delete_user(db, user_id)
    # 204 不返回响应体


# ==============================================
# 商品 CRUD 接口
# ==============================================


@app.post("/items/", response_model=schemas.ItemResponse, status_code=status.HTTP_201_CREATED, tags=["items"])
def create_item(item_in: schemas.ItemCreate, db: Session = Depends(get_db)):
    return crud.create_item(db, item_in)


@app.get("/items/", response_model=list[schemas.ItemResponse], tags=["items"])
def list_items(
    skip: int = 0,
    limit: int = 100,
    owner_id: int | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    db: Session = Depends(get_db),
):
    """获取商品列表，支持按所有者和价格范围过滤"""
    return crud.get_items(db, skip=skip, limit=limit, owner_id=owner_id, min_price=min_price, max_price=max_price)


@app.get("/items/{item_id}", response_model=schemas.ItemResponse, tags=["items"])
def get_item(item_id: int, db: Session = Depends(get_db)):
    item = crud.get_item(db, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="商品不存在")
    return item


@app.patch("/items/{item_id}", response_model=schemas.ItemResponse, tags=["items"])
def update_item(item_id: int, item_in: schemas.ItemUpdate, db: Session = Depends(get_db)):
    """部分更新商品"""
    item = crud.get_item(db, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="商品不存在")
    return crud.update_item(db, item, item_in)


@app.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["items"])
def delete_item(item_id: int, db: Session = Depends(get_db)):
    crud.delete_item(db, item_id)


if __name__ == "__main__":
    uvicorn.run("step15_crud_api.main:app", host="127.0.0.1", port=8000, reload=True)
