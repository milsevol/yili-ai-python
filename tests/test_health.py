from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health_check():
    """测试健康检查端点"""
    response = client.get("/api/v1/health/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}