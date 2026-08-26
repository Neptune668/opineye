"""uvicorn 启动脚本。

用法：
    python run.py
等价于：
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
"""
import asyncio
import sys

import uvicorn

# Windows 上 asyncio 子进程需要 ProactorEventLoop（必须在 uvicorn 创建 loop 前设置）
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
