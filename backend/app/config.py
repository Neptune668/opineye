"""全局配置加载。

从 config.json 读取配置；文件不存在或损坏时回退到内置默认值，
保证服务在任何情况下都能启动。
"""
from __future__ import annotations

import copy
import json
import logging
from typing import Any

from app import settings

logger = logging.getLogger(__name__)

# 默认配置模板（与开发文档 6.1 一致）
DEFAULT_CONFIG: dict[str, Any] = {
    "system": {
        "name": "舆情分析平台",
        "default_apps": ["search", "media", "forum", "insight", "report"],
    },
    "collection": {
        "forum": {"interval_seconds": 300, "max_pages": 10},
        "default_source_types": ["news", "image", "video", "forum_post", "internal_data"],
    },
    "analysis": {"insight_enabled": True, "sentiment_mode": "rule_based"},
    "runtime": {"log_level": "INFO", "output_retention_days": 30},
}

# 进程内缓存
_config_cache: dict[str, Any] | None = None


def _deep_merge(base: dict, override: dict) -> dict:
    """递归合并 override 到 base（base 中的默认字段不会丢失）。"""
    result = copy.deepcopy(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_config() -> dict[str, Any]:
    """从磁盘读取配置，失败时回退默认值（不抛出异常）。"""
    try:
        with open(settings.CONFIG_PATH, "r", encoding="utf-8") as f:
            raw = json.load(f)
        if not isinstance(raw, dict):
            raise ValueError("config.json 顶层必须为对象")
        # 用默认值补齐缺失字段
        return _deep_merge(DEFAULT_CONFIG, raw)
    except FileNotFoundError:
        logger.warning("配置文件 %s 不存在，使用默认配置", settings.CONFIG_PATH)
    except (json.JSONDecodeError, ValueError) as exc:
        logger.warning("配置文件 %s 损坏，回退默认配置：%s", settings.CONFIG_PATH, exc)
    return copy.deepcopy(DEFAULT_CONFIG)


def get_config() -> dict[str, Any]:
    """获取配置（进程内缓存）。"""
    global _config_cache
    if _config_cache is None:
        _config_cache = load_config()
    return _config_cache


def set_config(config: dict[str, Any]) -> None:
    """更新进程内缓存（配置落盘由 config_service 负责）。"""
    global _config_cache
    _config_cache = config


def invalidate_cache() -> None:
    """使缓存失效，下次 get_config 重新从磁盘加载。"""
    global _config_cache
    _config_cache = None
