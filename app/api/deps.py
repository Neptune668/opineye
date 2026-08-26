"""FastAPI 鉴权依赖：从 Authorization 头解析 token 并校验角色。

三种角色（需求文档 2.2.2）：
  - admin（系统管理员）：全部权限
  - operator（操作用户）：启停应用、发起检索、查看输出
  - viewer（报告查看人）：只读（报告/图谱/论坛日志/来源证据）
"""

from __future__ import annotations

from fastapi import Header

from app.services.auth_service import (
    ROLE_ADMIN,
    ROLE_OPERATOR,
    ROLE_VIEWER,
    TokenPayload,
    UnauthorizedError,
    decode_token,
    role_at_least,
)


def _parse_token(authorization: str | None) -> TokenPayload:
    if not authorization or not authorization.startswith("Bearer "):
        raise UnauthorizedError("缺少 Authorization 头")
    token = authorization[len("Bearer "):].strip()
    return decode_token(token)


def get_current_user(authorization: str | None = Header(None)) -> TokenPayload:
    """解析当前登录用户（任意角色）。"""
    return _parse_token(authorization)


def require_viewer(authorization: str | None = Header(None)) -> TokenPayload:
    """要求 viewer 及以上角色（只读查看）。"""
    payload = _parse_token(authorization)
    if not role_at_least(payload.role, ROLE_VIEWER):
        from app.services.auth_service import ForbiddenError
        raise ForbiddenError(f"角色 {payload.role} 无权访问该资源")
    return payload


def require_operator(authorization: str | None = Header(None)) -> TokenPayload:
    """要求 operator 及以上角色（可操作/检索）。"""
    payload = _parse_token(authorization)
    if not role_at_least(payload.role, ROLE_OPERATOR):
        from app.services.auth_service import ForbiddenError
        raise ForbiddenError(f"角色 {payload.role} 无权访问该资源")
    return payload


def require_admin(authorization: str | None = Header(None)) -> TokenPayload:
    """要求 admin 角色（系统管理员）。"""
    payload = _parse_token(authorization)
    if not role_at_least(payload.role, ROLE_ADMIN):
        from app.services.auth_service import ForbiddenError
        raise ForbiddenError(f"角色 {payload.role} 无权访问该资源")
    return payload


# 向后兼容别名：旧代码中 require_user 等价于 operator 及以上
require_user = require_operator
