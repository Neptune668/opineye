"""store.py 文件读写工具测试。"""
from __future__ import annotations

import json

from app.core import store


def test_write_and_read_json(tmp_data_root):
    path = tmp_data_root / "test.json"
    data = {"a": 1, "b": "x"}
    store.write_json(path, data)
    assert path.exists()
    assert store.read_json(path) == data


def test_read_json_missing_returns_none(tmp_data_root):
    assert store.read_json(tmp_data_root / "missing.json") is None


def test_read_json_missing_returns_default(tmp_data_root):
    assert store.read_json(tmp_data_root / "missing.json", default={}) == {}


def test_ensure_data_dirs_creates_config(tmp_data_root):
    store.ensure_data_dirs()
    config_path = tmp_data_root / "config.json"
    assert config_path.exists()
    content = store.read_json(config_path)
    assert "system" in content
    assert "collection" in content


def test_append_log(tmp_data_root):
    path = tmp_data_root / "a.log"
    store.append_log(path, "line1")
    store.append_log(path, "line2")
    lines = path.read_text(encoding="utf-8").splitlines()
    assert lines == ["line1", "line2"]
