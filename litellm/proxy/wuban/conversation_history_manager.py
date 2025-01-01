from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from litellm.proxy.utils import PrismaClient
from litellm.proxy._types import UserAPIKeyAuth
import uuid
import traceback
from .logger_util import WubanLogger
import prisma
from fastapi import HTTPException

# 重置并获取 logger
logger = WubanLogger.reset_logger()

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
    endpoint_type: Optional[str] = None
    files: Optional[List[Dict]] = None

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
    endpoint_type: Optional[str] = None
    is_created_by_user: bool = False
    error: Optional[str] = None
    files: Optional[List[Dict]] = None  # 添加 files 字段

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
            endpoint_type=message.endpoint_type,
            is_created_by_user=message.is_created_by_user,
            error=message.error if isinstance(message, ErrorMessage) else None,
            files=message.files if hasattr(message, 'files') else None
        )

class ConversationHistoryManager:
    NO_PARENT = "00000000-0000-0000-0000-000000000000"
    
    def __init__(self, prisma_client: PrismaClient):
        self.prisma_client = prisma_client
        logger.info("Initializing ConversationHistoryManager")

    async def _ensure_connected(self):
        """确保数据库连接已建立"""
        try:
            # 尝试重新连接
            await self.prisma_client.connect()
            logger.info("Database connected successfully")
        except Exception as e:
            logger.error(f"Database connection error: {str(e)}")
            raise
    
    async def _ensure_user_exists(self, wuban_user_id: str, litellm_user_id: str) -> None:
        """确保用户映射关系存在，如果不存在则创建"""
        try:
            # 查找映射关系
            mapping = await self.prisma_client.db.wubanusermapping.find_unique(
                where={"wuban_user_id": wuban_user_id}
            )
            
            if not mapping:
                logger.info(f"Creating new user mapping: wuban_id={wuban_user_id}, litellm_id={litellm_user_id}")
                # 创建新的映射关系
                await self.prisma_client.db.wubanusermapping.create(
                    data={
                        "wuban_user_id": wuban_user_id,
                        "litellm_user_id": litellm_user_id
                    }
                )
                logger.info(f"Created user mapping for wuban_user_id: {wuban_user_id}")
            elif mapping.litellm_user_id != litellm_user_id:
                # 如果映射存在但 litellm_user_id 不匹配，更新映射
                logger.info(f"Updating user mapping for wuban_user_id: {wuban_user_id}")
                await self.prisma_client.db.wubanusermapping.update(
                    where={"wuban_user_id": wuban_user_id},
                    data={"litellm_user_id": litellm_user_id}
                )
                
        except Exception as e:
            logger.error(f"Error ensuring user mapping exists: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    
    async def _ensure_conversation_exists(self, message: BaseMessage, litellm_user_id: str) -> None:
        """确保会话存在，如果不存在则创建"""
        try:
            # 首先确保用户映射存在
            await self._ensure_user_exists(message.user_id, litellm_user_id)
            
            existing_conversation = await self.prisma_client.db.conversation.find_first(
                where={"conversationId": message.conversation_id}
            )
            
            if not existing_conversation:
                logger.info(f"Creating new conversation: {message.conversation_id}")
                await self.prisma_client.db.conversation.create(
                    data={
                        "conversationId": message.conversation_id,
                        "userId": message.user_id,
                        "title": self._generate_title(message.text),
                        "model": message.model,
                        "modelDisplayLabel": message.model,
                        "endpoint": message.endpoint or "",
                        "endpointType": message.endpoint_type or ""
                    }
                )
                logger.info(f"Created conversation: {message.conversation_id}")
            
            return existing_conversation
        except Exception as e:
            logger.error(f"Error ensuring conversation exists: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    
    def _generate_title(self, text: str, max_length: int = 10) -> str:
        """从消息文本生成会话标题"""
        # 如果文本为空，返回 "新会话"
        if not text.strip():
            return "新会话"
        
        # 移除多余空白字符
        title = " ".join(text.split())
        # 截取合适长度
        return title[:max_length] if len(title) >= max_length else title


    
    async def save_user_message(
        self, 
        message: UserMessage, 
        litellm_user_id: str
    ) -> Tuple[str, str]:
        """保存用户消息
        
        Args:
            message: 用户消息对象
            litellm_user_id: LiteLLM 用户 ID
            
        Returns:
            Tuple[str, str]: (conversation_id, message_id)
        """
        try:
            
            # 检查并创建会话（如果不存在）
            await self._ensure_conversation_exists(message, litellm_user_id=litellm_user_id)

            # 3. 创建消息
            chat_message = ChatMessage.from_base_message(message)
           
            return await self._save_message(chat_message)
                
        except prisma.errors.PrismaError as e:
            logger.error(f"Database error while saving user message: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Database error while saving user message"
            )
        except Exception as e:
            logger.error(f"Error saving user message: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save user message: {str(e)}"
            )

    async def save_assistant_message(self, message: AssistantMessage, litellm_user_id: str) -> str:
        logger.info(f"Saving assistant message: {message}")
        try:
            # 确保会话存在
            await self._ensure_conversation_exists(message,litellm_user_id=litellm_user_id)
            
            chat_message = ChatMessage.from_base_message(message)
            return await self._save_message(chat_message)
            
        except Exception as e:
            logger.error(f"Error saving assistant message: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    async def save_error_message(self, message: ErrorMessage,litellm_user_id: str) -> str:
        """保存错误响应消息"""
        try:
            # 确保会话存在
            await self._ensure_conversation_exists(message,litellm_user_id=litellm_user_id)
            
            chat_message = ChatMessage.from_base_message(message)
            return await self._save_message(chat_message)
            
        except Exception as e:
            logger.error(f"Error saving error message: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    async def _save_message(self, message: ChatMessage) -> str:
        """保存单条消息的内部方法"""
        # 创建消息基本数据
        message_data = {
            "messageId": message.message_id,
            "conversationId": message.conversation_id,
            "userId": message.user_id,
            "text": message.text,
            "sender": message.sender,
            "parentMessageId": message.parent_message_id,
            "isCreatedByUser": message.is_created_by_user,
            "model": message.model,
            "endpoint": message.endpoint,
            "endpointType": message.endpoint_type,
            "error": message.error
        }

        # 创建消息
        await self.prisma_client.db.message.create(
            data=message_data
        )

        # 如果有文件，创建文件关联
        if message.files:
            for file_info in message.files:
                try:
                    # 创建消息-文件关联
                    await self.prisma_client.db.messagefile.create(
                        data={
                            "messageId": message.message_id,
                            "fileId": file_info["_id"]  # 直接使用已存在文件的ID
                        }
                    )
                except Exception as e:
                    logger.error(f"Error saving file {file_info.get('_id')}: {str(e)}")
                    continue

        return message.message_id


    async def get_chat_history(
        self,
        user_id: str,
        conversation_id: Optional[str] = None,
        limit: int = 25,
        skip: int = 0
    ) -> Dict:
        """获取聊天历史记录"""
        try:
            where = {"userId": user_id}
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
                    "endpoint": conv.endpoint,
                    "isArchived": False,
                    "messages": [msg.messageId for msg in conv.messages],
                    "model": conv.model,
                    "modelDisplayLabel": conv.modelDisplayLabel,
                    "resendFiles": True,
                    "tags": [],
                    "title": conv.title
                }
                
                # 只有当 endpointType 不为空时才添加
                if conv.endpointType:
                    formatted_conv["endpointType"] = conv.endpointType
                    
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
        wuban_user_id: str,
        conversation_id: str
    ) -> Dict[str, int]:
        """删除聊天历史记录
        
        Returns:
            包含删除消息数量的字典
        """
        try:
            # 先统计消息数量
            message_count = await self.prisma_client.db.message.count(
                where={
                    "conversationId": conversation_id,
                    "userId": wuban_user_id
                }
            )
            
            # 先删除所有相关消息
            await self.prisma_client.db.message.delete_many(
                where={
                    "conversationId": conversation_id,
                    "userId": wuban_user_id
                }
            )
            
            # 再删除会话
            await self.prisma_client.db.conversation.delete_many(
                where={
                    "conversationId": conversation_id,
                    "userId": wuban_user_id
                }
            )
            
            return {
                "messages_deleted": message_count
            }
            
        except prisma.errors.PrismaError as e:
            if "Record to delete does not exist" in str(e):
                raise HTTPException(
                    status_code=404,
                    detail="Conversation not found or unauthorized"
                )
            logger.error(f"Database error while deleting chat history: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Database error while deleting chat history"
            )
        except Exception as e:
            logger.error(f"Error deleting chat history: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete chat history: {str(e)}"
            )

    async def get_conversation_messages(
        self,
        user_id: str,
        conversation_id: str
    ) -> List[Dict]:
        """获取指定会话的所有消息"""
        try:
            # 查询会话消息
            messages = await self.prisma_client.db.message.find_many(
                where={
                    "conversationId": conversation_id,
                    "userId": user_id
                },
                order={
                    "createdAt": "asc"  # 按时间正序排列消息
                }
            )
            
            # 格式化消息数据
            formatted_messages = []
            for msg in messages:
                message_dict = {
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
                
                # 只有当 endpointType 不为空时才添加
                if msg.endpointType:
                    message_dict["endpointType"] = msg.endpointType
                    
                formatted_messages.append(message_dict)
            
            return formatted_messages
            
        except Exception as e:
            logger.error(f"Error getting conversation messages: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise Exception(f"Failed to get conversation messages: {str(e)}")

    async def update_conversation(
        self, 
        user_id: str, 
        conversation_id: str, 
        update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """更新会话信息（标题或归档状态）"""
        try:
            # 1. 更新会话信息
            conversation = await self.prisma_client.db.conversation.update(
                where={
                    "conversationId": conversation_id,
                    "userId": user_id
                },
                data=update_data
            )
            
            if not conversation:
                raise HTTPException(
                    status_code=404,
                    detail=f"Conversation {conversation_id} not found"
                )
            
            # 2. 获取相关消息ID列表
            messages = await self.prisma_client.db.message.find_many(
                where={
                    "conversationId": conversation_id
                }
            )
            
            # 3. 构建响应
            return {
                "_id": str(uuid.uuid4()),
                "user": user_id,
                "conversationId": conversation_id,
                "__v": 0,
                "createdAt": conversation.createdAt.isoformat(),
                "endpoint": conversation.endpoint or "",
                "endpointType": conversation.endpointType or "",
                "files": [],
                "isArchived": conversation.isArchived,
                "messages": [msg.messageId for msg in messages],  # 直接从完整消息对象中获取 messageId
                "model": conversation.model or "",
                "resendFiles": True,
                "tags": [],
                "title": conversation.title,
                "updatedAt": conversation.updatedAt.isoformat()
            }
            
        except prisma.errors.PrismaError as e:
            if "Record to update not found" in str(e):
                raise HTTPException(
                    status_code=404,
                    detail=f"Conversation {conversation_id} not found"
                )
            logger.error(f"Database error while updating conversation: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Database error while updating conversation"
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating conversation: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to update conversation: {str(e)}"
            )