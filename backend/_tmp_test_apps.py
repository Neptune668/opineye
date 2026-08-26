import asyncio
from app.main import app
from app.core.process_manager import process_manager as pm


async def run_one(name, wait=3):
    print(f"===== 启动 {name} =====")
    ok = await pm.start(name)
    print(f"start 返回: {ok}")
    await asyncio.sleep(wait)
    print(f"状态: {pm.status(name)}")
    log = await pm.read_log(name, 30)
    print(f"--- {name} 日志 ---")
    for line in log:
        print("  ", line)
    await pm.stop(name)
    print(f"停止后状态: {pm.status(name)}")
    print()


async def main():
    await run_one("search", wait=4)
    await run_one("media", wait=3)
    await run_one("insight", wait=3)
    await run_one("report", wait=3)
    await run_one("forum", wait=5)


asyncio.run(main())
