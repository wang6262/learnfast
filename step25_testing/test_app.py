# ==============================================
# 文件名：step25_testing/test_app.py
# 基础功能：使用 TestClient 和 pytest 测试 FastAPI 应用
# 核心学习知识点：
#   1. TestClient — FastAPI 内置的 HTTP 测试客户端（基于 httpx）
#   2. pytest fixtures — 共享测试依赖（client）
#   3. assert 断言 — 验证状态码、JSON 响应体、Header
#   4. 测试命名规范 — test_ 前缀
#   5. 测试覆盖 — 正常路径 + 错误路径
#   6. .json() — 解析 JSON 响应
# 运行方式：uv run pytest step25_testing/ -v
# ==============================================
import pytest
from fastapi.testclient import TestClient
from .app import app


@pytest.fixture
def client():
    """
    测试夹具：每个测试函数获得一个独立的 TestClient 实例。
    TestClient 不需要真实启动服务器，直接通过 ASGI 协议与应用通信。
    【进阶】with 语句确保每个测试后清理资源
    """
    with TestClient(app) as c:
        yield c


class TestRoot:
    """根路径测试组"""

    def test_root_returns_200(self, client):
        """测试：GET / 返回 200"""
        response = client.get("/")
        assert response.status_code == 200

    def test_root_json(self, client):
        """测试：GET / 返回正确的 JSON"""
        response = client.get("/")
        data = response.json()
        assert "message" in data
        assert data["message"] == "Hello Test"


class TestGetItem:
    """商品查询测试组"""

    def test_get_existing_item(self, client):
        """测试：查询存在的商品"""
        response = client.get("/items/1")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "键盘"
        assert data["price"] == 299.0

    def test_get_nonexistent_item(self, client):
        """测试：查询不存在的商品 → 404"""
        response = client.get("/items/999")
        assert response.status_code == 404
        assert "detail" in response.json()

    def test_get_item_invalid_id(self, client):
        """测试：非法的 item_id → 422"""
        response = client.get("/items/abc")
        assert response.status_code == 422


class TestCreateItem:
    """商品创建测试组"""

    def test_create_item_success(self, client):
        """测试：成功创建商品 → 201"""
        response = client.post("/items/", json={"name": "鼠标", "price": 149.0})
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["name"] == "鼠标"

    def test_create_item_invalid_data(self, client):
        """测试：缺少必填字段 → 422"""
        response = client.post("/items/", json={"name": "无价格商品"})
        # 缺少 price → 422
        assert response.status_code == 422

    def test_create_item_negative_price(self, client):
        """测试：负数价格（price 没有 >0 限制，应通过）"""
        response = client.post("/items/", json={"name": "测试", "price": -10.0})
        # 当前 app 的 ItemCreate 没有做 gt=0 校验，所以 201
        # 这个测试验证了"缺少校验规则"的边界情况
        assert response.status_code == 201
