from enum import Enum
from typing import Optional

from fastapi import HTTPException
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_405_METHOD_NOT_ALLOWED,
    HTTP_429_TOO_MANY_REQUESTS,
    HTTP_500_INTERNAL_SERVER_ERROR,
    HTTP_200_OK
)


class ErrorCode(Enum):
    """错误码枚举"""
    # HTTP错误 (100-999)
    BAD_REQUEST = (400, "Bad request", HTTP_400_BAD_REQUEST)
    UNAUTHORIZED = (401, "Unauthorized", HTTP_401_UNAUTHORIZED)
    FORBIDDEN = (403, "Forbidden", HTTP_403_FORBIDDEN)
    NOT_FOUND = (404, "Resource not found", HTTP_404_NOT_FOUND)
    METHOD_NOT_ALLOWED = (405, "Method not allowed", HTTP_405_METHOD_NOT_ALLOWED)
    TOO_MANY_REQUESTS = (429, "Too many requests", HTTP_429_TOO_MANY_REQUESTS)
    INTERNAL_ERROR = (500, "Internal server error", HTTP_500_INTERNAL_SERVER_ERROR)

    # 业务错误 (1000+)
    PARAM_ERROR = (1001, "Invalid request parameters", HTTP_400_BAD_REQUEST)
    INVALID_PHONE = (2003, "Invalid phone number", HTTP_200_OK)
    # 短信相关错误 (3000-3999)
    SMS_SEND_FAILED = (3000, "Failed to send SMS", HTTP_200_OK)
    SMS_CODE_INVALID = (3001, "Invalid SMS code", HTTP_200_OK)
    SMS_CODE_EXPIRED = (3002, "SMS code expired", HTTP_200_OK)
    SMS_RATE_LIMIT = (3003, "SMS rate limit exceeded", HTTP_200_OK)

    def __init__(self, code: int, message: str, status_code: int):
        self.code = code
        self.message = message
        self.status_code = status_code


class BusinessError(HTTPException):
    """业务异常基类"""

    def __init__(
            self,
            error_code: ErrorCode,
            detail: Optional[str] = None,
            headers: Optional[dict] = None
    ):
        self.error_code = error_code
        super().__init__(
            status_code=error_code.status_code,  # 使用错误码对应的HTTP状态码
            detail=detail or error_code.message,
            headers=headers
        )

    def to_dict(self) -> dict:
        """转换为响应字典"""
        return {
            "code": self.error_code.code,
            "message": self.detail,
            "data": None
        }
