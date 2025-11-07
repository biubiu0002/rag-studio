"""
仓储工厂
根据配置创建相应的存储实现
"""

from typing import Type, TypeVar

from app.config import settings
from app.models.base import BaseModelMixin
from app.repositories.base import BaseRepository
from app.repositories.json_repository import JsonRepository
from app.repositories.mysql_repository import MySQLRepository

T = TypeVar("T", bound=BaseModelMixin)


class RepositoryFactory:
    """
    仓储工厂类
    根据配置的存储类型创建相应的仓储实例
    """
    
    @staticmethod
    def create(entity_type: Type[T], collection_name: str) -> BaseRepository[T]:
        """
        创建仓储实例
        
        Args:
            entity_type: 实体类型
            collection_name: 集合/表名称
        
        Returns:
            仓储实例
        
        Raises:
            ValueError: 不支持的存储类型
        """
        storage_type = settings.STORAGE_TYPE.lower()
        
        if storage_type == "json":
            return JsonRepository(entity_type, collection_name)
        elif storage_type == "mysql":
            return MySQLRepository(entity_type, collection_name)
        else:
            raise ValueError(
                f"不支持的存储类型: {storage_type}，"
                f"支持的类型: json, mysql"
            )
    
    @staticmethod
    def create_knowledge_base_repository():
        """创建知识库仓储"""
        from app.models.knowledge_base import KnowledgeBase
        return RepositoryFactory.create(KnowledgeBase, "knowledge_bases")
    
    @staticmethod
    def create_document_repository():
        """创建文档仓储"""
        from app.models.document import Document
        return RepositoryFactory.create(Document, "documents")
    
    @staticmethod
    def create_document_chunk_repository():
        """创建文档分块仓储"""
        from app.models.document import DocumentChunk
        return RepositoryFactory.create(DocumentChunk, "document_chunks")
    
    @staticmethod
    def create_test_set_repository():
        """创建测试集仓储"""
        from app.models.test import TestSet
        return RepositoryFactory.create(TestSet, "test_sets")
    
    @staticmethod
    def create_test_case_repository():
        """创建测试用例仓储"""
        from app.models.test import TestCase
        return RepositoryFactory.create(TestCase, "test_cases")
    
    @staticmethod
    def create_retrieval_test_result_repository():
        """创建检索测试结果仓储"""
        from app.models.test import RetrievalTestResult
        return RepositoryFactory.create(RetrievalTestResult, "retrieval_test_results")
    
    @staticmethod
    def create_generation_test_result_repository():
        """创建生成测试结果仓储"""
        from app.models.test import GenerationTestResult
        return RepositoryFactory.create(GenerationTestResult, "generation_test_results")
    
    @staticmethod
    def create_retriever_evaluation_repository():
        """创建检索器评估结果仓储"""
        from app.models.retriever_evaluation import RetrieverEvaluationResult
        return RepositoryFactory.create(RetrieverEvaluationResult, "retriever_evaluations")

