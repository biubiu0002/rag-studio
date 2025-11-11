"""
稀疏向量服务
支持多种稀疏向量生成方法
"""

from typing import List, Dict, Tuple, Optional
from abc import ABC, abstractmethod
import math
from collections import Counter, defaultdict

from app.services.tokenizer_service import get_tokenizer_service


class BaseSparseVectorService(ABC):
    """稀疏向量服务抽象基类"""
    
    def add_document(self, text: str):
        """
        添加文档到语料库（用于需要语料库统计的稀疏向量方法）
        
        Args:
            text: 文档文本
        """
        # 默认实现为空，子类可以根据需要重写
        pass
    
    def add_documents(self, texts: List[str]):
        """
        批量添加文档到语料库
        
        Args:
            texts: 文档文本列表
        """
        for text in texts:
            self.add_document(text)
    
    @abstractmethod
    def generate_sparse_vector(self, text: str) -> Dict[str, float]:
        """
        生成稀疏向量
        
        Args:
            text: 输入文本
            
        Returns:
            稀疏向量，格式为 {token: weight}
        """
        pass


class BM25SparseVectorService(BaseSparseVectorService):
    """
    基于BM25的稀疏向量服务
    """
    
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        """
        初始化BM25稀疏向量服务
        
        Args:
            k1: BM25参数，控制词频饱和度
            b: BM25参数，控制文档长度归一化
        """
        self.k1 = k1
        self.b = b
        self.tokenizer = get_tokenizer_service()
        self.doc_count = 0
        self.token_doc_freq = defaultdict(int)
        self.avg_doc_length = 0.0
        self.total_tokens = 0
    
    def add_document(self, text: str):
        """
        添加文档到语料库，用于计算IDF
        
        Args:
            text: 文档文本
        """
        tokens = self.tokenizer.tokenize(text)
        self.doc_count += 1
        self.total_tokens += len(tokens)
        self.avg_doc_length = self.total_tokens / self.doc_count if self.doc_count > 0 else 0
        
        # 记录包含每个token的文档数
        unique_tokens = set(tokens)
        for token in unique_tokens:
            self.token_doc_freq[token] += 1
    
    def add_documents(self, texts: List[str]):
        """
        批量添加文档到语料库
        
        Args:
            texts: 文档文本列表
        """
        for text in texts:
            self.add_document(text)
    
    def generate_sparse_vector(self, text: str) -> Dict[str, float]:
        """
        使用BM25算法生成稀疏向量
        
        Args:
            text: 输入文本
            
        Returns:
            稀疏向量，格式为 {token: weight}
        """
        tokens = self.tokenizer.tokenize(text)
        token_freq = Counter(tokens)
        doc_length = len(tokens)
        
        # 如果没有语料库统计（调试模式），则使用简化的BM25
        # 将当前文档作为单文档语料库
        if self.doc_count == 0:
            # 调试模式：使用简化计算
            sparse_vector = {}
            for token, freq in token_freq.items():
                # 简化的IDF（假设单文档语料库）
                idf = 1.0  # 默认IDF权重
                
                # 计算TF
                tf = freq
                norm_tf = (tf * (self.k1 + 1)) / (
                    tf + self.k1 * (1 - self.b + self.b * doc_length / 1.0)
                )
                
                # BM25分数
                score = idf * norm_tf
                if score > 0:
                    sparse_vector[token] = score
            return sparse_vector
        
        # 标准BM25计算（有语料库统计）
        sparse_vector = {}
        for token, freq in token_freq.items():
            # 计算IDF
            doc_freq = self.token_doc_freq.get(token, 0)
            if doc_freq == 0:
                # 如果token不在语料库中，使用默认IDF
                idf = math.log(self.doc_count + 1)
            else:
                idf = math.log((self.doc_count - doc_freq + 0.5) / (doc_freq + 0.5) + 1.0)
            
            # 计算TF
            tf = freq
            norm_tf = (tf * (self.k1 + 1)) / (
                tf + self.k1 * (1 - self.b + self.b * doc_length / self.avg_doc_length)
            )
            
            # BM25分数
            score = idf * norm_tf
            if score > 0:
                sparse_vector[token] = score
        
        return sparse_vector


class TFSparseVectorService(BaseSparseVectorService):
    """
    基于TF-IDF的稀疏向量服务
    """
    
    def __init__(self):
        """
        初始化TF-IDF稀疏向量服务
        """
        self.tokenizer = get_tokenizer_service()
        self.doc_count = 0
        self.token_doc_freq = defaultdict(int)
        self.total_tokens = 0
    
    def add_document(self, text: str):
        """
        添加文档到语料库，用于计算IDF
        
        Args:
            text: 文档文本
        """
        tokens = self.tokenizer.tokenize(text)
        self.doc_count += 1
        self.total_tokens += len(tokens)
        
        # 记录包含每个token的文档数
        unique_tokens = set(tokens)
        for token in unique_tokens:
            self.token_doc_freq[token] += 1
    
    def add_documents(self, texts: List[str]):
        """
        批量添加文档到语料库
        
        Args:
            texts: 文档文本列表
        """
        for text in texts:
            self.add_document(text)
    
    def generate_sparse_vector(self, text: str) -> Dict[str, float]:
        """
        使用TF-IDF算法生成稀疏向量
        
        Args:
            text: 输入文本
            
        Returns:
            稀疏向量，格式为 {token: weight}
        """
        tokens = self.tokenizer.tokenize(text)
        token_freq = Counter(tokens)
        doc_length = len(tokens)
        
        # 如果没有语料库统计（调试模式），使用简化的TF-IDF
        if self.doc_count == 0:
            # 调试模式：只使用TF权重
            sparse_vector = {}
            for token, freq in token_freq.items():
                # 简化的TF计算（归一化词频）
                tf = freq / doc_length if doc_length > 0 else 0
                if tf > 0:
                    sparse_vector[token] = tf
            return sparse_vector
        
        # 标准TF-IDF计算（有语料库统计）
        sparse_vector = {}
        for token, freq in token_freq.items():
            # 计算TF (词频)
            tf = freq / doc_length if doc_length > 0 else 0
            
            # 计算IDF (逆文档频率)
            doc_freq = self.token_doc_freq.get(token, 0)
            if doc_freq == 0:
                # 如果token不在语料库中，使用默认IDF
                idf = math.log(self.doc_count + 1)
            else:
                idf = math.log(self.doc_count / doc_freq)
            
            # TF-IDF分数
            score = tf * idf
            if score > 0:
                sparse_vector[token] = score
        
        return sparse_vector


class SimpleSparseVectorService(BaseSparseVectorService):
    """
    简单稀疏向量服务
    直接使用词频作为权重
    """
    
    def __init__(self):
        self.tokenizer = get_tokenizer_service()
    
    def generate_sparse_vector(self, text: str) -> Dict[str, float]:
        """
        生成稀疏向量
        
        Args:
            text: 输入文本
            
        Returns:
            稀疏向量，格式为 {token: weight}
        """
        tokens = self.tokenizer.tokenize(text)
        token_freq = Counter(tokens)
        
        # 直接使用词频作为权重
        return dict(token_freq)


class SparseVectorServiceFactory:
    """稀疏向量服务工厂"""
    
    @staticmethod
    def create(service_type: str, **kwargs) -> BaseSparseVectorService:
        """
        创建稀疏向量服务实例
        
        Args:
            service_type: 服务类型 ('bm25', 'tf-idf', 'simple', 'splade')
            **kwargs: 其他参数
            
        Returns:
            稀疏向量服务实例
        """
        if service_type == "bm25":
            return BM25SparseVectorService(
                k1=kwargs.get("k1", 1.5),
                b=kwargs.get("b", 0.75)
            )
        elif service_type == "tf-idf" or service_type == "tf":
            return TFSparseVectorService()
        elif service_type == "simple":
            return SimpleSparseVectorService()
        elif service_type == "splade":
            # SPLADE暂时使用简单稀疏向量服务作为占位符
            # 后续可以替换为真正的SPLADE模型实现
            return SimpleSparseVectorService()
        else:
            raise ValueError(f"不支持的稀疏向量服务类型: {service_type}")


def convert_sparse_vector_to_qdrant_format(
    sparse_vector: Dict[str, float],
    token_to_id_map: Optional[Dict[str, int]] = None
) -> Tuple[List[int], List[float]]:
    """
    将稀疏向量转换为Qdrant格式
    
    Args:
        sparse_vector: 稀疏向量 {token: weight}
        token_to_id_map: token到ID的映射表（可选）
        
    Returns:
        (indices, values) 元组，Qdrant稀疏向量格式
    """
    if token_to_id_map is None:
        # 如果没有提供映射表，直接使用token的hash值作为ID
        token_to_id_map = {token: abs(hash(token)) % (2**31) for token in sparse_vector.keys()}
    
    indices = []
    values = []
    
    for token, weight in sparse_vector.items():
        token_id = token_to_id_map.get(token)
        if token_id is not None:
            indices.append(token_id)
            values.append(weight)
    
    return indices, values