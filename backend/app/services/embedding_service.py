"""
嵌入服务
支持多种嵌入模型提供商
"""

from typing import List
from abc import ABC, abstractmethod
import logging
import httpx
import asyncio

from app.models.knowledge_base import EmbeddingProvider
from app.config import settings

logger = logging.getLogger(__name__)


class BaseEmbeddingService(ABC):
    """嵌入服务抽象基类"""
    
    @abstractmethod
    async def embed_text(self, text: str) -> List[float]:
        """
        嵌入单个文本
        
        Args:
            text: 输入文本
        
        Returns:
            向量嵌入
        """
        pass
    
    @abstractmethod
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        批量嵌入文本
        
        Args:
            texts: 文本列表
        
        Returns:
            向量嵌入列表
        """
        pass


class OllamaEmbeddingService(BaseEmbeddingService):
    """
    Ollama嵌入服务
    
    通过HTTP API调用Ollama服务获取文本嵌入向量
    """
    
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.base_url = settings.OLLAMA_BASE_URL.rstrip('/')
        self.api_url = f"{self.base_url}/api/embeddings"
        self.timeout = 60.0  # 请求超时时间（秒）
        self.max_retries = 3  # 最大重试次数
    
    async def _call_ollama_api(self, text: str, retry_count: int = 0) -> List[float]:
        """
        调用Ollama API获取嵌入向量
        
        Args:
            text: 输入文本
            retry_count: 当前重试次数
        
        Returns:
            嵌入向量列表
        
        Raises:
            Exception: API调用失败
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.api_url,
                    json={
                        "model": self.model_name,
                        "prompt": text
                    }
                )
                response.raise_for_status()
                result = response.json()
                
                if "embedding" not in result:
                    raise ValueError(f"Ollama API响应格式错误: 缺少 'embedding' 字段")
                
                embedding = result["embedding"]
                if not isinstance(embedding, list) or len(embedding) == 0:
                    raise ValueError(f"Ollama API返回的嵌入向量格式错误: {type(embedding)}")
                
                return embedding
                
        except httpx.HTTPStatusError as e:
            error_msg = f"Ollama API HTTP错误: {e.response.status_code} - {e.response.text}"
            logger.error(error_msg)
            
            # 对于5xx错误，进行重试
            if e.response.status_code >= 500 and retry_count < self.max_retries:
                logger.warning(f"Ollama API服务器错误，进行第 {retry_count + 1} 次重试...")
                await asyncio.sleep(1 * (retry_count + 1))  # 指数退避
                return await self._call_ollama_api(text, retry_count + 1)
            
            raise Exception(error_msg) from e
            
        except httpx.TimeoutException as e:
            error_msg = f"Ollama API请求超时（{self.timeout}秒）"
            logger.error(error_msg)
            
            # 超时也进行重试
            if retry_count < self.max_retries:
                logger.warning(f"Ollama API请求超时，进行第 {retry_count + 1} 次重试...")
                await asyncio.sleep(1 * (retry_count + 1))
                return await self._call_ollama_api(text, retry_count + 1)
            
            raise Exception(error_msg) from e
            
        except httpx.RequestError as e:
            error_msg = f"Ollama API连接错误: {str(e)}"
            logger.error(error_msg)
            
            # 连接错误也进行重试
            if retry_count < self.max_retries:
                logger.warning(f"Ollama API连接错误，进行第 {retry_count + 1} 次重试...")
                await asyncio.sleep(1 * (retry_count + 1))
                return await self._call_ollama_api(text, retry_count + 1)
            
            raise Exception(f"无法连接到Ollama服务 ({self.base_url})，请确保服务已启动") from e
            
        except Exception as e:
            logger.error(f"Ollama API调用失败: {str(e)}", exc_info=True)
            raise
    
    async def embed_text(self, text: str) -> List[float]:
        """
        嵌入单个文本
        
        Args:
            text: 输入文本
        
        Returns:
            向量嵌入
        """
        if not text or not text.strip():
            raise ValueError("输入文本不能为空")
        
        return await self._call_ollama_api(text)
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        批量嵌入文本
        
        使用并发请求提高性能，但限制并发数以避免过载
        
        Args:
            texts: 文本列表
        
        Returns:
            向量嵌入列表
        """
        if not texts:
            return []
        
        # 验证输入
        for i, text in enumerate(texts):
            if not text or not text.strip():
                raise ValueError(f"第 {i+1} 个文本不能为空")
        
        # 使用信号量限制并发数（避免过多并发请求导致Ollama过载）
        semaphore = asyncio.Semaphore(10)  # 最多10个并发请求
        
        async def embed_with_semaphore(text: str) -> List[float]:
            async with semaphore:
                return await self._call_ollama_api(text)
        
        # 并发执行所有请求
        tasks = [embed_with_semaphore(text) for text in texts]
        embeddings = await asyncio.gather(*tasks)
        
        return list(embeddings)


class CustomEmbeddingService(BaseEmbeddingService):
    """
    自研嵌入服务（预留）
    
    TODO: 实现
    1. 配置自研服务地址和认证
    2. 实现HTTP调用
    3. 处理响应格式
    """
    
    def __init__(self, service_url: str, api_key: str, model_name: str):
        self.service_url = service_url
        self.api_key = api_key
        self.model_name = model_name
    
    async def embed_text(self, text: str) -> List[float]:
        """嵌入单个文本（待实现）"""
        # TODO: 调用自研服务API
        # import httpx
        # async with httpx.AsyncClient() as client:
        #     response = await client.post(
        #         f"{self.service_url}/embed",
        #         headers={"Authorization": f"Bearer {self.api_key}"},
        #         json={"text": text, "model": self.model_name}
        #     )
        #     return response.json()["embedding"]
        
        return [0.0] * 768
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """批量嵌入文本（待实现）"""
        embeddings = []
        for text in texts:
            embedding = await self.embed_text(text)
            embeddings.append(embedding)
        return embeddings


class EmbeddingServiceFactory:
    """嵌入服务工厂"""
    
    @staticmethod
    def create(
        provider: EmbeddingProvider,
        model_name: str,
        service_url: str = None,
        api_key: str = None
    ) -> BaseEmbeddingService:
        """
        创建嵌入服务实例
        
        Args:
            provider: 嵌入提供商
            model_name: 模型名称
            service_url: 服务地址（自研服务用）
            api_key: API密钥（自研服务用）
        
        Returns:
            嵌入服务实例
        """
        if provider == EmbeddingProvider.OLLAMA:
            return OllamaEmbeddingService(model_name)
        elif provider == EmbeddingProvider.CUSTOM:
            if not service_url:
                service_url = settings.CUSTOM_SERVICE_URL
            if not api_key:
                api_key = settings.CUSTOM_SERVICE_API_KEY
            return CustomEmbeddingService(service_url, api_key, model_name)
        else:
            raise ValueError(f"不支持的嵌入提供商: {provider}")

