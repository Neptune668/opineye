"""LLM 连通性测试：用 LangChain 的 OpenAI 兼容封装调用 Moonshot。

用法：
    .venv/Scripts/python.exe test/llm_test.py
"""

from __future__ import annotations

from app.analysis.llm import HttpLLMClient
from app.config import settings


def main() -> None:
    print(f"base_url = {settings.llm_base_url}")
    print(f"model    = {settings.llm_model}")
    print(f"key_set  = {bool(settings.llm_api_key)}")

    client = HttpLLMClient()
    try:
        out = client.analyze("请用一句话介绍什么是舆情分析。", "写一句简短介绍")
        print("SUCCESS:")
        print(out)
    except Exception as e:  # noqa: BLE001 - 测试需打印原始异常
        print(f"FAILED: {type(e).__name__}: {e}")


if __name__ == "__main__":
    main()