"""
JSON文件存储实现
适合本地开发和链路排查
"""

import json
import os
from typing import Type, Optional, List, Dict, Any, Generic
from pathlib import Path

from app.repositories.base import BaseRepository, T
from app.config import settings
from app.core.exceptions import NotFoundException, InternalServerException


class JsonRepository(BaseRepository[T], Generic[T]):
    """
    JSON文件存储仓储实现
    每个实体类型对应一个JSON文件
    """
    
    def __init__(self, entity_type: Type[T], collection_name: str):
        """
        初始化JSON仓储
        
        Args:
            entity_type: 实体类型
            collection_name: 集合名称（文件名）
        """
        self.entity_type = entity_type
        self.collection_name = collection_name
        self.file_path = Path(settings.STORAGE_PATH) / f"{collection_name}.json"
        
        # 确保存储目录存在
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 初始化文件
        if not self.file_path.exists():
            self._save_data([])
    
    def _load_data(self) -> List[Dict[str, Any]]:
        """加载JSON文件数据"""
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            raise InternalServerException(
                message=f"读取存储文件失败: {str(e)}",
                details={"file": str(self.file_path)}
            )
    
    def _save_data(self, data: List[Dict[str, Any]]) -> None:
        """保存数据到JSON文件"""
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            raise InternalServerException(
                message=f"保存存储文件失败: {str(e)}",
                details={"file": str(self.file_path)}
            )
    
    def _match_filters(self, entity_dict: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """检查实体是否匹配过滤条件"""
        for key, value in filters.items():
            if key not in entity_dict or entity_dict[key] != value:
                return False
        return True
    
    async def create(self, entity: T) -> T:
        """创建实体"""
        data = self._load_data()
        
        # 检查ID是否已存在
        if any(item["id"] == entity.id for item in data):
            from app.core.exceptions import ConflictException
            raise ConflictException(
                message=f"实体ID已存在: {entity.id}",
                details={"id": entity.id}
            )
        
        # 添加新实体
        entity_dict = entity.model_dump()
        data.append(entity_dict)
        self._save_data(data)
        
        return entity
    
    async def get_by_id(self, entity_id: str) -> Optional[T]:
        """根据ID获取实体"""
        data = self._load_data()
        
        for item in data:
            if item["id"] == entity_id:
                return self.entity_type(**item)
        
        return None
    
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None
    ) -> List[T]:
        """获取所有实体"""
        data = self._load_data()
        
        # 应用过滤器
        if filters:
            data = [item for item in data if self._match_filters(item, filters)]
        
        # 应用排序
        if order_by:
            reverse = False
            field_name = order_by
            if order_by.startswith('-'):
                reverse = True
                field_name = order_by[1:]
            
            # 分离None和非None值
            items_with_none = []
            items_with_value = []
            
            for item in data:
                value = item.get(field_name)
                if value is None:
                    items_with_none.append(item)
                else:
                    items_with_value.append(item)
            
            # 对非None值排序
            items_with_value.sort(key=lambda x: x.get(field_name), reverse=reverse)
            
            # 合并：倒序时None在前，正序时None在后
            if reverse:
                data = items_with_none + items_with_value
            else:
                data = items_with_value + items_with_none
        else:
            # 默认按创建时间倒序
            if 'created_at' in (data[0] if data else {}):
                data = sorted(data, key=lambda x: x.get('created_at') or '', reverse=True)
        
        # 应用分页
        data = data[skip:skip + limit]
        
        # 转换为实体对象
        return [self.entity_type(**item) for item in data]
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """统计实体数量"""
        data = self._load_data()
        
        if filters:
            data = [item for item in data if self._match_filters(item, filters)]
        
        return len(data)
    
    async def update(self, entity_id: str, entity: T) -> Optional[T]:
        """更新实体"""
        data = self._load_data()
        
        for i, item in enumerate(data):
            if item["id"] == entity_id:
                # 更新时间戳
                entity.update_timestamp()
                
                # 更新数据
                data[i] = entity.model_dump()
                self._save_data(data)
                
                return entity
        
        return None
    
    async def delete(self, entity_id: str) -> bool:
        """删除实体"""
        data = self._load_data()
        original_len = len(data)
        
        data = [item for item in data if item["id"] != entity_id]
        
        if len(data) < original_len:
            self._save_data(data)
            return True
        
        return False
    
    async def exists(self, entity_id: str) -> bool:
        """检查实体是否存在"""
        data = self._load_data()
        return any(item["id"] == entity_id for item in data)

