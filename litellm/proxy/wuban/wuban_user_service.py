import traceback
import aiohttp
from typing import Dict, Optional, List
from aiohttp.web_exceptions import HTTPException
from pydantic import BaseModel
import json
from .logger_util import WubanLogger
import uuid
import os

logger = WubanLogger.get_logger()


class WubanUserInfo(BaseModel):
    """Wuban 用户信息模型 - 用于 Librechat 的用户信息"""
    name: str = '屋伴用户'
    username: str = 'wuban'
    email: str = ''
    emailVerified: bool = True
    avatar: str = ''
    provider: str = 'local'
    role: str = 'user'
    plugins: list = []
    termsAccepted: bool = False
    refreshToken: list = []
    createdAt: str = ''
    updatedAt: str = ''
    id: str

class WubanUserService:
    def __init__(self, rpc_url: str = None):
        # 优先使用环境变量中的 RPC URL，如果没有则使用默认值
        self.rpc_url = rpc_url or os.getenv(
            'WUBAN_RPC_URL', 
            'http://host.docker.internal:8080/jsonrpc'
        )
        self.logger = logger

    async def get_user_info(self, user_id: str, token: str) -> WubanUserInfo:
        try:
            # 构建 JSON-RPC 请求
            payload = {
                "jsonrpc": "2.0",
                "method": "uc:fetchUserProfile",
                "params": {
                    "condition": user_id if user_id else "",
                    "searchCase": 0
                },
                "id": str(uuid.uuid4().hex)
            }
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": token
            }
            
            self.logger.info(f"Sending RPC request to {self.rpc_url}")
            self.logger.debug(f"Request payload: {payload}")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.rpc_url,
                    json=payload,
                    headers=headers
                ) as response:
                    if response.status != 200:
                        self.logger.warning(f"RPC request failed with status {response.status}, using default user info")
                        return WubanUserInfo(id=user_id)
                    
                    result = await response.json()
                    self.logger.debug(f"RPC response: {result}")
                    
                    # 检查错误信息
                    error = result.get("error")
                    if error:
                        error_msg = error.get("message", "")
                        if any(msg in error_msg for msg in [
                            "The user does not exist!",
                            "fetchUserProfile failed!",
                            "condition is invalided!"
                        ]):
                            self.logger.warning(f"RPC returned error: {error_msg}, using default user info")
                            return WubanUserInfo(id=user_id)
                        raise Exception(f"RPC error: {error_msg}")
                    
                    # 解析响应数据
                    result_data = result.get("result", {})
                    personal_info_list = result_data.get("personalInfoList", [])
                    if not personal_info_list:
                        return WubanUserInfo(id=user_id)
                    
                    user_data = personal_info_list[0]
                    return WubanUserInfo(
                        name=user_data.get("userRealName") or user_data.get("userName", '屋伴用户'),
                        username=user_data.get("userName", 'wuban'),
                        email=user_data.get("emailAddresses", [''])[0] if user_data.get("emailAddresses") else '',
                        avatar=user_data.get("avatarInfo", ''),
                        id=user_data.get("userId", user_id),
                        createdAt=user_data.get("kvs", {}).get("userCreateTime", '')
                    )
                    
        except Exception as e:
            self.logger.error(f"Error getting user info: {str(e)}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return WubanUserInfo(id=user_id) 