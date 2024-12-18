from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from litellm.proxy.utils import PrismaClient
from litellm.proxy._types import UserAPIKeyAuth
import litellm
import uuid
import logging
import traceback

logger = logging.getLogger(__name__)

@dataclass
class BaseMessage:
    """基础消息数据类"""
    text: str
    user_id: str
    model: str
    conversation_id: str
    parent_message_id: str
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    endpoint: Optional[str] = None

@dataclass
class UserMessage(BaseMessage):
    """用户消息数据类"""
    sender: str = "user"
    is_created_by_user: bool = True

@dataclass
class AssistantMessage(BaseMessage):
    """助手消息数据类"""
    sender: str = "assistant"
    is_created_by_user: bool = False

@dataclass
class ErrorMessage(BaseMessage):
    """错误消息数据类"""
    sender: str = "assistant"
    is_created_by_user: bool = False
    error: Optional[str] = None  # 添加错误信息字段

@dataclass
class ChatMessage:
    """聊天消息数据类,用于数据库操作"""
    conversation_id: str
    user_id: str
    text: str
    sender: str
    parent_message_id: str
    message_id: str
    model: Optional[str] = None
    endpoint: Optional[str] = None
    is_created_by_user: bool = False
    error: Optional[str] = None  # 添加错误信息字段

    @classmethod
    def from_base_message(cls, message: BaseMessage) -> 'ChatMessage':
        """从基础消息创建聊天消息"""
        return cls(
            conversation_id=message.conversation_id,
            user_id=message.user_id,
            text=message.text,
            sender=message.sender,
            parent_message_id=message.parent_message_id,
            message_id=message.message_id,
            model=message.model,
            endpoint=message.endpoint,
            is_created_by_user=message.is_created_by_user,
            error=message.error if isinstance(message, ErrorMessage) else None
        )

class ConversationHistoryManager:
    NO_PARENT = "00000000-0000-0000-0000-000000000000"
    
    def __init__(self, prisma_client: PrismaClient):
        self.prisma_client = prisma_client
        self.logger = logging.getLogger(__name__)

    async def _ensure_connected(self):
        """确保数据库连接已建立"""
        try:
            # 尝试重新连接
            await self.prisma_client.connect()
            logger.info("Database connected successfully")
        except Exception as e:
            logger.error(f"Database connection error: {str(e)}")
            raise
    
    async def _ensure_conversation_exists(self, message: BaseMessage) -> None:
        """确保会话存在，如果不存在则创建"""
        try:
            existing_conversation = await self.prisma_client.db.conversation.find_first(
                where={"conversationId": message.conversation_id}
            )
            
            if not existing_conversation:
                self.logger.info(f"Creating new conversation: {message.conversation_id}")
                await self.prisma_client.db.conversation.create(
                    data={
                        "conversationId": message.conversation_id,
                        "userId": message.user_id,
                        "title": self._generate_title(message.text),
                        "model": message.model,
                        "modelDisplayLabel": message.model,
                        "endpoint": message.endpoint or "openai",
                        "endpointType": "custom"
                    }
                )
                self.logger.info(f"Created conversation: {message.conversation_id}")
            
            return existing_conversation
        except Exception as e:
            self.logger.error(f"Error ensuring conversation exists: {str(e)}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    
    def _generate_title(self, text: str, max_length: int = 100) -> str:
        """从消息文本生成会话标题"""
        # 移除多余空白字符
        title = " ".join(text.split())
        # 截取合适长度
        return title[:max_length] if len(title) > max_length else title


    
    async def save_user_message(self, message: UserMessage) -> Tuple[str, str]:
        try:            
            # 确保会话存在
            await self._ensure_conversation_exists(message)
            # 创建并保存消息
            chat_message = ChatMessage.from_base_message(message)
            message_id = await self._save_message(chat_message)
            
            return message.conversation_id, message_id
            
        except Exception as e:
            logger.error(f"Error saving user message: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    async def save_assistant_message(self, message: AssistantMessage) -> str:
        """保存助手消息"""
        try:
            # 确保会话存在
            await self._ensure_conversation_exists(message)
            
            chat_message = ChatMessage.from_base_message(message)
            return await self._save_message(chat_message)
            
        except Exception as e:
            logger.error(f"Error saving assistant message: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    async def save_error_message(self, message: ErrorMessage) -> str:
        """保存错误响应消息"""
        try:
            # 确保会话存在
            await self._ensure_conversation_exists(message)
            
            chat_message = ChatMessage.from_base_message(message)
            return await self._save_message(chat_message)
            
        except Exception as e:
            logger.error(f"Error saving error message: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    async def _save_message(self, message: ChatMessage) -> str:
        """保存单条消息的内部方法"""
        await self.prisma_client.db.message.create(
            data={
                "messageId": message.message_id,
                "conversationId": message.conversation_id,
                "userId": message.user_id,
                "text": message.text,
                "sender": message.sender,
                "parentMessageId": message.parent_message_id,
                "isCreatedByUser": message.is_created_by_user,
                "model": message.model,
                "endpoint": message.endpoint,
                "error": message.error  # 保存错误信息
            }
        )
        return message.message_id


    async def get_chat_history(
        self,
        user_api_key_dict: UserAPIKeyAuth,
        conversation_id: Optional[str] = None,
        limit: int = 25,
        skip: int = 0
    ) -> Dict:
        """获取聊天历史记录"""
        try:
            where = {"userId": user_api_key_dict.user_id}
            if conversation_id:
                where["conversationId"] = conversation_id
                
            # 获取总记录数
            total_count = await self.prisma_client.db.conversation.count(
                where=where
            )
            
            # 计算总页数
            total_pages = (total_count + limit - 1) // limit
            
            # 获取当前页数据
            conversations = await self.prisma_client.db.conversation.find_many(
                where=where,
                take=limit,
                skip=skip,
                order={"updatedAt": "desc"},
                include={
                    "messages": True
                }
            )
            
            # 格式化会话数据
            formatted_conversations = []
            for conv in conversations:
                formatted_conv = {
                    "_id": conv.id,
                    "user": conv.userId,
                    "conversationId": conv.conversationId,
                    "__v": 0,
                    "createdAt": conv.createdAt,
                    "updatedAt": conv.updatedAt,
                    "endpoint": "openai",
                    "endpointType": "custom",
                    "isArchived": False,
                    "messages": [msg.messageId for msg in conv.messages],
                    "model": conv.model,
                    "modelDisplayLabel": conv.modelDisplayLabel,
                    "resendFiles": True,
                    "tags": [],
                    "title": conv.title
                }
                formatted_conversations.append(formatted_conv)
            
            return {
                "conversations": formatted_conversations,
                "pages": total_pages,
                "pageNumber": (skip // limit) + 1,
                "pageSize": limit
            }
            
        except Exception as e:
            logger.error(f"Error getting chat history: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise Exception(f"Failed to get chat history: {str(e)}")

    async def delete_chat_history(
        self,
        user_api_key_dict: UserAPIKeyAuth,
        conversation_id: str
    ):
        """
        删除聊天历史记录
        """
        # 验证会话属
        conversation = await self.prisma_client.db.conversation.find_first(
            where={
                "conversationId": conversation_id,
                "userId": user_api_key_dict.user_id
            }
        )
        
        if not conversation:
            raise Exception("Conversation not found or unauthorized")
            
        # 删除会话���相关消息
        await self.prisma_client.db.messages.delete_many(
            where={"conversationId": conversation_id}
        )
        await self.prisma_client.db.conversation.delete(
            where={"conversationId": conversation_id}
        ) 

    async def get_conversation_messages(
        self,
        user_api_key_dict: UserAPIKeyAuth,
        conversation_id: str
    ) -> List[Dict]:
        """获取指定会话的所有消息"""
        try:
            # 查询会话消息
            messages = await self.prisma_client.db.message.find_many(
                where={
                    "conversationId": conversation_id,
                    "userId": user_api_key_dict.user_id
                },
                order={
                    "createdAt": "asc"  # 按时间正序排列消息
                }
            )
            
            # 格式化消息数据
            formatted_messages = [
                {
                    "id": msg.id,
                    "messageId": msg.messageId,
                    "conversationId": msg.conversationId,
                    "text": msg.text,
                    "sender": msg.sender,
                    "parentMessageId": msg.parentMessageId,
                    "isCreatedByUser": msg.isCreatedByUser,
                    "model": msg.model,
                    "endpoint": msg.endpoint,
                    "createdAt": msg.createdAt
                }
                for msg in messages
            ]
            
            return formatted_messages
            
        except Exception as e:
            logger.error(f"Error getting conversation messages: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise Exception(f"Failed to get conversation messages: {str(e)}")