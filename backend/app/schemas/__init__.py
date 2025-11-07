"""
Pydantic Schemas模块
用于API请求和响应的数据验证
"""

from app.schemas.common import PaginationParams, IDResponse, MessageResponse
from app.schemas.knowledge_base import (
    KnowledgeBaseCreate,
    KnowledgeBaseUpdate,
    KnowledgeBaseResponse,
)
from app.schemas.document import (
    DocumentUploadResponse,
    DocumentResponse,
    DocumentChunkResponse,
    DocumentProcessRequest,
)
from app.schemas.test import (
    TestSetCreate,
    TestSetUpdate,
    TestSetResponse,
    TestCaseCreate,
    TestCaseUpdate,
    TestCaseResponse,
    RunRetrievalTestRequest,
    RetrievalTestResultResponse,
    RunGenerationTestRequest,
    GenerationTestResultResponse,
)

__all__ = [
    # 通用
    "PaginationParams",
    "IDResponse",
    "MessageResponse",
    
    # 知识库
    "KnowledgeBaseCreate",
    "KnowledgeBaseUpdate",
    "KnowledgeBaseResponse",
    
    # 文档
    "DocumentUploadResponse",
    "DocumentResponse",
    "DocumentChunkResponse",
    "DocumentProcessRequest",
    
    # 测试
    "TestSetCreate",
    "TestSetUpdate",
    "TestSetResponse",
    "TestCaseCreate",
    "TestCaseUpdate",
    "TestCaseResponse",
    "RunRetrievalTestRequest",
    "RetrievalTestResultResponse",
    "RunGenerationTestRequest",
    "GenerationTestResultResponse",
]
