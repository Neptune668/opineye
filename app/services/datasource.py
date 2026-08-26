"""可插拔数据源适配器框架。

提供统一的 DataSource 抽象，支持从 config.json 配置数据源类型，
实现 news / image / video / forum_post 等来源的采集。

数据源类型：
  - file：从本地 JSON 文件读取（离线可用，默认）
  - http：从 HTTP 接口获取（需配置 url，后续接入真实数据源）

配置约定（config.json 的 "datasources" 段）：
  {
    "datasources": {
      "news":      { "type": "file", "path": "data/news.json" },
      "image":     { "type": "file", "path": "data/image.json" },
      "video":     { "type": "file", "path": "data/video.json" },
      "forum_post":{ "type": "file", "path": "data/forum_post.json" }
    }
  }

真实数据源接入方式：将 type 改为 "http" 并配置 url 即可，不改采集逻辑。
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from app.services.collector import CollectRequest, SourceItem
from app.utils.logging import get_logger
from app.utils.storage import PROJECT_ROOT

logger = get_logger(__name__)


class DataSource(Protocol):
    """数据源接口（契约，冻结）。"""

    def fetch(self, query: str) -> list[SourceItem]: ...


@dataclass(frozen=True)
class FileSourceConfig:
    """文件数据源配置。"""

    path: str


class FileDataSource:
    """文件数据源：从本地 JSON 文件读取预置数据。

    文件结构为 SourceItem 列表，按 query 做标题/摘要关键词过滤。
    """

    def __init__(self, path: str) -> None:
        self._path = PROJECT_ROOT / path

    def fetch(self, query: str) -> list[SourceItem]:
        if not self._path.exists():
            logger.warning("数据源文件不存在", extra={"path": str(self._path)})
            return []
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            logger.exception("数据源文件解析失败", extra={"path": str(self._path)})
            return []
        items = [self._to_item(x) for x in raw if isinstance(x, dict)]
        q = query.strip().lower()
        if not q:
            return items
        return [it for it in items if q in it.title.lower() or (it.summary or "").lower().find(q) >= 0]

    @staticmethod
    def _to_item(x: dict) -> SourceItem:
        return SourceItem(
            source_type=x.get("source_type", "unknown"),
            title=x.get("title", ""),
            url=x.get("url"),
            summary=x.get("summary"),
            published_at=x.get("published_at"),
        )


class HttpDataSource:
    """HTTP 数据源：从配置的 HTTP 接口获取数据。

    接口约定：GET {url}?query={query}，返回 SourceItem 列表 JSON。
    用于后续接入真实公开信息/论坛数据源。
    """

    def __init__(self, url: str) -> None:
        self._url = url

    def fetch(self, query: str) -> list[SourceItem]:
        import requests

        resp = requests.get(self._url, params={"query": query}, timeout=30)
        resp.raise_for_status()
        raw = resp.json()
        return [SourceItem(**x) for x in raw if isinstance(x, dict)]


def build_datasource(config: dict[str, Any]) -> DataSource:
    """根据配置构建数据源适配器。

    config 形如 {"type": "file", "path": "data/news.json"}
    """
    ds_type = config.get("type", "file")
    if ds_type == "file":
        return FileDataSource(config.get("path", ""))
    if ds_type == "http":
        return HttpDataSource(config.get("url", ""))
    raise ValueError(f"未知数据源类型：{ds_type}")
