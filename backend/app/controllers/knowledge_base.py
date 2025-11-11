"""
知识库管理控制器
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.schemas.knowledge_base import (
    KnowledgeBaseCreate,
    KnowledgeBaseUpdate,
    KnowledgeBaseResponse,
)
from app.schemas.common import PaginationParams, IDResponse, MessageResponse
from app.core.response import success_response, page_response
from app.core.exceptions import NotFoundException, BadRequestException

router = APIRouter(prefix="/knowledge-bases", tags=["知识库管理"])


@router.post("", response_model=None, summary="创建知识库")
async def create_knowledge_base(data: KnowledgeBaseCreate):
    """
    创建新的知识库
    
    - **name**: 知识库名称（必填）
    - **description**: 知识库描述
    - **embedding_model**: 嵌入模型名称
    - **vector_db_type**: 向量数据库类型
    - **chunk_size**: 文档分块大小
    - **retrieval_top_k**: 检索返回的文档数量
    """
    from app.services.knowledge_base import KnowledgeBaseService
    
    service = KnowledgeBaseService()
    kb = await service.create_knowledge_base(data)
    
    return JSONResponse(
        content=success_response(
            data=kb.model_dump(),
            message="知识库创建成功"
        )
    )


@router.get("", response_model=None, summary="获取知识库列表")
async def list_knowledge_bases(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    is_active: bool = Query(None, description="是否激活"),
):
    """
    获取知识库列表（支持分页）
    
    - **page**: 页码
    - **page_size**: 每页大小
    - **is_active**: 筛选激活状态
    """
    from app.services.knowledge_base import KnowledgeBaseService
    
    service = KnowledgeBaseService()
    kbs, total = await service.list_knowledge_bases(page, page_size, is_active)
    
    # 转换为响应格式
    data = [kb.model_dump() for kb in kbs]
    
    return JSONResponse(
        content=page_response(
            data=data,
            total=total,
            page=page,
            page_size=page_size,
        )
    )


@router.get("/{kb_id}", response_model=None, summary="获取知识库详情")
async def get_knowledge_base(kb_id: str):
    """
    根据ID获取知识库详情
    
    - **kb_id**: 知识库ID
    """
    from app.services.knowledge_base import KnowledgeBaseService
    
    service = KnowledgeBaseService()
    kb = await service.get_knowledge_base(kb_id)
    
    if not kb:
        raise NotFoundException(message=f"知识库不存在: {kb_id}")
    
    return JSONResponse(
        content=success_response(
            data=kb.model_dump()
        )
    )


@router.put("/{kb_id}", response_model=None, summary="更新知识库")
async def update_knowledge_base(kb_id: str, data: KnowledgeBaseUpdate):
    """
    更新知识库配置
    
    - **kb_id**: 知识库ID
    - **data**: 更新的字段
    """
    from app.services.knowledge_base import KnowledgeBaseService
    
    service = KnowledgeBaseService()
    kb = await service.update_knowledge_base(kb_id, data)
    
    if not kb:
        raise NotFoundException(message=f"知识库不存在: {kb_id}")
    
    return JSONResponse(
        content=success_response(
            data=kb.model_dump(),
            message="知识库更新成功"
        )
    )


@router.delete("/{kb_id}", response_model=None, summary="删除知识库")
async def delete_knowledge_base(kb_id: str):
    """
    删除知识库
    
    - **kb_id**: 知识库ID
    
    注意：删除知识库会同时删除其下的所有文档和索引
    """
    from app.services.knowledge_base import KnowledgeBaseService
    
    service = KnowledgeBaseService()
    success = await service.delete_knowledge_base(kb_id)
    
    if not success:
        raise NotFoundException(message=f"知识库不存在: {kb_id}")
    
    return JSONResponse(
        content=success_response(
            message="知识库删除成功"
        )
    )


@router.get("/{kb_id}/config", response_model=None, summary="获取知识库配置")
async def get_knowledge_base_config(kb_id: str):
    """
    获取知识库的详细配置信息（用于链路排查）
    
    - **kb_id**: 知识库ID
    """
    from app.services.knowledge_base import KnowledgeBaseService
    
    service = KnowledgeBaseService()
    kb = await service.get_knowledge_base(kb_id)
    
    if not kb:
        raise NotFoundException(message=f"知识库不存在: {kb_id}")
    
    # 返回详细配置信息
    config = {
        "basic_info": {
            "id": kb.id,
            "name": kb.name,
            "description": kb.description,
            "is_active": kb.is_active,
        },
        "embedding_config": {
            "provider": kb.embedding_provider,
            "model": kb.embedding_model,
            "dimension": kb.embedding_dimension,
        },
        "vector_db_config": {
            "type": kb.vector_db_type,
            "config": kb.vector_db_config,
        },
        "chunk_config": {
            "chunk_size": kb.chunk_size,
            "chunk_overlap": kb.chunk_overlap,
        },
        "retrieval_config": {
            "top_k": kb.retrieval_top_k,
            "score_threshold": kb.retrieval_score_threshold,
        },
        "statistics": {
            "document_count": kb.document_count,
            "chunk_count": kb.chunk_count,
        },
    }
    
    return JSONResponse(
        content=success_response(data=config)
    )


@router.get("/{kb_id}/stats", response_model=None, summary="获取知识库统计信息")
async def get_knowledge_base_stats(kb_id: str):
    """
    获取知识库的统计信息
    
    - **kb_id**: 知识库ID
    
    返回：
    - 文档数量
    - 分块数量
    - 索引状态
    - 存储大小等
    """
    from app.services.knowledge_base import KnowledgeBaseService
    
    service = KnowledgeBaseService()
    stats = await service.get_knowledge_base_stats(kb_id)
    
    return JSONResponse(
        content=success_response(data=stats)
    )


@router.get("/{kb_id}/schema", response_model=None, summary="获取知识库Schema配置")
async def get_knowledge_base_schema(kb_id: str):
    """
    获取知识库的Schema配置
    
    - **kb_id**: 知识库ID
    
    返回：
    - Schema配置（包含字段列表和向量数据库类型）
    """
    from app.services.knowledge_base import KnowledgeBaseService
    
    service = KnowledgeBaseService()
    schema = await service.get_knowledge_base_schema(kb_id)
    
    if schema is None:
        raise NotFoundException(message=f"知识库Schema不存在: {kb_id}")
    
    return JSONResponse(
        content=success_response(data=schema)
    )


class UpdateSchemaRequest(BaseModel):
    """更新Schema请求"""
    schema_fields: List[dict] = Field(..., description="Schema字段列表")
    vector_db_type: Optional[str] = Field(None, description="向量数据库类型")
    vector_db_config: Optional[Dict[str, Any]] = Field(None, description="向量数据库配置")


@router.put("/{kb_id}/schema", response_model=None, summary="更新知识库Schema配置")
async def update_knowledge_base_schema(
    kb_id: str,
    request: UpdateSchemaRequest
):
    """
    更新知识库的Schema配置
    
    - **kb_id**: 知识库ID
    - **schema_fields**: Schema字段列表
    - **vector_db_type**: 向量数据库类型（可选）
    """
    from app.services.knowledge_base import KnowledgeBaseService
    
    service = KnowledgeBaseService()
    success = await service.update_knowledge_base_schema(
        kb_id,
        request.schema_fields,
        request.vector_db_type,
        request.vector_db_config
    )
    
    if not success:
        raise NotFoundException(message=f"知识库不存在: {kb_id}")
    
    return JSONResponse(
        content=success_response(
            message="Schema配置更新成功"
        )
    )

