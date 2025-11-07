"""
RAG链路调试控制器
提供可视化调试接口
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import logging
import tempfile
import os
import json
import uuid
from pathlib import Path
from datetime import datetime

from app.core.response import success_response
from app.services.document_processor import DocumentProcessor, DocumentParser, Chunk
from app.services.tokenizer_service import get_tokenizer_service
from app.services.retrieval_service import RetrievalService, RRFFusion
from app.services.embedding_service import EmbeddingServiceFactory
from app.models.knowledge_base import EmbeddingProvider
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/debug", tags=["链路调试"])


# ========== 请求/响应模型 ==========

class ChunkRequest(BaseModel):
    """分块请求"""
    text: str = Field(..., description="输入文本")
    method: str = Field("fixed_size", description="分块方法: fixed_size, paragraph, sentence")
    chunk_size: int = Field(500, description="分块大小（字符数）")
    chunk_overlap: int = Field(50, description="重叠大小（字符数）")
    max_sentences: int = Field(5, description="句子分块时每块的最大句子数")


class TokenizeRequest(BaseModel):
    """分词请求"""
    texts: List[str] = Field(..., description="文本列表")
    mode: str = Field("default", description="分词模式: default, search, all")
    use_stop_words: bool = Field(True, description="是否过滤停用词")


class EmbedRequest(BaseModel):
    """向量化请求"""
    texts: List[str] = Field(..., description="文本列表")
    model: str = Field("bge-m3:latest", description="Embedding模型")
    provider: str = Field("ollama", description="Embedding服务提供商")


class HybridSearchRequest(BaseModel):
    """混合检索请求"""
    kb_id: str = Field(..., description="知识库ID")
    query: str = Field(..., description="查询文本")
    top_k: int = Field(10, description="返回数量")
    vector_weight: float = Field(0.7, description="向量检索权重", ge=0, le=1)
    keyword_weight: float = Field(0.3, description="关键词检索权重", ge=0, le=1)
    rrf_k: int = Field(60, description="RRF参数k", ge=1)
    embedding_model: str = Field("bge-m3:latest", description="Embedding模型")
    tokenize_mode: str = Field("search", description="分词模式")


# ========== 步骤1: 文档处理 ==========

@router.post("/document/upload", summary="上传文档")
async def upload_document(file: UploadFile = File(..., description="上传的文件")):
    """
    上传文档并保存到临时目录
    
    Args:
        file: 上传的文件
    
    Returns:
        文件信息和临时路径
    """
    try:
        # 验证文件是否存在
        if not file:
            raise HTTPException(status_code=400, detail="未提供文件")
        
        # 验证文件名
        if not file.filename:
            raise HTTPException(status_code=400, detail="文件名不能为空")
        
        # 读取文件内容
        content = await file.read()
        
        # 验证文件内容不为空
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="文件内容不能为空")
        
        # 创建临时文件
        suffix = os.path.splitext(file.filename)[1] or ".txt"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        file_info = {
            "filename": file.filename,
            "size": len(content),
            "content_type": file.content_type,
            "temp_path": tmp_path
        }
        
        return JSONResponse(
            content=success_response(
                data=file_info,
                message="文件上传成功"
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文件上传失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.post("/document/parse", summary="解析文档")
async def parse_document(file_path: str):
    """
    解析文档内容
    
    Args:
        file_path: 文件路径（通常是上传接口返回的temp_path）
        
    Returns:
        解析后的文本内容
    """
    try:
        text = DocumentParser.parse_file(file_path)
        
        return JSONResponse(
            content=success_response(
                data={
                    "text": text,
                    "length": len(text),
                    "lines": len(text.split('\n'))
                },
                message="文档解析成功"
            )
        )
        
    except Exception as e:
        logger.error(f"文档解析失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"解析失败: {str(e)}")


@router.post("/document/chunk", summary="文档分块")
async def chunk_document(request: ChunkRequest):
    """
    对文档进行分块
    
    Returns:
        分块结果列表
    """
    try:
        chunks = DocumentProcessor.chunk_document(
            text=request.text,
            method=request.method,
            chunk_size=request.chunk_size,
            chunk_overlap=request.chunk_overlap,
            max_sentences=request.max_sentences
        )
        
        # 转换为字典
        chunks_data = [chunk.to_dict() for chunk in chunks]
        
        # 统计信息
        stats = {
            "total_chunks": len(chunks),
            "avg_chunk_size": sum(c.char_count for c in chunks) / len(chunks) if chunks else 0,
            "max_chunk_size": max((c.char_count for c in chunks), default=0),
            "min_chunk_size": min((c.char_count for c in chunks), default=0)
        }
        
        return JSONResponse(
            content=success_response(
                data={
                    "chunks": chunks_data,
                    "statistics": stats
                },
                message=f"分块完成: {len(chunks)} 个分块"
            )
        )
        
    except Exception as e:
        logger.error(f"文档分块失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"分块失败: {str(e)}")


# ========== 步骤2: 文档嵌入 ==========

@router.post("/embedding/embed", summary="文档向量化")
async def embed_documents(request: EmbedRequest):
    """
    对文本列表进行向量化
    
    Returns:
        向量列表和统计信息
    """
    try:
        # 获取embedding服务
        # 将字符串转换为枚举类型
        provider_enum = EmbeddingProvider(request.provider)
        embedding_service = EmbeddingServiceFactory.create(
            provider=provider_enum,
            model_name=request.model
        )
        
        # 批量向量化
        vectors = []
        for text in request.texts:
            vector = await embedding_service.embed_text(text)
            vectors.append(vector)
        
        # 统计信息
        stats = {
            "total_texts": len(request.texts),
            "vector_dimension": len(vectors[0]) if vectors else 0,
            "model": request.model,
            "provider": request.provider
        }
        
        # 只返回前几个向量的预览（避免响应过大）
        preview_vectors = [
            {
                "index": i,
                "dimension": len(v),
                "preview": v[:5],  # 只显示前5维
                "norm": float(sum(x**2 for x in v) ** 0.5)
            }
            for i, v in enumerate(vectors[:10])  # 只预览前10个
        ]
        
        return JSONResponse(
            content=success_response(
                data={
                    "vectors": vectors,  # 完整向量（前端可能需要）
                    "preview": preview_vectors,  # 预览信息
                    "statistics": stats
                },
                message=f"向量化完成: {len(vectors)} 个向量"
            )
        )
        
    except Exception as e:
        logger.error(f"向量化失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"向量化失败: {str(e)}")


@router.get("/embedding/models", summary="获取可用的embedding模型")
async def get_embedding_models():
    """
    获取可用的embedding模型列表
    """
    models = [
        {
            "name": "bge-m3:latest",
            "provider": "ollama",
            "dimension": 1024,
            "description": "BGE-M3中文embedding模型"
        },
        {
            "name": "nomic-embed-text:latest",
            "provider": "ollama",
            "dimension": 768,
            "description": "Nomic嵌入模型"
        }
    ]
    
    return JSONResponse(
        content=success_response(
            data=models,
            message="获取模型列表成功"
        )
    )


# ========== 步骤3: 文档分词 ==========

@router.post("/tokenize/jieba", summary="jieba分词")
async def tokenize_jieba(request: TokenizeRequest):
    """
    使用jieba对文本进行分词
    
    Returns:
        分词结果和统计信息
    """
    try:
        tokenizer = get_tokenizer_service()
        
        # 批量分词
        tokens_list = tokenizer.batch_tokenize(
            texts=request.texts,
            mode=request.mode,
            use_stop_words=request.use_stop_words
        )
        
        # 统计词频
        word_freq = tokenizer.get_word_freq(
            texts=request.texts,
            top_k=20,
            use_stop_words=request.use_stop_words
        )
        
        # 构建预览数据
        preview_data = [
            {
                "index": i,
                "original": text[:100] + "..." if len(text) > 100 else text,
                "tokens": tokens,
                "token_count": len(tokens)
            }
            for i, (text, tokens) in enumerate(zip(request.texts, tokens_list))
        ]
        
        stats = {
            "total_texts": len(request.texts),
            "total_tokens": sum(len(tokens) for tokens in tokens_list),
            "avg_tokens_per_text": sum(len(tokens) for tokens in tokens_list) / len(tokens_list) if tokens_list else 0,
            "unique_tokens": len(set(token for tokens in tokens_list for token in tokens)),
            "top_words": [{"word": w, "freq": f} for w, f in list(word_freq.items())[:20]]
        }
        
        return JSONResponse(
            content=success_response(
                data={
                    "tokens": tokens_list,
                    "preview": preview_data,
                    "statistics": stats
                },
                message=f"分词完成: {len(tokens_list)} 个文本"
            )
        )
        
    except Exception as e:
        logger.error(f"分词失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"分词失败: {str(e)}")


# ========== 步骤4: 索引写入 ==========

@router.post("/index/vector/write", summary="写入向量索引")
async def write_vector_index(
    kb_id: str,
    chunks: List[Dict[str, Any]],
    vectors: List[List[float]]
):
    """
    将向量写入向量数据库
    
    Args:
        kb_id: 知识库ID
        chunks: 分块数据列表
        vectors: 向量列表
        
    Returns:
        写入结果
    """
    try:
        # TODO: 实现向量索引写入
        # 1. 获取向量数据库连接
        # 2. 批量写入向量
        # 3. 返回结果
        
        logger.warning("向量索引写入功能待实现")
        
        return JSONResponse(
            content=success_response(
                data={
                    "kb_id": kb_id,
                    "written_count": len(vectors),
                    "status": "pending_implementation"
                },
                message="向量索引写入功能待实现"
            )
        )
        
    except Exception as e:
        logger.error(f"向量索引写入失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"写入失败: {str(e)}")


@router.post("/index/keyword/write", summary="写入关键词索引")
async def write_keyword_index(
    kb_id: str,
    chunks: List[Dict[str, Any]],
    tokens_list: List[List[str]]
):
    """
    将分词结果写入关键词索引
    
    Args:
        kb_id: 知识库ID
        chunks: 分块数据列表
        tokens_list: 分词结果列表
        
    Returns:
        写入结果
    """
    try:
        # TODO: 实现关键词索引写入
        # 1. 构建倒排索引
        # 2. 保存索引
        # 3. 返回结果
        
        logger.warning("关键词索引写入功能待实现")
        
        return JSONResponse(
            content=success_response(
                data={
                    "kb_id": kb_id,
                    "written_count": len(tokens_list),
                    "unique_tokens": len(set(token for tokens in tokens_list for token in tokens)),
                    "status": "pending_implementation"
                },
                message="关键词索引写入功能待实现"
            )
        )
        
    except Exception as e:
        logger.error(f"关键词索引写入失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"写入失败: {str(e)}")


# ========== 步骤5: 检索调试 ==========

@router.post("/retrieve/hybrid", summary="混合检索")
async def hybrid_search(request: HybridSearchRequest):
    """
    执行混合检索（向量 + 关键词 + RRF融合）
    
    Returns:
        检索结果
    """
    try:
        # 1. 对查询进行向量化
        embedding_service = EmbeddingServiceFactory.create(
            provider=EmbeddingProvider.OLLAMA,
            model_name=request.embedding_model
        )
        query_vector = await embedding_service.embed_text(request.query)
        
        # 2. 对查询进行分词
        tokenizer = get_tokenizer_service()
        query_tokens = tokenizer.tokenize(request.query, mode=request.tokenize_mode)
        
        # 3. 执行混合检索
        retrieval_service = RetrievalService()
        results = await retrieval_service.hybrid_search(
            kb_id=request.kb_id,
            query=request.query,
            query_vector=query_vector,
            query_tokens=query_tokens,
            top_k=request.top_k,
            vector_weight=request.vector_weight,
            keyword_weight=request.keyword_weight,
            rrf_k=request.rrf_k
        )
        
        # 转换为字典
        results_data = [r.to_dict() for r in results]
        
        return JSONResponse(
            content=success_response(
                data={
                    "query": request.query,
                    "query_tokens": query_tokens,
                    "results": results_data,
                    "config": {
                        "top_k": request.top_k,
                        "vector_weight": request.vector_weight,
                        "keyword_weight": request.keyword_weight,
                        "rrf_k": request.rrf_k
                    }
                },
                message=f"检索完成: {len(results)} 个结果"
            )
        )
        
    except Exception as e:
        logger.error(f"混合检索失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"检索失败: {str(e)}")


# ========== 工具接口 ==========

@router.post("/test/rrf", summary="测试RRF融合算法")
async def test_rrf_fusion(
    results_lists: List[List[Dict[str, Any]]],
    k: int = 60,
    weights: Optional[List[float]] = None
):
    """
    测试RRF融合算法（用于调试）
    
    Args:
        results_lists: 多个检索结果列表
        k: RRF参数
        weights: 权重列表
        
    Returns:
        融合后的结果
    """
    try:
        from app.services.retrieval_service import RetrievalResult
        
        # 转换为RetrievalResult对象
        results_objs = []
        for results_list in results_lists:
            results_obj_list = []
            for r in results_list:
                result_obj = RetrievalResult(
                    doc_id=r.get("doc_id", ""),
                    chunk_id=r.get("chunk_id", ""),
                    content=r.get("content", ""),
                    score=r.get("score", 0.0),
                    rank=r.get("rank", 0),
                    source=r.get("source", "unknown")
                )
                results_obj_list.append(result_obj)
            results_objs.append(results_obj_list)
        
        # RRF融合
        fused_results = RRFFusion.fusion(results_objs, k=k, weights=weights)
        
        # 转换回字典
        fused_data = [r.to_dict() for r in fused_results]
        
        return JSONResponse(
            content=success_response(
                data={
                    "fused_results": fused_data,
                    "config": {"k": k, "weights": weights}
                },
                message=f"RRF融合完成: {len(fused_results)} 个结果"
            )
        )
        
    except Exception as e:
        logger.error(f"RRF融合失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"融合失败: {str(e)}")


# ========== 调试结果存储管理 ==========

class SaveDebugResultRequest(BaseModel):
    """保存调试结果请求"""
    name: str = Field(..., description="结果名称")
    type: str = Field(..., description="结果类型: chunks, embeddings, tokens, index_data, schemas, knowledge_bases")
    data: Dict[str, Any] = Field(..., description="结果数据")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")


@router.post("/result/save", summary="保存调试结果")
async def save_debug_result(request: SaveDebugResultRequest):
    """
    保存调试结果到storage目录
    
    Args:
        request: 保存请求
    
    Returns:
        保存的结果ID
    """
    try:
        # 创建存储目录
        storage_dir = Path(settings.STORAGE_PATH) / "debug_results" / request.type
        storage_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成唯一ID
        result_id = f"{request.type}_{int(datetime.now().timestamp() * 1000)}_{uuid.uuid4().hex[:8]}"
        
        # 构建结果对象
        result = {
            "id": result_id,
            "name": request.name,
            "type": request.type,
            "data": request.data,
            "timestamp": int(datetime.now().timestamp() * 1000),
            "metadata": request.metadata or {}
        }
        
        # 保存到JSON文件
        file_path = storage_dir / f"{result_id}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2, default=str)
        
        # 更新索引文件
        index_file = storage_dir / "_index.json"
        index_data = []
        if index_file.exists():
            with open(index_file, "r", encoding="utf-8") as f:
                index_data = json.load(f)
        
        # 添加新结果到索引
        index_data.append({
            "id": result_id,
            "name": request.name,
            "timestamp": result["timestamp"],
            "metadata": result["metadata"]
        })
        
        # 按时间戳倒序排序
        index_data.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
        
        # 保存索引
        with open(index_file, "w", encoding="utf-8") as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)
        
        return JSONResponse(
            content=success_response(
                data={"id": result_id},
                message="保存成功"
            )
        )
        
    except Exception as e:
        logger.error(f"保存调试结果失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"保存失败: {str(e)}")


@router.get("/result/list/{result_type}", summary="列出调试结果")
async def list_debug_results(result_type: str):
    """
    列出指定类型的所有调试结果
    
    Args:
        result_type: 结果类型 (chunks, embeddings, tokens, index_data, schemas, knowledge_bases)
    
    Returns:
        结果列表
    """
    try:
        index_file = Path(settings.STORAGE_PATH) / "debug_results" / result_type / "_index.json"
        
        if not index_file.exists():
            return JSONResponse(
                content=success_response(
                    data=[],
                    message="暂无结果"
                )
            )
        
        with open(index_file, "r", encoding="utf-8") as f:
            index_data = json.load(f)
        
        return JSONResponse(
            content=success_response(
                data=index_data,
                message=f"共 {len(index_data)} 个结果"
            )
        )
        
    except Exception as e:
        logger.error(f"列出调试结果失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"列出失败: {str(e)}")


@router.get("/result/load/{result_type}/{result_id}", summary="加载调试结果")
async def load_debug_result(result_type: str, result_id: str):
    """
    加载指定的调试结果
    
    Args:
        result_type: 结果类型
        result_id: 结果ID
    
    Returns:
        结果数据
    """
    try:
        file_path = Path(settings.STORAGE_PATH) / "debug_results" / result_type / f"{result_id}.json"
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="结果不存在")
        
        with open(file_path, "r", encoding="utf-8") as f:
            result = json.load(f)
        
        return JSONResponse(
            content=success_response(
                data=result,
                message="加载成功"
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"加载调试结果失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"加载失败: {str(e)}")


@router.delete("/result/delete/{result_type}/{result_id}", summary="删除调试结果")
async def delete_debug_result(result_type: str, result_id: str):
    """
    删除指定的调试结果
    
    Args:
        result_type: 结果类型
        result_id: 结果ID
    
    Returns:
        删除结果
    """
    try:
        storage_dir = Path(settings.STORAGE_PATH) / "debug_results" / result_type
        file_path = storage_dir / f"{result_id}.json"
        index_file = storage_dir / "_index.json"
        
        # 删除文件
        if file_path.exists():
            file_path.unlink()
        
        # 更新索引
        if index_file.exists():
            with open(index_file, "r", encoding="utf-8") as f:
                index_data = json.load(f)
            
            index_data = [item for item in index_data if item.get("id") != result_id]
            
            with open(index_file, "w", encoding="utf-8") as f:
                json.dump(index_data, f, ensure_ascii=False, indent=2)
        
        return JSONResponse(
            content=success_response(
                data=None,
                message="删除成功"
            )
        )
        
    except Exception as e:
        logger.error(f"删除调试结果失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")

