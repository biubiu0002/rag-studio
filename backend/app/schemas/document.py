"""
文档相关的请求和响应Schema
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from app.models.document import DocumentStatus, DocumentType


class DocumentUploadResponse(BaseModel):
    """文档上传响应"""
    
    id: str
    kb_id: str
    name: str
    file_path: str
    file_size: int
    file_type: DocumentType
    status: DocumentStatus
    created_at: str
    
    class Config:
        from_attributes = True


class DocumentResponse(BaseModel):
    """文档响应"""
    
    id: str
    kb_id: str
    name: str
    file_path: str
    file_size: int
    file_type: DocumentType
    status: DocumentStatus
    error_message: Optional[str]
    chunk_count: int
    metadata: Dict[str, Any]
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


class DocumentChunkResponse(BaseModel):
    """文档分块响应"""
    
    id: str
    document_id: str
    kb_id: str
    content: str
    chunk_index: int
    token_count: Optional[int]
    is_indexed: bool
    metadata: Dict[str, Any]
    created_at: str
    
    class Config:
        from_attributes = True


class DocumentProcessRequest(BaseModel):
    """文档处理请求"""
    
    document_id: str = Field(..., description="文档ID")
    force_reprocess: bool = Field(default=False, description="是否强制重新处理")

