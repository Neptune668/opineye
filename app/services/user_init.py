"""用户初始化：确保内置 root 管理员存在。"""

from __future__ import annotations

from app.models.base import SessionLocal
from app.models.user import User
from app.services.auth_service import ROLE_ROOT, hash_password
from app.utils.logging import get_logger

logger = get_logger(__name__)


def ensure_root_user() -> None:
    """确保 root 管理员存在，不存在则创建（初始密码 1234）。"""
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == "root").first()
        if existing:
            return
        db.add(User(username="root", password_hash=hash_password("1234"), role=ROLE_ROOT))
        db.commit()
        logger.info("已初始化内置 root 管理员（初始密码 1234）")
    finally:
        db.close()
