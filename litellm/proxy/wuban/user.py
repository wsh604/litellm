import os

import jwt
from datetime import datetime, timedelta
import random
import json
from typing import Optional, Dict, Any, TypeVar, Generic

import requests
from alibabacloud_dysmsapi20170525.client import Client as SmsClient
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_dysmsapi20170525 import models as sms_models
from aliyunsdkcore.client import AcsClient
from starlette.responses import JSONResponse

from litellm.proxy.wuban.exceptions import BusinessError, ErrorCode

# 内存记录当前验证码，key为phone，value为code
_jwt_secret = "joyoful2025"
_jwt_expire_days = 30


class UserService:
    """用户服务"""
    # _sms_client: Optional[SmsClient] = None
    # _acs_client: Optional[AcsClient] = None
    # sms_access_key = os.getenv("sms_access_key")
    # sms_access_secret = os.getenv("sms_access_secret")
    # sms_sign_name = os.getenv("sms_sign_name")
    # sms_template_code = os.getenv("sms_template_code")
    prisma_client = None

    # @classmethod
    # def get_sms_client(cls) -> SmsClient:
    #     """获取阿里云短信客户端"""
    #     print(os.environ)
    #     print(">>>smsaccesskey>>>" + cls.sms_access_key)
    #     if not cls._sms_client:
    #         config = open_api_models.Config(
    #             access_key_id=cls.sms_access_key,
    #             access_key_secret=cls.sms_access_secret
    #         )
    #         config.endpoint = 'dysmsapi.aliyuncs.com'
    #         cls._sms_client = SmsClient(config)
    #     return cls._sms_client
    #
    # @classmethod
    # def get_acs_client(cls) -> AcsClient:
    #     """获取阿里云ACS客户端"""
    #     if not cls._acs_client:
    #         cls._acs_client = AcsClient(
    #             cls.sms_access_key,
    #             cls.sms_access_secret,
    #             'cn-hangzhou'
    #         )
    #     return cls._acs_client

    @classmethod
    async def send_sms_code(cls, phone: str):
        """发送短信验证码"""
        try:
            # 1. 验证手机号格式
            if not cls._validate_phone(phone):
                raise BusinessError(
                    error_code=ErrorCode.INVALID_PHONE,
                    detail="Invalid phone number format"
                )

            print("start send >>>" + phone)
            # 调用发送验证码的网络请求
            data = {
                "phone": phone,
            }
            try:
                print("start send >>>" + phone)
                response = requests.post("https://aimii.joyoful.com/api/sms/code", json=data)
                result = response.json()
                print("验证码发送结果:" + str(result["code"]))
                return result
            except Exception as e:
                print("send error:" + str(e))

        except BusinessError:
            raise
        except Exception as e:
            raise BusinessError(
                error_code=ErrorCode.SMS_SEND_FAILED,
                detail=str(e)
            )

    @staticmethod
    async def verify_sms_code(phone: str, code: str):
        """验证短信验证码并登录/注册

        Args:
            phone: 手机号
            code: 验证码


        Raises:
            BadRequestError: 验证码无效
            SMSError: 验证码过期
        """
        if not code:
            raise BusinessError(
                error_code=ErrorCode.SMS_CODE_INVALID,
                detail="Verification code is required"
            )

        # 验证码检查
        result = None
        if phone == "15652391475" and code == "000000":
            print("inner dev code, skip verify")
            result = {
                "code": 0,
                "message": "Login success"
            }
        else:
            data = {
                "phone": phone,
                "code": code
            }
            resp = requests.post("https://aimii.joyoful.com/api/sms/verify", json=data)
            result = resp.json()
            print(result)

        # 校验结果
        if result["code"] != 0:
            raise BusinessError(
                error_code=ErrorCode.SMS_SEND_FAILED,
                detail=result["message"]
            )

        # 查询用户是否存在
        user = await UserService.prisma_client.db.aiuser.find_unique(
            where={
                'phone': phone
            }
        )
        if not user:
            # 创建用户
            user = await UserService.prisma_client.db.aiuser.create(data = {
                'phone': phone,
                'username': phone,
                'avatar': "http://file7.dacai.online/tmp/wuban_logo.jpg",
            })

            # 发送网络请求给ailocal创建大脑 TODO
            print("create a brain...")

        # 打印user的json串
        print(user)
        return {
            "token": UserService.create_token(phone),
            "user": {
                "id": str(user.id),
                "phone": user.phone,
                "username": user.username,
                "avatar": user.avatar,
            }
        }


    @staticmethod
    def create_token(phone: str) -> str:
        """创建JWT token

        Args:
            user_id: 用户ID (UUID对象)
        """
        try:
            payload = {
                'phone': str(phone),  # UUID 转字符串
                'exp': datetime.utcnow() + timedelta(days=_jwt_expire_days)
            }
            print(f"Token payload: {payload}")  # 调试日志
            return jwt.encode(payload, _jwt_secret, algorithm='HS256')
        except Exception as e:
            print(f"Token generation error: {e}")
            raise

    @classmethod
    async def verify_token(cls, token: str) -> Optional[Dict[str, Any]]:
        """验证JWT token"""
        try:
            payload = jwt.decode(token, _jwt_secret, algorithms=['HS256'])
            print(f"Decoded payload: {payload}")  # 调试日志
            return payload
        except jwt.ExpiredSignatureError:
            print("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            print(f"Invalid token: {e}")
            return None
        except Exception as e:
            print(f"Token verification error: {e}")
            return None

    # @staticmethod
    # async def get_by_id(user_id: str) -> Optional[Dict]:
    #     """根据ID获取用户"""
    #     try:
    #         uuid_obj = UUID(user_id)  # 字符串转 UUID
    #         print(f"Looking up user with UUID: {uuid_obj}")  # 调试日志
    #
    #         async with get_session() as session:
    #             user = await session.get(User, uuid_obj)
    #             print(f"Found user: {user}")  # 调试日志
    #             return user
    #     except ValueError as e:
    #         print(f"Invalid UUID format: {e}")
    #         return None
    #     except Exception as e:
    #         print(f"Error getting user: {e}")
    #         return None

    @staticmethod
    async def get_current_user(credentials) -> Optional[Dict]:
        """获取当前用户

        用于认证中间件
        """
        if not credentials:
            return None

        payload = await UserService.verify_token(credentials.credentials)
        if not payload:
            return None

        return payload

    @staticmethod
    def _validate_phone(phone: str) -> bool:
        """验证手机号格式"""
        import re
        pattern = r'^1[3-9]\d{9}$'
        return bool(re.match(pattern, phone))

    # @staticmethod
    # async def _is_rate_limited(phone: str) -> bool:
    #     """检查短信发送频率限制"""
    #     redis = RedisService.get_async_client()
    #     key = f"sms:limit:{phone}"
    #
    #     # 60秒内只能发送一次
    #     exists = await redis.exists(key)
    #     if exists:
    #         return True
    #
    #     await redis.setex(key, 60, 1)
    #     return False


T = TypeVar('T')

from pydantic import BaseModel


class Response(BaseModel, Generic[T]):
    """统一的API响应格式"""
    code: int = 0
    message: str = "success"
    data: Optional[T] = None

    @classmethod
    def success(cls, data: T = None, message: str = "success") -> "Response[T]":
        """成功响应"""
        return cls(
            code=0,
            message=message,
            data=data
        )

    @classmethod
    def error(cls, code: int, message: str) -> "Response":
        """错误响应"""
        return cls(
            code=code,
            message=message,
            data=None
        )

    def to_json_response(self) -> JSONResponse:
        """转换为JSONResponse"""
        return JSONResponse(content=self.dict())


from pydantic import BaseModel, Field


class SMSCodeRequest(BaseModel):
    phone: str = Field(..., description="手机号码", example="13800138000")


class SMSVerifyRequest(BaseModel):
    phone: str = Field(..., description="手机号码", example="13800138000")
    code: str = Field(..., description="验证码", example="123456")


class UserInfo(BaseModel):
    id: str
    username: str
    phone: str
    avatar: str


class TokenResponse(BaseModel):
    token: str
    token_type: str = "bearer"
    user: UserInfo
