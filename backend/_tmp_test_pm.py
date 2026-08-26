import asyncio
from app.core.process_manager import process_manager as pm


async def t():
    print("start:", await pm.start("search"))
    await asyncio.sleep(4)
    print("status after:", pm.status("search"))
    print("log tail:", await pm.read_log("search", 5))
    await pm.stop("search")
    print("final:", pm.status("search"))


asyncio.run(t())
