"""
知识库相关的请求和响应Schema
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

from app.models.knowledge_base import EmbeddingProvider, VectorDBType


class KnowledgeBaseCreate(BaseModel):
    """创建知识库请求"""
    
    name: str = Field(..., description="知识库名称", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="知识库描述", max_length=500)
    
    embedding_provider: EmbeddingProvider = Field(
        default=EmbeddingProvider.OLLAMA,
        description="嵌入模型提供商"
    )
    embedding_model: str = Field(..., description="嵌入模型名称")
    embedding_dimension: int = Field(default=768, description="向量维度")
    
    vector_db_type: VectorDBType = Field(..., description="向量数据库类型")
    vector_db_config: Dict[str, Any] = Field(default_factory=dict, description="向量数据库配置")
    
    chunk_size: int = Field(default=512, description="分块大小", ge=100, le=2000)
    chunk_overlap: int = Field(default=50, description="分块重叠", ge=0, le=500)
    
    retrieval_top_k: int = Field(default=5, description="检索返回数量", ge=1, le=50)
    retrieval_score_threshold: float = Field(
        default=0.7,
        description="检索分数阈值",
        ge=0.0,
        le=1.0
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "技术文档库",
                "description": "存储公司技术文档",
                "embedding_provider": "ollama",
                "embedding_model": "nomic-embed-text",
                "embedding_dimension": 768,
                "vector_db_type": "qdrant",
                "chunk_size": 512,
                "chunk_overlap": 50,
                "retrieval_top_k": 5,
                "retrieval_score_threshold": 0.7
            }
        }


class KnowledgeBaseUpdate(BaseModel):
    """更新知识库请求"""
    
    name: Optional[str] = Field(None, description="知识库名称", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="知识库描述", max_length=500)
    
    chunk_size: Optional[int] = Field(None, description="分块大小", ge=100, le=2000)
    chunk_overlap: Optional[int] = Field(None, description="分块重叠", ge=0, le=500)
    
    retrieval_top_k: Optional[int] = Field(None, description="检索返回数量", ge=1, le=50)
    retrieval_score_threshold: Optional[float] = Field(
        None,
        description="检索分数阈值",
        ge=0.0,
        le=1.0
    )
    
    is_active: Optional[bool] = Field(None, description="是否激活")


class KnowledgeBaseResponse(BaseModel):
    """知识库响应"""
    
    id: str
    name: str
    description: Optional[str]
    
    embedding_provider: EmbeddingProvider
    embedding_model: str
    embedding_dimension: int
    
    vector_db_type: VectorDBType
    vector_db_config: Dict[str, Any]
    
    chunk_size: int
    chunk_overlap: int
    
    retrieval_top_k: int
    retrieval_score_threshold: float
    
    document_count: int
    chunk_count: int
    
    is_active: bool
    
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


class UpdateSchemaRequest(BaseModel):
    """更新Schema请求"""
    schema_fields: List[dict] = Field(..., description="Schema字段列表")
    vector_db_type: Optional[str] = Field(None, description="向量数据库类型")
    vector_db_config: Optional[Dict[str, Any]] = Field(None, description="向量数据库配置")

