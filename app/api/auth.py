"""认证路由：/api/register、/api/login。"""

from __future__ import annotations

from pydantic import BaseModel, Field

from fastapi import APIRouter

from app.exceptions import AppError
from app.models.base import SessionLocal
from app.models.user import User
from app.services.auth_service import (
    ROLE_USER,
    create_token,
    hash_password,
    verify_password,
)
from app.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api", tags=["auth"])


class RegisterBody(BaseModel):
    username: str = Field(..., min_length=2, max_length=64)
    password: str = Field(..., min_length=1, max_length=128)


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
    """注册操作用户（角色固定为 user）。"""
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == body.username).first()
        if existing:
            raise UserExistsError()
        user = User(
            username=body.username,
            password_hash=hash_password(body.password),
            role=ROLE_USER,
        )
        db.add(user)
        db.commit()
        logger.info("用户注册", extra={"username": body.username})
        return {"code": 0, "message": "success", "data": {"username": body.username, "role": ROLE_USER}}
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
        token = create_token(user.username, user.role)
        logger.info("用户登录", extra={"username": user.username})
        return {
            "code": 0,
            "message": "success",
            "data": {"token": token, "username": user.username, "role": user.role},
        }
    finally:
        db.close()
