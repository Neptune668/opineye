"""REST API 接口测试。"""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def make_client():
    return TestClient(app)


def test_status():
    c = make_client()
    r = c.get("/api/status")
    assert r.status_code == 200
    body = r.json()
    assert body["code"] == 0
    assert "apps" in body["data"]


def test_invalid_app_name_422():
    c = make_client()
    r = c.get("/api/start/bad-name!")
    assert r.status_code == 422


def test_output_empty_when_no_output():
    c = make_client()
    r = c.get("/api/output/search")
    assert r.status_code == 200
    assert r.json()["data"]["app_name"] == "search"


def test_test_log_empty():
    c = make_client()
    r = c.get("/api/test_log/search?tail=10")
    assert r.status_code == 200
    assert r.json()["data"]["lines"] == []


def test_system_status():
    c = make_client()
    r = c.get("/api/system/status")
    assert r.status_code == 200
    assert "system_status" in r.json()["data"]


def test_system_shutdown_and_start():
    c = make_client()
    r1 = c.post("/api/system/shutdown")
    assert r1.json()["data"]["system_status"] == "offline"
    r2 = c.post("/api/system/start")
    assert r2.json()["data"]["system_status"] == "online"
