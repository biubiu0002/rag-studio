"""
Pydantic Schemas模块
用于API请求和响应的数据验证
"""

from app.schemas.common import PaginationParams, IDResponse, MessageResponse
from app.schemas.knowledge_base import (
    KnowledgeBaseCreate,
    KnowledgeBaseUpdate,
    KnowledgeBaseResponse,
    UpdateSchemaRequest,
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
)
from app.schemas.evaluation import (
    CreateEvaluationTaskRequest,
    ExecuteEvaluationTaskRequest,
)
from app.schemas.debug_pipeline import (
    ChunkRequest,
    TokenizeRequest,
    EmbedRequest,
    UnifiedSearchRequest,
    HybridSearchRequest,
    QdrantHybridSearchRequest,
    SparseVectorRequest,
    WriteVectorIndexRequest,
    WriteKeywordIndexRequest,
    WriteSparseVectorIndexRequest,
    WriteHybridIndexRequest,
    SaveDebugResultRequest,
    GenerationRequest,
    GenerationResponse,
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
    "UpdateSchemaRequest",
    
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
    
    # 评估
    "CreateEvaluationTaskRequest",
    "ExecuteEvaluationTaskRequest",
    
    # 链路调试
    "ChunkRequest",
    "TokenizeRequest",
    "EmbedRequest",
    "UnifiedSearchRequest",
    "HybridSearchRequest",
    "QdrantHybridSearchRequest",
    "SparseVectorRequest",
    "WriteVectorIndexRequest",
    "WriteKeywordIndexRequest",
    "WriteSparseVectorIndexRequest",
    "WriteHybridIndexRequest",
    "SaveDebugResultRequest",
    "GenerationRequest",
    "GenerationResponse",
]
