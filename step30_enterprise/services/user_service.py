"""用户服务（业务逻辑编排）"""
from fastapi import HTTPException
from ..repositories.user_repo import UserRepository
from ..models.user import User


class UserService:
    """用户业务逻辑"""

    def __init__(self, repo: UserRepository):
        self.repo = repo

    async def register(self, username: str, email: str, password: str) -> User:
        # 检查用户名重复
        if await self.repo.get_by_username(username):
            raise HTTPException(status_code=400, detail="用户名已存在")
        # 创建用户（实际应哈希密码）
        user = User(username=username, email=email, hashed_password=f"hashed_{password}")
        return await self.repo.create(user)

    async def get_user(self, user_id: int) -> User:
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        return user
