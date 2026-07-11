# ==============================================
# 文件名：step18_repository_uow/main.py
# 基础功能：Repository 模式 + Unit of Work + Service 层 — 企业级数据访问架构
# 核心学习知识点：
#   1. Repository 模式 — 封装数据访问逻辑，对上层屏蔽 SQL 细节
#   2. Unit of Work — 统一事务管理，保证多个仓储操作在同一事务中
#   3. Service 层 — 业务流程编排，协调多个仓储
#   4. 依赖注入 — 路由 → Service → Repository → DB 的完整依赖链
#   5. 可测试性 — 仓储接口可被 Mock 替换（多态替代）
# 企业级架构分层：
#   路由（Router）→ 服务（Service）→ 仓储（Repository）→ 数据库（DB）
#   路由只做 HTTP 处理，Service 做业务编排，Repository 做数据访问
#   任何一层都可以独立替换和测试
# 运行方式：uv run python -m step18_repository_uow.main
# ==============================================
import uvicorn
from typing import Generic, TypeVar, Type
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy import select, func as sqlfunc
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict

from .database import engine, Base, SessionLocal, get_db


# ==============================================
# 模型（简化版，专注架构演示）
# ==============================================
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base


class DBUser(Base):
    """用户 ORM 模型"""
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class DBItem(Base):
    """商品 ORM 模型"""
    __tablename__ = "items"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    price = Column(Integer, default=0)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    owner = relationship("DBUser")


# ==============================================
# Pydantic Schema
# ==============================================
class UserCreate(BaseModel):
    username: str
    email: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    email: str
    is_active: bool


# ==============================================
# 泛型基础仓储（Base Repository）
# 【基础】封装所有模型通用的 CRUD 操作
# 【进阶】泛型 Generic[T] 让一个基类为所有模型提供 CRUD
#   无需为每个模型重复写 create/get/list/delete 代码
#   SQLAlchemy 2.0 的 select() 语法让泛型实现更简洁
# ==============================================
ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):
    """
    泛型基础仓储。
    为任意 ORM 模型提供标准 CRUD 操作。
    用法：user_repo = BaseRepository[DBUser](DBUser)
    """

    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model
        self.db = db

    def create(self, **kwargs) -> ModelType:
        obj = self.model(**kwargs)
        self.db.add(obj)
        self.db.flush()  # flush 不提交事务，只是发送 SQL 到数据库（获取自增ID等）
        return obj

    def get_by_id(self, obj_id: int) -> ModelType | None:
        """按主键查询单个对象"""
        stmt = select(self.model).where(self.model.id == obj_id)
        return self.db.execute(stmt).scalars().first()

    def list(self, skip: int = 0, limit: int = 100) -> list[ModelType]:
        """分页查询"""
        stmt = select(self.model).offset(skip).limit(limit)
        return list(self.db.execute(stmt).scalars().all())

    def delete(self, obj_id: int) -> ModelType | None:
        obj = self.get_by_id(obj_id)
        if obj:
            self.db.delete(obj)
            self.db.flush()
        return obj

    def count(self) -> int:
        """统计记录总数"""
        stmt = select(sqlfunc.count()).select_from(self.model)
        return self.db.execute(stmt).scalar() or 0


# ==============================================
# 专用用户仓储（继承基础仓储 + 用户专属操作）
# 【基础】UserRepository = BaseRepository 的所有方法 + 用户专属的 get_by_email
# 【进阶】继承泛型仓储 + 扩展特定方法 → OCP（开闭原则）：对扩展开放，对修改封闭
# ==============================================
class UserRepository(BaseRepository[DBUser]):
    """用户仓储 — 继承基础 CRUD + 用户专属查询"""

    def __init__(self, db: Session):
        super().__init__(DBUser, db)

    def get_by_email(self, email: str) -> DBUser | None:
        stmt = select(self.model).where(self.model.email == email)
        return self.db.execute(stmt).scalars().first()

    def get_active_users(self) -> list[DBUser]:
        stmt = select(self.model).where(self.model.is_active == True)
        return list(self.db.execute(stmt).scalars().all())


class ItemRepository(BaseRepository[DBItem]):
    """商品仓储"""

    def __init__(self, db: Session):
        super().__init__(DBItem, db)

    def get_by_owner(self, owner_id: int) -> list[DBItem]:
        stmt = select(self.model).where(self.model.owner_id == owner_id)
        return list(self.db.execute(stmt).scalars().all())


# ==============================================
# Unit of Work
# 【基础】UoW 管理事务边界：多个仓储操作共享同一个 Session
#   commit() → 一次性提交所有更改
#   rollback() → 任何失败，全部回滚
# 【进阶】UoW 的价值：
#   1. 原子性：多个仓储的操作作为一个整体成功或失败
#      例如：创建用户 + 创建商品，要么都成功，要么都失败
#   2. 事务一致性：A 扣款 + B 加款 必须是原子操作
#   3. 性能优化：多次写入合并为一次 commit（减少网络往返）
#   4. 测试友好：Mock 一个 UoW 就 Mock 了所有仓储
# 设计模式：UoW 是"工作单元"模式（Martin Fowler《企业应用架构模式》）
# ==============================================
class UnitOfWork:
    """工作单元：管理事务边界 + 持有所有仓储实例"""

    def __init__(self, db: Session):
        self.db = db
        # 【基础】在 __init__ 中创建所有仓储，确保它们共享同一个 db session
        self.users = UserRepository(db)
        self.items = ItemRepository(db)

    def commit(self):
        """提交事务 — 所有更改一次性写入数据库"""
        self.db.commit()

    def rollback(self):
        """回滚事务 — 放弃所有更改"""
        self.db.rollback()

    def __enter__(self):
        """上下文管理器入口：with UnitOfWork(db) as uow:"""
        return self

    def __exit__(self, exc_type, exc_val, traceback):
        """上下文管理器出口：自动提交或回滚"""
        if exc_type is not None:
            self.rollback()  # 有异常 → 回滚
            return False     # 继续传播异常
        self.commit()        # 无异常 → 提交
        return False


# ==============================================
# Service 层
# 【基础】Service 层编排业务流程，调用多个仓储完成复杂的业务操作
# 【进阶】Service 是"领域逻辑"的承载层：
#   - 路由不应该包含任何业务逻辑（只做参数/响应处理）
#   - 仓储不应该包含业务逻辑（只做数据存取）
#   - Service 是唯一应该包含 if/else 业务判断的地方
# 这里简化处理，实际项目 Service 会处理更复杂的业务规则
# ==============================================
class UserService:
    """用户服务 — 编排用户相关的业务流程"""

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def register_user(self, username: str, email: str) -> DBUser:
        """注册用户（含重复检查）"""
        # 业务规则：邮箱唯一
        existing = self.uow.users.get_by_email(email)
        if existing:
            raise ValueError(f"邮箱 {email} 已被注册")

        # 业务规则：用户名唯一
        existing_name = self.uow.users.get_by_email(username)
        if existing_name:
            raise ValueError(f"用户名 {username} 已被占用")

        user = self.uow.users.create(username=username, email=email)
        return user

    def get_user_stats(self) -> dict:
        """获取用户统计"""
        return {
            "total": self.uow.users.count(),
            "active": len(self.uow.users.get_active_users()),
        }


# ==============================================
# FastAPI 依赖：获取 UnitOfWork
# ==============================================
def get_uow(db: Session = Depends(get_db)) -> UnitOfWork:
    """
    FastAPI 依赖：创建 UnitOfWork 实例。
    每次请求创建一个独立的 UoW，请求结束后自动归还连接。
    """
    return UnitOfWork(db)


# ==============================================
# 应用实例 + 路由
# ==============================================
app = FastAPI(
    title="LearnFast API — Repository & UoW",
    description="FastAPI 学习 Step18：Repository 模式 + Unit of Work + Service 层",
    version="0.1.0",
)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


@app.post("/users/", response_model=UserResponse, status_code=status.HTTP_201_CREATED, tags=["users"])
def create_user(user_in: UserCreate, uow: UnitOfWork = Depends(get_uow)):
    """
    【基础功能】创建用户（Service 编排 → Repository 数据访问 → UoW 事务管理）
    【学习知识点】
        1. 路由 → Service → Repository → DB 的完整调用链
        2. Service 层处理业务规则（邮箱/用户名唯一性校验）
        3. Repository 层封装数据访问（create/get_by_email）
        4. UoW 管理事务边界
    """
    service = UserService(uow)
    try:
        user = service.register_user(user_in.username, user_in.email)
        uow.commit()
        return user
    except ValueError as e:
        uow.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/users/", response_model=list[UserResponse], tags=["users"])
def list_users(skip: int = 0, limit: int = 100, uow: UnitOfWork = Depends(get_uow)):
    return uow.users.list(skip=skip, limit=limit)


@app.get("/users/{user_id}", response_model=UserResponse, tags=["users"])
def get_user(user_id: int, uow: UnitOfWork = Depends(get_uow)):
    user = uow.users.get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user


@app.get("/users/stats/", tags=["users"])
def user_stats(uow: UnitOfWork = Depends(get_uow)):
    service = UserService(uow)
    return service.get_user_stats()


@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["users"])
def delete_user(user_id: int, uow: UnitOfWork = Depends(get_uow)):
    uow.users.delete(user_id)
    uow.commit()


if __name__ == "__main__":
    uvicorn.run("step18_repository_uow.main:app", host="127.0.0.1", port=8000, reload=True)
