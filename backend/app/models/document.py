"""
文档相关数据模型
"""

from typing import Optional, List, Dict, Any
from enum import Enum
from dataclasses import dataclass, field
from pydantic import Field

from app.models.base import BaseModelMixin


class DocumentStatus(str, Enum):
    """文档处理状态"""
    UPLOADING = "uploading"        # 上传中
    UPLOADED = "uploaded"          # 已上传
    PROCESSING = "processing"      # 处理中
    CHUNKING = "chunking"          # 分块中
    EMBEDDING = "embedding"        # 嵌入中
    INDEXING = "indexing"          # 索引中
    COMPLETED = "completed"        # 已完成
    FAILED = "failed"              # 失败


class DocumentType(str, Enum):
    """文档类型"""
    TXT = "txt"
    PDF = "pdf"
    DOCX = "docx"
    MD = "md"
    HTML = "html"
    JSON = "json"


class Document(BaseModelMixin):
    """文档模型"""
    
    kb_id: str = Field(..., description="所属知识库ID")
    
    # 文档基本信息
    name: str = Field(..., description="文档名称", min_length=1, max_length=200)
    external_id: Optional[str] = Field(None, description="外部数据源ID（如T2Ranking的doc_id）")
    file_path: str = Field(..., description="文件存储路径")
    file_size: int = Field(default=0, description="文件大小(字节)")
    file_type: DocumentType = Field(..., description="文件类型")
    
    # 文档内容
    content: Optional[str] = Field(None, description="文档原始内容")
    
    # 处理状态
    status: DocumentStatus = Field(
        default=DocumentStatus.UPLOADED,
        description="处理状态"
    )
    error_message: Optional[str] = Field(None, description="错误信息")
    
    # 处理结果
    chunk_count: int = Field(default=0, description="分块数量")
    
    # 元数据
    metadata: Dict[str, Any] = Field(default_factory=dict, description="文档元数据")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "doc_001",
                "kb_id": "kb_001",
                "name": "Python开发指南.pdf",
                "file_path": "/storage/documents/python_guide.pdf",
                "file_size": 1024000,
                "file_type": "pdf",
                "status": "completed",
                "chunk_count": 50
            }
        }


@dataclass
class Chunk:
    """文档分块（用于文档处理）"""
    index: int
    content: str
    start_pos: int
    end_pos: int
    char_count: int
    token_count: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "content": self.content,
            "start_pos": self.start_pos,
            "end_pos": self.end_pos,
            "char_count": self.char_count,
            "token_count": self.token_count,
            "metadata": self.metadata if self.metadata is not None else {}
        }


class DocumentChunk(BaseModelMixin):
    """文档分块模型"""
    
    document_id: str = Field(..., description="所属文档ID")
    kb_id: str = Field(..., description="所属知识库ID")
    
    # 分块内容
    content: str = Field(..., description="分块内容")
    chunk_index: int = Field(..., description="分块序号", ge=0)
    
    # 分块元数据
    start_pos: Optional[int] = Field(None, description="起始位置")
    end_pos: Optional[int] = Field(None, description="结束位置")
    token_count: Optional[int] = Field(None, description="Token数量")
    
    # 向量信息
    embedding: Optional[List[float]] = Field(None, description="向量嵌入")
    embedding_model: Optional[str] = Field(None, description="嵌入模型")
    
    # 索引信息
    vector_id: Optional[str] = Field(None, description="向量数据库中的ID")
    is_indexed: bool = Field(default=False, description="是否已索引")
    
    # 元数据
    metadata: Dict[str, Any] = Field(default_factory=dict, description="分块元数据")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "chunk_001",
                "document_id": "doc_001",
                "kb_id": "kb_001",
                "content": "Python是一种高级编程语言...",
                "chunk_index": 0,
                "token_count": 128,
                "is_indexed": True
            }
        }

