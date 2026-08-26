"""FastAPI 鉴权依赖：从 Authorization 头解析 token 并校验角色。"""

from __future__ import annotations

from fastapi import Header

from app.services.auth_service import (
    ROLE_ROOT,
    ROLE_USER,
    TokenPayload,
    UnauthorizedError,
    decode_token,
    require_role,
)


def _parse_token(authorization: str | None) -> TokenPayload:
    if not authorization or not authorization.startswith("Bearer "):
        raise UnauthorizedError("缺少 Authorization 头")
    token = authorization[len("Bearer "):].strip()
    return decode_token(token)


def get_current_user(authorization: str | None = Header(None)) -> TokenPayload:
    """解析当前登录用户（任意角色）。"""
    return _parse_token(authorization)


def require_user(authorization: str | None = Header(None)) -> TokenPayload:
    """要求 user 及以上角色（user 或 root）。"""
    payload = _parse_token(authorization)
    require_role(payload.role, {ROLE_USER, ROLE_ROOT})
    return payload


def require_admin(authorization: str | None = Header(None)) -> TokenPayload:
    """要求 root 角色。"""
    payload = _parse_token(authorization)
    require_role(payload.role, {ROLE_ROOT})
    return payload
