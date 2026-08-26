"""应用注册表：app_name → Celery Task 映射。

应用清单从 config.json 的 apps 段读取，避免硬编码。
"""

from __future__ import annotations

from dataclasses import dataclass

from app.utils.constants import AppState

# 应用名称 → 占位任务名（T4 阶段统一指向 placeholder_task）
DEFAULT_APPS: dict[str, str] = {
    "topic_search": "opineye.placeholder",
    "media_search": "opineye.placeholder",
    "forum_collect": "opineye.placeholder",
    "insight": "opineye.placeholder",
    "report": "opineye.placeholder",
    "graph": "opineye.placeholder",
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
