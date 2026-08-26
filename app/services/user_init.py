"""用户初始化：确保内置 admin 管理员存在。"""

from __future__ import annotations

from app.models.base import SessionLocal
from app.models.user import User
from app.services.auth_service import ROLE_ADMIN, hash_password
from app.utils.logging import get_logger

logger = get_logger(__name__)


def ensure_admin_user() -> None:
    """确保 admin 管理员存在，不存在则创建（初始密码 1234）。

    兼容旧数据：若已存在 root 角色用户，将其视作 admin。
    """
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == "admin").first()
        if existing:
            return
        # 兼容旧版本 root 用户：将其角色升级为 admin，用户名保留为 root
        legacy = db.query(User).filter(User.username == "root").first()
        if legacy:
            if legacy.role != ROLE_ADMIN:
                legacy.role = ROLE_ADMIN
                db.commit()
            logger.info("检测到旧 root 管理员，已升级为 admin 角色")
            return
        db.add(User(username="admin", password_hash=hash_password("1234"), role=ROLE_ADMIN))
        db.commit()
        logger.info("已初始化内置 admin 管理员（初始密码 1234）")
    finally:
        db.close()


def ensure_root_user() -> None:
    """向后兼容别名，指向 ensure_admin_user。"""
    ensure_admin_user()
