"""配置服务：配置读取、保存、热更新。"""
from __future__ import annotations

import logging
from typing import Any

from app import settings
from app.core import store
from app.config import get_config, invalidate_cache

logger = logging.getLogger(__name__)


def get_config() -> dict[str, Any]:
    """读取当前配置。"""
    return store.read_json(settings.CONFIG_PATH, default={})


def update_config(new_config: dict[str, Any]) -> dict[str, Any]:
    """更新配置：先备份，再落盘，最后刷新缓存实现热更新。"""
    # 备份当前配置
    if settings.CONFIG_PATH.exists():
        backup_path = settings.CONFIG_PATH.with_suffix(".json.bak")
        store.write_text(backup_path, settings.CONFIG_PATH.read_text(encoding="utf-8"))

    store.write_json(settings.CONFIG_PATH, new_config)
    invalidate_cache()  # 使缓存失效，下次读取生效
    logger.info("配置已更新并热生效")
    return new_config
