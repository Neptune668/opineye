"""可插拔大模型适配层：LLMClient 接口与规则/LLM 双实现。

LLM 模式：通过统一接口接入大模型 API，实现观点聚类/风险润色等增强。
未配置密钥时自动回退规则模式（保证离线可运行）。
"""

from __future__ import annotations

from typing import Protocol

from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)


class LLMClient(Protocol):
    """大模型客户端接口（契约，冻结）。"""

    def available(self) -> bool: ...

    def analyze(self, text: str, task: str) -> str: ...


class RuleLLMClient:
    """规则回退实现：不调用任何外部服务，直接返回原文。

    当未配置 LLM 密钥或调用失败时使用，保证分析流程不中断。
    """

    def available(self) -> bool:
        return False

    def analyze(self, text: str, task: str) -> str:
        return text


class HttpLLMClient:
    """HTTP 大模型实现：通过 LangChain 的 OpenAI 兼容封装调用（Moonshot / OpenAI 等）。

    未配置密钥时 available() 返回 False，由上层回退到规则实现。
    """

    def __init__(self) -> None:
        self._api_key = settings.llm_api_key
        self._base_url = settings.llm_base_url or "https://api.openai.com/v1"
        self._model = settings.llm_model or "gpt-4o-mini"
        self._chat = None

    def available(self) -> bool:
        return bool(self._api_key)

    def _client(self):
        """懒加载 ChatOpenAI 客户端（未配置/未安装依赖时不触发 import）。"""
        if self._chat is None:
            from langchain_openai import ChatOpenAI

            self._chat = ChatOpenAI(
                model=self._model,
                api_key=self._api_key,
                base_url=self._base_url,
                # 思考类模型（如 kimi-k2.6）仅接受 temperature=1，省略则用模型默认值
            )
        return self._chat

    def analyze(self, text: str, task: str) -> str:
        resp = self._client().invoke(
            [
                ("system", f"你是舆情分析助手，请完成以下任务：{task}"),
                ("human", text),
            ]
        )
        content = resp.content
        return content if isinstance(content, str) else str(content)


class FallbackLLMClient:
    """带自动回退的 LLM 客户端：优先 LLM，失败回退规则。

    供上层（SearchEngine）统一调用，屏蔽可用性细节。
    """

    def __init__(self, primary: LLMClient, fallback: LLMClient) -> None:
        self._primary = primary
        self._fallback = fallback

    def available(self) -> bool:
        return self._primary.available()

    def analyze(self, text: str, task: str) -> str:
        if not self._primary.available():
            return self._fallback.analyze(text, task)
        try:
            return self._primary.analyze(text, task)
        except Exception:  # noqa: BLE001 - LLM 异常回退规则
            logger.exception("LLM 调用失败，回退规则模式")
            return self._fallback.analyze(text, task)


def build_llm_client() -> LLMClient:
    """构建 LLM 客户端：LLM 主实现 + 规则回退。"""
    return FallbackLLMClient(primary=HttpLLMClient(), fallback=RuleLLMClient())
