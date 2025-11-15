"""
数据模型和模型管理模块
"""

from app.models.base import BaseModelMixin
from app.models.knowledge_base import (
    KnowledgeBase,
    EmbeddingProvider,
    VectorDBType,
)
from app.models.document import (
    Document,
    DocumentChunk,
    DocumentStatus,
    DocumentType,
)
from app.models.test import (
    TestSet,
    TestCase,
    RetrievalTestResult,
    GenerationTestResult,
    TestType,
    TestStatus,
)

__all__ = [
    # 基础
    "BaseModelMixin",
    
    # 知识库
    "KnowledgeBase",
    "EmbeddingProvider",
    "VectorDBType",
    
    # 文档
    "Document",
    "DocumentChunk",
    "DocumentStatus",
    "DocumentType",
    
    # 测试
    "TestSet",
    "TestCase",
    "RetrievalTestResult",
    "GenerationTestResult",
    "TestType",
    "TestStatus",
]
