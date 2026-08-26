"""论坛采集服务：采集任务控制、日志输出、历史归档。

论坛采集状态机：idle → running → stopped / failed
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any

from app import settings
from app.core import store

logger = logging.getLogger(__name__)

# 论坛采集状态
FORUM_IDLE = "idle"
FORUM_RUNNING = "running"
FORUM_STOPPED = "stopped"
FORUM_FAILED = "failed"

_task_status = FORUM_IDLE
_collect_task: asyncio.Task | None = None


def get_task_status() -> str:
    return _task_status


async def start_collection() -> str:
    """启动论坛采集任务。"""
    global _task_status, _collect_task
    if _task_status == FORUM_RUNNING:
        return _task_status

    _task_status = FORUM_RUNNING
    _collect_task = asyncio.create_task(_collect_loop())
    await _append_event("collect", "论坛采集任务已启动", FORUM_RUNNING)
    return _task_status


async def stop_collection() -> str:
    """停止论坛采集任务。"""
    global _task_status, _collect_task
    if _collect_task:
        _collect_task.cancel()
        try:
            await _collect_task
        except asyncio.CancelledError:
            pass
        _collect_task = None
    _task_status = FORUM_STOPPED
    await _append_event("stop", "论坛采集任务已停止", FORUM_STOPPED)
    return _task_status


async def _collect_loop() -> None:
    """采集循环（演示：周期性写入日志条目）。"""
    global _task_status
    try:
        count = 0
        while True:
            count += 1
            await _append_event(
                "collect", f"采集到帖子 {count * 12} 条", FORUM_RUNNING
            )
            await asyncio.sleep(3)
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        _task_status = FORUM_FAILED
        await _append_event("error", f"采集异常：{exc}", FORUM_FAILED)


async def _append_event(event: str, message: str, status: str) -> None:
    """写入 latest.log 并归档到 history/{date}.json。"""
    time_str = datetime.now().isoformat()
    line = f"{time_str} [{event}] {message}"
    store.append_log(settings.FORUM_LATEST_LOG, line)

    entry = {
        "time": time_str,
        "event": event,
        "message": message,
        "task_status": status,
    }
    await _append_history(entry)


async def _append_history(entry: dict[str, Any]) -> None:
    """按日期归档历史日志条目。"""
    date_str = datetime.now().strftime("%Y-%m-%d")
    path = settings.RUNTIME_FORUM_HISTORY_DIR / f"{date_str}.json"
    entries = store.read_json(path, default=[])
    entries.append(entry)
    store.write_json(path, entries)


async def read_latest_log(tail: int = 200) -> list[str]:
    """读取最新日志（尾部）。"""
    if not settings.FORUM_LATEST_LOG.exists():
        return []
    text = settings.FORUM_LATEST_LOG.read_text(encoding="utf-8")
    return text.splitlines()[-tail:]


async def read_history(date: str) -> list[dict[str, Any]]:
    """按日期读取历史日志。"""
    path = settings.RUNTIME_FORUM_HISTORY_DIR / f"{date}.json"
    return store.read_json(path, default=[])
