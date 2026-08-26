"""论坛采集应用（单功能应用子进程入口）。"""
from __future__ import annotations

import sys


def main() -> None:
    print("[forum] 论坛采集应用已启动")
    print("[forum] 开始采集论坛帖子...")
    print("[forum] 论坛采集完成")


if __name__ == "__main__":
    main()
    sys.exit(0)
