"""认证路由：/api/register、/api/login、/api/me。

三种角色（需求文档 2.2.2）：
  - operator（操作用户）
  - viewer（报告查看人）
  - admin（系统管理员，内置）
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from fastapi import APIRouter, Header

from app.exceptions import AppError, ValidationError
from app.models.base import SessionLocal
from app.models.user import User
from app.services.auth_service import (
    ROLE_OPERATOR,
    ROLE_VIEWER,
    TokenPayload,
    create_token,
    decode_token,
    hash_password,
    verify_password,
    normalize_role,
)
from app.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api", tags=["auth"])

ALLOWED_REGISTER_ROLES = {ROLE_OPERATOR, ROLE_VIEWER}


class RegisterBody(BaseModel):
    username: str = Field(..., min_length=2, max_length=64)
    password: str = Field(..., min_length=1, max_length=128)
    role: str = Field(default=ROLE_VIEWER, description="operator / viewer")


class LoginBody(BaseModel):
    username: str
    password: str


class UserExistsError(AppError):
    code = 409
    http_status = 409

    def __init__(self, message: str = "用户名已存在") -> None:
        super().__init__(message)
        self.message = message


class LoginFailedError(AppError):
    code = 401
    http_status = 401

    def __init__(self, message: str = "用户名或密码错误") -> None:
        super().__init__(message)
        self.message = message


@router.post("/register")
def register(body: RegisterBody) -> dict:
    """注册用户，角色仅允许 operator / viewer（admin 仅内置）。"""
    role = body.role
    if role not in ALLOWED_REGISTER_ROLES:
        raise ValidationError(f"角色 {role} 不允许注册，可选：operator / viewer")
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == body.username).first()
        if existing:
            raise UserExistsError()
        user = User(
            username=body.username,
            password_hash=hash_password(body.password),
            role=role,
        )
        db.add(user)
        db.commit()
        logger.info("用户注册", extra={"username": body.username, "role": role})
        return {"code": 0, "message": "success", "data": {"username": body.username, "role": role}}
    finally:
        db.close()


@router.post("/login")
def login(body: LoginBody) -> dict:
    """登录，返回 JWT token。"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == body.username).first()
        if not user or not verify_password(body.password, user.password_hash):
            raise LoginFailedError()
        role = normalize_role(user.role)
        token = create_token(user.username, user.role)
        logger.info("用户登录", extra={"username": user.username})
        return {
            "code": 0,
            "message": "success",
            "data": {"token": token, "username": user.username, "role": role},
        }
    finally:
        db.close()


@router.get("/me")
def me(authorization: str | None = Header(None)) -> dict:
    """获取当前登录用户信息（前端刷新时校验 token）。"""
    if not authorization or not authorization.startswith("Bearer "):
        from app.services.auth_service import UnauthorizedError
        raise UnauthorizedError("缺少 Authorization 头")
    token = authorization[len("Bearer "):].strip()
    payload: TokenPayload = decode_token(token)
    return {
        "code": 0,
        "message": "success",
        "data": {"username": payload.username, "role": payload.role},
    }
