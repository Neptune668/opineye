"""主题检索应用（单功能应用子进程入口）。

以子进程运行，输出到 stdout（由 ProcessManager 采集）。
"""
from __future__ import annotations

import asyncio
import sys


async def main() -> None:
    print("[search] 主题检索应用已启动")
    print("[search] 等待检索任务...（示例输出）")
    # 演示：输出几行日志后正常退出
    for i in range(3):
        print(f"[search] 处理批次 {i + 1}")
        await asyncio.sleep(1)
    print("[search] 检索应用正常退出")


if __name__ == "__main__":
    asyncio.run(main())
    sys.exit(0)
