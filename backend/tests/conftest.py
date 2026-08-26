"""pytest 共享 fixtures 与配置。"""
from __future__ import annotations

import pytest

from app import settings


@pytest.fixture
def tmp_data_root(tmp_path, monkeypatch):
    """每个测试用例使用独立的临时数据目录，测试结束自动清理。"""
    monkeypatch.setattr(settings, "DATA_ROOT", tmp_path)
    monkeypatch.setattr(settings, "CONFIG_PATH", tmp_path / "config.json")
    monkeypatch.setattr(settings, "RUNTIME_APPS_DIR", tmp_path / "runtime" / "apps")
    monkeypatch.setattr(settings, "RUNTIME_FORUM_DIR", tmp_path / "runtime" / "forum")
    monkeypatch.setattr(
        settings, "RUNTIME_FORUM_HISTORY_DIR", tmp_path / "runtime" / "forum" / "history"
    )
    monkeypatch.setattr(settings, "REPORTS_DIR", tmp_path / "reports")
    monkeypatch.setattr(settings, "GRAPHS_DIR", tmp_path / "graphs")
    monkeypatch.setattr(settings, "OUTPUTS_DIR", tmp_path / "outputs")
    monkeypatch.setattr(
        settings, "FORUM_LATEST_LOG", tmp_path / "runtime" / "forum" / "latest.log"
    )
    monkeypatch.setattr(
        settings,
        "REQUIRED_DIRS",
        (
            settings.RUNTIME_APPS_DIR,
            settings.RUNTIME_FORUM_DIR,
            settings.RUNTIME_FORUM_HISTORY_DIR,
            settings.REPORTS_DIR,
            settings.GRAPHS_DIR,
            settings.OUTPUTS_DIR,
        ),
    )
    return tmp_path
