"""鉴权模块：密码哈希、JWT 签发/校验、角色权限控制。

角色：
  - root：系统管理员（内置，全部权限）
  - user：报告人/操作用户（检索/查看图谱/查看论坛日志等只读权限）
初始密码：1234
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

ROLE_ROOT = "root"
ROLE_USER = "user"

# 各接口所需角色（接口前缀 -> 允许的角色集合）
# user 可访问：检索、图谱查看、论坛查看、报告查看、健康检查
# root 额外可访问：系统启停、配置修改、应用启停、用户管理
USER_ALLOWED_PREFIXES = [
    "/api/search",
    "/api/graph",
    "/api/forum/log",
    "/api/config",  # GET 允许，POST 需 root（见 _check_config）
]


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
        "role": role,
        "exp": int(time.time()) + 24 * 3600,
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def decode_token(token: str) -> TokenPayload:
    """校验并解析 JWT，失败抛出 UnauthorizedError。"""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        return TokenPayload(username=payload["username"], role=payload["role"])
    except jwt.ExpiredSignatureError:
        raise UnauthorizedError("token 已过期")
    except jwt.InvalidTokenError:
        raise UnauthorizedError("token 无效")


def require_role(role: str, allowed_roles: set[str]) -> None:
    """校验角色是否在允许集合内，否则抛 ForbiddenError。"""
    if role not in allowed_roles:
        raise ForbiddenError(f"角色 {role} 无权访问该资源")
