"""ProcessManager 状态转换与启停流程测试（mock 子进程）。"""
from __future__ import annotations

import asyncio
import sys

import pytest

from app.core.process_manager import ProcessManager


def make_manager():
    return ProcessManager()


def test_status_default_stopped():
    pm = make_manager()
    assert pm.status("search") == "stopped"


def test_invalid_app_name_rejected():
    pm = make_manager()
    assert asyncio.run(pm.start("bad-name!")) is False


def test_start_missing_script_returns_false(tmp_data_root, monkeypatch):
    # 脚本不存在时 start 返回 False，且状态置 failed
    pm = make_manager()
    result = asyncio.run(pm.start("nonexistent_app"))
    assert result is False
    assert pm.status("nonexistent_app") == "failed"


@pytest.mark.asyncio
async def test_stop_when_not_running(tmp_data_root):
    pm = make_manager()
    # 未启动时 stop 返回 True，无异常
    assert await pm.stop("search") is True
