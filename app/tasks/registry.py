"""应用注册表：app_name → Celery Task 映射。

应用清单从 config.json 的 apps 段读取，避免硬编码。
每个 app_name 映射到真实任务（T6/T7 整合后）。
"""

from __future__ import annotations

from dataclasses import dataclass

from app.utils.constants import AppState

# 应用名称 → 真实任务名
DEFAULT_APPS: dict[str, str] = {
    "topic_search": "opineye.topic_search",
    "media_search": "opineye.media_search",
    "forum_collect": "opineye.forum_collect",
    "insight": "opineye.insight",
    "report": "opineye.report",
    "graph": "opineye.graph",
}


@dataclass(frozen=True)
class AppSpec:
    """应用规格定义。"""

    app_name: str
    task_name: str


class AppRegistry:
    """应用注册表，维护 app_name 到任务的映射。"""

    def __init__(self, apps: dict[str, str] | None = None) -> None:
        self._apps: dict[str, str] = dict(apps or DEFAULT_APPS)

    def get(self, app_name: str) -> AppSpec | None:
        task_name = self._apps.get(app_name)
        if task_name is None:
            return None
        return AppSpec(app_name=app_name, task_name=task_name)

    def names(self) -> list[str]:
        return list(self._apps.keys())

    def __contains__(self, app_name: str) -> bool:
        return app_name in self._apps
