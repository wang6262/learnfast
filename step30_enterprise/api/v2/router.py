"""v2 路由聚合（演示 API 版本化）"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/users/")
async def list_users_v2():
    """
    v2 版本的用户列表（模拟返回不同的数据结构）。
    API 版本化允许新旧版本同时存在，客户端逐步迁移。
    """
    return {
        "version": "v2",
        "data": [{"username": "v2_user1"}, {"username": "v2_user2"}],
        "meta": {"total": 2, "note": "v2 版本增加了 meta 字段（向下兼容示例）"},
    }
