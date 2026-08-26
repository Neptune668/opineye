"""单功能应用输出查看模块：AppOutputReader 接口与文件实现。

职责：读取单功能应用的标准输出/错误输出与最近文本输出。
对应需求 2.2.7 文件布局：
  - runtime/apps/{app_name}.log        标准输出与错误输出
  - outputs/{app_name}/latest.txt      最近一次文本输出结果
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from app.utils.storage import OUTPUTS_DIR, RUNTIME_DIR, write_text


def write_output(app_name: str, text: str) -> None:
    """将应用最近一次文本输出落盘到 outputs/{app_name}/latest.txt。

    对应需求 2.2.7：保存单功能应用最近一次文本输出结果，
    供 /api/output/{app_name} 查询。
    """
    if not text:
        return
    write_text(OUTPUTS_DIR / app_name / "latest.txt", text)


class AppOutputReader(Protocol):
    """应用输出读取接口（契约，冻结）。"""

    def read_output(self, app_name: str) -> str: ...

    def read_log(self, app_name: str, tail: int = 200) -> list[str]: ...


class FileAppOutputReader:
    """基于文件的应用输出读取实现。"""

    def __init__(self, runtime_dir: Path = RUNTIME_DIR, outputs_dir: Path = OUTPUTS_DIR) -> None:
        self._runtime_dir = runtime_dir
        self._outputs_dir = outputs_dir

    def read_output(self, app_name: str) -> str:
        """读取应用最近一次文本输出（outputs/{app}/latest.txt）。"""
        path = self._outputs_dir / app_name / "latest.txt"
        if not path.exists():
            return ""
        return path.read_text(encoding="utf-8")

    def read_log(self, app_name: str, tail: int = 200) -> list[str]:
        """读取应用日志末尾 tail 行（runtime/apps/{app}.log）。"""
        path = self._runtime_dir / "apps" / f"{app_name}.log"
        if not path.exists():
            return []
        lines = path.read_text(encoding="utf-8").splitlines()
        return lines[-tail:] if tail > 0 else lines
