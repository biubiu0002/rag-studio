"""
RAG链路调试控制器
提供可视化调试接口
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional, Tuple
import logging
import tempfile
import os
import json
import uuid
from pathlib import Path
from datetime import datetime

from app.core.response import success_response
from app.services.document_processor import DocumentProcessor, DocumentParser
from app.models.document import Chunk
from app.services.tokenizer_service import get_tokenizer_service
from app.services.retrieval_service import RetrievalService, RRFFusion
from app.services.embedding_service import EmbeddingServiceFactory
from app.models.knowledge_base import EmbeddingProvider
from app.config import settings
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

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/debug", tags=["链路调试"])


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
            model_name=request.model,
            service_url=request.service_url,  # 传递自定义服务地址
            api_key=request.api_key  # 传递API密钥
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




@router.post("/index/hybrid/write", summary="写入混合索引（稠密+稀疏向量）")
async def write_hybrid_index(request: WriteHybridIndexRequest):
    """
    一次性写入稠密向量和/或稀疏向量到向量数据库
    每个point同时包含稠密向量和稀疏向量
    
    Returns:
        写入结果
    """
    try:
        # 验证至少提供了一种向量
        if not request.dense_vectors and not request.sparse_vectors:
            raise HTTPException(status_code=400, detail="必须提供dense_vectors或sparse_vectors中的至少一种")
        
        # 验证数量一致性
        num_chunks = len(request.chunks)
        if request.dense_vectors and len(request.dense_vectors) != num_chunks:
            raise HTTPException(
                status_code=400,
                detail=f"chunks数量({num_chunks})与dense_vectors数量({len(request.dense_vectors)})不匹配"
            )
        if request.sparse_vectors and len(request.sparse_vectors) != num_chunks:
            raise HTTPException(
                status_code=400,
                detail=f"chunks数量({num_chunks})与sparse_vectors数量({len(request.sparse_vectors)})不匹配"
            )
        
        # 准备chunk文本和元数据
        chunks_text = []
        metadata_list = []
        
        for i, chunk in enumerate(request.chunks):
            # 提取文本内容
            chunk_text = chunk.get("content", "")
            chunks_text.append(chunk_text)
            
            # 构建metadata（保留chunk中的所有字段，除了content）
            metadata = {"kb_id": request.kb_id}
            for key, value in chunk.items():
                if key != "content":
                    metadata[key] = value
            
            # 确保基础字段存在
            if "chunk_id" not in metadata:
                metadata["chunk_id"] = chunk.get("id", f"chunk_{i}")
            if "content" not in metadata:
                metadata["content"] = chunk_text
            if "char_count" not in metadata:
                metadata["char_count"] = len(chunk_text)
            
            metadata_list.append(metadata)
        
        # 创建文档写入任务
        from app.services.task_queue_service import TaskQueueService
        from app.models.task_queue import TaskType
        
        task_service = TaskQueueService()
        task = await task_service.create_task(
            task_type=TaskType.DOCUMENT_WRITE,
            payload={
                "kb_id": request.kb_id,
                "chunks": chunks_text,
                "metadata_list": metadata_list,
                "dense_vectors": request.dense_vectors,
                "sparse_vectors": request.sparse_vectors
            }
        )
        
        return JSONResponse(
            content=success_response(
                data={
                    "task_id": task.id,
                    "status": task.status.value,
                    "task_type": task.task_type.value
                },
                message="文档写入任务已创建，正在后台处理"
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"混合索引写入失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"写入失败: {str(e)}")

# ========== 步骤5: 检索调试 ==========

@router.post("/retrieve/unified", summary="统一检索接口")
async def unified_search(request: UnifiedSearchRequest):
    """
    统一检索接口，支持三种模式：
    - semantic: 语义向量检索（基于稠密向量）
    - keyword: 关键词检索（基于稀疏向量/BM25）
    - hybrid: 混合检索（语义+关键词融合）
    
    融合方法：
    - rrf: 基于排名的倒数融合
    - weighted: 加权平均融合
    
    Returns:
        检索结果
    """
    try:
        from app.services.knowledge_base import KnowledgeBaseService
        from app.services.retrieval_service import RetrievalService
        
        # 获取知识库配置（用于返回元数据）
        kb_service = KnowledgeBaseService()
        kb = await kb_service.get_knowledge_base(request.kb_id)
        if not kb:
            raise HTTPException(status_code=404, detail=f"知识库不存在: {request.kb_id}")
        
        # 使用统一检索服务
        retrieval_service = RetrievalService()
        results = await retrieval_service.unified_search(
            kb_id=request.kb_id,
            query=request.query,
            retrieval_mode=request.retrieval_mode,
            top_k=request.top_k,
            score_threshold=request.score_threshold,
            fusion_method=request.fusion_method,
            semantic_weight=request.semantic_weight,
            keyword_weight=request.keyword_weight,
            rrf_k=request.rrf_k
        )
        
        # 转换为字典
        results_data = [r.to_dict() for r in results]
        
        return JSONResponse(
            content=success_response(
                data={
                    "query": request.query,
                    "results": results_data,
                    "config": {
                        "retrieval_mode": request.retrieval_mode,
                        "top_k": request.top_k,
                        "fusion_method": request.fusion_method,
                        "rrf_k": request.rrf_k,
                        "semantic_weight": request.semantic_weight,
                        "keyword_weight": request.keyword_weight
                    },
                    "metadata": {
                        "embedding_model": kb.embedding_model,
                        "embedding_provider": kb.embedding_provider.value,
                        "vector_db_type": kb.vector_db_type
                    }
                },
                message=f"{request.retrieval_mode}检索完成: {len(results)} 个结果"
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"检索失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"检索失败: {str(e)}")




# ========== 工具接口 ==========


# ========== 调试结果存储管理 ==========


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


# ========== 稀疏向量生成 ==========

@router.post("/sparse-vector/generate", summary="生成稀疏向量")
async def generate_sparse_vector(request: SparseVectorRequest):
    """
    生成稀疏向量（调试模式，不强依赖知识库）
    
    Returns:
        稀疏向量和Qdrant格式
    """
    try:
        # 直接使用稀疏向量服务
        from app.services.sparse_vector_service import SparseVectorServiceFactory
        
        # 创建稀疏向量服务
        sparse_service = SparseVectorServiceFactory.create(request.method)
        
        # 生成稀疏向量
        sparse_vector = sparse_service.generate_document_sparse_vector(request.text)

        # 转换为Qdrant格式
        
        qdrant_sparse_vector = sparse_service.convert_to_qdrant_format(sparse_vector)
        
        return JSONResponse(
            content=success_response(
                data={
                    "sparse_vector": sparse_vector,
                    "qdrant_format": qdrant_sparse_vector,
                    "sparsity": len(sparse_vector),  # 非零元素数量
                    "total_tokens": len(sparse_vector)  # 总token数量
                },
                message=f"稀疏向量生成完成: {len(sparse_vector)} 个非零元素"
            )
        )
        
    except Exception as e:
        logger.error(f"生成稀疏向量失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")


# 添加转换函数
def convert_sparse_vector_to_qdrant_format(
    sparse_vector: Dict[str, float]
) -> Tuple[List[int], List[float]]:
    """
    将稀疏向量转换为Qdrant格式
    
    Args:
        sparse_vector: 稀疏向量 {token: weight}
        
    Returns:
        (indices, values) 元组，Qdrant稀疏向量格式
    """
    indices = []
    values = []
    
    # 使用token的hash值作为索引
    for token, weight in sparse_vector.items():
        if weight != 0:  # 只保留非零权重
            token_id = abs(hash(token)) % (2**31)  # 确保是正整数
            indices.append(token_id)
            values.append(weight)
    
    return indices, values


# ========== 生成测试 ==========


@router.post("/generate", summary="生成测试")
async def generate(request: GenerationRequest):
    """
    基于上下文生成答案
    
    Args:
        request: 生成请求
    
    Returns:
        生成的答案
    """
    try:
        import time
        start_time = time.time()
        
        # 1. 获取上下文
        context = request.context
        if not context and request.kb_id:
            # 需要自动检索上下文
            logger.warning("自动检索上下文功能待实现，请手动提供上下文")
        
        # 2. 构建prompt - 分离prompt模板和内容
        # 定义prompt模板
        if context:
            prompt_template = """基于以下上下文回答问题。如果上下文中没有相关信息，请说'信息不足'。

上下文：
{context}

问题：{query}

答案："""
        else:
            prompt_template = """请回答以下问题：

问题：{query}

答案："""
        
        # 填充模板
        prompt = prompt_template.format(context=context or "", query=request.query)
        
        # 3. 调用LLM生成答案
        answer = await call_llm(
            prompt=prompt,
            provider=request.llm_provider,
            model=request.llm_model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            stream=request.stream
        )
        
        generation_time = time.time() - start_time
        
        return JSONResponse(
            content=success_response(
                data={
                    "query": request.query,
                    "context": context,
                    "answer": answer,
                    "prompt": prompt,  # 返回完整的prompt供调试
                    "generation_time": generation_time,
                    "llm_model": request.llm_model,
                    "config": {
                        "provider": request.llm_provider,
                        "model": request.llm_model,
                        "temperature": request.temperature,
                        "max_tokens": request.max_tokens
                    }
                },
                message="生成完成"
            )
        )
        
    except Exception as e:
        logger.error(f"生成失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")


async def call_llm(
    prompt: str,
    provider: str = "ollama",
    model: str = "deepseek-r1:1.5b",
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    stream: bool = False
) -> str:
    """
    调用LLM生成答案
    
    Args:
        prompt: 提示词
        provider: LLM服务提供商 (ollama)
        model: LLM模型
        temperature: 生成参数
        max_tokens: 最大token数
        stream: 是否流式输出
        
    Returns:
        生成的文本
    """
    try:
        if provider == "ollama":
            import httpx
            
            # 使用httpx调用Ollama API
            async with httpx.AsyncClient(timeout=60.0) as client:
                payload = {
                    "model": model,
                    "prompt": prompt,
                    "temperature": temperature,
                    "stream": False  # 暂不支持流式
                }
                
                if max_tokens:
                    payload["num_predict"] = max_tokens
                
                response = await client.post(
                    f"{settings.OLLAMA_BASE_URL}/api/generate",
                    json=payload
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get("response", "")
                else:
                    logger.error(f"Ollama API请求失败: {response.status_code}")
                    return "LLM调用失败"
        else:
            logger.warning(f"不支持的LLM提供商: {provider}")
            return "不支持的LLM提供商"
            
    except Exception as e:
        logger.error(f"调用LLM失败: {e}", exc_info=True)
        raise
