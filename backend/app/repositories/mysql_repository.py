"""
MySQL ORM 存储实现
用于生产环境的数据持久化
"""

import asyncio
from typing import Type, Optional, List, Dict, Any, Generic
from sqlalchemy import select, update, delete, and_
from sqlalchemy.orm import Session

from app.repositories.base import BaseRepository, T
from app.database import get_db, SessionLocal
from app.core.exceptions import NotFoundException, ConflictException, InternalServerException
import logging

logger = logging.getLogger(__name__)


class MySQLRepository(BaseRepository[T], Generic[T]):
    """
    MySQL存储仓储实现
    使用 SQLAlchemy ORM
    """
    
    # ORM模型映射表（需要在子类或工厂中配置）
    _orm_model_map: Dict[str, Type] = {}
    
    def __init__(self, entity_type: Type[T], table_name: str):
        """
        初始化MySQL仓储
        
        Args:
            entity_type: 实体类型（Pydantic模型）
            table_name: 数据表名称
        """
        self.entity_type = entity_type
        self.table_name = table_name
        self.orm_model = self._get_orm_model()
    
    def _get_orm_model(self):
        """获取对应的ORM模型"""
        # 动态导入ORM模型
        from app.database.models import (
            TestSetORM, TestCaseORM, EvaluationTaskORM,
            EvaluationCaseResultORM, EvaluationSummaryORM,
            RetrieverTestCaseORM, GenerationTestCaseORM,
            RetrieverEvaluationResultORM, GenerationEvaluationResultORM,
            TaskQueueORM, TestSetKnowledgeBaseORM, ImportTaskORM,
            KnowledgeBaseORM, DocumentORM, DocumentChunkORM
        )
        
        model_map = {
            "test_sets": TestSetORM,
            "test_cases": TestCaseORM,
            "evaluation_tasks": EvaluationTaskORM,
            "evaluation_case_results": EvaluationCaseResultORM,
            "evaluation_summaries": EvaluationSummaryORM,
            "retriever_test_cases": RetrieverTestCaseORM,
            "generation_test_cases": GenerationTestCaseORM,
            "retriever_evaluation_results": RetrieverEvaluationResultORM,
            "generation_evaluation_results": GenerationEvaluationResultORM,
            "task_queue": TaskQueueORM,
            "test_set_knowledge_bases": TestSetKnowledgeBaseORM,
            "import_tasks": ImportTaskORM,
            "knowledge_bases": KnowledgeBaseORM,
            "documents": DocumentORM,
            "document_chunks": DocumentChunkORM,
        }
        
        if self.table_name not in model_map:
            raise ValueError(f"未找到表 {self.table_name} 对应的ORM模型")    
        return model_map[self.table_name]
    
    def _pydantic_to_orm(self, entity: T) -> Any:
        """将Pydantic模型转换为ORM模型"""
        entity_dict = entity.model_dump(exclude={'created_at', 'updated_at'})
        
        # 处理 metadata -> meta_data 映射（如果 ORM 模型使用 meta_data）
        if 'metadata' in entity_dict and hasattr(self.orm_model, 'meta_data'):
            entity_dict['meta_data'] = entity_dict.pop('metadata')
        
        # 处理datetime字符串转换为datetime对象
        from datetime import datetime
        if 'created_at' in entity.model_dump() and entity.created_at:
            if isinstance(entity.created_at, str):
                entity_dict['created_at'] = datetime.fromisoformat(entity.created_at.replace('Z', '+00:00'))
            else:
                entity_dict['created_at'] = entity.created_at
        if 'updated_at' in entity.model_dump() and entity.updated_at:
            if isinstance(entity.updated_at, str):
                entity_dict['updated_at'] = datetime.fromisoformat(entity.updated_at.replace('Z', '+00:00'))
            else:
                entity_dict['updated_at'] = entity.updated_at
        return self.orm_model(**entity_dict)
    
    def _orm_to_pydantic(self, orm_obj: Any) -> T:
        """将ORM模型转换为Pydantic模型"""
        if orm_obj is None:
            return None
        
        # 获取Pydantic模型的字段集合（排除schema_config等内部字段）
        pydantic_fields = set(self.entity_type.model_fields.keys())
        
        # 将ORM对象转换为字典
        result_dict = {}
        for column in self.orm_model.__table__.columns:
            # 获取数据库列名
            db_column_name = column.name
            
            # 跳过不在Pydantic模型中的字段（如schema_config）
            if db_column_name not in pydantic_fields and db_column_name != 'metadata':
                continue
            
            # 检查是否有对应的 Python 属性（可能不同名）
            # 如果列名是 metadata，但属性名是 meta_data
            if db_column_name == 'metadata' and hasattr(orm_obj, 'meta_data'):
                value = getattr(orm_obj, 'meta_data', None)
                pydantic_key = 'metadata'  # Pydantic 模型使用 metadata
            else:
                # 使用列名作为属性名
                value = getattr(orm_obj, db_column_name, None)
                pydantic_key = db_column_name
            
            # 处理datetime
            if hasattr(value, 'isoformat'):
                value = value.isoformat()
            # 处理None值
            elif value is None:
                value = None
            
            result_dict[pydantic_key] = value
        
        return self.entity_type(**result_dict)
    
    def _build_filters(self, filters: Optional[Dict[str, Any]], query):
        """构建过滤条件"""
        if not filters:
            return query
        
        conditions = []
        for key, value in filters.items():
            if hasattr(self.orm_model, key):
                conditions.append(getattr(self.orm_model, key) == value)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        return query
    
    async def create(self, entity: T) -> T:
        """创建实体"""
        def _create_sync():
            db = SessionLocal()
            try:
                # 检查ID是否已存在
                existing = db.query(self.orm_model).filter(
                    self.orm_model.id == entity.id
                ).first()
                if existing:
                    raise ConflictException(
                        message=f"实体ID已存在: {entity.id}",
                        details={"id": entity.id}
                    )
                
                # 创建ORM对象
                orm_obj = self._pydantic_to_orm(entity)
                db.add(orm_obj)
                db.commit()
                db.refresh(orm_obj)
                return self._orm_to_pydantic(orm_obj)
            except ConflictException:
                raise
            except Exception as e:
                db.rollback()
                logger.error(f"创建实体失败: {e}", exc_info=True)
                raise InternalServerException(
                    message=f"创建实体失败: {str(e)}",
                    details={"entity_id": entity.id}
                )
            finally:
                db.close()
        
        return await asyncio.to_thread(_create_sync)
    
    async def get_by_id(self, entity_id: str) -> Optional[T]:
        """根据ID获取实体"""
        def _get_sync():
            db = SessionLocal()
            try:
                orm_obj = db.query(self.orm_model).filter(
                    self.orm_model.id == entity_id
                ).first()
                return self._orm_to_pydantic(orm_obj) if orm_obj else None
            except Exception as e:
                logger.error(f"获取实体失败: {e}", exc_info=True)
                raise InternalServerException(
                    message=f"获取实体失败: {str(e)}",
                    details={"entity_id": entity_id}
                )
            finally:
                db.close()
        
        return await asyncio.to_thread(_get_sync)
    
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None
    ) -> List[T]:
        """获取所有实体（支持分页和过滤）"""
        def _get_all_sync():
            db = SessionLocal()
            try:
                query = db.query(self.orm_model)
                
                # 应用过滤条件
                if filters:
                    conditions = []
                    for key, value in filters.items():
                        if hasattr(self.orm_model, key):
                            conditions.append(getattr(self.orm_model, key) == value)
                    if conditions:
                        query = query.filter(and_(*conditions))
                
                # 应用排序
                if order_by:
                    if order_by.startswith('-'):
                        # 倒序
                        field_name = order_by[1:]
                        if hasattr(self.orm_model, field_name):
                            query = query.order_by(getattr(self.orm_model, field_name).desc())
                    else:
                        # 正序
                        if hasattr(self.orm_model, order_by):
                            query = query.order_by(getattr(self.orm_model, order_by))
                else:
                    # 默认按创建时间倒序
                    if hasattr(self.orm_model, 'created_at'):
                        query = query.order_by(self.orm_model.created_at.desc())
                
                # 分页
                orm_objs = query.offset(skip).limit(limit).all()
                return [self._orm_to_pydantic(obj) for obj in orm_objs]
            except Exception as e:
                logger.error(f"获取实体列表失败: {e}", exc_info=True)
                raise InternalServerException(
                    message=f"获取实体列表失败: {str(e)}"
                )
            finally:
                db.close()
        
        return await asyncio.to_thread(_get_all_sync)
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """统计实体数量"""
        def _count_sync():
            db = SessionLocal()
            try:
                query = db.query(self.orm_model)
                
                # 应用过滤条件
                if filters:
                    conditions = []
                    for key, value in filters.items():
                        if hasattr(self.orm_model, key):
                            conditions.append(getattr(self.orm_model, key) == value)
                    if conditions:
                        query = query.filter(and_(*conditions))
                
                return query.count()
            except Exception as e:
                logger.error(f"统计实体数量失败: {e}", exc_info=True)
                raise InternalServerException(
                    message=f"统计实体数量失败: {str(e)}"
                )
            finally:
                db.close()
        
        return await asyncio.to_thread(_count_sync)
    
    async def update(self, entity_id: str, entity: T) -> Optional[T]:
        """更新实体"""
        def _update_sync():
            db = SessionLocal()
            try:
                orm_obj = db.query(self.orm_model).filter(
                    self.orm_model.id == entity_id
                ).first()
                
                if not orm_obj:
                    return None
                
                # 更新字段
                entity_dict = entity.model_dump(exclude={'id', 'created_at', 'updated_at'})
                for key, value in entity_dict.items():
                    if hasattr(orm_obj, key):
                        setattr(orm_obj, key, value)
                
                db.commit()
                db.refresh(orm_obj)
                return self._orm_to_pydantic(orm_obj)
            except Exception as e:
                db.rollback()
                logger.error(f"更新实体失败: {e}", exc_info=True)
                raise InternalServerException(
                    message=f"更新实体失败: {str(e)}",
                    details={"entity_id": entity_id}
                )
            finally:
                db.close()
        
        return await asyncio.to_thread(_update_sync)
    
    async def delete(self, entity_id: str) -> bool:
        """删除实体"""
        def _delete_sync():
            db = SessionLocal()
            try:
                orm_obj = db.query(self.orm_model).filter(
                    self.orm_model.id == entity_id
                ).first()
                
                if not orm_obj:
                    return False
                
                db.delete(orm_obj)
                db.commit()
                return True
            except Exception as e:
                db.rollback()
                logger.error(f"删除实体失败: {e}", exc_info=True)
                raise InternalServerException(
                    message=f"删除实体失败: {str(e)}",
                    details={"entity_id": entity_id}
                )
            finally:
                db.close()
        
        return await asyncio.to_thread(_delete_sync)
    
    async def exists(self, entity_id: str) -> bool:
        """检查实体是否存在"""
        def _exists_sync():
            db = SessionLocal()
            try:
                count = db.query(self.orm_model).filter(
                    self.orm_model.id == entity_id
                ).count()
                return count > 0
            except Exception as e:
                logger.error(f"检查实体存在性失败: {e}", exc_info=True)
                raise InternalServerException(
                    message=f"检查实体存在性失败: {str(e)}",
                    details={"entity_id": entity_id}
                )
            finally:
                db.close()
        
        return await asyncio.to_thread(_exists_sync)

