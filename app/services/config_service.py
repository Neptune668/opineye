"""配置模块：ConfigService 接口与实现。

职责：读取/保存 config.json、运行参数热更新、版本乐观锁。
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Protocol

from app.exceptions import VersionConflictError
from app.utils.logging import get_logger
from app.utils.storage import CONFIG_PATH, read_json, write_json

logger = get_logger(__name__)


@dataclass(frozen=True)
class Config:
    """配置数据对象（不可变快照）。"""

    data: dict[str, Any]
    version: int


class ConfigService(Protocol):
    """配置服务接口（契约，冻结）。"""

    def read(self) -> Config: ...

    def save(self, data: dict[str, Any], expected_version: int) -> Config: ...

    def watch(self, key: str, callback: Callable[[Any], None]) -> None: ...


class JsonConfigService:
    """基于 config.json 的配置服务实现，进程内线程安全。"""

    def __init__(self, path: Path = CONFIG_PATH) -> None:
        self._path = path
        self._lock = threading.RLock()
        self._watchers: dict[str, list[Callable[[Any], None]]] = {}
        self._cache: Config | None = None

    def read(self) -> Config:
        with self._lock:
            if self._cache is not None:
                return self._cache
            data = read_json(self._path, default={})
            version = int(data.get("version", 0))
            self._cache = Config(data=data, version=version)
            return self._cache

    def save(self, data: dict[str, Any], expected_version: int) -> Config:
        with self._lock:
            current = self.read()
            if current.version != expected_version:
                raise VersionConflictError(
                    f"配置版本冲突：期望 {expected_version}，实际 {current.version}"
                )
            new_version = current.version + 1
            new_data = {**data, "version": new_version}
            write_json(self._path, new_data)
            self._cache = Config(data=new_data, version=new_version)
            self._notify(new_data)
            logger.info("配置已更新", extra={"version": new_version})
            return self._cache

    def watch(self, key: str, callback: Callable[[Any], None]) -> None:
        with self._lock:
            self._watchers.setdefault(key, []).append(callback)

    def _notify(self, data: dict[str, Any]) -> None:
        """配置变更后触发对应 key 的 watcher，实现运行参数热更新。"""
        for key, callbacks in self._watchers.items():
            if key in data:
                for cb in callbacks:
                    try:
                        cb(data[key])
                    except Exception:  # noqa: BLE001
                        logger.exception("配置 watcher 执行异常 key=%s", key)
