from prisma import Prisma
import json
from typing import List, Dict, Any, Optional
from prisma.errors import RawQueryError
from functools import partial
from .logger_util import WubanLogger

logger = WubanLogger.get_logger()

class SafeUpsertWrapper:
    """用于安全处理数据库 upsert 操作的包装器类
    
    主要解决以下问题：
    1. 处理空字符串、空列表、空字典等特殊值
    2. 确保数据在写入 SQLite 时的格式正确
    3. 提供详细的日志记录用于调试
    
    示例:
    ```python
    # 原始数据可能包含空值或特殊格式
    data = {
        'name': '',
        'tags': [],
        'metadata': {}
    }
    
    # 使用包装器处理后的数据
    cleaned_data = {
        'tags': '[]',
        'metadata': '{}'
    }
    # 注意：空字符串的 'name' 字段被移除
    ```
    """
    def __init__(self, original_model):
        self._original = original_model
        logger.debug(f"Initializing SafeUpsertWrapper with model: {original_model}")
        # 保留所有原始属性
        for attr in dir(original_model):
            if not attr.startswith('_') and attr != 'upsert':
                setattr(self, attr, getattr(original_model, attr))

    def _clean_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """清理和转换数据，确保数据格式适合 SQLite 存储
        
        处理规则：
        1. 移除空字符串值
        2. 将空列表转换为字符串 "[]"
        3. 将空字典转换为字符串 "{}"
        
        Args:
            data: 需要清理的原始数据字典
            
        Returns:
            清理后的数据字典
            
        示例:
        ```python
        wrapper = SafeUpsertWrapper(model)
        original_data = {
            'username': '',
            'preferences': [],
            'settings': {}
        }
        cleaned = wrapper._clean_data(original_data)
        # 结果: {'preferences': '[]', 'settings': '{}'}
        ```
        """
        logger.debug(f"Cleaning data: {data}")
        if not data:
            return data
        
        result = {}
        for key, value in data.items():
            if value == "":
                logger.debug(f"Skipping empty string for field: {key}")
                continue
            elif isinstance(value, (list, dict)):
                if isinstance(value, list) and len(value) == 0:
                    logger.debug(f"Converting empty list to '[]' for field: {key}")
                    result[key] = "[]"
                elif isinstance(value, dict) and len(value) == 0:
                    logger.debug(f"Converting empty dict to '{{}}' for field: {key}")
                    result[key] = "{}"
            else:
                result[key] = value
        
        logger.debug(f"Cleaned data result: {result}")
        return result

    async def upsert(self, **kwargs):
        """执行安全的 upsert 操作，确保数据被正确清理
        
        处理流程：
        1. 分别清理 create 和 update 数据
        2. 执行实际的 upsert 操作
        3. 记录详细的操作日志
        
        Args:
            **kwargs: upsert 操作的参数，通常包含 'data' 字典
            
        Returns:
            upsert 操作的结果
            
        示例:
        ```python
        wrapper = SafeUpsertWrapper(user_model)
        result = await wrapper.upsert(
            where={'email': 'user@example.com'},
            data={
                'create': {'name': 'New User', 'tags': []},
                'update': {'last_login': 'now', 'metadata': {}}
            }
        )
        ```
        """
        logger.info(f"Upsert operation started with data: {kwargs}")
        
        if 'data' in kwargs:
            if 'create' in kwargs['data']:
                logger.debug("Cleaning create data")
                kwargs['data']['create'] = self._clean_data(kwargs['data']['create'])
            if 'update' in kwargs['data']:
                logger.debug("Cleaning update data")
                kwargs['data']['update'] = self._clean_data(kwargs['data']['update'])
        
        logger.debug(f"Final upsert data: {kwargs}")
        try:
            result = await self._original.upsert(**kwargs)
            logger.info("Upsert operation completed successfully")
            return result
        except Exception as e:
            logger.error(f"Upsert operation failed: {str(e)}")
            raise

def extend_prisma_client(client: Prisma) -> Prisma:
    """扩展 Prisma 客户端，添加 SQLite 特定的功能支持
    
    主要功能：
    1. 注册 JSON 序列化器
    2. 为特定表添加安全的 upsert 操作
    3. 添加 SQLite 视图支持
    4. 实现 create_many 批量创建功能
    
    Args:
        client: 原始的 Prisma 客户端实例
        
    Returns:
        扩展后的 Prisma 客户端
        
    示例:
    ```python
    prisma = Prisma()
    await prisma.connect()
    
    # 扩展客户端
    extended_client = extend_prisma_client(prisma)
    
    # 现在可以使用扩展功能
    await extended_client.db.users.create_many(
        data=[
            {'name': 'User 1', 'email': 'user1@example.com'},
            {'name': 'User 2', 'email': 'user2@example.com'}
        ]
    )
    ```
    """
    logger.info("Starting Prisma client extension")
    
    # 注册 JSON 类型转换器
    client._json_serializer = json.dumps
    client._json_deserializer = json.loads
    logger.debug("JSON serializers registered")

    # 需要包装的表列表 适配litellm原有的一些数据库操作不支持sqlite
    tables_to_wrap = [
        'litellm_config',
        'litellm_spendlogs',
        'litellm_usertable',
        'litellm_verificationtoken'
    ]

    # 循环包装所有需要的表
    for table_name in tables_to_wrap:
        try:
            original_model = getattr(client.db, table_name)
            logger.debug(f"Preloaded {table_name} table")
            setattr(client.db, table_name, SafeUpsertWrapper(original_model))
            logger.debug(f"Wrapped {table_name} table")
        except Exception as e:
            logger.warning(f"Failed to wrap table {table_name}: {str(e)}")

    # SQLite 视图检查
    async def check_view_exists_sqlite(view_name: Optional[str] = None) -> bool:
        """检查 SQLite 数据库中是否存在指定的视图
        
        Args:
            view_name: 要检查的视图名称，如果为 None 则检查是否存在任何视图
            
        Returns:
            bool: 视图是否存在
            
        示例:
        ```python
        # 检查特定视图
        exists = await check_view_exists_sqlite('user_stats_view')
        
        # 检查是否有任何视图
        has_views = await check_view_exists_sqlite()
        ```
        """
        try:
            if not view_name:
                query = "SELECT name FROM sqlite_master WHERE type='view' LIMIT 1"
                result = await client.query_raw(query)
                return bool(result)
            else:
                query = "SELECT name FROM sqlite_master WHERE type='view' AND name=?"
                result = await client.query_raw(query, view_name)
                return bool(result)
        except Exception:
            return False

    # 包装 check_view_exists 方法
    original_check_view_exists = client.check_view_exists
    
    async def wrapped_check_view_exists(view_name: Optional[str] = None) -> bool:
        try:
            if view_name is None:
                return await original_check_view_exists()
            return await original_check_view_exists(view_name)
        except RawQueryError as e:
            if "no such table: pg_views" in str(e):
                return await check_view_exists_sqlite(view_name)
            raise e

    client.check_view_exists = wrapped_check_view_exists

    # 通用的 create_many 包装函数
    def create_safe_create_many(model):
        """创建一个安全的批量创建函数，用于替代 SQLite 不支持的 create_many
        
        实现原理：
        通过循环调用单个 create 操作来模拟批量创建功能
        
        Args:
            model: 数据库模型对象
            
        Returns:
            一个异步函数，用于执行批量创建操作
            
        示例:
        ```python
        # 为 user 模型创建批量插入功能
        user_model.create_many = create_safe_create_many(user_model)
        
        # 使用批量创建
        await user_model.create_many(data=[
            {'name': 'Alice', 'age': 25},
            {'name': 'Bob', 'age': 30}
        ])
        ```
        """
        async def safe_create_many(data: List[Dict[str, Any]], **kwargs):
            """直接使用单个创建来模拟 create_many"""
            logger.debug(f"Creating multiple records: {len(data)} items")
            results = []
            for item in data:
                try:
                    result = await model.create(data=item)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Failed to create item: {str(e)}")
                    raise e
            return results
        return safe_create_many

    # 为所有模型添加 safe_create_many
    logger.debug("Adding safe_create_many to all models")
    logger.debug(f"dir(client.db): {dir(client.db)}")
    for attr_name in dir(client.db):
        if not attr_name.startswith('_'):
            model = getattr(client.db, attr_name)
            if hasattr(model, 'create_many'):
                try:
                    logger.debug(f"Adding safe_create_many to model: {attr_name}")
                    setattr(model, 'create_many', create_safe_create_many(model))
                except Exception as e:
                    logger.error(f"Failed to add safe_create_many to {attr_name}: {str(e)}")
                    continue

    # 添加 SQLite 特定的行数查询
    async def _get_spend_logs_row_count_sqlite(*args, **kwargs) -> int:
        """SQLite 兼容的获取表行数方法"""
        try:
            query = """
            SELECT COUNT(*) as count 
            FROM "LiteLLM_SpendLogs"
            """
            result = await client.query_raw(query)
            return result[0]["count"] if result else 0
        except Exception as e:
            logger.error(f"Error getting LiteLLM_SpendLogs row count: {e}")
            return 0
    # 直接使用 SQLite 的行数查询
    async def _get_spend_logs_row_count_sqlite(*args, **kwargs) -> int:
        """SQLite 兼容的获取表行数方法"""
        try:
            query = """
            SELECT COUNT(*) as count 
            FROM "LiteLLM_SpendLogs"
            """
            result = await client.query_raw(query)
            return result[0]["count"] if result else 0
        except Exception as e:
            logger.error(f"Error getting LiteLLM_SpendLogs row count: {e}")
            return 0
    # 替换原始方法
    setattr(client, '_get_spend_logs_row_count', _get_spend_logs_row_count_sqlite)

    logger.info("Prisma client extension completed")
    return client