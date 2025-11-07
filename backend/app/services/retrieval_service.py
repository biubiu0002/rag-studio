"""
检索服务
提供向量检索、关键词检索、混合检索和RRF融合
"""

from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict
import logging
import math

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
    metadata: Dict[str, Any] = None
    
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
        pass
    
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
        # TODO: 实现向量检索
        # 1. 连接向量数据库
        # 2. 执行相似度搜索
        # 3. 过滤分数低于阈值的结果
        # 4. 构建结果对象
        
        logger.warning("向量检索功能待实现")
        return []
    
    async def keyword_search(
        self,
        kb_id: str,
        query: str,
        query_tokens: List[str],
        top_k: int = 10,
        score_threshold: float = 0.0
    ) -> List[RetrievalResult]:
        """
        关键词检索（基于BM25算法）
        
        Args:
            kb_id: 知识库ID
            query: 查询文本
            query_tokens: 查询分词结果
            top_k: 返回数量
            score_threshold: 分数阈值
            
        Returns:
            检索结果列表
        """
        # TODO: 实现关键词检索
        # 1. 从倒排索引中查找包含查询词的文档
        # 2. 计算BM25分数
        # 3. 排序并返回top_k
        
        logger.warning("关键词检索功能待实现")
        return []
    
    async def hybrid_search(
        self,
        kb_id: str,
        query: str,
        query_vector: List[float],
        query_tokens: List[str],
        top_k: int = 10,
        vector_weight: float = 0.7,
        keyword_weight: float = 0.3,
        rrf_k: int = 60
    ) -> List[RetrievalResult]:
        """
        混合检索（向量 + 关键词 + RRF融合）
        
        Args:
            kb_id: 知识库ID
            query: 查询文本
            query_vector: 查询向量
            query_tokens: 查询分词
            top_k: 返回数量
            vector_weight: 向量检索权重
            keyword_weight: 关键词检索权重
            rrf_k: RRF参数k
            
        Returns:
            融合后的检索结果
        """
        # 1. 执行向量检索
        vector_results = await self.vector_search(
            kb_id=kb_id,
            query=query,
            query_vector=query_vector,
            top_k=top_k * 2  # 获取更多结果用于融合
        )
        
        # 2. 执行关键词检索
        keyword_results = await self.keyword_search(
            kb_id=kb_id,
            query=query,
            query_tokens=query_tokens,
            top_k=top_k * 2
        )
        
        # 3. RRF融合
        fused_results = RRFFusion.fusion(
            results_lists=[vector_results, keyword_results],
            k=rrf_k,
            weights=[vector_weight, keyword_weight]
        )
        
        # 4. 返回top_k
        return fused_results[:top_k]


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

