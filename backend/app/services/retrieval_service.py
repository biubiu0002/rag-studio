"""
检索服务
提供向量检索、关键词检索、混合检索和RRF融合
"""

from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict
import logging
import math

# 添加导入
from app.services.knowledge_base import KnowledgeBaseService
from app.services.vector_db_service import VectorDBServiceFactory, QdrantService
from app.services.sparse_vector_service import SparseVectorServiceFactory
from app.models.knowledge_base import VectorDBType

logger = logging.getLogger(__name__)


@dataclass
class RetrievalResult:
    """检索结果"""
    doc_id: str
    chunk_id: str
    content: str
    score: float
    rank: int
    source: str  # "vector", "keyword", "hybrid"
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> dict:
        return {
            "doc_id": self.doc_id,
            "chunk_id": self.chunk_id,
            "content": self.content,
            "score": self.score,
            "rank": self.rank,
            "source": self.source,
            "metadata": self.metadata or {}
        }


class RRFFusion:
    """RRF (Reciprocal Rank Fusion) 融合算法"""
    
    @staticmethod
    def rrf_score(rank: int, k: int = 60) -> float:
        """
        计算RRF分数
        
        Args:
            rank: 排名位置（从1开始）
            k: 常数，通常为60
            
        Returns:
            RRF分数
        """
        return 1.0 / (k + rank)
    
    @classmethod
    def fusion(
        cls,
        results_lists: List[List[RetrievalResult]],
        k: int = 60,
        weights: Optional[List[float]] = None
    ) -> List[RetrievalResult]:
        """
        融合多个检索结果列表
        
        Args:
            results_lists: 多个检索结果列表
            k: RRF参数
            weights: 各结果列表的权重（如果为None则均等权重）
            
        Returns:
            融合后的结果列表
        """
        if not results_lists:
            return []
        
        # 默认均等权重
        if weights is None:
            weights = [1.0] * len(results_lists)
        
        # 检查权重数量
        if len(weights) != len(results_lists):
            raise ValueError("权重数量必须与结果列表数量一致")
        
        # 归一化权重
        weight_sum = sum(weights)
        weights = [w / weight_sum for w in weights]
        
        # 计算每个文档的RRF分数
        doc_scores = defaultdict(float)
        doc_info = {}  # 保存文档信息
        
        for idx, results in enumerate(results_lists):
            weight = weights[idx]
            for rank, result in enumerate(results, start=1):
                chunk_id = result.chunk_id
                rrf_score = cls.rrf_score(rank, k)
                doc_scores[chunk_id] += rrf_score * weight
                
                # 保存文档信息（使用第一次出现的）
                if chunk_id not in doc_info:
                    doc_info[chunk_id] = result
        
        # 按RRF分数排序
        sorted_docs = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)
        
        # 构建最终结果
        final_results = []
        for rank, (chunk_id, score) in enumerate(sorted_docs, start=1):
            result = doc_info[chunk_id]
            # 创建新的结果对象，更新分数和排名
            fused_result = RetrievalResult(
                doc_id=result.doc_id,
                chunk_id=result.chunk_id,
                content=result.content,
                score=score,
                rank=rank,
                source="hybrid",
                metadata={
                    **result.metadata,
                    "original_score": result.score,
                    "original_source": result.source
                }
            )
            final_results.append(fused_result)
        
        logger.info(f"RRF融合完成: {len(final_results)} 个结果")
        return final_results


class RetrievalService:
    """检索服务"""
    
    def __init__(self):
        """初始化检索服务"""
        self.kb_service = KnowledgeBaseService()
    
    async def vector_search(
        self,
        kb_id: str,
        query: str,
        query_vector: List[float],
        top_k: int = 10,
        score_threshold: float = 0.0
    ) -> List[RetrievalResult]:
        """
        向量检索
        
        Args:
            kb_id: 知识库ID
            query: 查询文本
            query_vector: 查询向量
            top_k: 返回数量
            score_threshold: 分数阈值
            
        Returns:
            检索结果列表
        """
        # 1. 获取知识库信息
        kb = await self.kb_service.get_knowledge_base(kb_id)
        if not kb:
            logger.warning(f"知识库不存在: {kb_id}")
            return []
        
        # 2. 创建向量数据库服务实例
        try:
            vector_db_service = VectorDBServiceFactory.create(
                kb.vector_db_type,
                config=kb.vector_db_config if kb.vector_db_config else None
            )
        except Exception as e:
            logger.error(f"创建向量数据库服务失败: {e}")
            return []
        
        # 3. 执行相似度搜索
        try:
            search_results = await vector_db_service.search(
                collection_name=kb_id,
                query_vector=query_vector,
                top_k=top_k,
                score_threshold=score_threshold
            )
        except Exception as e:
            logger.error(f"向量检索失败: {e}")
            return []
        
        # 4. 构建结果对象
        results = []
        for rank, result in enumerate(search_results, start=1):
            payload = result.get("payload", {})
            
            # 提取文档信息
            doc_id = payload.get("doc_id", "")
            chunk_id = payload.get("chunk_id", str(result.get("id", "")))
            content = payload.get("content", "")
            
            # 创建检索结果对象
            retrieval_result = RetrievalResult(
                doc_id=doc_id,
                chunk_id=chunk_id,
                content=content,
                score=result.get("score", 0.0),
                rank=rank,
                source="vector",
                metadata=payload
            )
            results.append(retrieval_result)
        
        logger.info(f"向量检索完成: {len(results)} 个结果")
        return results
    
    async def keyword_search(
        self,
        kb_id: str,
        query: str,
        query_sparse_vector: Optional[Dict[str, Any]] = None,
        top_k: int = 10,
        score_threshold: float = 0.0
    ) -> List[RetrievalResult]:
        """
        关键词检索（基于稀疏向量）
        
        对于Qdrant等支持稀疏向量的数据库，直接使用稀疏向量检索；
        对于不支持的数据库，回退到BM25算法。
        
        Args:
            kb_id: 知识库ID
            query: 查询文本
            query_sparse_vector: 稀疏查询向量 (indices和values的字典)
            top_k: 返回数量
            score_threshold: 分数阈值
            
        Returns:
            检索结果列表
        """
        # 1. 获取知识库信息
        kb = await self.kb_service.get_knowledge_base(kb_id)
        if not kb:
            logger.warning(f"知识库不存在: {kb_id}")
            return []
        
        # 2. 如果没有提供稀疏向量，生成稀疏向量
        if query_sparse_vector is None:
            sparse_method = kb.vector_db_config.get("sparse_method", "bm25") if kb.vector_db_config else "bm25"
            sparse_service = SparseVectorServiceFactory.create(sparse_method)
            query_sparse_dict = sparse_service.generate_query_sparse_vector(query)
            converted_sparse = sparse_service.convert_to_qdrant_format(query_sparse_dict)
            # 确保是字典类型
            if isinstance(converted_sparse, list):
                query_sparse_vector = converted_sparse[0] if len(converted_sparse) > 0 else {"indices": [], "values": []}
            else:
                query_sparse_vector = converted_sparse
        
        # 3. 根据向量数据库类型选择检索方式
        if kb.vector_db_type == VectorDBType.QDRANT:
            # 对于Qdrant，使用稀疏向量检索
            return await self._qdrant_sparse_search(
                kb_id=kb_id,
                query_sparse_vector=query_sparse_vector,
                top_k=top_k,
                score_threshold=score_threshold
            )
        else:
            # 对于其他数据库，暂未实现
            pass
            # from app.services.tokenizer_service import get_tokenizer_service
            # tokenizer = get_tokenizer_service()
            # query_tokens = tokenizer.tokenize(query)
            # return await self._bm25_search(
            #     kb_id=kb_id,
            #     query_tokens=query_tokens,
            #     top_k=top_k,
            #     score_threshold=score_threshold
            # )
    
    async def _qdrant_sparse_search(
        self,
        kb_id: str,
        query_sparse_vector: Dict[str, Any],
        top_k: int = 10,
        score_threshold: float = 0.0
    ) -> List[RetrievalResult]:
        """
        Qdrant稀疏向量检索（内部方法）
        
        使用Qdrant的query_points API，只查询稀疏向量字段
        """
        # 1. 获取知识库信息
        kb = await self.kb_service.get_knowledge_base(kb_id)
        if not kb:
            return []
        
        # 2. 创建Qdrant服务实例
        try:
            qdrant_service = QdrantService(config=kb.vector_db_config if kb.vector_db_config else None)
        except Exception as e:
            logger.error(f"创建Qdrant服务失败: {e}")
            return []
        
        # 3. 获取稀疏向量字段名称
        try:
            from qdrant_client.http.models import SparseVector
            
            collection_info = qdrant_service.client.get_collection(kb_id)
            sparse_vector_name = "sparse_vector"  # 默认名称
            
            if hasattr(collection_info.config.params, 'sparse_vectors'):
                sparse_vectors_config = collection_info.config.params.sparse_vectors
                if isinstance(sparse_vectors_config, dict) and len(sparse_vectors_config) > 0:
                    sparse_vector_name = next(iter(sparse_vectors_config.keys()))
            
            # 构建稀疏向量查询
            sparse_vector = SparseVector(
                indices=query_sparse_vector["indices"],
                values=query_sparse_vector["values"]
            )
            
            # 执行稀疏向量检索
            search_result = qdrant_service.client.query_points(
                collection_name=kb_id,
                query=sparse_vector,
                using=sparse_vector_name,
                limit=top_k,
                score_threshold=score_threshold if score_threshold > 0 else None
            )
            
            # 构建结果对象
            results = []
            for rank, scored_point in enumerate(search_result.points, start=1):
                payload = scored_point.payload
                if payload is not None:
                    results.append(RetrievalResult(
                        doc_id=payload.get("doc_id", ""),
                        chunk_id=payload.get("chunk_id", str(scored_point.id)),
                        content=payload.get("content", ""),
                        score=scored_point.score,
                        rank=rank,
                        source="keyword",
                        metadata=payload
                    ))
            
            logger.info(f"Qdrant稀疏向量检索完成: {len(results)} 个结果")
            return results
            
        except Exception as e:
            logger.error(f"Qdrant稀疏向量检索失败: {e}", exc_info=True)
            return []
    
    async def _bm25_search(
        self,
        kb_id: str,
        query_tokens: List[str],
        top_k: int = 10,
        score_threshold: float = 0.0
    ) -> List[RetrievalResult]:
        """
        BM25检索（内部方法，用于不支持稀疏向量的数据库）
        """
        # 1. 获取知识库信息
        kb = await self.kb_service.get_knowledge_base(kb_id)
        if not kb:
            return []
        
        # 2. 获取文档服务
        from app.services.document import DocumentService
        doc_service = DocumentService()
        
        # 3. 获取知识库中的所有文档
        docs, _ = await doc_service.list_documents(kb_id=kb_id)
        if not docs:
            logger.warning(f"知识库中没有文档: {kb_id}")
            return []
        
        # 4. 收集所有文档的分块内容
        all_chunks = []
        doc_chunk_mapping = {}  # 映射chunk_id到文档信息
        
        for doc in docs:
            chunks, _ = await doc_service.list_document_chunks(document_id=doc.id)
            for chunk in chunks:
                all_chunks.append(chunk)
                doc_chunk_mapping[chunk.id] = {
                    "doc_id": doc.id,
                    "chunk_id": chunk.id,
                    "content": chunk.content,
                    "chunk_index": chunk.chunk_index
                }
        
        if not all_chunks:
            logger.warning(f"知识库中没有分块: {kb_id}")
            return []
        
        # 5. 初始化BM25算法
        bm25 = BM25()
        
        # 6. 计算文档频率和平均文档长度
        doc_freq = defaultdict(int)
        total_docs = len(all_chunks)
        total_length = 0
        
        # 为每个分块分词并统计词频
        chunk_tokens = {}
        for chunk in all_chunks:
            from app.services.tokenizer_service import get_tokenizer_service
            tokenizer = get_tokenizer_service()
            tokens = tokenizer.tokenize(chunk.content)
            chunk_tokens[chunk.id] = tokens
            total_length += len(tokens)
            
            # 统计包含每个词的文档数
            unique_tokens = set(tokens)
            for token in unique_tokens:
                doc_freq[token] += 1
        
        avg_doc_length = total_length / total_docs if total_docs > 0 else 0
        
        # 7. 计算每个分块的BM25分数
        scores = []
        for chunk in all_chunks:
            chunk_id = chunk.id
            tokens = chunk_tokens.get(chunk_id, [])
            score = bm25.score(query_tokens, tokens, doc_freq, total_docs, avg_doc_length)
            
            if score >= score_threshold:
                scores.append((chunk_id, score))
        
        # 8. 按分数排序
        scores.sort(key=lambda x: x[1], reverse=True)
        
        # 9. 构建结果对象
        results = []
        for rank, (chunk_id, score) in enumerate(scores[:top_k], start=1):
            doc_info = doc_chunk_mapping.get(chunk_id)
            if doc_info:
                retrieval_result = RetrievalResult(
                    doc_id=doc_info["doc_id"],
                    chunk_id=doc_info["chunk_id"],
                    content=doc_info["content"],
                    score=score,
                    rank=rank,
                    source="keyword",
                    metadata={
                        "chunk_index": doc_info["chunk_index"]
                    }
                )
                results.append(retrieval_result)
        
        logger.info(f"BM25检索完成: {len(results)} 个结果")
        return results
    
    async def hybrid_search(
        self,
        kb_id: str,
        query: str,
        query_vector: Optional[List[float]] = None,
        query_sparse_vector: Optional[Dict[str, Any]] = None,
        top_k: int = 10,
        score_threshold: float = 0.0,
        fusion: str = "rrf",
        semantic_weight: float =0.7,
        keyword_weight: float = 0.3,
        rrf_k: int = 10
    ) -> List[RetrievalResult]:
        """
        混合检索（稠密向量+稀疏向量）
        
        根据向量数据库类型自动选择最优检索策略：
        - Qdrant: 使用原生混合检索（Prefetch + Fusion）
        - 其他: 使用RRF融合多路检索结果
        
        Args:
            kb_id: 知识库ID
            query: 查询文本
            query_vector: 稠密查询向量
            query_sparse_vector: 稀疏查询向量 (indices和values的字典)
            top_k: 返回数量
            score_threshold: 分数阈值
            fusion: 融合方法 ("rrf" 或 "dbsf")
            semantic_weight: 浓密向量权重
            keyword_weight: 关键词权重
            rrf_k: RRF融合参数
            
        Returns:
            检索结果列表
        """
        # 1. 获取知识库信息
        kb = await self.kb_service.get_knowledge_base(kb_id)
        if not kb:
            logger.warning(f"知识库不存在: {kb_id}")
            return []
        
        # 2. 根据数据库类型选择混合检索策略
        if kb.vector_db_type == VectorDBType.QDRANT:
            # 使用Qdrant原生混合检索
            return await self._qdrant_hybrid_search(
                kb_id=kb_id,
                query=query,
                query_vector=query_vector,
                query_sparse_vector=query_sparse_vector,
                top_k=top_k,
                score_threshold=score_threshold,
                fusion=fusion,
                semantic_weight=semantic_weight,
                keyword_weight=keyword_weight,
                rrf_k=rrf_k
            )
        else:
            # 使用RRF融合多路检索 暂未实现
            return []
    
    async def _qdrant_hybrid_search(
        self,
        kb_id: str,
        query: str,
        query_vector: Optional[List[float]] = None,
        query_sparse_vector: Optional[Dict[str, Any]] = None,
        top_k: int = 10,
        score_threshold: float = 0.0,
        fusion: str = "rrf",
        semantic_weight: float =0.7,
        keyword_weight: float = 0.3,
        rrf_k: int = 10
    ) -> List[RetrievalResult]:
        """
        Qdrant原生混合检索（内部方法）
        
        使用Qdrant的Prefetch + Fusion机制实现混合检索
        """
        # 1. 获取知识库信息
        kb = await self.kb_service.get_knowledge_base(kb_id)
        if not kb:
            logger.warning(f"知识库不存在: {kb_id}")
            return []
        
        # 3. 创建Qdrant服务实例
        try:
            qdrant_service = QdrantService(config=kb.vector_db_config if kb.vector_db_config else None)
        except Exception as e:
            logger.error(f"创建Qdrant服务失败: {e}")
            return []
        
        # 4. 如果没有提供稠密向量，自动生成
        if query_vector is None:
            from app.services.embedding_service import EmbeddingServiceFactory
            from app.models.knowledge_base import EmbeddingProvider
            try:
                # 转换provider字符串为枚举
                if isinstance(kb.embedding_provider, str):
                    provider = EmbeddingProvider(kb.embedding_provider)
                else:
                    provider = kb.embedding_provider
                
                # 创建嵌入服务实例
                embedding_service = EmbeddingServiceFactory.create(
                    provider=provider,
                    model_name=kb.embedding_model
                )
                # 生成向量
                query_vector = await embedding_service.embed_text(query)
            except Exception as e:
                logger.error(f"生成查询向量失败: {e}", exc_info=True)
                return []
        
        # 5. 如果没有提供稀疏向量，但知识库配置了稀疏向量字段，则尝试生成稀疏向量
        if query_sparse_vector is None:
            # 生成BM25稀疏向量
            from app.services.sparse_vector_service import SparseVectorServiceFactory
            # todo service_type从kb配置来 目前仅支持bm25
            service_type = "bm25"
            sparse_service = SparseVectorServiceFactory.create(service_type="bm25")
            
            sparse_vector = sparse_service.generate_query_sparse_vector(query=query)
            query_sparse_vector = sparse_service.convert_to_qdrant_format(sparse_vector) # pyright: ignore[reportAssignmentType]
        
        # 6. 执行Qdrant原生混合检索
        #    Qdrant DBSF是自适应根据标准差计算分数的，权重传参不生效，不支持rrf_k参数
        try:
            search_results = await qdrant_service.hybrid_search(
                collection_name=kb_id,
                query_vector=query_vector,
                query_sparse_vector=query_sparse_vector,
                top_k=top_k,
                score_threshold=score_threshold,
                fusion=fusion,
            )
        except Exception as e:
            logger.error(f"Qdrant混合检索失败: {e}")
            return []
        
        # 7. 构建结果对象
        results = []
        for rank, result in enumerate(search_results, start=1):
            payload = result.get("payload", {})
            
            # 提取文档信息
            doc_id = payload.get("doc_id", "")
            chunk_id = payload.get("chunk_id", str(result.get("id", "")))
            content = payload.get("content", "")
            
            # 创建检索结果对象
            retrieval_result = RetrievalResult(
                doc_id=doc_id,
                chunk_id=chunk_id,
                content=content,
                score=result.get("score", 0.0),
                rank=rank,
                source="hybrid",
                metadata=payload
            )
            results.append(retrieval_result)
        
        logger.info(f"Qdrant原生混合检索完成: {len(results)} 个结果")
        return results
    
    async def unified_search(
        self,
        kb_id: str,
        query: str,
        retrieval_mode: str = "hybrid",  # "semantic" | "keyword" | "hybrid"
        top_k: int = 10,
        score_threshold: float = 0.0,
        fusion_method: str = "rrf",  # "rrf" | "weighted"
        semantic_weight: float = 0.7,
        keyword_weight: float = 0.3,
        rrf_k: int = 60
    ) -> List[RetrievalResult]:
        """
        统一检索接口，支持三种检索模式
        
        Args:
            kb_id: 知识库ID
            query: 查询文本
            retrieval_mode: 检索模式 ("semantic" | "keyword" | "hybrid")
            top_k: 返回数量
            score_threshold: 分数阈值
            fusion_method: 融合方法 ("rrf" | "weighted")，仅在 hybrid 模式有效
            semantic_weight: 语义向量权重，仅在 hybrid 模式有效
            keyword_weight: 关键词权重，仅在 hybrid 模式有效
            rrf_k: RRF融合参数k，仅在 hybrid 模式有效
            
        Returns:
            检索结果列表
        """
        if retrieval_mode == "semantic":
            # 语义向量检索：需要先生成 embedding
            kb = await self.kb_service.get_knowledge_base(kb_id)
            if not kb:
                logger.warning(f"知识库不存在: {kb_id}")
                return []
            
            from app.services.embedding_service import EmbeddingServiceFactory
            from app.models.knowledge_base import EmbeddingProvider
            
            try:
                # 转换provider字符串为枚举
                if isinstance(kb.embedding_provider, str):
                    provider = EmbeddingProvider(kb.embedding_provider)
                else:
                    provider = kb.embedding_provider
                
                # 创建嵌入服务实例并生成向量
                embedding_service = EmbeddingServiceFactory.create(
                    provider=provider,
                    model_name=kb.embedding_model
                )
                query_vector = await embedding_service.embed_text(query)
                
                # 调用向量检索
                return await self.vector_search(
                    kb_id=kb_id,
                    query=query,
                    query_vector=query_vector,
                    top_k=top_k,
                    score_threshold=score_threshold
                )
            except Exception as e:
                logger.error(f"语义向量检索失败: {e}", exc_info=True)
                return []
        
        elif retrieval_mode == "keyword":
            # 关键词检索
            return await self.keyword_search(
                kb_id=kb_id,
                query=query,
                query_sparse_vector=None,  # 自动生成
                top_k=top_k,
                score_threshold=score_threshold
            )
        
        elif retrieval_mode == "hybrid":
            # 混合检索：根据 fusion_method 选择融合策略
            # fusion_method "rrf" -> fusion "rrf"
            # fusion_method "weighted" -> fusion "dbsf" (Qdrant的加权融合)
            fusion_strategy = "rrf" if fusion_method == "rrf" else "dbsf"
            
            return await self.hybrid_search(
                kb_id=kb_id,
                query=query,
                query_vector=None,  # 自动生成
                query_sparse_vector=None,  # 自动生成
                top_k=top_k,
                score_threshold=score_threshold,
                fusion=fusion_strategy,
                semantic_weight=semantic_weight,
                keyword_weight=keyword_weight,
                rrf_k=rrf_k
            )
        
        else:
            logger.error(f"不支持的检索模式: {retrieval_mode}")
            return []


class BM25:
    """BM25算法实现"""
    
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        """
        初始化BM25
        
        Args:
            k1: 词频饱和度参数
            b: 长度归一化参数
        """
        self.k1 = k1
        self.b = b
    
    def score(
        self,
        query_tokens: List[str],
        doc_tokens: List[str],
        doc_freq: Dict[str, int],  # 词在整个文档集中的文档频率
        total_docs: int,
        avg_doc_length: float
    ) -> float:
        """
        计算BM25分数
        
        Args:
            query_tokens: 查询分词
            doc_tokens: 文档分词
            doc_freq: 词的文档频率
            total_docs: 文档总数
            avg_doc_length: 平均文档长度
            
        Returns:
            BM25分数
        """
        score = 0.0
        doc_length = len(doc_tokens)
        
        # 计算词频
        term_freq = defaultdict(int)
        for token in doc_tokens:
            term_freq[token] += 1
        
        # 对查询中的每个词计算得分
        for token in query_tokens:
            if token not in term_freq:
                continue
            
            # 词频
            tf = term_freq[token]
            
            # 文档频率（包含该词的文档数）
            df = doc_freq.get(token, 0)
            if df == 0:
                continue
            
            # IDF计算
            idf = math.log((total_docs - df + 0.5) / (df + 0.5) + 1.0)
            
            # BM25公式
            norm_tf = (tf * (self.k1 + 1)) / (
                tf + self.k1 * (1 - self.b + self.b * doc_length / avg_doc_length)
            )
            
            score += idf * norm_tf
        
        return score


class VectorSimilarity:
    """向量相似度计算"""
    
    @staticmethod
    def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """
        余弦相似度
        
        Args:
            vec1: 向量1
            vec2: 向量2
            
        Returns:
            余弦相似度 [0, 1]
        """
        import numpy as np
        
        v1 = np.array(vec1)
        v2 = np.array(vec2)
        
        dot_product = np.dot(v1, v2)
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))
    
    @staticmethod
    def euclidean_distance(vec1: List[float], vec2: List[float]) -> float:
        """
        欧氏距离
        
        Args:
            vec1: 向量1
            vec2: 向量2
            
        Returns:
            欧氏距离
        """
        import numpy as np
        
        v1 = np.array(vec1)
        v2 = np.array(vec2)
        
        return float(np.linalg.norm(v1 - v2))
    
    @staticmethod
    def dot_product(vec1: List[float], vec2: List[float]) -> float:
        """
        点积
        
        Args:
            vec1: 向量1
            vec2: 向量2
            
        Returns:
            点积值
        """
        import numpy as np
        
        v1 = np.array(vec1)
        v2 = np.array(vec2)
        
        return float(np.dot(v1, v2))

