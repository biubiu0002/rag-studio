"""
稀疏向量服务
支持多种稀疏向量生成方法：TF-IDF、Simple
"""

from typing import List, Dict, Tuple, Optional, Union, Any
from abc import ABC, abstractmethod
import math
from collections import Counter, defaultdict
import dashtext
import logging

from app.services.tokenizer_service import get_tokenizer_service

logger = logging.getLogger(__name__)

class BaseSparseVectorService(ABC):
    """稀疏向量服务抽象基类"""
    
    @abstractmethod
    def generate_query_sparse_vector(self, query: str|list[str]) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        生成查询的稀疏向量
        """
        pass
    
    @abstractmethod
    def generate_document_sparse_vector(self, text: str|list[str]) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        生成文档的稀疏向量
        """
        pass
    
    @abstractmethod
    def convert_to_qdrant_format(self, token_weights:  Union[Dict[str, Any], List[Dict[str, Any]]]) -> Union[Dict[str, Any],list[Dict[str,Any]]]:
        """
        将 token:weight 格式转换为 Qdrant 格式
        
        Args:
            token_weights: {token: weight} 格式
            
        Returns:
            {indices: [...], values: [...]} 格式
        """
        pass


class BM25SparseVectorService(BaseSparseVectorService):
    """
    基于 dashtext 的 BM25 稀疏向量服务
    使用预训练的中文 BM25 模型
    """
    
    def __init__(self, model_path: str):
        """
        初始化 BM25 稀疏向量服务
        
        Args:
            model_path: BM25 模型文件路径
            
        Raises:
            FileNotFoundError: 模型文件不存在
            RuntimeError: 模型加载失败
        """
        from pathlib import Path
        import json
        
        if not Path(model_path).exists():
            raise FileNotFoundError(f"BM25 模型文件不存在: {model_path}")
        
        try:
            from dashtext import SparseVectorEncoder
            self.encoder = SparseVectorEncoder()
            self.encoder.load(path=model_path)
            logger.info(f"✅ BM25 模型加载成功: {model_path}")
        except Exception as e:
            raise RuntimeError(f"BM25 模型加载失败: {str(e)}") from e
        
    def generate_query_sparse_vector(self, query: str|list[str]) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        生成查询的稀疏向量
        """
        return self.encoder.encode_queries(query)
    
    def generate_document_sparse_vector(self, text: str|list[str]) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        生成文档的稀疏向量
        """
        return self.encoder.encode_documents(text)


    def convert_to_qdrant_format(self, token_weights:  Union[Dict[str, Any], list[Dict[str, Any]]]) -> Union[Dict[str, Any],list[Dict[str,Any]]]:
        """
        将 token:weight 格式转换为 Qdrant 格式
        
        Args:
            token_weights: {token: weight} 格式
            
        Returns:
            {indices: [...], values: [...]} 格式
        """
        if isinstance(token_weights, list):
            return [self._convert_to_qdrant_format(item) for item in token_weights]
        return self._convert_to_qdrant_format(token_weights)
        
    def _convert_to_qdrant_format(self, token_weights: Dict[str, float]) -> Dict[str, Any]:
        if not token_weights or len(token_weights) == 0:
            return {"indices": [], "values": []}
        return {
            "indices": list(token_weights.keys()),
            "values": list(token_weights.values())
        }


class SparseVectorServiceFactory:
    """稀疏向量服务工厂"""
    
    # 单例实例
    _bm25_instance = None
    
    @staticmethod
    def create(service_type: str, **kwargs) -> BaseSparseVectorService:
        """
        创建稀疏向量服务实例
        
        Args:
            service_type: 服务类型 ('bm25', 'tf-idf', 'simple')
            **kwargs: 其他参数
                - model_path: BM25 模型路径 (service_type='bm25' 时必需)
            
        Returns:
            稀疏向量服务实例
            
        Raises:
            ValueError: 不支持的服务类型或缺少必需参数
            FileNotFoundError: 模型文件不存在
            RuntimeError: 模型加载失败
        """
        service_type = service_type.lower().strip()
        
        if service_type == "bm25":
            # BM25 使用单例模式，避免重复加载模型
            if SparseVectorServiceFactory._bm25_instance is None:
                model_path = kwargs.get('model_path')
                if not model_path:
                    raise ValueError("创建 BM25 服务时必须提供 model_path 参数")
                SparseVectorServiceFactory._bm25_instance = BM25SparseVectorService(model_path)
            return SparseVectorServiceFactory._bm25_instance
        
        else:
            raise ValueError(f"不支持的稀疏向量服务类型: {service_type}。支持的类型: bm25, tf-idf, simple")

