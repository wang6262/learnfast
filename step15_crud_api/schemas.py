# ==============================================
# 文件名：step15_crud_api/schemas.py
# 基础功能：Pydantic 请求/响应 Schema 定义
# 核心学习知识点：
#   1. 输入/输出模型分离 — 创建/更新/查询各自独立 Schema
#   2. from_attributes=True — ORM 模型直接转为 Pydantic 模型（Pydantic v2）
#   3. Optional 字段 — 可选的更新字段
#   4. model_config — Pydantic v2 配置方式
#   5. 嵌套 Schema — ItemResponse 中包含 UserResponse
# ==============================================
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


# --- User Schemas ---
class UserBase(BaseModel):
    """用户基础 Schema（公共字段）"""
    username: str = Field(min_length=1, max_length=50)
    email: str = Field(min_length=1, max_length=100)
    full_name: str | None = None


class UserCreate(UserBase):
    """创建用户的输入 Schema（需要密码）"""
    password: str = Field(min_length=6, max_length=100)


class UserUpdate(BaseModel):
    """
    更新用户的输入 Schema（所有字段可选）。
    PATCH 语义：只传要改的字段，None 表示"不更新此字段"。
    """
    username: str | None = Field(default=None, min_length=1, max_length=50)
    email: str | None = Field(default=None, min_length=1, max_length=100)
    full_name: str | None = None
    password: str | None = Field(default=None, min_length=6, max_length=100)
    is_active: bool | None = None


class UserResponse(UserBase):
    """查询用户的输出 Schema（不含密码，含 ORM 字段）"""
    # 【基础】model_config 替代 Pydantic v1 的 class Config
    # 【进阶】from_attributes=True → 可以从 ORM 对象或 dict 创建实例
    #   v1 中叫 orm_mode=True，v2 改名 from_attributes
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    is_active: bool
    created_at: datetime | None = None


class UserDetailResponse(UserResponse):
    """用户详情输出（含关联商品列表）"""
    items: list["ItemResponse"] = []


# --- Item Schemas ---
class ItemBase(BaseModel):
    """商品基础 Schema"""
    name: str = Field(min_length=1, max_length=100)
    description: str | None = None
    price: float = Field(ge=0, description="价格（非负数）")
    stock: int = Field(ge=0, default=0)


class ItemCreate(ItemBase):
    """创建商品的输入 Schema"""
    owner_id: int = Field(gt=0)


class ItemUpdate(BaseModel):
    """更新商品的输入 Schema（所有字段可选）"""
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None
    price: float | None = Field(default=None, ge=0)
    stock: int | None = Field(default=None, ge=0)
    is_available: bool | None = None


class ItemResponse(ItemBase):
    """商品查询输出"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_available: bool
    owner_id: int
    created_at: datetime | None = None
    owner: UserResponse | None = None  # 嵌套用户信息


# 修复前向引用（UserDetailResponse 使用了 ItemResponse）
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    pass  # Pydantic v2 自动处理前向引用，不需要额外操作
