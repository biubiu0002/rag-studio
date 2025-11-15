"""
索引写入编排服务
负责向量生成、数据准备、格式转换和写入向量数据库的完整流程
"""

from typing import List, Dict, Any, Optional, Tuple
import logging

from app.services.knowledge_base import KnowledgeBaseService
from app.services.embedding_service import EmbeddingServiceFactory
from app.services.sparse_vector_service import SparseVectorServiceFactory
from app.services.vector_db_service import VectorDBServiceFactory
from app.models.knowledge_base import VectorDBType, EmbeddingProvider
from app.core.exceptions import NotFoundException
from app.config import settings

logger = logging.getLogger(__name__)


class IndexWritingService:
    """索引写入编排服务"""
    
    def __init__(self):
        self.kb_service = KnowledgeBaseService()
    
    async def write_chunks_to_index(
        self,
        kb_id: str,
        chunks: List[str],
        metadata_list: Optional[List[Dict[str, Any]]] = None,
        dense_vectors: Optional[List[List[float]]] = None,
        sparse_vectors: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        将文档分块写入向量数据库
        
        Args:
            kb_id: 知识库ID
            chunks: 文本分块列表
            metadata_list: 可选的元数据列表，每个元素对应一个chunk
            dense_vectors: 可选的稠密向量列表（如果提供则跳过生成）
            sparse_vectors: 可选的稀疏向量列表（如果提供则跳过生成）
        
        Returns:
            写入结果字典，包含写入数量等信息
        """
        if not chunks:
            raise ValueError("chunks不能为空")
        
        # 获取知识库配置和schema
        kb = await self.kb_service.get_knowledge_base(kb_id)
        if not kb:
            raise NotFoundException(message=f"知识库不存在: {kb_id}")
        
        kb_schema = await self.kb_service.get_knowledge_base_schema(kb_id)
        
        # 生成或使用提供的稠密向量
        if dense_vectors is None:
            dense_vectors = await self._generate_dense_embeddings(kb, chunks)
        
        # 生成或使用提供的稀疏向量
        if sparse_vectors is None:
            sparse_vectors = await self._generate_sparse_vectors(kb, kb_schema, chunks)
        
        # 准备元数据
        metadatas = self._prepare_metadata(kb_id, chunks, metadata_list, kb_schema)
        
        # 准备向量数据
        vectors, ids = self._prepare_vectors(
            dense_vectors, sparse_vectors, chunks, kb_schema, metadata_list
        )
        
        # 确保集合存在
        await self._ensure_collection_exists(kb, kb_schema, kb_id, dense_vectors)
        
        # 写入向量数据库
        await self._write_to_vector_db(kb, kb_id, vectors, metadatas, ids)
        
        return {
            "kb_id": kb_id,
            "written_count": len(vectors),
            "has_dense": dense_vectors is not None and len(dense_vectors) > 0,
            "has_sparse": sparse_vectors is not None and len(sparse_vectors) > 0,
            "status": "success"
        }
    
    async def _generate_dense_embeddings(
        self,
        kb: Any,
        chunks: List[str]
    ) -> List[List[float]]:
        """
        生成稠密向量
        
        Args:
            kb: 知识库对象
            chunks: 文本分块列表
        
        Returns:
            稠密向量列表
        """
        embedding_service = EmbeddingServiceFactory.create(
            provider=EmbeddingProvider(kb.embedding_provider),
            model_name=kb.embedding_model
        )
        
        embeddings = await embedding_service.embed_texts(chunks)
        logger.info(f"为 {len(chunks)} 个chunk生成了稠密向量")
        
        return embeddings
    
    async def _generate_sparse_vectors(
        self,
        kb: Any,
        kb_schema: Optional[Dict[str, Any]],
        chunks: List[str]
    ) -> List[Dict[str, Any]]:
        """
        生成稀疏向量（如果schema配置了稀疏向量字段）
        
        Args:
            kb: 知识库对象
            kb_schema: 知识库schema配置
            chunks: 文本分块列表
        
        Returns:
            稀疏向量列表，如果没有配置则返回空列表
        """
        sparse_vectors = []
        
        # 检查schema中是否配置了稀疏向量字段
        has_sparse_vector_field = False
        sparse_vector_method = None
        
        if kb_schema:
            for field in kb_schema.get("fields", []):
                if field.get("type") == "sparse_vector":
                    has_sparse_vector_field = True
                    # 从字段配置中获取生成方法，默认为 bm25
                    sparse_vector_method = field.get("method", "bm25")
                    break
        
        # 如果配置了稀疏向量字段，生成稀疏向量
        if has_sparse_vector_field and sparse_vector_method:
            try:
                # 创建稀疏向量服务
                # BM25需要model_path参数
                model_path = getattr(settings, 'BM25_MODEL_PATH', None)
                if not model_path:
                    # 尝试使用默认路径
                    import os
                    default_path = os.path.join(
                        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                        "resources", "models", "bm25_zh_default.json"
                    )
                    if os.path.exists(default_path):
                        model_path = default_path
                    else:
                        raise ValueError("BM25模型路径未配置且默认路径不存在")
                
                sparse_service = SparseVectorServiceFactory.create(
                    sparse_vector_method,
                    model_path=model_path
                )
                
                # 为每个chunk生成稀疏向量
                # BM25SparseVectorService使用预训练模型，不需要先添加文档到语料库
                for chunk_content in chunks:
                    sparse_vector_dict = sparse_service.generate_document_sparse_vector(chunk_content)
                    # 转换为Qdrant格式
                    qdrant_format = sparse_service.convert_to_qdrant_format(sparse_vector_dict)
                    sparse_vectors.append(qdrant_format)
                
                logger.info(f"为 {len(chunks)} 个chunk生成了稀疏向量")
            except Exception as e:
                logger.warning(f"生成稀疏向量失败: {e}，将跳过稀疏向量", exc_info=True)
                sparse_vectors = []
        
        return sparse_vectors
    
    def _prepare_metadata(
        self,
        kb_id: str,
        chunks: List[str],
        metadata_list: Optional[List[Dict[str, Any]]],
        kb_schema: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        准备元数据
        
        Args:
            kb_id: 知识库ID
            chunks: 文本分块列表
            metadata_list: 可选的元数据列表
            kb_schema: 知识库schema配置
        
        Returns:
            元数据列表
        """
        metadatas = []
        schema_fields = kb_schema.get("fields", []) if kb_schema else []
        
        for i, chunk in enumerate(chunks):
            # 从metadata_list获取基础元数据，如果没有则创建空字典
            metadata: Dict[str, Any] = {}
            if metadata_list and i < len(metadata_list):
                metadata.update(metadata_list[i])
            
            # 确保基础字段存在
            if "kb_id" not in metadata:
                metadata["kb_id"] = kb_id
            if "content" not in metadata:
                metadata["content"] = chunk
            if "char_count" not in metadata:
                metadata["char_count"] = len(chunk)
            if "chunk_id" not in metadata:
                metadata["chunk_id"] = f"chunk_{i}"
            
            # 根据schema添加字段
            for field in schema_fields:
                field_name = field["name"]
                # 跳过向量字段
                if field.get("type") in ["dense_vector", "sparse_vector"]:
                    continue
                # 如果字段已存在，跳过
                if field_name in metadata:
                    continue
                
                # 设置默认值
                field_type = field.get("type", "text")
                if field_type == "text":
                    metadata[field_name] = ""
                elif field_type == "integer":
                    metadata[field_name] = 0
                elif field_type == "float":
                    metadata[field_name] = 0.0
                elif field_type == "boolean":
                    metadata[field_name] = False
                elif field_type == "keyword":
                    metadata[field_name] = ""
                else:
                    metadata[field_name] = ""
            
            metadatas.append(metadata)
        
        return metadatas
    
    def _prepare_vectors(
        self,
        dense_vectors: List[List[float]],
        sparse_vectors: List[Dict[str, Any]],
        chunks: List[str],
        kb_schema: Optional[Dict[str, Any]],
        metadata_list: Optional[List[Dict[str, Any]]] = None
    ) -> Tuple[List[Dict[str, Any]], List[Any]]:
        """
        准备向量数据
        
        Args:
            dense_vectors: 稠密向量列表
            sparse_vectors: 稀疏向量列表
            chunks: 文本分块列表
            kb_schema: 知识库schema配置
            metadata_list: 可选的元数据列表
        
        Returns:
            (向量数据列表, ID列表)
        """
        schema_fields = kb_schema.get("fields", []) if kb_schema else []
        
        # 确定向量字段名称
        dense_field_name = "dense"
        sparse_field_name = "sparse_vector"
        
        for field in schema_fields:
            if field.get("type") == "dense_vector":
                dense_field_name = field.get("name", "dense")
            elif field.get("type") == "sparse_vector":
                sparse_field_name = field.get("name", "sparse_vector")
        
        # 构建向量数据和ID
        vectors = []
        ids = []
        
        for i, chunk in enumerate(chunks):
            vector_data: Dict[str, Any] = {}
            
            # 添加稠密向量
            if i < len(dense_vectors):
                vector_data[dense_field_name] = dense_vectors[i]
            
            # 添加稀疏向量（如果生成了）
            if i < len(sparse_vectors):
                sparse_vector = sparse_vectors[i]
                # 处理不同的稀疏向量格式
                if isinstance(sparse_vector, dict):
                    # 如果已经是Qdrant格式（包含indices和values）
                    if "indices" in sparse_vector and "values" in sparse_vector:
                        vector_data[sparse_field_name] = sparse_vector
                    # 如果是嵌套格式
                    elif "qdrant_format" in sparse_vector:
                        vector_data[sparse_field_name] = sparse_vector["qdrant_format"]
                    elif "sparse_vector" in sparse_vector:
                        sparse_data = sparse_vector["sparse_vector"]
                        if "qdrant_format" in sparse_data:
                            vector_data[sparse_field_name] = sparse_data["qdrant_format"]
                        elif "indices" in sparse_data and "values" in sparse_data:
                            vector_data[sparse_field_name] = sparse_data
                else:
                    # 其他格式，尝试直接使用
                    vector_data[sparse_field_name] = sparse_vector
            
            vectors.append(vector_data)
            
            # 生成ID：优先使用metadata_list中的chunk_id，否则使用索引
            chunk_id = f"chunk_{i}"
            if metadata_list and i < len(metadata_list):
                metadata = metadata_list[i]
                if "chunk_id" in metadata:
                    chunk_id = metadata["chunk_id"]
            
            # 尝试转换为整数ID（Qdrant支持）
            try:
                int_id = int(chunk_id)
                if int_id >= 0:
                    ids.append(int_id)
                else:
                    ids.append(chunk_id)
            except (ValueError, TypeError):
                # 如果不是数字字符串，尝试从chunk_id中提取数字部分
                # 如果chunk_id格式为 "chunk_123"，提取123
                if chunk_id.startswith("chunk_"):
                    try:
                        num_part = chunk_id.replace("chunk_", "")
                        int_id = int(num_part)
                        if int_id >= 0:
                            ids.append(int_id)
                        else:
                            ids.append(chunk_id)
                    except ValueError:
                        ids.append(chunk_id)
                else:
                    ids.append(chunk_id)
        
        return vectors, ids
    
    async def _ensure_collection_exists(
        self,
        kb: Any,
        kb_schema: Optional[Dict[str, Any]],
        kb_id: str,
        dense_vectors: List[List[float]]
    ):
        """
        确保集合存在
        
        Args:
            kb: 知识库对象
            kb_schema: 知识库schema配置
            kb_id: 知识库ID
            dense_vectors: 稠密向量列表（用于确定维度）
        """
        # 确定向量维度
        vector_dimension = kb.embedding_dimension
        if kb_schema:
            for field in kb_schema.get("fields", []):
                if field.get("type") == "dense_vector" and "dimension" in field:
                    vector_dimension = field["dimension"]
                    break
        
        # 如果提供了向量，验证维度
        if dense_vectors and len(dense_vectors) > 0:
            actual_dimension = len(dense_vectors[0])
            if actual_dimension != vector_dimension:
                logger.warning(
                    f"向量维度不匹配: 配置维度 {vector_dimension}, 实际维度 {actual_dimension}，使用实际维度"
                )
                vector_dimension = actual_dimension
        
        # 创建向量数据库服务
        vector_db_service = VectorDBServiceFactory.create(
            VectorDBType(kb.vector_db_type),
            config=kb.vector_db_config if kb.vector_db_config else None
        )
        
        # 创建集合（如果不存在）
        try:
            await vector_db_service.create_collection(
                collection_name=kb_id,
                dimension=vector_dimension,
                schema_fields=kb_schema.get("fields", []) if kb_schema else []
            )
        except Exception as e:
            # 如果集合已存在，忽略错误
            error_str = str(e).lower()
            if "already exists" not in error_str and "collection already exists" not in error_str:
                logger.warning(f"创建集合时发生错误: {e}")
    
    async def _write_to_vector_db(
        self,
        kb: Any,
        kb_id: str,
        vectors: List[Dict[str, Any]],
        metadatas: List[Dict[str, Any]],
        ids: List[Any]
    ):
        """
        写入向量数据库
        
        Args:
            kb: 知识库对象
            kb_id: 知识库ID
            vectors: 向量数据列表
            metadatas: 元数据列表
            ids: ID列表
        """
        vector_db_service = VectorDBServiceFactory.create(
            VectorDBType(kb.vector_db_type),
            config=kb.vector_db_config if kb.vector_db_config else None
        )
        
        await vector_db_service.insert_vectors(
            collection_name=kb_id,
            vectors=vectors,
            metadatas=metadatas,
            ids=ids
        )
        
        logger.info(f"成功写入 {len(vectors)} 个向量到 {kb.vector_db_type}")

