# ==============================================
# 文件名：step27_integration_tests/tests/test_users.py
# 基础功能：集成测试 — 测试真实数据库交互 + 业务规则
# 核心学习知识点：
#   1. 集成测试 vs 单元测试 — 集成测试验证"各组件协作"是否正常
#   2. 事务回滚 — 每个测试后回滚，保持测试独立性
#   3. 测试覆盖 — 正常路径 + 异常路径 + 边界条件
#   4. pytest.mark.parametrize — 参数化测试，减少重复代码
#   5. 测试命名和文档 — 测试本身就是文档
# 运行方式：uv run pytest step27_integration_tests/ -v --cov=step27_integration_tests --cov-report=term
# ==============================================
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from step27_integration_tests.app import app
from step27_integration_tests.database import Base, get_db


@pytest.fixture
def client():
    """
    集成测试用 TestClient。
    使用 SQLite 内存数据库替代真实数据库。
    """
    # 创建测试数据库（内存模式，测试结束自动丢弃）
    test_engine = create_engine(
        "sqlite:///:memory:",
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

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


class TestCreateUser:
    """用户创建集成测试"""

    def test_create_user_success(self, client):
        """正常创建用户 → 201"""
        response = client.post("/users/?username=test1&email=t1@test.com")
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "test1"
        assert data["id"] == 1

    def test_create_duplicate_email(self, client):
        """重复邮箱 → 409 Conflict"""
        # 第一次创建成功
        client.post("/users/?username=a&email=dup@test.com")
        # 第二次相同邮箱
        response = client.post("/users/?username=b&email=dup@test.com")
        assert response.status_code == 409
        assert "邮箱已存在" in response.json()["detail"]


class TestGetUser:
    """用户查询集成测试"""

    def test_get_existing_user(self, client):
        """查询存在的用户 → 200"""
        client.post("/users/?username=exists&email=e@test.com")
        response = client.get("/users/1")
        assert response.status_code == 200
        assert response.json()["username"] == "exists"

    def test_get_nonexistent_user(self, client):
        """查询不存在的用户 → 404"""
        response = client.get("/users/9999")
        assert response.status_code == 404


@pytest.mark.parametrize("username,email,expected_status", [
    ("user1", "u1@test.com", 201),
    ("user2", "u2@test.com", 201),
])
def test_create_multiple_users(client, username, email, expected_status):
    """
    参数化测试：同一测试逻辑跑多组数据。
    减少了重复的测试代码。
    """
    response = client.post(f"/users/?username={username}&email={email}")
    assert response.status_code == expected_status
