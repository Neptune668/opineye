"""config.py 配置加载测试。"""
from __future__ import annotations

import json

from app import config
from app.core import store


def test_load_config_default_when_missing(tmp_data_root):
    store.ensure_data_dirs()  # 会写入默认配置
    store.write_json(tmp_data_root / "config.json", {})  # 清空
    # 删除配置文件
    (tmp_data_root / "config.json").unlink()
    result = config.load_config()
    assert result["system"]["name"] == "舆情分析平台"


def test_load_config_corrupted_falls_back(tmp_data_root):
    path = tmp_data_root / "config.json"
    path.write_text("{ invalid json", encoding="utf-8")
    result = config.load_config()
    assert result["system"]["name"] == "舆情分析平台"


def test_deep_merge_fills_missing_fields(tmp_data_root):
    store.write_json(tmp_data_root / "config.json", {"system": {"name": "自定义"}})
    result = config.load_config()
    # 自定义字段保留
    assert result["system"]["name"] == "自定义"
    # 缺失字段用默认值补齐
    assert "default_apps" in result["system"]
    assert "collection" in result
