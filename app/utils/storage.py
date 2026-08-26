"""文件存储封装：统一处理 config.json、runtime、reports、graphs、outputs 的读写。

对应需求 2.2.7 的文件布局。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# 项目根目录（app/utils/ 的上级上级）
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

CONFIG_PATH = PROJECT_ROOT / "config.json"
RUNTIME_DIR = PROJECT_ROOT / "runtime"
REPORTS_DIR = PROJECT_ROOT / "reports"
GRAPHS_DIR = PROJECT_ROOT / "graphs"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
FORUM_DIR = RUNTIME_DIR / "forum"


def ensure_dirs() -> None:
    """初始化运行所需的目录结构。"""
    for d in (RUNTIME_DIR, FORUM_DIR, REPORTS_DIR, GRAPHS_DIR, OUTPUTS_DIR):
        d.mkdir(parents=True, exist_ok=True)


def read_json(path: Path, default: Any) -> Any:
    """读取 JSON 文件，不存在时返回默认值。"""
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Any) -> None:
    """写入 JSON 文件，自动创建父目录。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def read_text(path: Path, default: str = "") -> str:
    """读取文本文件，不存在时返回默认值。"""
    if not path.exists():
        return default
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    """写入文本文件，自动创建父目录。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def append_text(path: Path, content: str) -> None:
    """追加写入文本文件（用于日志追加）。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(content)
