"""
抽象存储层基类
定义统一的数据访问接口
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List, Dict, Any

from app.models.base import BaseModelMixin

T = TypeVar("T", bound=BaseModelMixin)


class BaseRepository(ABC, Generic[T]):
    """
    基础仓储抽象类
    定义CRUD操作接口
    """
    
    @abstractmethod
    async def create(self, entity: T) -> T:
        """
        创建实体
        
        Args:
            entity: 实体对象
        
        Returns:
            创建的实体
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, entity_id: str) -> Optional[T]:
        """
        根据ID获取实体
        
        Args:
            entity_id: 实体ID
        
        Returns:
            实体对象，不存在返回None
        """
        pass
    
    @abstractmethod
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[T]:
        """
        获取所有实体（支持分页和过滤）
        
        Args:
            skip: 跳过数量
            limit: 限制数量
            filters: 过滤条件
        
        Returns:
            实体列表
        """
        pass
    
    @abstractmethod
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        统计实体数量
        
        Args:
            filters: 过滤条件
        
        Returns:
            实体数量
        """
        pass
    
    @abstractmethod
    async def update(self, entity_id: str, entity: T) -> Optional[T]:
        """
        更新实体
        
        Args:
            entity_id: 实体ID
            entity: 更新后的实体对象
        
        Returns:
            更新后的实体，不存在返回None
        """
        pass
    
    @abstractmethod
    async def delete(self, entity_id: str) -> bool:
        """
        删除实体
        
        Args:
            entity_id: 实体ID
        
        Returns:
            是否删除成功
        """
        pass
    
    @abstractmethod
    async def exists(self, entity_id: str) -> bool:
        """
        检查实体是否存在
        
        Args:
            entity_id: 实体ID
        
        Returns:
            是否存在
        """
        pass

