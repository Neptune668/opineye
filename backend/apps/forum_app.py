"""论坛采集应用（单功能应用子进程入口）。

启动后执行一轮论坛采集（复用 forum_service 的采集逻辑，采集固定次数后完成）。
"""
from __future__ import annotations

import asyncio
import sys

from app.services import forum_service


async def main() -> None:
    print("[forum] 论坛采集应用已启动")

    # 复用论坛采集服务：写入日志 + 归档历史
    await forum_service.start_collection()
    print("[forum] 采集任务已启动，开始采集...")

    # 采集 3 轮（每轮 1 秒），模拟真实采集过程
    for i in range(3):
        await asyncio.sleep(1)
        print(f"[forum] 采集第 {i + 1} 轮，累计 { (i + 1) * 12 } 条帖子")

    await forum_service.stop_collection()
    print("[forum] 论坛采集完成")


if __name__ == "__main__":
    asyncio.run(main())
    sys.exit(0)
