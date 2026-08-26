"""鉴权模块：密码哈希、JWT 签发/校验、角色权限控制。

三种角色（对应需求文档 2.2.2）：
  - admin：系统管理员（内置，全部权限）
  - operator：操作用户（启停单功能应用、发起主题检索、查看输出）
  - viewer：报告查看人（只读：查看报告/图谱/论坛日志/来源证据）

角色层级：admin > operator > viewer。
初始管理员：admin / 1234
"""

from __future__ import annotations

import hashlib
import hmac
import time
from dataclasses import dataclass

import jwt

from app.config import settings
from app.exceptions import AppError
from app.utils.logging import get_logger

logger = get_logger(__name__)

ROLE_ADMIN = "admin"
ROLE_OPERATOR = "operator"
ROLE_VIEWER = "viewer"

# 兼容旧角色别名（历史数据可能为 root/user，统一映射）
ROLE_ROOT = ROLE_ADMIN
ROLE_USER = ROLE_OPERATOR

# 角色层级（用于「某角色及以上」判断）
_ROLE_RANK = {
    ROLE_VIEWER: 1,
    ROLE_OPERATOR: 2,
    ROLE_ADMIN: 3,
}


def _normalize_role(role: str) -> str:
    """兼容旧角色命名，root -> admin，user -> operator。"""
    return {"root": ROLE_ADMIN, "user": ROLE_OPERATOR}.get(role, role)


def normalize_role(role: str) -> str:
    """公开的角色规范化接口（供 auth 路由使用）。"""
    return _normalize_role(role)


def role_at_least(role: str, minimum: str) -> bool:
    """判断 role 是否达到 minimum 层级。"""
    return _ROLE_RANK.get(_normalize_role(role), 0) >= _ROLE_RANK.get(minimum, 3)


class UnauthorizedError(AppError):
    code = 401
    http_status = 401

    def __init__(self, message: str = "未授权") -> None:
        super().__init__(message)
        self.message = message


class ForbiddenError(AppError):
    code = 403
    http_status = 403

    def __init__(self, message: str = "无权限") -> None:
        super().__init__(message)
        self.message = message


@dataclass(frozen=True)
class TokenPayload:
    """JWT 载荷。"""

    username: str
    role: str


def hash_password(password: str) -> str:
    """使用 HMAC-SHA256 加盐哈希（基于 secret_key），不存明文。"""
    salt = settings.secret_key.encode("utf-8")
    return hmac.new(salt, password.encode("utf-8"), hashlib.sha256).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    """校验密码是否匹配哈希。"""
    return hmac.compare_digest(hash_password(password), password_hash)


def create_token(username: str, role: str) -> str:
    """签发 JWT token，有效期 24 小时。"""
    payload = {
        "username": username,
        "role": _normalize_role(role),
        "exp": int(time.time()) + 24 * 3600,
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def decode_token(token: str) -> TokenPayload:
    """校验并解析 JWT，失败抛出 UnauthorizedError。"""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        return TokenPayload(
            username=payload["username"],
            role=_normalize_role(payload["role"]),
        )
    except jwt.ExpiredSignatureError:
        raise UnauthorizedError("token 已过期")
    except jwt.InvalidTokenError:
        raise UnauthorizedError("token 无效")


def require_role(role: str, allowed_roles: set[str]) -> None:
    """校验角色是否在允许集合内，否则抛 ForbiddenError。"""
    normalized = _normalize_role(role)
    if normalized not in {_normalize_role(r) for r in allowed_roles}:
        raise ForbiddenError(f"角色 {role} 无权访问该资源")
