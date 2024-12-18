from datetime import datetime
from fastapi import APIRouter, Depends, Request, Response, HTTPException
from pydantic.main import BaseModel
from litellm.proxy.auth.user_api_key_auth import user_api_key_auth
from litellm.proxy.wuban.conversation_history_manager import (
    ConversationHistoryManager, 
    UserMessage, 
    AssistantMessage, 
    ErrorMessage
)
from typing import List, Optional, AsyncGenerator, Dict, Any,Union
from litellm.proxy._types import UserAPIKeyAuth
import asyncio
import uuid
import json
from fastapi.responses import StreamingResponse
import traceback
from fastapi.logger import logger as fastapi_logger

# 添加路由查找函数
def get_route_by_path(request: Request, path: str):
    """根据路径获取路由"""
    for route in request.app.router.routes:
        if route.path == path:
            return route
    raise HTTPException(status_code=500, detail=f"Route {path} not found")

librechat_router = APIRouter(
    prefix="/api",
    tags=["librechat"],
    dependencies=[Depends(user_api_key_auth)]
)

# 添加 prisma_client 属性
librechat_router.prisma_client = None

# 初始化 ConversationHistoryManager
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
    createdAt: datetime
    isCreatedByUser: bool

class ConversationResponse(BaseModel):
    conversationId: str
    title: Optional[str]
    model: Optional[str]
    modelDisplayLabel: Optional[str]
    createdAt: datetime
    updatedAt: datetime
    messages: List[MessageResponse]

# 获取会话列表
@librechat_router.get(
    "/convos",
    description="获取用户的所有聊天会话列表"
)
async def list_conversations(
    pageNumber: int = 1,
    user_api_key_dict: UserAPIKeyAuth = Depends(user_api_key_auth),
    conversation_history_manager: ConversationHistoryManager = Depends(get_conversation_history_manager)
):
    try:
        page_size = 25
        skip = (pageNumber - 1) * page_size
        
        result = await conversation_history_manager.get_chat_history(
            user_api_key_dict=user_api_key_dict,
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
    response_model=List[MessageResponse],  # 修改返回类型
    description="获取指定会话的消息列表"
)
async def get_conversation(
    conversation_id: str,
    user_api_key_dict: UserAPIKeyAuth = Depends(user_api_key_auth),
    conversation_history_manager: ConversationHistoryManager = Depends(get_conversation_history_manager)
):
    """获取指定会话的消息列表"""
    try:
        messages = await conversation_history_manager.get_conversation_messages(
            user_api_key_dict=user_api_key_dict,
            conversation_id=conversation_id
        )
        
        if not messages:
            raise HTTPException(
                status_code=404,
                detail="No messages found"
            )
            
        return messages
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching messages: {str(e)}"
        )

# 删除会话
@librechat_router.delete(
    "/conversations/{conversation_id}",
    description="删除指定的聊天会话及其所有消息"
)
async def delete_conversation(
    conversation_id: str,
    user_api_key_dict: UserAPIKeyAuth = Depends(user_api_key_auth),
    conversation_history_manager: ConversationHistoryManager = Depends(get_conversation_history_manager)
):
    """删除指定的聊天会话及其所有相关消息"""
    try:
        await conversation_history_manager.delete_chat_history(
            user_api_key_dict=user_api_key_dict,
            session_id=conversation_id
        )
        return {"status": "success", "message": "Conversation deleted successfully"}
    except Exception as e:
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
        self.logger = fastapi_logger
    
    def process_chunk(self, chunk: Union[str, bytes]) -> Optional[str]:
        """处理单个数据块并返回格式化的事件"""
        try:
            # 处理 chunk 格式
            chunk_str = self._normalize_chunk(chunk)
            if chunk_str is None:
                return None
                
            # 解析内容
            content = self._extract_content(chunk_str)
            if not content:
                return None
                
            # 更新完整响应
            self.full_response += content
            
            # 生成事件
            return self._create_message_event(content)
            
        except Exception as e:
            self.logger.error(f"Error processing chunk: {str(e)}")
            return None
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
                content = chunk_data["choices"][0].get("delta", {}).get("content", "")
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
            "message": {
                "messageId": self.assistant_message_id,
                "parentMessageId": self.user_message.message_id,
                "conversationId": self.user_message.conversation_id,
                "sender": "Assistant",
                "text": content,
                "isCreatedByUser": False,
                "model": self.model
            }
        }
        
        if self.first_chunk:
            event_data["created"] = True
            self.first_chunk = False
            self.logger.info("Added 'created' flag to first chunk")
        
        return self._format_event("message", event_data)
    
    def format_user_message_event(self,text:str) -> str:
        """格式化用户消息事件"""
        event_data = {
            "message": {
                "messageId": self.user_message.message_id,
                "parentMessageId": self.user_message.parent_message_id,
                "conversationId": self.user_message.conversation_id,
                "sender": "User",
                "text": text,
                "isCreatedByUser": True
            },
            "created": True
        }
        return self._format_event("message", event_data)
    
    def format_final_event(self) -> str:
        """格式化最终事件"""
        event_data = {
            "final": True,
            "conversation": self._get_conversation_data(),
            "title": self.user_message.text[:50],
            "requestMessage": self._get_request_message_data(),
            "responseMessage": self._get_response_message_data()
        }
        return self._format_event("message", event_data)
    
    def _get_conversation_data(self) -> Dict[str, Any]:
        """获取会话数据"""
        return {
            "_id": self.user_message.conversation_id,
            "user": self.user_message.user_id,
            "conversationId": self.user_message.conversation_id,
            "__v": 0,
            "createdAt": datetime.now().isoformat(),
            "endpoint": "openai",
            "endpointType": "custom",
            "isArchived": False,
            "messages": [self.user_message.message_id, self.assistant_message_id],
            "model": self.model,
            "resendFiles": True,
            "tags": [],
            "title": self.user_message.text[:50],
            "updatedAt": datetime.now().isoformat()
        }
    
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
    user_api_key_dict: UserAPIKeyAuth,
    conversation_history_manager: ConversationHistoryManager
) -> AsyncGenerator[str, None]:
    """处理流式响应并保存消息"""
    
    event_manager = StreamEventManager(user_message, model)
    
    first_chunk = True
    
    try:
        async for chunk in response.body_iterator:
            if formatted_event := event_manager.process_chunk(chunk):
                yield formatted_event
                
    except Exception as e:
        fastapi_logger.error(f"Error in stream processing: {str(e)}")
        raise
    finally:
        try:
            # 发送最终事件
            yield event_manager.format_final_event()
            
            # 保存助手消息
            assistant_message = AssistantMessage(
                text=event_manager.full_response,
                user_id=user_api_key_dict.user_id,
                model=model,
                conversation_id=user_message.conversation_id,
                parent_message_id=user_message.message_id,
                message_id=event_manager.assistant_message_id
            )
            asyncio.create_task(
                conversation_history_manager.save_assistant_message(assistant_message)
            )
        except Exception as e:
            fastapi_logger.error(f"Error in final event processing: {str(e)}")

@librechat_router.post("/ask/{model}")
async def chat_completion_with_history(
    request: Request,
    model: str,
    user_api_key_dict: UserAPIKeyAuth = Depends(user_api_key_auth),
    conversation_history_manager: ConversationHistoryManager = Depends(get_conversation_history_manager)
):
    user_message = None
    try:
        fastapi_logger.info(f"Starting request for model: {model}")
        data = await request.json()
        is_streaming = data.get("stream", False)
        fastapi_logger.info(f"Streaming mode: {is_streaming}")
        
        # 构建用户消息
        conversation_id = data.get("conversationId") or str(uuid.uuid4())
        parent_message_id = data.get("parentMessageId") or ConversationHistoryManager.NO_PARENT
        endpoint = data.get("endpoint") or ""
        fastapi_logger.info(f"Conversation ID: {conversation_id}")
        fastapi_logger.info(f"Parent message ID: {parent_message_id}")
        
        user_message = UserMessage(
            text=data["messages"][-1]["content"],
            user_id=user_api_key_dict.user_id,
            model=model,
            conversation_id=conversation_id,
            parent_message_id=parent_message_id,
            endpoint=endpoint
        )
        fastapi_logger.info(f"Created user message: {user_message}")
        
        # 异步保存用户消息
        fastapi_logger.info("Saving user message")
        asyncio.create_task(
            conversation_history_manager.save_user_message(user_message)
        )
        
        # 获取 chat_completion 路由
        fastapi_logger.info("Getting chat completion route")
        chat_completion_route = get_route_by_path(request, "/v1/chat/completions")
        
        # 调用 chat_completion
        data["model"] = model
        fastapi_logger.info("Calling chat completion endpoint")
        response = await chat_completion_route.endpoint(
            request=request,
            fastapi_response=Response(),
            model=model,
            user_api_key_dict=user_api_key_dict
        )

        if is_streaming:
            fastapi_logger.info("Processing streaming response")
            return StreamingResponse(
                stream_and_save(
                    response=response,
                    user_message=user_message,
                    model=model,
                    user_api_key_dict=user_api_key_dict,
                    conversation_history_manager=conversation_history_manager
                ),
                media_type=response.media_type
            )
        else:
            fastapi_logger.info("Processing non-streaming response")
            # 非流式响应，直接保存助手消息
            assistant_message = AssistantMessage(
                text=response.choices[0].message.content,
                user_id=user_api_key_dict.user_id,
                model=model,
                conversation_id=user_message.conversation_id,
                parent_message_id=user_message.message_id,
                endpoint=user_message.endpoint
            )
            fastapi_logger.info(f"Created assistant message: {assistant_message}")
            
            asyncio.create_task(
                conversation_history_manager.save_assistant_message(assistant_message)
            )
            # 构建响应
            libre_response = {
                "messageId": assistant_message.message_id,
                "conversationId": assistant_message.conversation_id,
                "text": assistant_message.text,
                "sender": assistant_message.sender,
                "parentMessageId": assistant_message.parent_message_id,
                "model": assistant_message.model,
                "endpoint": assistant_message.endpoint,
                "isCreatedByUser": assistant_message.is_created_by_user
            }
            
            fastapi_logger.info("Request completed successfully")
            return libre_response
            
    except Exception as e:
        fastapi_logger.error(f"Error occurred: {str(e)}")
        fastapi_logger.error(f"Traceback: {traceback.format_exc()}")
        # 异步保存错误消息
        if conversation_history_manager and user_message:
            error_message = ErrorMessage(
                text=str(e),
                user_id=user_api_key_dict.user_id,
                model=model,
                conversation_id=user_message.conversation_id,
                parent_message_id=user_message.message_id,
                error=str(e)
            )
            fastapi_logger.error(f"Created error message: {error_message}")
            asyncio.create_task(
                conversation_history_manager.save_error_message(error_message)
            )
        raise