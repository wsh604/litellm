from datetime import datetime
from fastapi import APIRouter, Depends, Request, Response, HTTPException
from pydantic.main import BaseModel
from litellm import router
from litellm.proxy.auth.user_api_key_auth import user_api_key_auth
from litellm.proxy.wuban.conversation_history_manager import (
    ConversationHistoryManager, 
    UserMessage, 
    AssistantMessage, 
    ErrorMessage
)
from typing import List, Optional, AsyncGenerator, Dict, Any,Union, Tuple
from litellm.proxy._types import UserAPIKeyAuth
import asyncio
import uuid
import json
from fastapi.responses import StreamingResponse
import traceback
from .wuban_auth_service import WubanAuthService, combined_auth, CombinedAuthResult
from .logger_util import WubanLogger
import base64
import aiohttp
import os
from .wuban_user_service import WubanUserService, WubanUserInfo
from litellm.proxy.wuban.models import router as wuban_model_router
import yaml

# 获取 WubanLogger 实例
logger = WubanLogger.get_logger()

# 路由查找函数
def get_route_by_path(request: Request, path: str):
    """根据路径获取路由"""
    for route in request.app.router.routes:
        if route.path == path:
            return route
    raise HTTPException(status_code=500, detail=f"Route {path} not found")

librechat_router = APIRouter(
    prefix="/api",
    tags=["librechat"]
)

librechat_router.prisma_client = None

conversation_history_manager = None

async def get_conversation_history_manager():
    global conversation_history_manager
    if conversation_history_manager is None:
        if librechat_router.prisma_client is None:
            raise HTTPException(status_code=500, detail="Database not initialized")
        conversation_history_manager = ConversationHistoryManager(
            prisma_client=librechat_router.prisma_client
        )
    return conversation_history_manager

#### LIBRECHAT ENDPOINTS ####
# 定义响应模型
class MessageResponse(BaseModel):
    messageId: str
    conversationId: str
    text: str
    sender: str
    parentMessageId: str
    model: Optional[str]
    endpoint: Optional[str]
    endpointType: Optional[str]
    createdAt: datetime
    isCreatedByUser: bool

class ConversationResponse(BaseModel):
    conversationId: str
    title: Optional[str]
    model: Optional[str]
    modelDisplayLabel: Optional[str]
    createdAt: datetime
    updatedAt: datetime
    messages: List[str]

# 获取会话列表
@librechat_router.get(
    "/convos",
    description="获取用户的所有聊天会话列表"
)
async def list_conversations(
    pageNumber: int = 1,
    auth_result: CombinedAuthResult = Depends(combined_auth),
    conversation_history_manager: ConversationHistoryManager = Depends(get_conversation_history_manager)
):
    try:
        page_size = 25
        skip = (pageNumber - 1) * page_size
        
        result = await conversation_history_manager.get_chat_history(
            user_id=auth_result.wuban_id,
            limit=page_size,
            skip=skip
        )
        
        # 直接返回完整的分页数据
        return {
            "conversations": result["conversations"],
            "pages": result["pages"],
            "pageNumber": result["pageNumber"],
            "pageSize": result["pageSize"]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching conversations: {str(e)}"
        )

# 获取单个会话详情
@librechat_router.get(
    "/messages/{conversation_id}",
    description="获取指定会话的消息列表"
)
async def get_conversation(
    conversation_id: str,
    auth_result: CombinedAuthResult = Depends(combined_auth),
    conversation_history_manager: ConversationHistoryManager = Depends(get_conversation_history_manager)
):
    """获取指定会话的消息列表"""
    try:
        messages = await conversation_history_manager.get_conversation_messages(
            user_id=auth_result.wuban_id,
            conversation_id=conversation_id
        )
        
        if not messages:
            return []
            
        return messages
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching messages: {str(e)}"
        )

# 定义删除会话的请求模型
class ConversationDeleteRequest(BaseModel):
    arg: Dict[str, str]

@librechat_router.post(
    "/convos/clear",
    description="删除指定的聊天会话及其所有消息"
)
async def delete_conversation(
    request: ConversationDeleteRequest,
    auth_result: CombinedAuthResult = Depends(combined_auth),
    conversation_history_manager: ConversationHistoryManager = Depends(get_conversation_history_manager)
):
    """删除指定的聊天会话及其所有相关消息"""
    try:
        conversation_id = request.arg.get("conversationId")
        if not conversation_id:
            raise HTTPException(
                status_code=400,
                detail="Missing conversationId"
            )
            
        logger.info(f"Deleting conversation: {conversation_id}")
        
        # 调用删除方法并获取删除结果
        result = await conversation_history_manager.delete_chat_history(
            wuban_user_id=auth_result.wuban_id,
            conversation_id=conversation_id
        )
        
        return {
            "acknowledged": True,
            "deletedCount": 1,
            "messages": {
                "acknowledged": True,
                "deletedCount": result["messages_deleted"]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting conversation: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting conversation: {str(e)}"
        )

class StreamEventManager:
    """管理流式事件的生成和格式化"""
    
    def __init__(self, user_message: UserMessage, model: str):
        self.user_message = user_message
        self.model = model
        self.assistant_message_id = str(uuid.uuid4())
        self.full_response = ""
        self.first_chunk = True
        self.logger = logger
    
    def process_chunk(self, chunk: Union[str, bytes]) -> Optional[str]:
        """处理单个数据块并返回格式化的事件"""
        try:
            # 处理 chunk 格式
            chunk_str = self._normalize_chunk(chunk)
            if chunk_str is None:
                return None
                
            # 解析内容
            content = self._extract_content(chunk_str)
            if content is None:
                return None
                
            # 更新完整响应
            self.full_response += content
            
            # 生成事件
            return self._create_message_event(self.full_response)
            
        except Exception as e:
            self.logger.error(f"Error processing chunk: {str(e)}")
            # 在发生错误时添加提示
            error_content = "\n[发生错误：响应可能不完整]"
            self.full_response += error_content
            return self._create_message_event(error_content)
    def _normalize_chunk(self, chunk: Union[str, bytes]) -> Optional[str]:
        """标准化 chunk 数据"""
        try:
            # 转换为字符串
            chunk_str = chunk if isinstance(chunk, str) else chunk.decode('utf-8')
            self.logger.debug(f"Raw chunk: {chunk_str}")
            
            # 处理特殊情况
            if chunk_str.strip() == "":
                return None
            if chunk_str.startswith('data: '):
                chunk_str = chunk_str[6:]
            if chunk_str.strip() == '[DONE]':
                return None
                
            return chunk_str
        except Exception as e:
            self.logger.error(f"Error normalizing chunk: {str(e)}")
            return None
    def _extract_content(self, chunk_str: str) -> Optional[str]:
        """从 chunk 中提取内容"""
        try:
            chunk_data = json.loads(chunk_str)
            self.logger.debug(f"Parsed JSON: {chunk_data}")
            
            if chunk_data.get("choices"):
                # 检查是否有完成标志
                if "finish_reason" in chunk_data["choices"][0]:
                    finish_reason = chunk_data["choices"][0].get("finish_reason")
                    if finish_reason == "length":
                        # 模型输出被截断
                        self.logger.warning("Model output was truncated due to length limit")
                        return "\n[Model output was truncated due to length limit]"
                    elif finish_reason == "stop":
                        # 正常结束
                        return None

                # 获取内容
                if "delta" in chunk_data["choices"][0]:
                    content = chunk_data["choices"][0]["delta"].get("content", "")
                else:
                    content = chunk_data["choices"][0].get("text", "")
                
                if content:
                    self.logger.debug(f"Extracted content: {content}")
                    return content
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON decode error: {str(e)}")
            return None
    def _create_message_event(self, content: str) -> str:
        """创建消息事件"""
        event_data = {
            "message": True,
            "messageId": self.user_message.message_id,
            "parentMessageId": self.user_message.parent_message_id,
            "text": content,
            "initial": False
        }
        
        if self.first_chunk:
            event_data["initial"] = True
            self.first_chunk = False
            self.logger.info("Added 'created' flag to first chunk")
        
        return self._format_event("message", event_data)
    
    def format_user_message_event(self,text:str) -> str:
        """格式化用户消息事件"""
        event_data = {
            "message": {
                "conversationId": self.user_message.conversation_id,
                "messageId": self.user_message.message_id,
                "parentMessageId": self.user_message.parent_message_id,
                "isCreatedByUser": True,
                "sender": "User", 
                "text": text
            },
            "created": True
        }
        return self._format_event("message", event_data)
    
    def _generate_title(self, text: str, max_length: int = 10) -> str:
        """从消息文本生成会话标题"""
        # 如果文本为空，返回 "新会话"
        if not text.strip():
            return "新会话"
        
        # 移除多余空白字符
        title = " ".join(text.split())
        # 截取适长度
        return title[:max_length] if len(title) >= max_length else title
    
    def format_final_event(self) -> str:
        """格式化最终事件"""
        event_data = {
            "final": True,
            "conversation": self._get_conversation_data(),
            "title": self._generate_title(self.user_message.text),
            "requestMessage": self._get_request_message_data(),
            "responseMessage": self._get_response_message_data()
        }
        return self._format_event("message", event_data)
    
    def _get_conversation_data(self) -> Dict[str, Any]:
        """获取会话数据"""
        # 构建基础数据
        conversation_data = {
            "_id": str(uuid.uuid4()),
            "user": self.user_message.user_id,
            "conversationId": self.user_message.conversation_id,
            "__v": 0,
            "createdAt": datetime.now().isoformat(),
            "endpoint": self.user_message.endpoint,
            "isArchived": False,
            "messages": [self.user_message.message_id, self.assistant_message_id],
            "model": self.model,
            "resendFiles": True,
            "files": [],
            "tags": [],
            "title":self._generate_title(self.user_message.text),
            "updatedAt": datetime.now().isoformat()
        }

        # 仅当 endpointType 不为空字符串时添加该字段
        if self.user_message.endpoint_type:
            conversation_data["endpointType"] = self.user_message.endpoint_type
        return conversation_data
    
    def _get_request_message_data(self) -> Dict[str, Any]:
        """获取请求消息数据"""
        return {
            "messageId": self.user_message.message_id,
            "parentMessageId": self.user_message.parent_message_id,
            "conversationId": self.user_message.conversation_id,
            "sender": "User",
            "text": self.user_message.text,
            "isCreatedByUser": True
        }
    
    def _get_response_message_data(self) -> Dict[str, Any]:
        """获取响应消息数据"""
        return {
            "messageId": self.assistant_message_id,
            "conversationId": self.user_message.conversation_id,
            "parentMessageId": self.user_message.message_id,
            "isCreatedByUser": False,
            "finish reason":"stop",
            "endpoint": self.user_message.endpoint,
            "model": self.model,
            "sender": "Assistant",
            "text": self.full_response
        }
    
    @staticmethod
    def _format_event(event_type: str, data: Dict[str, Any]) -> str:
        """格式化事件字符串"""
        return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"

async def stream_and_save(
    response: StreamingResponse,
    user_message: UserMessage,
    model: str,
    litellm_user_id: str,
    conversation_history_manager: ConversationHistoryManager
) -> AsyncGenerator[str, None]:
    """处理流式响应并保存消息"""
    
    event_manager = StreamEventManager(user_message, model)
    
    yield event_manager.format_user_message_event(user_message.text)
    try:
        async for chunk in response.body_iterator:
            if formatted_event := event_manager.process_chunk(chunk):
                yield formatted_event
                
    except Exception as e:
        logger.error(f"Error in stream processing: {str(e)}")
        raise
    finally:
        try:
            # 发送最终事件
            yield event_manager.format_final_event()
            
            # 保存助手消息
            assistant_message = AssistantMessage(
                text=event_manager.full_response,
                user_id=user_message.user_id,
                model=model,
                conversation_id=user_message.conversation_id,
                parent_message_id=user_message.message_id,
                message_id=event_manager.assistant_message_id,
                endpoint=user_message.endpoint,
                endpoint_type=user_message.endpoint_type
            )
            asyncio.create_task(
                conversation_history_manager.save_assistant_message(assistant_message,litellm_user_id=litellm_user_id)
            )
        except Exception as e:
            logger.error(f"Error in final event processing: {str(e)}")

# 文件处理相关的辅助函数
async def download_and_encode_file(file_info: Dict) -> str:
    """下载文件并转换为 base64 编码"""
    try:
        filepath = file_info["filepath"]
        
        # 如果是本地文件路径，直接读取
        if os.path.exists(filepath):
            with open(filepath, "rb") as f:
                file_content = f.read()
        else:
            # 如果是网络URL，下载文件
            async with aiohttp.ClientSession() as session:
                async with session.get(filepath) as response:
                    if response.status != 200:
                        raise Exception(f"Failed to download file: {filepath}")
                    file_content = await response.read()
        
        # 转换为 base64
        base64_content = base64.b64encode(file_content).decode('utf-8')
        return base64_content
        
    except Exception as e:
        logger.error(f"Error processing file {file_info.get('file_id')}: {str(e)}")
        raise

async def process_files(files: List[Dict]) -> List[Dict]:
    """处理文件列表，返回包含 base64 编码的文件信息"""
    if not files:
        return []
        
    processed_files = []
    for file_info in files:
        try:
            base64_content = await download_and_encode_file(file_info)
            processed_file = {
                "file_id": file_info["file_id"],
                "type": file_info["type"],
                "base64": base64_content
            }
            # 如果有图片尺寸信息，添加到处理后的文件信息中
            if "height" in file_info and "width" in file_info:
                processed_file["height"] = file_info["height"]
                processed_file["width"] = file_info["width"]
                
            processed_files.append(processed_file)
            
        except Exception as e:
            logger.error(f"Failed to process file: {str(e)}")
            continue
            
    return processed_files

async def check_model_capabilities(model_name: str, files: List[Dict], auth_result: CombinedAuthResult) -> Tuple[bool, str]:
    """检查模型是否支持文件处理能力"""
    return True, ""
    # logger.info(f"Checking model capabilities for {model_name} with files: {files}")
    # if not files:  # 如果没有文件,则不需要检查
    #     return True, ""
        
    # try:
    #     # 获取配置文件路径
    #     cwd = os.getcwd()  # 获取当前工作目录
    #     config_paths = [
    #         os.path.join(cwd, 'lite_config.yaml'),  # 当前工作目录
    #         os.getenv('CONFIG_FILE_PATH'),          # 环境变量
    #         '/app/lite_config.yaml',                # Docker 环境
    #     ]
    #     logger.debug(f"Current working directory: {cwd}")
        
    #     # 读取配置文件
    #     config = None
    #     for path in config_paths:
    #         if path and os.path.exists(path):
    #             logger.debug(f"Found config file at: {path}")
    #             with open(path, 'r') as f:
    #                 config = yaml.safe_load(f)
    #                 break
                    
    #     if config is None:
    #         raise Exception(f"Could not find lite_config.yaml in any location. Searched paths: {config_paths}")
            
    #     # 在配置中查找对应的模型
    #     model_config = None
    #     for m in config.get('model_list', []):
    #         # 修改匹配逻辑，使用 model_name 而不是 model
    #         if m['model_name'] == model_name:
    #             model_config = m
    #             break
                
    #     if model_config is None:
    #         logger.warning(f"Model {model_name} not found in configuration")
    #         return False, f"Model {model_name} not found in configuration"
            
    #     # 从配置中获取 capabilities
    #     capabilities = model_config.get("litellm_params", {}).get("capabilities", [])
    #     logger.debug(f"Model {model_name} capabilities from config: {capabilities}")
        
    #     # 检查每个文件类型是否被支持
    #     for file in files:
    #         file_type = file.get("type", "").split("/")[0]  # "image/jpeg" -> "image"
    #         if not capabilities or file_type not in capabilities:
    #             return False, f"Model {model_name} does not support {file_type} input"
                
    #     return True, ""
        
    # except Exception as e:
    #     logger.error(f"Error checking model capabilities: {str(e)}")
    #     logger.error(f"Traceback: {traceback.format_exc()}")
    #     return False, f"Error checking model capabilities: {str(e)}"
# chat_completion_with_history 方法
@librechat_router.post("/ask/{model}")
async def chat_completion_with_history(
    request: Request,
    model: str,
    auth_result: CombinedAuthResult = Depends(combined_auth),
    conversation_history_manager: ConversationHistoryManager = Depends(get_conversation_history_manager),
):
    try:
        user_api_key_dict = auth_result.litellm_auth
        wuban_user_id = auth_result.wuban_id
        litellm_user_id = user_api_key_dict.user_id
        
        user_message = None
        logger.info(f"Starting request for model: {model}")
        data = await request.json()
        logger.info(f"Received request data: {data}")
        # 处理文件
        files = data.get("files", [])
        
        # 构建用户消息参数
        is_streaming = True if data.get("stream") is None else data.get("stream")
        conversation_id = data.get("conversationId") or str(uuid.uuid4())
        parent_message_id = data.get("parentMessageId") or ConversationHistoryManager.NO_PARENT
        endpoint = data.get("endpoint") or ""
        endpoint_type = data.get("endpointType") or ""  # 保留 endpointType
        model_name = data.get('model')
        override_parent_message_id = data.get("overrideParentMessageId")
        

        # 创建用户消息对象
        user_message = UserMessage(
            text=data["text"],  # 使用text字段
            user_id=wuban_user_id,
            model=model_name, 
            files=files,
            conversation_id=conversation_id,
            parent_message_id=parent_message_id,
            endpoint=endpoint,
            endpoint_type=endpoint_type  # 添加 endpoint_type
        )

        # 如果存在 overrideParentMessageId，代表目前是修改响应消息 跳过用户消息保存
        if override_parent_message_id:
            logger.info(f"Using overrideParentMessageId: {override_parent_message_id}")
            user_message.message_id = override_parent_message_id
            logger.info("Skipping user message save due to message override")
        else:
            # 只有在非覆盖模式下才保存用户消息
            logger.info("Saving user message")
            await conversation_history_manager.save_user_message(
                message=user_message,
                litellm_user_id=litellm_user_id
            )

        # 获取 chat_completion 路由
        chat_completion_route = get_route_by_path(request, "/v1/chat/completions")
        
        # 重构请求数据为所需格式
        messages = []
        warning_message = None
        
        # 如果有上下文消息，添加到消息列表中
        generation = data.get("generation", "")
        if generation:
            messages.append({
                "role": "assistant",
                "content": generation
            })
        
        if files:
            # 检查模型是否支持文件处理能力
            is_supported, error_message = await check_model_capabilities(f"{data.get('endpoint', '')}/{data.get('model')}", files, auth_result)
            logger.info(f"Model capabilities check result: is_supported={is_supported}, error_message={error_message}")
            
            if not is_supported:
                # 记录警告消息
                warning_message = f"注意：{error_message}。我将只处理文本内容。"
                # 只处理文本部分
                messages.append({
                    "role": "user",
                    "content": data["text"]
                })
            else:
                # 模型支持文件处理，正常处理
                processed_files = await process_files(files)
                messages.append({
                    "role": "user",
                    "content": [
                        {"type": "text", "text": data["text"]},
                        *[{
                            "type": file["type"].split('/')[0],
                            file["type"].split('/')[0]: {
                                "data": file["base64"],
                                "height": file.get("height"),
                                "width": file.get("width")
                            }
                        } for file in processed_files]
                    ]
                })
        else:
            # 没有文件，使用简单的消息格式
            messages.append({
                "role": "user",
                "content": data["text"]
            })

        # 如果有警告消息，添加到用户输入前
        # if warning_message:
        #     messages.insert(0, {
        #         "role": "system",
        #         "content": warning_message
        #     })

        formatted_data = {
            "model": f"{endpoint}/{model_name}",
            "messages": messages,
            "endpoint": endpoint,
            "stream": is_streaming
        }
        
        # 创建新的请求对象并设置请求体
        async def mock_receive():
            return {
                "type": "http.request",
                "body": json.dumps(formatted_data).encode(),
                "more_body": False
            }

        new_request = Request(
            scope={
                **request.scope,
                "path": "/v1/chat/completions",
                "method": "POST",
            },
            receive=mock_receive
        )

        # 调用 chat_completion
        logger.info(f"Calling chat completion endpoint with data: {formatted_data}")
        try:
            response = await chat_completion_route.endpoint(
                request=new_request,
                fastapi_response=Response(),
                model=model,
                user_api_key_dict=UserAPIKeyAuth(
                    api_key=user_api_key_dict.api_key,
                    user_id=user_api_key_dict.user_id,
                    user_role=user_api_key_dict.user_role
                )
            )
        except Exception as e:
            logger.error(f"Chat completion error: {str(e)}")
            logger.error(f"Request data: {formatted_data}")
            raise

        if is_streaming:
            logger.info("Processing streaming response")
            return StreamingResponse(
                stream_and_save(
                    response=response,
                    user_message=user_message,
                    model=model_name,
                    litellm_user_id=litellm_user_id,
                    conversation_history_manager=conversation_history_manager
                ),
                media_type=response.media_type
            )
        else:
            logger.info("Processing non-streaming response")
            # 非流式响应处理
            assistant_message = AssistantMessage(
                text=response.choices[0].message.content,
                user_id=wuban_user_id,
                model=model,
                conversation_id=user_message.conversation_id,
                parent_message_id=user_message.message_id,
                endpoint=user_message.endpoint,
                endpoint_type=user_message.endpoint_type
            )
            
            asyncio.create_task(
                conversation_history_manager.save_assistant_message(assistant_message,litellm_user_id=litellm_user_id)
            )
            
            # 构建响应
            libre_response = {
                "messageId": assistant_message.message_id,
                "conversationId": assistant_message.conversation_id,
                "text": assistant_message.text,
                "sender": assistant_message.sender,
                "userId": wuban_user_id,
                "parentMessageId": assistant_message.parent_message_id,
                "model": assistant_message.model,
                "endpoint": assistant_message.endpoint,
                "endpointType": assistant_message.endpoint_type,  # 添加 endpoint_type
                "isCreatedByUser": assistant_message.is_created_by_user
            }
            
            logger.info("Request completed successfully")
            return libre_response
            
    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        # 错误处理
        if conversation_history_manager and user_message:
            error_message = ErrorMessage(
                text=str(e),
                user_id=wuban_user_id,
                model=model,
                conversation_id=user_message.conversation_id,
                parent_message_id=user_message.message_id,
                error=str(e)
            )
            logger.error(f"Created error message: {error_message}")
            asyncio.create_task(
                conversation_history_manager.save_error_message(error_message,litellm_user_id=litellm_user_id)
            )
        raise

# 创建 WubanUserService 实例
user_service = WubanUserService()

@librechat_router.get(
    "/user",
    response_model=WubanUserInfo,
    description="获取 Wuban 用户信息"
)
async def get_user_info(
    request: Request,
    auth_result: CombinedAuthResult = Depends(combined_auth)
):
    """获取用户信息"""
    try:
        # 从请求头获取认证信息
        token = request.headers.get("Authorization")
        if not token:
            raise HTTPException(
                status_code=401,
                detail="No authorization token provided"
            )
        
        # 获取用户信息
        user_info = await user_service.get_user_info(
            user_id=auth_result.wuban_id,
            token=token
        )
        
        return user_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_user_info: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get user info: {str(e)}"
        )

# 定义请求模型
class ConversationUpdateRequest(BaseModel):
    arg: Dict[str, str]

@librechat_router.post(
    "/convos/update",
    description="更新会话信息，如标题或归档状态"
)
async def update_conversation(
    request: ConversationUpdateRequest,
    auth_result: CombinedAuthResult = Depends(combined_auth),
    conversation_history_manager: ConversationHistoryManager = Depends(get_conversation_history_manager)
):
    """更新会话信息"""
    try:
        conversation_id = request.arg.get("conversationId")
        if not conversation_id:
            raise HTTPException(
                status_code=400,
                detail="Missing conversationId"
            )
            
        # 构建更新数据
        update_data = {}
        
        # 处理标题更新
        if "title" in request.arg:
            update_data["title"] = request.arg["title"]
            
        # 处理归档状态更新
        if "isArchived" in request.arg:
            update_data["isArchived"] = request.arg["isArchived"]
            
        if not update_data:
            raise HTTPException(
                status_code=400,
                detail="No update data provided"
            )
            
        logger.info(f"Updating conversation {conversation_id} with data: {update_data}")
        
        # 使用封装的方法处理数据库操作
        response = await conversation_history_manager.update_conversation(
            user_id=auth_result.wuban_id,
            conversation_id=conversation_id,
            update_data=update_data
        )
        
        logger.info(f"Successfully updated conversation: {conversation_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in update_conversation endpoint: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update conversation: {str(e)}"
        )