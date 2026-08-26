"""系统/应用/论坛状态枚举与来源类型常量（契约，冻结）。"""

from __future__ import annotations

from enum import Enum


class AppState(str, Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    FAILED = "failed"


class ForumState(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    STOPPED = "stopped"
    FAILED = "failed"


class SystemState(str, Enum):
    OFFLINE = "offline"
    STARTING = "starting"
    ONLINE = "online"
    SHUTTING_DOWN = "shutting_down"


class SourceType(str, Enum):
    NEWS = "news"
    IMAGE = "image"
    VIDEO = "video"
    FORUM_POST = "forum_post"
    INTERNAL_DATA = "internal_data"
