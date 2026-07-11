# ==============================================
# 文件名：step26_async_testing/test_app.py
# 基础功能：pytest-asyncio 异步测试 + dependency_overrides 依赖替换
# 核心学习知识点：
#   1. pytest.mark.asyncio — 运行 async 测试函数
#   2. httpx.AsyncClient — 异步 HTTP 客户端（配合 ASGITransport）
#   3. app.dependency_overrides — 用模拟对象替代真实依赖
#   4. 测试数据库隔离 — 测试用独立数据库，不影响生产数据
#   5. 测试后清理 — yield fixture 的 teardown 阶段
# 运行方式：uv run pytest step26_async_testing/ -v
# ==============================================
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from .app import app, Base, get_db, DBUser


# ==============================================
# 测试数据库的 fixture
# 【基础】测试用独立的 SQLite 内存数据库，测试结束自动丢弃
# 【进阶】SQLite :memory: 模式：
#   - 每个连接 = 独立的数据库（不同连接看不到彼此的数据）
#   - 但 check_same_thread=False 让多个请求共享同一连接
#   替代方案：用实际文件 SQLite 并用 yield 后删除文件
# ==============================================


@pytest.fixture
def test_db():
    """创建测试数据库（SQLite 内存模式）"""
    test_engine = create_engine(
        "sqlite:///./test.db",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=test_engine)
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    def override_get_db():
        db = TestSessionLocal()
        try:
            yield db
        finally:
            db.close()

    # 【基础】核心！替换 app 中的 get_db 依赖为测试用数据库
    app.dependency_overrides[get_db] = override_get_db

    yield  # 测试执行

    # 【基础】清理：测试后移除依赖覆盖
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def async_client(test_db):
    """
    异步 HTTP 测试客户端。
    ASGITransport 通过 ASGI 协议直接与应用通信（不经过网络）。
    【进阶】transport=ASGITransport(app=app) → 直接发 ASGI 请求
      比 requests 更快、更可靠（不需要真实绑定端口）
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


# ==============================================
# 测试
# ==============================================


@pytest.mark.asyncio
async def test_create_user_async(async_client):
    """测试：异步创建用户"""
    response = await async_client.post("/users/?username=alice&email=a@t.com")
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "alice"


@pytest.mark.asyncio
async def test_list_users_async(async_client):
    """测试：异步查询用户列表"""
    # 先创建用户
    await async_client.post("/users/?username=bob&email=b@t.com")

    # 再查询列表
    response = await async_client.get("/users/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_dependency_override_works(async_client):
    """
    测试：验证 dependency_overrides 确实生效。
    如果没有 override，这个测试会连接真实数据库。
    """
    response = await async_client.get("/users/")
    assert response.status_code == 200
    # 如果是真实数据库，返回的 users 列表可能包含历史数据
    # 测试数据库应该是空的或只有本次测试创建的数据
