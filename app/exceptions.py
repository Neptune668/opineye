"""异常类型定义（契约，冻结）。对应文档 4.8 节异常映射表。"""

from __future__ import annotations


class AppError(Exception):
    """业务异常基类。"""

    code: int = 5001
    http_status: int = 500

    def __init__(self, message: str = "") -> None:
        super().__init__(message or self.__class__.__name__)
        self.message = message or self.__class__.__name__


class ValidationError(AppError):
    code = 1001
    http_status = 400


class NotFoundError(AppError):
    code = 1002
    http_status = 404


class InvalidStateError(AppError):
    code = 2001
    http_status = 409


class VersionConflictError(AppError):
    code = 2001
    http_status = 409


class TaskFailedError(AppError):
    code = 4001
    http_status = 500


class StorageError(AppError):
    code = 3001
    http_status = 500


class DatabaseError(AppError):
    code = 3002
    http_status = 500
