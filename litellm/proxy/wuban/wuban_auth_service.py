import asyncio
from typing import Optional, Tuple
from datetime import datetime
from pydantic import BaseModel
import httpx
from litellm.proxy._types import UserAPIKeyAuth
from fastapi import Depends, Request, HTTPException
from litellm.proxy.auth.user_api_key_auth import user_api_key_auth
from .logger_util import WubanLogger
from .user import UserService

# 获取 WubanLogger 实例
logger = WubanLogger.get_logger()

class WubanAuthResponse(BaseModel):
    """Wuban 认证响应"""
    user_id: str
    token: str
    expires_at: Optional[datetime] = None


class CombinedAuthResult(BaseModel):
    litellm_auth: UserAPIKeyAuth
    wuban_id: str

    class Config:
        arbitrary_types_allowed = True

class WubanAuthService:
    def __init__(self, auth_url: str):
        self.auth_url = auth_url
        
    async def verify_token(self, token: str) -> WubanAuthResponse:
        """验证 Wuban Token"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.auth_url}/verify",
                json={"token": token}
            )
            if response.status_code != 200:
                raise Exception("Invalid token")
            
            data = response.json()
            return WubanAuthResponse(**data)
            
    async def get_or_create_litellm_user(
        self, 
        wuban_user_id: str
    ) -> None:
        """获取或创建 LiteLLM 用户映射"""
        from litellm.proxy.proxy_server import (
            litellm_proxy_admin_name as litellm_proxy_default_admin_id,
            prisma_client
        )
        

        mapping = await prisma_client.db.wubanusermapping.find_unique(
            where={"wuban_user_id": wuban_user_id}
        )
        
        if not mapping:
            # 创建新映射
            mapping = await prisma_client.db.wubanusermapping.create(
                data={
                    "wuban_user_id": wuban_user_id,
                    "litellm_user_id": litellm_proxy_default_admin_id
                }
            )

    async def authenticate_request_for_desk(
            self,
            request: Request
    ) -> Tuple[UserAPIKeyAuth, str]:
        """
        1. 获取并验证 token
        2. 从 token中获取当前用户的电话号码
        3. 返回 (UserAPIKeyAuth, wuban_user_id)
        """
        # 1. 获取并验证 token，Authorization已经被使用，这里我们使用 wuban_token
        wuban_token = request.headers.get("Authorization")
        if not wuban_token:
            raise HTTPException(status_code=401, detail="No token provided")

        # 通过jwt解析token内容
        payload = await UserService.verify_token(wuban_token)
        if not payload or not payload["phone"]:
            raise HTTPException(status_code=401, detail="Invalid token")

        phone = payload["phone"]


        from litellm.proxy.proxy_server import (
            litellm_proxy_admin_name as litellm_proxy_default_admin_id,
            master_key
        )

        user_api_key_dict = UserAPIKeyAuth(
            api_key=f"Bearer {master_key}",
            user_id=litellm_proxy_default_admin_id,
            user_role="proxy_admin"
        )

        # 返回 (UserAPIKeyAuth, wuban_user_id)
        return user_api_key_dict, phone


    async def authenticate_request(
        self,
        request: Request
    ) -> Tuple[UserAPIKeyAuth, str]:
        # 1. 获取并验证 token
        wuban_token = request.headers.get("Authorization")
        if not wuban_token:
            raise HTTPException(status_code=401, detail="No token provided")
        
        # wuban_user = await self.verify_token(wuban_token)
        # 从 header 中直接读取 wuban-user-id 目前还没有鉴权接口 v1.0
        # 2. 从 header 中直接读取 wuban-user-id
        wuban_user_id = request.headers.get("wuban-user-id")
        if not wuban_user_id:
            raise HTTPException(status_code=401, detail="No user id provided")
            
        wuban_user = WubanAuthResponse(
            user_id=wuban_user_id,
            token=wuban_token
        )
        
        # 3. 获取或创建 LiteLLM 用户映射
        asyncio.create_task(self.get_or_create_litellm_user(
            wuban_user.user_id
        ))

        from litellm.proxy.proxy_server import (
            litellm_proxy_admin_name as litellm_proxy_default_admin_id,
            master_key
        )
        
        user_api_key_dict=UserAPIKeyAuth(
            api_key=f"Bearer {master_key}",
            user_id=litellm_proxy_default_admin_id,
            user_role="proxy_admin"
        )

        # 返回 (UserAPIKeyAuth, wuban_user_id)
        return user_api_key_dict, wuban_user_id

# 创建依赖函数
async def wuban_auth(
    request: Request,
    wuban_auth_service: WubanAuthService = Depends(lambda: WubanAuthService(auth_url="https://wuban-auth-url"))
) -> Tuple[UserAPIKeyAuth, str]:
    
    return await wuban_auth_service.authenticate_request_for_desk(
        request=request
    )

# 组合认证函数
async def combined_auth(
    request: Request,
    wuban_result: Tuple[UserAPIKeyAuth, str] = Depends(wuban_auth),
) -> CombinedAuthResult:
    """组合 Wuban 认证和 LiteLLM 认证"""
    try:
        user_api_key_dict, wuban_user_id = wuban_result
        
        logger.debug(f"[AUTH] Starting combined authentication for user: {wuban_user_id}")
        logger.debug(f"[AUTH] LiteLLM auth result: {user_api_key_dict}")
        
        litellm_auth = await user_api_key_auth(
            request=request, 
            api_key=user_api_key_dict.api_key
        )
        logger.debug(f"[AUTH] LiteLLM auth result: {litellm_auth}")
        
        # 返回 CombinedAuthResult 对象
        return CombinedAuthResult(
            litellm_auth=litellm_auth,
            wuban_id=wuban_user_id
        )
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=f"Authentication failed: {str(e)}"
        )