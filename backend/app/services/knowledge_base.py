"""
知识库业务逻辑服务
"""

from typing import Optional, List, Tuple, Dict, Any
from datetime import datetime
import uuid
import json
import asyncio
from pathlib import Path

from app.models.knowledge_base import KnowledgeBase
from app.schemas.knowledge_base import KnowledgeBaseCreate, KnowledgeBaseUpdate
from app.repositories.factory import RepositoryFactory
from app.config import settings
from app.core.exceptions import NotFoundException, ConflictException
from app.core.singleton import singleton


@singleton
class KnowledgeBaseService:
    """知识库服务 - 根据STORAGE_TYPE选择存储方式"""
    
    def __init__(self):
        self.repository = RepositoryFactory.create_knowledge_base_repository()
        self.storage_type = settings.STORAGE_TYPE.lower()
        
        # Schema存储路径（仅用于json模式）
        if self.storage_type == "json":
            self.schema_dir = Path(settings.STORAGE_PATH) / "knowledge_base_schemas"
            self.schema_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_schema_file_path(self, kb_id: str) -> Path:
        """获取schema文件路径（仅用于json模式）"""
        return self.schema_dir / f"{kb_id}.json"
    
    async def _save_schema(self, kb_id: str, schema: Dict[str, Any]) -> None:
        """保存schema配置"""
        if self.storage_type == "json":
            schema_file = self._get_schema_file_path(kb_id)
            with open(schema_file, "w", encoding="utf-8") as f:
                json.dump(schema, f, ensure_ascii=False, indent=2)
        elif self.storage_type == "mysql":
            # MySQL模式下，schema存储在数据库的schema_config字段中
            def _save_schema_sync():
                from app.database.models import KnowledgeBaseORM
                from app.database import SessionLocal
                db = SessionLocal()
                try:
                    orm_obj = db.query(KnowledgeBaseORM).filter(KnowledgeBaseORM.id == kb_id).first()
                    if orm_obj:
                        orm_obj.schema_config = schema
                        db.commit()
                except Exception as e:
                    db.rollback()
                    raise
                finally:
                    db.close()
            
            await asyncio.to_thread(_save_schema_sync)
    
    async def _load_schema(self, kb_id: str) -> Optional[Dict[str, Any]]:
        """加载schema配置"""
        if self.storage_type == "json":
            schema_file = self._get_schema_file_path(kb_id)
            if schema_file.exists():
                with open(schema_file, "r", encoding="utf-8") as f:
                    return json.load(f)
        elif self.storage_type == "mysql":
            # MySQL模式下，从数据库的schema_config字段加载
            def _load_schema_sync():
                from app.database.models import KnowledgeBaseORM
                from app.database import SessionLocal
                db = SessionLocal()
                try:
                    orm_obj = db.query(KnowledgeBaseORM).filter(KnowledgeBaseORM.id == kb_id).first()
                    if orm_obj and orm_obj.schema_config:
                        return orm_obj.schema_config
                    return None
                finally:
                    db.close()
            
            return await asyncio.to_thread(_load_schema_sync)
        return None
    
    def _get_default_schema_fields(self) -> List[Dict[str, Any]]:
        """获取默认的schema字段"""
        return [
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
    
    async def create_knowledge_base(self, data: KnowledgeBaseCreate, schema_fields: Optional[List[Dict[str, Any]]] = None) -> KnowledgeBase:
        """
        创建知识库
        
        Args:
            data: 创建知识库的数据
            schema_fields: Schema字段配置（可选）
        
        Returns:
            创建的知识库对象
        """
        # 生成唯一ID
        kb_id = f"kb_{uuid.uuid4().hex[:12]}"
        
        # 创建知识库对象
        kb = KnowledgeBase(
            id=kb_id,
            **data.model_dump()
        )
        
        # TODO: 初始化向量数据库集合/索引
        # await self._initialize_vector_db(kb)
        
        # 保存知识库基本信息到仓储
        await self.repository.create(kb)
        
        # 保存schema配置
        if schema_fields is None:
            schema_fields = self._get_default_schema_fields()
        
        schema = {
            "vector_db_type": kb.vector_db_type,
            "fields": schema_fields
        }
        await self._save_schema(kb_id, schema)
        
        return kb
    
    async def get_knowledge_base(self, kb_id: str) -> Optional[KnowledgeBase]:
        """
        获取知识库
        
        Args:
            kb_id: 知识库ID
        
        Returns:
            知识库对象，不存在返回None
        """
        return await self.repository.get_by_id(kb_id)
    
    async def list_knowledge_bases(
        self,
        page: int = 1,
        page_size: int = 20,
        is_active: Optional[bool] = None
    ) -> Tuple[List[KnowledgeBase], int]:
        """
        获取知识库列表
        
        Args:
            page: 页码
            page_size: 每页大小
            is_active: 是否激活状态筛选
        
        Returns:
            (知识库列表, 总数量)
        """
        filters = {}
        if is_active is not None:
            filters["is_active"] = is_active
        
        skip = (page - 1) * page_size
        kbs = await self.repository.get_all(skip=skip, limit=page_size, filters=filters)
        total = await self.repository.count(filters=filters)
        
        return kbs, total
    
    async def update_knowledge_base(
        self,
        kb_id: str,
        data: KnowledgeBaseUpdate,
        schema_fields: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[KnowledgeBase]:
        """
        更新知识库
        
        Args:
            kb_id: 知识库ID
            data: 更新的数据
            schema_fields: Schema字段配置（可选）
        
        Returns:
            更新后的知识库对象
        """
        kb = await self.repository.get_by_id(kb_id)
        if not kb:
            return None
        
        # 更新字段
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(kb, field, value)
        
        # 保存更新到仓储
        updated_kb = await self.repository.update(kb_id, kb)
        
        # 如果提供了schema_fields，更新schema配置
        if schema_fields is not None:
            schema = {
                "vector_db_type": kb.vector_db_type,
                "fields": schema_fields
            }
            await self._save_schema(kb_id, schema)
        
        return updated_kb
    
    async def delete_knowledge_base(self, kb_id: str) -> bool:
        """
        删除知识库
        
        Args:
            kb_id: 知识库ID
        
        Returns:
            是否删除成功
        """
        # TODO: 删除关联的文档和向量索引
        # await self._delete_documents(kb_id)
        # await self._delete_vector_index(kb_id)
        
        # 删除schema文件（json模式）
        if self.storage_type == "json":
            schema_file = self._get_schema_file_path(kb_id)
            if schema_file.exists():
                schema_file.unlink()
        
        return await self.repository.delete(kb_id)
    
    async def get_knowledge_base_stats(self, kb_id: str) -> dict:
        """
        获取知识库统计信息
        
        Args:
            kb_id: 知识库ID
        
        Returns:
            统计信息字典
        """
        kb = await self.repository.get_by_id(kb_id)
        if not kb:
            raise NotFoundException(message=f"知识库不存在: {kb_id}")
        
        # TODO: 从向量数据库获取实时统计
        # vector_stats = await self._get_vector_stats(kb_id)
        
        return {
            "kb_id": kb_id,
            "document_count": kb.document_count,
            "chunk_count": kb.chunk_count,
            "indexed_count": 0,  # TODO: 从向量数据库获取
            "storage_size": 0,   # TODO: 计算存储大小
        }
    
    async def get_knowledge_base_schema(self, kb_id: str) -> Optional[Dict[str, Any]]:
        """
        获取知识库的 schema 配置
        
        Args:
            kb_id: 知识库ID
        
        Returns:
            Schema配置，不存在返回None
        """
        # 检查知识库是否存在
        kb = await self.repository.get_by_id(kb_id)
        if not kb:
            return None
        
        return await self._load_schema(kb_id)
    
    async def update_knowledge_base_schema(
        self,
        kb_id: str,
        schema_fields: List[Dict[str, Any]],
        vector_db_type: Optional[str] = None,
        vector_db_config: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        更新知识库的 schema 配置
        
        Args:
            kb_id: 知识库ID
            schema_fields: Schema字段列表
            vector_db_type: 向量数据库类型（可选）
            vector_db_config: 向量数据库配置（可选）
        
        Returns:
            是否更新成功
        """
        # 检查知识库是否存在
        kb = await self.repository.get_by_id(kb_id)
        if not kb:
            return False
        
        # 如果提供了vector_db_type，更新知识库的vector_db_type
        if vector_db_type:
            kb.vector_db_type = vector_db_type
            await self.repository.update(kb_id, kb)
        
        # 如果提供了vector_db_config，更新知识库的vector_db_config
        if vector_db_config is not None:
            kb.vector_db_config = vector_db_config
            await self.repository.update(kb_id, kb)
        
        # 保存schema配置
        schema = {
            "vector_db_type": vector_db_type or kb.vector_db_type,
            "fields": schema_fields
        }
        await self._save_schema(kb_id, schema)
        
        return True
    
    # ========== 私有方法（待实现） ==========
    
    async def _initialize_vector_db(self, kb: KnowledgeBase):
        """
        初始化向量数据库集合/索引
        
        TODO: 实现
        1. 根据 vector_db_type 选择对应的向量数据库
        2. 创建集合/索引
        3. 配置向量维度和参数
        """
        pass
    
    async def _delete_documents(self, kb_id: str):
        """
        删除知识库的所有文档
        
        TODO: 实现
        """
        pass
    
    async def _delete_vector_index(self, kb_id: str):
        """
        删除向量索引
        
        TODO: 实现
        """
        pass
    
    async def _get_vector_stats(self, kb_id: str) -> dict:
        """
        从向量数据库获取统计信息
        
        TODO: 实现
        """
        return {}

