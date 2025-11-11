"""
知识库配置存储服务
使用 debug_results 机制存储知识库配置，整合 schema 信息
"""

import json
from typing import Optional, List, Dict, Any
from pathlib import Path
from datetime import datetime
import uuid

from app.config import settings
from app.models.knowledge_base import KnowledgeBase
from app.core.exceptions import NotFoundException, ConflictException, InternalServerException


class KnowledgeBaseStorageService:
    """知识库配置存储服务 - 使用 debug_results 机制"""
    
    def __init__(self):
        self.storage_dir = Path(settings.STORAGE_PATH) / "debug_results" / "knowledge_bases"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.storage_dir / "_index.json"
    
    def _load_index(self) -> List[Dict[str, Any]]:
        """加载索引文件"""
        if not self.index_file.exists():
            return []
        try:
            with open(self.index_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            raise InternalServerException(
                message=f"读取索引文件失败: {str(e)}",
                details={"file": str(self.index_file)}
            )
    
    def _save_index(self, index_data: List[Dict[str, Any]]) -> None:
        """保存索引文件"""
        try:
            with open(self.index_file, "w", encoding="utf-8") as f:
                json.dump(index_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            raise InternalServerException(
                message=f"保存索引文件失败: {str(e)}",
                details={"file": str(self.index_file)}
            )
    
    def _get_file_path(self, kb_id: str) -> Path:
        """获取知识库配置文件路径"""
        # 从索引中查找文件路径
        index_data = self._load_index()
        for item in index_data:
            item_id = item.get("id")
            if item_id and item_id == kb_id:
                # 使用索引中的 id 作为文件名
                return self.storage_dir / f"{kb_id}.json"
        # 如果索引中没有，尝试直接使用 kb_id
        return self.storage_dir / f"{kb_id}.json"
    
    def _load_kb_config(self, kb_id: str) -> Optional[Dict[str, Any]]:
        """加载知识库配置"""
        file_path = self._get_file_path(kb_id)
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            raise InternalServerException(
                message=f"读取知识库配置失败: {str(e)}",
                details={"file": str(file_path), "kb_id": kb_id}
            )
    
    def _save_kb_config(self, config: Dict[str, Any]) -> None:
        """保存知识库配置"""
        kb_id = config.get("id") or config.get("data", {}).get("id")
        if not kb_id:
            raise ValueError("知识库配置缺少ID")
        
        file_path = self.storage_dir / f"{kb_id}.json"
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            raise InternalServerException(
                message=f"保存知识库配置失败: {str(e)}",
                details={"file": str(file_path), "kb_id": kb_id}
            )
    
    async def create(self, kb: KnowledgeBase, schema_fields: Optional[List[Dict[str, Any]]] = None) -> KnowledgeBase:
        """创建知识库配置"""
        index_data = self._load_index()
        
        # 检查ID是否已存在
        if any(item.get("id") == kb.id for item in index_data):
            raise ConflictException(
                message=f"知识库ID已存在: {kb.id}",
                details={"id": kb.id}
            )
        
        # 如果没有提供schema_fields，使用默认的包含稀疏向量字段的schema
        if schema_fields is None:
            schema_fields = [
                {"name": "content", "type": "text", "isIndexed": True, "isVectorIndex": False},
                {
                    "name": "embedding", 
                    "type": "dense_vector", 
                    "isIndexed": True, 
                    "isVectorIndex": True,
                    "dimension": 1024,
                    "distance": "Cosine",
                    "hnsw": {
                        "m": 16,
                        "ef_construct": 100,
                        "full_scan_threshold": 10000,
                        "on_disk": False
                    }
                },
                {"name": "sparse_vector", "type": "sparse_vector", "isIndexed": True, "isSparseVectorIndex": True}
            ]
        
        # 构建配置对象（使用 debug_results 格式）
        config = {
            "id": kb.id,
            "name": kb.name,
            "type": "knowledge_bases",
            "data": {
                **kb.model_dump(),
                "schema": {
                    "vector_db_type": kb.vector_db_type,
                    "fields": schema_fields
                }
            },
            "timestamp": int(datetime.now().timestamp() * 1000),
            "metadata": {
                "kb_id": kb.id,
                "kb_name": kb.name,
                "vector_db_type": kb.vector_db_type,
                "field_count": len(schema_fields)
            }
        }
        
        # 保存配置
        self._save_kb_config(config)
        
        # 更新索引
        index_data.append({
            "id": kb.id,
            "name": kb.name,
            "timestamp": config["timestamp"],
            "metadata": config["metadata"]
        })
        index_data.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
        self._save_index(index_data)
        
        return kb
    
    async def get_by_id(self, kb_id: str) -> Optional[KnowledgeBase]:
        """根据ID获取知识库"""
        config = self._load_kb_config(kb_id)
        if not config:
            return None
        
        # 从 data 中提取知识库信息
        kb_data = config.get("data", {})
        # 移除 schema 字段，因为它是额外的配置
        kb_dict = {k: v for k, v in kb_data.items() if k != "schema"}
        
        return KnowledgeBase(**kb_dict)
    
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[KnowledgeBase]:
        """获取所有知识库"""
        index_data = self._load_index()
        
        # 应用过滤器
        if filters:
            filtered_items = []
            for item in index_data:
                match = True
                item_id = item.get("id")
                if not item_id:
                    continue
                for key, value in filters.items():
                    if key == "is_active":
                        # 需要加载完整配置来检查 is_active
                        config = self._load_kb_config(item_id)
                        if config:
                            kb_data = config.get("data", {})
                            if kb_data.get("is_active") != value:
                                match = False
                                break
                    elif item.get("metadata", {}).get(key) != value:
                        match = False
                        break
                if match:
                    filtered_items.append(item)
            index_data = filtered_items
        
        # 应用分页
        paginated_items = index_data[skip:skip + limit]
        
        # 加载知识库对象
        kbs = []
        for item in paginated_items:
            item_id = item.get("id")
            if not item_id:
                continue
            kb = await self.get_by_id(item_id)
            if kb:
                kbs.append(kb)
        
        return kbs
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """统计知识库数量"""
        index_data = self._load_index()
        
        if filters:
            count = 0
            for item in index_data:
                match = True
                item_id = item.get("id")
                if not item_id:
                    continue
                for key, value in filters.items():
                    if key == "is_active":
                        config = self._load_kb_config(item_id)
                        if config:
                            kb_data = config.get("data", {})
                            if kb_data.get("is_active") != value:
                                match = False
                                break
                    elif item.get("metadata", {}).get(key) != value:
                        match = False
                        break
                if match:
                    count += 1
            return count
        
        return len(index_data)
    
    async def update(self, kb_id: str, kb: KnowledgeBase, schema_fields: Optional[List[Dict[str, Any]]] = None) -> Optional[KnowledgeBase]:
        """更新知识库配置"""
        config = self._load_kb_config(kb_id)
        if not config:
            return None
        
        # 更新知识库数据
        kb_dict = kb.model_dump()
        if schema_fields is not None:
            kb_dict["schema"] = {
                "vector_db_type": kb.vector_db_type,
                "fields": schema_fields
            }
        
        config["data"] = kb_dict
        config["timestamp"] = int(datetime.now().timestamp() * 1000)
        config["name"] = kb.name
        config["metadata"] = {
            "kb_id": kb.id,
            "kb_name": kb.name,
            "vector_db_type": kb.vector_db_type,
            "field_count": len(schema_fields) if schema_fields else config.get("data", {}).get("schema", {}).get("fields", [])
        }
        
        # 保存更新
        self._save_kb_config(config)
        
        # 更新索引
        index_data = self._load_index()
        for i, item in enumerate(index_data):
            if item.get("id") == kb_id:
                index_data[i] = {
                    "id": kb_id,
                    "name": kb.name,
                    "timestamp": config["timestamp"],
                    "metadata": config["metadata"]
                }
                break
        index_data.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
        self._save_index(index_data)
        
        return kb
    
    async def delete(self, kb_id: str) -> bool:
        """删除知识库配置"""
        config = self._load_kb_config(kb_id)
        if not config:
            return False
        
        # 删除文件
        file_path = self._get_file_path(kb_id)
        if file_path.exists():
            file_path.unlink()
        
        # 更新索引
        index_data = self._load_index()
        original_len = len(index_data)
        index_data = [item for item in index_data if item.get("id") != kb_id]
        
        if len(index_data) < original_len:
            self._save_index(index_data)
            return True
        
        return False
    
    async def get_schema(self, kb_id: str) -> Optional[Dict[str, Any]]:
        """获取知识库的 schema 配置"""
        config = self._load_kb_config(kb_id)
        if not config:
            return None
        
        return config.get("data", {}).get("schema")
    
    async def update_schema(self, kb_id: str, schema_fields: List[Dict[str, Any]], vector_db_type: Optional[str] = None, vector_db_config: Optional[Dict[str, Any]] = None) -> bool:
        """更新知识库的 schema 配置"""
        config = self._load_kb_config(kb_id)
        if not config:
            return False
        
        kb_data = config.get("data", {})
        if vector_db_type:
            kb_data["vector_db_type"] = vector_db_type
        
        # 更新向量数据库配置
        if vector_db_config is not None:
            kb_data["vector_db_config"] = vector_db_config
        
        kb_data["schema"] = {
            "vector_db_type": vector_db_type or kb_data.get("vector_db_type"),
            "fields": schema_fields
        }
        
        config["data"] = kb_data
        config["metadata"]["field_count"] = len(schema_fields)
        if vector_db_type:
            config["metadata"]["vector_db_type"] = vector_db_type
            kb_data["vector_db_type"] = vector_db_type
        
        self._save_kb_config(config)
        
        # 更新索引中的 metadata
        index_data = self._load_index()
        for i, item in enumerate(index_data):
            if item.get("id") == kb_id:
                index_data[i]["metadata"] = config["metadata"]
                break
        self._save_index(index_data)
        
        return True

