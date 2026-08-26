"""全局配置加载（pydantic-settings），读取 .env 与环境变量。"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用运行时配置，来源于 .env 与环境变量。"""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    env: str = "dev"
    database_url: str = "mysql+pymysql://root:password@localhost:3306/opineye"
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"

    # 仓储后端：mysql | memory
    repo_backend: str = "mysql"

    log_level: str = "DEBUG"

    # LLM（可选）
    llm_api_key: str = ""
    llm_base_url: str = ""
    llm_model: str = ""

    # Tavily 搜索
    tavily_api_key: str = ""

    # 知乎（z_c0 登录凭证，用于访问热榜接口）
    z_c0: str = ""

    secret_key: str = "change-me"


@lru_cache
def get_settings() -> Settings:
    """进程内单例，避免重复解析 .env。"""
    return Settings()


settings = get_settings()
