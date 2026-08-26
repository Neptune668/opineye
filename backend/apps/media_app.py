"""多媒体检索应用（单功能应用子进程入口）。

启动后检索多媒体来源（image/video），复用 search_service 真实采集逻辑。
"""
from __future__ import annotations

import asyncio
import sys

from app.services import search_service


async def main() -> None:
    topic = "多媒体内容示例"
    source_types = ["image", "video"]

    print(f"[media] 开始多媒体检索：{topic}")
    print(f"[media] 来源类型：{', '.join(source_types)}")

    record = await search_service.search(topic, source_types)
    image_count = sum(1 for it in record["items"] if it["source_type"] == "image")
    video_count = sum(1 for it in record["items"] if it["source_type"] == "video")
    print(f"[media] 图片来源：{image_count} 条，视频来源：{video_count} 条")
    print("[media] 多媒体检索完成")


if __name__ == "__main__":
    asyncio.run(main())
    sys.exit(0)
