"""可插拔数据源适配器框架。

提供统一的 DataSource 抽象，支持从 config.json 配置数据源类型，
实现 news / image / video / forum_post 等来源的采集。

数据源类型：
  - file：从本地 JSON 文件读取（离线可用，默认）
  - http：从 HTTP 接口获取（需配置 url，后续接入真实数据源）
  - tavily：通过 Tavily Search API 获取真实网络搜索结果

配置约定（config.json 的 "datasources" 段）：
  {
    "datasources": {
      "news":      { "type": "tavily", "topic": "news" },
      "image":     { "type": "file", "path": "data/image.json" },
      "video":     { "type": "file", "path": "data/video.json" },
      "forum_post":{ "type": "file", "path": "data/forum_post.json" }
    }
  }
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from app.services.collect_models import SourceItem
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


class TavilyDataSource:
    """Tavily 搜索数据源：通过 Tavily Search API 获取真实网络搜索结果。

    API：POST https://api.tavily.com/search
    认证：Header Authorization: Bearer tvly-{api_key}
    响应 results[] 含 title/url/content/score。
    """

    ENDPOINT = "https://api.tavily.com/search"

    def __init__(self, api_key: str, topic: str = "general", max_results: int = 10) -> None:
        self._api_key = api_key
        self._topic = topic
        self._max_results = max_results

    def fetch(self, query: str) -> list[SourceItem]:
        if not self._api_key:
            logger.warning("Tavily API Key 未配置，跳过采集")
            return []
        import requests

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "query": query,
            "topic": self._topic,
            "max_results": self._max_results,
            "include_answer": False,
            "search_depth": "basic",
        }
        try:
            resp = requests.post(self.ENDPOINT, json=payload, headers=headers, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except Exception:  # noqa: BLE001 - 网络异常返回空，不影响其他来源
            logger.exception("Tavily 搜索失败", extra={"query": query})
            return []

        results = data.get("results", [])
        return [
            SourceItem(
                source_type="news",
                title=r.get("title", ""),
                url=r.get("url"),
                summary=r.get("content"),
                published_at=None,
            )
            for r in results
            if isinstance(r, dict)
        ]


class ZhihuDataSource:
    """知乎热榜数据源：调用知乎热榜接口获取热搜数据。

    API：GET https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total
    需携带 Cookie（登录态）访问，否则返回 401。
    返回 data[]，每项含 target.title、target.url、detail_text（热度）。
    映射为 forum_post 来源（论坛帖子）。
    """

    ENDPOINT = "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total"

    def __init__(self, source_type: str = "forum_post", max_results: int = 20, z_c0: str = "") -> None:
        self._source_type = source_type
        self._max_results = max_results
        self._z_c0 = z_c0

    def fetch(self, query: str) -> list[SourceItem]:
        import requests

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            "Referer": "https://www.zhihu.com/hot",
            "Accept": "application/json, text/plain, */*",
        }
        if self._z_c0:
            headers["Cookie"] = f"z_c0={self._z_c0}"
        else:
            logger.warning("知乎 z_c0 未配置，热榜接口可能返回 401")

        try:
            resp = requests.get(self.ENDPOINT, headers=headers, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except Exception:  # noqa: BLE001 - 网络异常返回空，降级到 file 数据源
            logger.exception("知乎热榜抓取失败")
            return []

        items: list[SourceItem] = []
        for item in data.get("data", [])[: self._max_results]:
            if not isinstance(item, dict):
                continue
            target = item.get("target") or {}
            title = target.get("title") or ""
            url = target.get("url") or ""
            hot = item.get("detail_text") or ""
            if not title:
                continue
            items.append(
                SourceItem(
                    source_type=self._source_type,
                    title=title,
                    url=url,
                    summary=hot,
                    published_at=None,
                )
            )
        logger.info("知乎热榜采集完成", extra={"count": len(items)})
        return items


def build_datasource(config: dict[str, Any]) -> DataSource:
    """根据配置构建数据源适配器。

    config 形如 {"type": "file", "path": "data/news.json"}
    或 {"type": "tavily", "topic": "news"}
    或 {"type": "zhihu", "source_type": "forum_post"}
    """
    ds_type = config.get("type", "file")
    if ds_type == "file":
        return FileDataSource(config.get("path", ""))
    if ds_type == "http":
        return HttpDataSource(config.get("url", ""))
    if ds_type == "tavily":
        from app.config import settings

        return TavilyDataSource(
            api_key=settings.tavily_api_key,
            topic=config.get("topic", "general"),
            max_results=int(config.get("max_results", 10)),
        )
    if ds_type == "zhihu":
        from app.config import settings

        return ZhihuDataSource(
            source_type=config.get("source_type", "forum_post"),
            max_results=int(config.get("max_results", 20)),
            z_c0=settings.z_c0,
        )
    raise ValueError(f"未知数据源类型：{ds_type}")
