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


def get_bm25_model_path() -> str:
    """
    获取BM25模型路径
    
    优先从配置中获取，如果未配置则使用默认路径
    
    Returns:
        BM25模型文件的完整路径
    
    Raises:
        ValueError: 如果模型路径不存在
    """
    from app.config import settings
    import os
    
    # 1. 尝试从配置获取
    model_path = getattr(settings, 'BM25_MODEL_PATH', None)
    if model_path and os.path.exists(model_path):
        return model_path
    
    # 2. 使用默认路径
    default_path = os.path.join(settings.MODELS_PATH, settings.BM25_MODEL_NAME)
    if os.path.exists(default_path):
        return default_path
    
    # 3. 尝试使用项目根目录的相对路径（向后兼容）
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    fallback_path = os.path.join(project_root, "resources", "models", settings.BM25_MODEL_NAME)
    if os.path.exists(fallback_path):
        return fallback_path
    
    # 4. 所有路径都不存在，抛出错误
    raise ValueError(
        f"BM25模型文件不存在。已尝试以下路径：\n"
        f"  1. 配置路径: {model_path if model_path else '(未配置)'}\n"
        f"  2. 默认路径: {default_path}\n"
        f"  3. 回退路径: {fallback_path}\n"
        f"请确保模型文件存在或配置正确的 BM25_MODEL_PATH"
    )


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
                # 如果未提供model_path，尝试自动获取
                if not model_path:
                    try:
                        model_path = get_bm25_model_path()
                    except ValueError as e:
                        raise ValueError(f"创建 BM25 服务失败: {e}")
                SparseVectorServiceFactory._bm25_instance = BM25SparseVectorService(model_path)
            return SparseVectorServiceFactory._bm25_instance
        
        else:
            raise ValueError(f"不支持的稀疏向量服务类型: {service_type}。支持的类型: bm25, tf-idf, simple")

