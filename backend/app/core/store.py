"""文件读写工具。

提供：
- 数据目录初始化
- JSON 安全读写（临时文件 + 原子替换 + 文件锁）
- 日志追加（加锁，避免并发交叉写入）
"""
from __future__ import annotations

import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Any

from filelock import FileLock

from app.config import DEFAULT_CONFIG, load_config
from app.settings import CONFIG_PATH, REQUIRED_DIRS

logger = logging.getLogger(__name__)

# 用于文件锁的锁文件目录（与数据文件同目录，后缀 .lock）
_LOCK_SUFFIX = ".lock"


def _lock_path(path: Path) -> Path:
    return Path(str(path) + _LOCK_SUFFIX)


def ensure_data_dirs() -> None:
    """确保 DATA_ROOT 下必要目录存在，config.json 不存在则写入默认模板。"""
    for d in REQUIRED_DIRS:
        d.mkdir(parents=True, exist_ok=True)

    if not CONFIG_PATH.exists():
        write_json(CONFIG_PATH, DEFAULT_CONFIG)
        logger.info("已生成默认配置 %s", CONFIG_PATH)


def read_json(path: Path, default: Any = None) -> Any:
    """读取并解析 JSON，文件不存在返回 default。"""
    if not path.exists():
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Any) -> None:
    """原子写 JSON：先写临时文件，再加锁 os.replace 替换。"""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # 先写临时文件（同目录，保证 os.replace 原子性）
    fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        # 加锁后原子替换，避免跨进程写冲突
        with FileLock(str(_lock_path(path))):
            os.replace(tmp_name, path)
    except Exception:
        # 清理临时文件后重新抛出
        if os.path.exists(tmp_name):
            os.remove(tmp_name)
        raise


def append_log(path: Path, line: str) -> None:
    """追加一行日志（加锁，避免多进程/协程交叉写入）。"""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with FileLock(str(_lock_path(path))):
        with open(path, "a", encoding="utf-8") as f:
            f.write(line)
            if not line.endswith("\n"):
                f.write("\n")
            f.flush()
