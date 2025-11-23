"""
知识库相关数据模型
"""

from typing import Optional, Dict, Any
from enum import Enum
from pydantic import Field

from app.models.base import BaseModelMixin


class EmbeddingProvider(str, Enum):
    """嵌入模型提供商"""
    OLLAMA = "ollama"
    CUSTOM = "custom"


class ChatProvider(str, Enum):
    """Chat模型提供商"""
    OLLAMA = "ollama"
    CUSTOM = "custom"


class VectorDBType(str, Enum):
    """向量数据库类型"""
    ELASTICSEARCH = "elasticsearch"
    QDRANT = "qdrant"
    MILVUS = "milvus"


class KnowledgeBase(BaseModelMixin):
    """知识库模型"""
    
    name: str = Field(..., description="知识库名称", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="知识库描述", max_length=500)
    
    # 嵌入配置
    embedding_provider: EmbeddingProvider = Field(
        default=EmbeddingProvider.OLLAMA,
        description="嵌入模型提供商"
    )
    embedding_model: str = Field(..., description="嵌入模型名称")
    embedding_dimension: int = Field(default=768, description="向量维度")
    embedding_endpoint: Optional[str] = Field(None, description="嵌入模型服务地址")
    
    # Chat模型配置
    chat_provider: ChatProvider = Field(
        default=ChatProvider.OLLAMA,
        description="Chat模型提供商"
    )
    chat_model: Optional[str] = Field(None, description="Chat模型名称")
    chat_endpoint: Optional[str] = Field(None, description="Chat模型服务地址")
    
    # 向量数据库配置
    vector_db_type: VectorDBType = Field(..., description="向量数据库类型")
    vector_db_config: Dict[str, Any] = Field(default_factory=dict, description="向量数据库配置")
    
    # 分块配置
    chunk_size: int = Field(default=512, description="分块大小", ge=100, le=2000)
    chunk_overlap: int = Field(default=50, description="分块重叠", ge=0, le=500)
    
    # 检索配置
    retrieval_top_k: int = Field(default=5, description="检索返回数量", ge=1, le=50)
    retrieval_score_threshold: float = Field(
        default=0.7,
        description="检索分数阈值",
        ge=0.0,
        le=1.0
    )
    
    # 统计信息
    document_count: int = Field(default=0, description="文档数量")
    chunk_count: int = Field(default=0, description="分块数量")
    
    # 状态
    is_active: bool = Field(default=True, description="是否激活")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "kb_001",
                "name": "技术文档库",
                "description": "存储公司技术文档",
                "embedding_provider": "ollama",
                "embedding_model": "nomic-embed-text",
                "embedding_dimension": 768,
                "vector_db_type": "qdrant",
                "chunk_size": 512,
                "chunk_overlap": 50,
                "retrieval_top_k": 5,
                "is_active": True
            }
        }

