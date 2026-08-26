"""论坛采集模块：ForumCollector 接口与实现。

职责：论坛采集任务控制、日志输出、历史记录保存。
状态机：idle → running → stopped → failed。

实现：
  - ZhihuForumCollector：轮询知乎热榜（ZhihuDataSource）产出真实日志，
    无 z_c0 或抓取失败时回退本地 file 数据源。
  - SimulatedForumCollector：模拟事件，作为降级兜底。

文件布局（对应需求 2.2.7）：
  - runtime/forum/latest.log        最新运行日志
  - runtime/forum/history/{date}.json  历史记录归档
  - outputs/forum_collect/latest.txt  最近采集结果
"""

from __future__ import annotations

import json
import random
import threading
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Protocol

from app.services.datasource import FileDataSource, ZhihuDataSource
from app.services.output_service import write_output
from app.utils.constants import ForumState
from app.utils.logging import get_logger
from app.utils.storage import FORUM_DIR

logger = get_logger(__name__)


@dataclass(frozen=True)
class ForumLogEntry:
    """论坛日志条目（对应需求 2.2.8：时间、事件类型、消息内容、任务状态）。"""

    ts: str
    event_type: str
    message: str
    task_status: str


class ForumCollector(Protocol):
    """论坛采集接口（契约，冻结）。"""

    def start(self) -> None: ...

    def stop(self) -> None: ...

    def latest_log(self, tail: int = 200) -> list[ForumLogEntry]: ...

    def history(self, date: str) -> list[ForumLogEntry]: ...


class _BaseForumCollector:
    """论坛采集器基类：负责状态机、线程循环与文件日志/归档。

    子类实现 _poll_once() 决定每次轮询产出的日志事件。
    """

    def __init__(self, forum_dir: Path = FORUM_DIR, poll_interval: float = 10.0) -> None:
        self._forum_dir = forum_dir
        self._poll_interval = poll_interval
        self._latest_path = forum_dir / "latest.log"
        self._history_dir = forum_dir / "history"
        self._lock = threading.RLock()
        self._state = ForumState.IDLE
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    # ---- 对外接口 ----

    def start(self) -> None:
        with self._lock:
            if self._state == ForumState.RUNNING:
                return
            self._state = ForumState.RUNNING
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()
        self._append("start", "论坛采集已启动", ForumState.RUNNING.value)
        logger.info("论坛采集启动")

    def stop(self) -> None:
        with self._lock:
            if self._state != ForumState.RUNNING:
                return
            self._state = ForumState.STOPPED
            self._stop_event.set()
        self._append("stop", "论坛采集已停止", ForumState.STOPPED.value)
        self._archive_today()
        logger.info("论坛采集停止")

    def latest_log(self, tail: int = 200) -> list[ForumLogEntry]:
        return self._read_log(self._latest_path, tail)

    def history(self, date: str) -> list[ForumLogEntry]:
        path = self._history_dir / f"{date}.json"
        if not path.exists():
            return []
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            return [ForumLogEntry(**x) for x in raw]
        except (json.JSONDecodeError, TypeError):
            logger.exception("历史日志解析失败", extra={"date": date})
            return []

    # ---- 内部 ----

    def _run(self) -> None:
        """采集循环：定时调用子类 _poll_once 产出日志事件。"""
        while not self._stop_event.is_set():
            try:
                self._poll_once()
            except Exception:  # noqa: BLE001 - 单次轮询异常不中断循环
                logger.exception("论坛采集轮询异常")
            self._stop_event.wait(self._poll_interval)

    def _poll_once(self) -> None:  # pragma: no cover - 由子类实现
        raise NotImplementedError

    def _append(self, event_type: str, message: str, task_status: str) -> None:
        entry = ForumLogEntry(
            ts=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            event_type=event_type,
            message=message,
            task_status=task_status,
        )
        line = json.dumps(asdict(entry), ensure_ascii=False) + "\n"
        with self._lock:
            self._forum_dir.mkdir(parents=True, exist_ok=True)
            with self._latest_path.open("a", encoding="utf-8") as f:
                f.write(line)

    def _read_log(self, path: Path, tail: int) -> list[ForumLogEntry]:
        if not path.exists():
            return []
        lines = path.read_text(encoding="utf-8").splitlines()
        result: list[ForumLogEntry] = []
        for line in lines[-tail:]:
            try:
                result.append(ForumLogEntry(**json.loads(line)))
            except (json.JSONDecodeError, TypeError):
                continue
        return result

    def _archive_today(self) -> None:
        """将今日日志归档到 history/{date}.json（覆盖合并，保证幂等）。"""
        date_str = datetime.now().strftime("%Y-%m-%d")
        entries = self.latest_log(tail=10000)
        self._history_dir.mkdir(parents=True, exist_ok=True)
        path = self._history_dir / f"{date_str}.json"
        path.write_text(
            json.dumps([asdict(e) for e in entries], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


class SimulatedForumCollector(_BaseForumCollector):
    """模拟论坛采集器：定时产出示例日志事件（降级兜底）。"""

    _EVENTS = [
        ("connect", "已连接论坛数据源"),
        ("fetch", "拉取新帖列表"),
        ("parse", "解析帖子内容"),
        ("store", "保存采集结果"),
        ("update", "更新采集游标"),
    ]

    def _poll_once(self) -> None:
        event_type, message = random.choice(self._EVENTS)
        self._append(event_type, message, ForumState.RUNNING.value)


class ZhihuForumCollector(_BaseForumCollector):
    """知乎热榜论坛采集器：轮询知乎热榜，产出真实日志。

    无 z_c0 或抓取失败时回退本地 file 数据源；按标题去重，
    仅记录新出现的热榜条目，并将最新热榜落盘到 outputs/forum_collect/latest.txt。
    """

    def __init__(
        self,
        forum_dir: Path = FORUM_DIR,
        poll_interval: float = 10.0,
        max_results: int = 20,
        z_c0: str = "",
        fallback_path: str = "data/forum_post.json",
    ) -> None:
        super().__init__(forum_dir=forum_dir, poll_interval=poll_interval)
        self._max_results = max_results
        self._source = ZhihuDataSource(
            source_type="forum_post", max_results=max_results, z_c0=z_c0
        )
        self._fallback = FileDataSource(fallback_path)
        self._seen: set[str] = set()

    def _poll_once(self) -> None:
        items = self._source.fetch("")
        if not items:
            # 无 z_c0 / 抓取失败：回退本地 file 数据源
            items = self._fallback.fetch("")

        if not items:
            self._append("fetch", "未获取到热榜数据（无 z_c0 或数据源不可用）", ForumState.RUNNING.value)
            return

        new_items = [it for it in items if it.title not in self._seen]
        for it in new_items[: self._max_results]:
            self._append("fetch", f"热榜：{it.title}", ForumState.RUNNING.value)
            self._seen.add(it.title)
        if new_items:
            self._append("store", f"本次采集 {len(new_items)} 条新帖", ForumState.RUNNING.value)

        # 落盘最近采集结果，供 /api/output/forum_collect 查询
        write_output("forum_collect", "\n".join(it.title for it in items))
