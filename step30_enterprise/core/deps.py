"""共享依赖（组合根）"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from .database import AsyncSessionLocal

from ..repositories.user_repo import UserRepository
from ..services.user_service import UserService


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


def get_user_repository(db: AsyncSession = get_db()) -> UserRepository:
    """注入用户仓储"""
    return UserRepository(db)


def get_user_service(repo: UserRepository = get_user_repository()) -> UserService:
    """注入用户服务"""
    return UserService(repo)
