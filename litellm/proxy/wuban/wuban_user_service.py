import ssl
import time
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
            'http://host.docker.internal:9999/homate/api/v2/call/generic'
        )
        self.logger = logger

    async def get_user_info(self, user_id: str, token: str) -> WubanUserInfo:
        try:
             # 构建 JSON-RPC 请求
            trace_id = str(uuid.uuid4().hex)
            device_id = "426F1DEC-84D6-431C-B615-D41C9221A130"  # 可以考虑从环境变量获取
            timestamp = int(time.time() * 1000)  # 当前时间戳（毫秒）
            if os.getenv("RUN_IN_BOX") == "0":
                return WubanUserInfo(id=user_id, name=user_id)
            payload = {
                "jsonrpc": "2.0",
                "method": "uc:fetchUserProfile",
                "params": {
                    "condition": user_id if user_id else "",
                    "searchCase": 0
                },
                "id": trace_id
            }
            self.logger.info(f"Using token: {token}")
            headers = {
                "Content-Type": "application/json",
                "Authorization": token,
                "jyf-request-timestamp": str(timestamp),
                "jyf-caller-trace-id": trace_id,
                "jyf-device-id": device_id,
                "jyf-app-version": "2.0",
                "User-Agent": "Homate/3.9.31 (com.joyoful.homate; build:241221; iOS 18.1.1) Alamofire/4.9.1",
                "Accept": "*/*",
                "Accept-Language": "zh-Hans-CN;q=1.0, en-CN;q=0.9"
            }
            
            self.logger.info(f"Sending RPC request to {self.rpc_url}")
            self.logger.debug(f"Request payload: {payload}")
             # 创建一个不验证SSL的连接上下文
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            # 使用 TCPConnector 禁用 SSL 验证
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.post(
                    self.rpc_url,
                    json=payload,
                    headers=headers
                ) as response:
                     # 打印详细的响应信息
                    self.logger.debug(f"Response status: {response.status}")
                    self.logger.debug(f"Response headers: {dict(response.headers)}")
                    
                    response_text = await response.text()
                    self.logger.debug(f"Response body: {response_text}")

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
                    avatar_info = user_data.get("avatarInfo", {})
                    return WubanUserInfo(
                        name=user_data.get("userRealName") or user_data.get("userName", '屋伴用户'),
                        username=user_data.get("userName", 'wuban'),
                        email=user_data.get("mobilePhoneNumbers", [''])[0] if user_data.get("mobilePhoneNumbers") else '',
                        avatar=avatar_info.get("imageInfoInBase64", ""),
                        id=user_data.get("userId", user_id),
                        createdAt=user_data.get("kvs", {}).get("userCreateTime", '')
                    )
                    
        except Exception as e:
            self.logger.error(f"Error getting user info: {str(e)}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return WubanUserInfo(id=user_id) 