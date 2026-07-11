"""用户 Pydantic Schema"""
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class UserCreate(BaseModel):
    username: str
    email: str
    full_name: str | None = None
    password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    email: str
    full_name: str | None
    is_active: bool
    role: str
    created_at: datetime | None
