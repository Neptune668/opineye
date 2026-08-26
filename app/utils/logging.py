"""结构化日志封装。

输出 JSON 结构化日志，字段：ts、level、module、task_id、message、extra。
"""

from __future__ import annotations

import json
import logging
import sys
import time
from typing import Any

from app.config import settings


class JsonFormatter(logging.Formatter):
    """将日志记录格式化为单行 JSON。"""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": time.time(),
            "level": record.levelname,
            "module": record.name,
            "message": record.getMessage(),
        }
        task_id = getattr(record, "task_id", None)
        if task_id:
            payload["task_id"] = task_id
        extra = getattr(record, "extra", None)
        if extra:
            payload["extra"] = extra
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def get_logger(name: str) -> logging.Logger:
    """获取模块级 logger，避免重复添加 handler。"""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
        logger.setLevel(settings.log_level.upper())
        logger.propagate = False
    return logger
