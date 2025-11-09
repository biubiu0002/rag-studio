"""
向量数据库服务
支持多种向量数据库
"""

from typing import List, Dict, Any, Optional, Union, Sequence
from abc import ABC, abstractmethod
import uuid

from app.models.knowledge_base import VectorDBType
from app.config import settings

# 尝试导入 Qdrant 客户端
try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import VectorParams, Distance, PointStruct
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False
    print("Warning: qdrant-client not installed. Qdrant functionality will be disabled.")


class BaseVectorDBService(ABC):
    """向量数据库服务抽象基类"""
    
    @abstractmethod
    async def create_collection(self, collection_name: str, dimension: int, **kwargs):
        """
        创建集合/索引
        
        Args:
            collection_name: 集合名称
            dimension: 向量维度
            **kwargs: 其他参数
        """
        pass
    
    @abstractmethod
    async def delete_collection(self, collection_name: str):
        """删除集合/索引"""
        pass
    
    @abstractmethod
    async def insert_vectors(
        self,
        collection_name: str,
        vectors: List[Union[List[float], Dict[str, Any]]],  # 支持稠密向量和稀疏向量
        metadatas: List[Dict[str, Any]],
        ids: List[str]
    ):
        """插入向量"""
        pass
    
    @abstractmethod
    async def search(
        self,
        collection_name: str,
        query_vector: List[float],
        top_k: int = 5,
        score_threshold: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        检索相似向量
        
        Args:
            collection_name: 集合名称
            query_vector: 查询向量
            top_k: 返回数量
            score_threshold: 分数阈值
        
        Returns:
            检索结果列表
        """
        pass
    
    async def hybrid_search(
        self,
        collection_name: str,
        query_vector: List[float],
        query_sparse_vector: Optional[Dict[str, Any]] = None,
        top_k: int = 5,
        score_threshold: float = 0.0,
        fusion: str = "rrf"
    ) -> List[Dict[str, Any]]:
        """
        混合检索（默认实现回退到普通向量检索）
        
        Args:
            collection_name: 集合名称
            query_vector: 查询向量
            query_sparse_vector: 稀疏查询向量
            top_k: 返回数量
            score_threshold: 分数阈值
            fusion: 融合方法
            
        Returns:
            检索结果列表
        """
        # 默认实现回退到普通向量检索
        return await self.search(collection_name, query_vector, top_k, score_threshold)
    
    @abstractmethod
    async def delete_vectors(self, collection_name: str, ids: List[str]):
        """删除向量"""
        pass


class ElasticsearchService(BaseVectorDBService):
    """
    Elasticsearch向量数据库服务
    
    TODO: 实现
    1. 连接ES集群
    2. 创建向量索引映射
    3. 实现向量检索
    """
    
    def __init__(self):
        self.url = settings.elasticsearch_url
    
    async def create_collection(self, collection_name: str, dimension: int, **kwargs):
        """创建ES索引（待实现）"""
        # TODO: 使用elasticsearch-py创建索引
        pass
    
    async def delete_collection(self, collection_name: str):
        """删除ES索引（待实现）"""
        pass
    
    async def insert_vectors(
        self,
        collection_name: str,
        vectors: List[Union[List[float], Dict[str, Any]]],  # 支持稠密向量和稀疏向量
        metadatas: List[Dict[str, Any]],
        ids: List[str]
    ):
        """插入向量（待实现）"""
        pass
    
    async def search(
        self,
        collection_name: str,
        query_vector: List[float],
        top_k: int = 5,
        score_threshold: float = 0.0
    ) -> List[Dict[str, Any]]:
        """检索（待实现）"""
        return []
    
    async def hybrid_search(
        self,
        collection_name: str,
        query_vector: List[float],
        query_sparse_vector: Optional[Dict[str, Any]] = None,
        top_k: int = 5,
        score_threshold: float = 0.0,
        fusion: str = "rrf"
    ) -> List[Dict[str, Any]]:
        """
        Elasticsearch混合检索（待实现）
        可以结合dense vector和sparse vector (如BM25)进行混合检索
        """
        # TODO: 实现Elasticsearch混合检索
        return await self.search(collection_name, query_vector, top_k, score_threshold)
    
    async def delete_vectors(self, collection_name: str, ids: List[str]):
        """删除向量（待实现）"""
        pass


class QdrantService(BaseVectorDBService):
    """
    Qdrant向量数据库服务
    """
    
    def __init__(self):
        if not QDRANT_AVAILABLE:
            raise ImportError("qdrant-client is not installed. Please install it with: pip install qdrant-client")
        
        self.host = settings.QDRANT_HOST
        self.port = settings.QDRANT_PORT
        self.api_key = settings.QDRANT_API_KEY
        
        # 初始化 Qdrant 客户端
        from qdrant_client import QdrantClient
        from qdrant_client.models import VectorParams, Distance, PointStruct
        
        self.client = QdrantClient(
            host=self.host,
            port=self.port,
            api_key=self.api_key if self.api_key else None
        )
        # 保存引用以便在其他方法中使用
        self.VectorParams = VectorParams
        self.Distance = Distance
        self.PointStruct = PointStruct
    
    async def create_collection(self, collection_name: str, dimension: int, **kwargs):
        """创建Qdrant集合"""
        # 检查集合是否已存在
        try:
            existing_collection = self.client.get_collection(collection_name)
            # 尝试检查维度是否匹配
            try:
                # 不同版本的Qdrant客户端可能有不同的API
                if hasattr(existing_collection, 'config') and hasattr(existing_collection.config, 'params'):
                    vectors_config = existing_collection.config.params.vectors
                    # 如果是字典形式的向量配置
                    if isinstance(vectors_config, dict):
                        # 取第一个向量配置的维度
                        first_config = next(iter(vectors_config.values()))
                        existing_dimension = getattr(first_config, 'size', None)
                    else:
                        # 单一向量配置
                        existing_dimension = getattr(vectors_config, 'size', None)
                    
                    if existing_dimension and existing_dimension != dimension:
                        print(f"Warning: Collection {collection_name} exists with dimension {existing_dimension}, "
                              f"but requested dimension is {dimension}. Recreating collection.")
                        # 如果维度不匹配，先删除集合
                        self.client.delete_collection(collection_name)
                    elif existing_dimension:
                        # 维度匹配，直接返回
                        return
            except Exception:
                # 无法获取维度信息，重新创建集合
                self.client.delete_collection(collection_name)
        except Exception:
            # 集合不存在，继续创建
            pass
        
        # 获取schema字段定义（如果提供）
        schema_fields = kwargs.get('schema_fields', [])
        
        # 构建Qdrant的向量配置
        from qdrant_client.models import VectorParams, Distance
        vectors_config = VectorParams(size=dimension, distance=Distance.COSINE)
        
        # 检查是否需要创建稀疏向量配置
        sparse_vectors_config = {}
        has_sparse_vector = False
        for field in schema_fields:
            if field.get("isSparseVectorIndex") or field.get("type") == "sparse_vector":
                vector_name = field.get("name", "sparse")
                # 使用SparseVectorParams创建稀疏向量配置
                from qdrant_client.models import SparseVectorParams
                sparse_vectors_config[vector_name] = SparseVectorParams()
                has_sparse_vector = True
        
        # 创建新的集合
        if has_sparse_vector:
            # 如果有稀疏向量配置，需要使用字典形式的向量配置
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config={"dense": vectors_config},  # 将稠密向量命名为"dense"
                sparse_vectors_config=sparse_vectors_config
            )
        else:
            # 如果没有稀疏向量配置，使用简单的向量配置
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=vectors_config
            )
        
        # 为标量字段创建索引
        for field in schema_fields:
            if field.get("isIndexed") and not field.get("isVectorIndex"):
                field_name = field["name"]
                field_type = field["type"]
                
                # 创建字段索引
                # 注意：Qdrant的索引创建方式可能需要根据版本调整
                try:
                    # 这里我们只是记录需要创建索引的字段
                    # 实际的索引创建会在数据插入时进行
                    pass
                except Exception as e:
                    print(f"Warning: Failed to create index for field {field_name}: {e}")
    
    async def delete_collection(self, collection_name: str):
        """删除集合"""
        try:
            self.client.delete_collection(collection_name)
        except Exception:
            # 集合不存在或删除失败，忽略错误
            pass
    
    async def insert_vectors(
        self,
        collection_name: str,
        vectors: List[Union[List[float], Dict[str, Any]]],  # 支持稠密向量和稀疏向量
        metadatas: List[Dict[str, Any]],
        ids: List[str]
    ):
        """插入向量"""
        # 首先检查集合配置，确定是否使用命名向量
        use_named_vectors = False
        has_sparse_vectors = False
        try:
            collection_info = self.client.get_collection(collection_name)
            if hasattr(collection_info, 'config') and hasattr(collection_info.config, 'params'):
                vectors_config = collection_info.config.params.vectors
                # 如果是字典形式的向量配置，说明使用了命名向量
                if isinstance(vectors_config, dict):
                    use_named_vectors = True
                    # 检查是否有稀疏向量配置
                    has_sparse_vectors = any("sparse" in key.lower() for key in vectors_config.keys())
        except Exception:
            # 如果无法获取集合信息，默认不使用命名向量
            pass
        
        # 创建点结构
        points = []
        for i, (vector, metadata, point_id) in enumerate(zip(vectors, metadatas, ids)):
            # 如果没有提供ID，生成一个UUID
            if not point_id:
                point_id = str(uuid.uuid4())
            else:
                # 确保ID是有效的Qdrant ID格式
                # 如果是数字字符串，转换为整数；否则保持为字符串（UUID格式）
                try:
                    # 尝试转换为整数
                    int_id = int(point_id)
                    if int_id >= 0:  # 确保是非负整数
                        point_id = int_id
                    else:
                        # 负数转换为UUID
                        point_id = str(uuid.uuid4())
                except ValueError:
                    # 不是数字，保持为字符串（假设是UUID格式）
                    # 验证是否为有效的UUID格式，如果不是则生成UUID
                    try:
                        uuid.UUID(point_id)
                    except ValueError:
                        # 不是有效的UUID，生成新的UUID
                        point_id = str(uuid.uuid4())
            
            # 根据Qdrant的要求处理metadata
            processed_payload = self._process_payload_for_qdrant(metadata)
            
            # 处理向量格式 - 支持命名向量和稀疏向量
            processed_vector: Union[List[float], Dict[str, Union[List[float], Any]]] = vector
            if use_named_vectors:
                # 如果是字典格式且包含稀疏向量，则直接使用
                if isinstance(vector, dict) and any(key in vector for key in ["sparse", "sparse_vector"]):
                    processed_vector = vector
                # 如果是普通向量，包装为稠密向量
                elif isinstance(vector, list):
                    processed_vector = {"dense": vector}
                # 如果是字典但不包含稀疏向量，添加稠密向量
                elif isinstance(vector, dict):
                    processed_vector = {"dense": vector.get("dense", []), **vector}
            
            point = self.PointStruct(
                id=point_id,
                vector=processed_vector,
                payload=processed_payload
            )
            points.append(point)
        
        # 批量插入
        self.client.upsert(
            collection_name=collection_name,
            points=points
        )
    
    def _process_payload_for_qdrant(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理payload以适配Qdrant的要求
        Qdrant对payload有一些限制，比如不支持嵌套对象
        """
        processed = {}
        for key, value in payload.items():
            # Qdrant支持的类型：字符串、数字、布尔值、数组（元素必须是相同类型）
            if isinstance(value, (str, int, float, bool)):
                processed[key] = value
            elif isinstance(value, list):
                # 检查数组元素类型是否一致
                if len(value) > 0:
                    first_type = type(value[0])
                    if all(isinstance(item, first_type) for item in value):
                        processed[key] = value
                    else:
                        # 如果类型不一致，转换为字符串
                        processed[key] = [str(item) for item in value]
                else:
                    processed[key] = value
            else:
                # 其他类型转换为字符串
                processed[key] = str(value)
        return processed
    
    async def search(
        self,
        collection_name: str,
        query_vector: List[float],
        top_k: int = 5,
        score_threshold: float = 0.0
    ) -> List[Dict[str, Any]]:
        """检索"""
        # 检查集合配置，确定是否使用命名向量
        use_named_vectors = False
        try:
            collection_info = self.client.get_collection(collection_name)
            if hasattr(collection_info, 'config') and hasattr(collection_info.config, 'params'):
                vectors_config = collection_info.config.params.vectors
                # 如果是字典形式的向量配置，说明使用了命名向量
                if isinstance(vectors_config, dict):
                    use_named_vectors = True
        except Exception:
            # 如果无法获取集合信息，默认不使用命名向量
            pass
        
        # 执行搜索
        if use_named_vectors:
            # 对于命名向量，需要指定向量名称
            search_result = self.client.search(
                collection_name=collection_name,
                query_vector=("dense", query_vector),  # 使用元组格式指定向量名称和向量
                limit=top_k,
                score_threshold=score_threshold
            )
        else:
            # 对于非命名向量，使用普通搜索
            search_result = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=top_k,
                score_threshold=score_threshold
            )
        
        # 转换结果格式
        results = []
        for scored_point in search_result:
            result = {
                "id": scored_point.id,
                "score": scored_point.score,
                "payload": scored_point.payload
            }
            results.append(result)
        
        return results
    
    async def hybrid_search(
        self,
        collection_name: str,
        query_vector: List[float],
        query_sparse_vector: Optional[Dict[str, Any]] = None,
        top_k: int = 5,
        score_threshold: float = 0.0,
        fusion: str = "rrf"
    ) -> List[Dict[str, Any]]:
        """
        Qdrant原生混合检索（稠密向量+稀疏向量）
        
        Args:
            collection_name: 集合名称
            query_vector: 稠密查询向量
            query_sparse_vector: 稀疏查询向量 (indices和values的字典)
            top_k: 返回数量
            score_threshold: 分数阈值
            fusion: 融合方法 ("rrf" 或 "dbsf")
            
        Returns:
            检索结果列表
        """
        try:
            from qdrant_client.models import Fusion, Prefetch
        except ImportError:
            # 如果Qdrant客户端版本不支持混合检索，回退到普通向量检索
            return await self.search(collection_name, query_vector, top_k, score_threshold)
        
        # 构建预取查询
        prefetch = [
            Prefetch(
                query=query_vector,
                using="dense",  # 假设稠密向量使用"dense"名称
                limit=top_k * 2  # 获取更多候选结果
            )
        ]
        
        # 如果提供了稀疏向量，添加稀疏向量预取查询
        if query_sparse_vector and "indices" in query_sparse_vector and "values" in query_sparse_vector:
            try:
                from qdrant_client.models import SparseVector
                sparse_vector = SparseVector(
                    indices=query_sparse_vector["indices"],
                    values=query_sparse_vector["values"]
                )
                prefetch.append(
                    Prefetch(
                        query=sparse_vector,
                        using="sparse",  # 假设稀疏向量使用"sparse"名称
                        limit=top_k * 2
                    )
                )
            except Exception:
                # 如果稀疏向量格式不正确，忽略稀疏向量检索
                pass
        
        # 执行混合检索
        try:
            # 根据融合方法选择相应的Fusion类型
            fusion_type = Fusion.RRF if fusion.lower() == "rrf" else Fusion.DBSF
            
            search_result = self.client.query_points(
                collection_name=collection_name,
                prefetch=prefetch,
                query=fusion_type,
                limit=top_k,
                score_threshold=score_threshold
            )
            
            # 转换结果格式
            results = []
            for scored_point in search_result.points:
                result = {
                    "id": scored_point.id,
                    "score": scored_point.score,
                    "payload": scored_point.payload
                }
                results.append(result)
            
            return results
        except Exception as e:
            # 如果混合检索失败，回退到普通向量检索
            print(f"Hybrid search failed, falling back to vector search: {e}")
            return await self.search(collection_name, query_vector, top_k, score_threshold)
    
    async def delete_vectors(self, collection_name: str, ids: List[str]):
        """删除向量"""
        # 处理ID格式以适配Qdrant的要求
        processed_ids = []
        for id_str in ids:
            try:
                # 尝试转换为整数
                int_id = int(id_str)
                if int_id >= 0:  # 确保是非负整数
                    processed_ids.append(int_id)
                else:
                    # 负数使用原字符串
                    processed_ids.append(id_str)
            except ValueError:
                # 不是数字，验证是否为有效的UUID格式
                try:
                    uuid.UUID(id_str)
                    processed_ids.append(id_str)
                except ValueError:
                    # 不是有效的UUID，跳过这个ID
                    continue
        
        # 使用filter方式删除，通过ID匹配
        from qdrant_client.models import Filter, FieldCondition, MatchAny
        try:
            self.client.delete(
                collection_name=collection_name,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="id",
                            match=MatchAny(any=processed_ids)
                        )
                    ]
                )
            )
        except Exception as e:
            # 如果filter方式失败，尝试直接传入ID列表
            self.client.delete(
                collection_name=collection_name,
                points_selector=processed_ids  # type: ignore
            )


class MilvusService(BaseVectorDBService):
    """
    Milvus向量数据库服务
    """
    
    def __init__(self):
        # 尝试导入 Milvus 客户端
        try:
            import importlib
            self.pymilvus = importlib.import_module('pymilvus')
            self.MILVUS_AVAILABLE = True
        except ImportError:
            self.MILVUS_AVAILABLE = False
            print("Warning: pymilvus not installed. Milvus functionality will be disabled.")
            return
        
        self.host = settings.MILVUS_HOST
        self.port = settings.MILVUS_PORT
        
        # 连接 Milvus
        try:
            self.pymilvus.connections.connect("default", host=self.host, port=self.port)
        except Exception as e:
            print(f"Warning: Failed to connect to Milvus: {e}")
    
    async def create_collection(self, collection_name: str, dimension: int, **kwargs):
        """创建Milvus集合"""
        if not self.MILVUS_AVAILABLE:
            raise ImportError("pymilvus is not installed. Please install it with: pip install pymilvus")
        
        # 删除已存在的集合
        if self.pymilvus.utility.has_collection(collection_name):
            self.pymilvus.utility.drop_collection(collection_name)
        
        # 获取schema字段定义（如果提供）
        schema_fields = kwargs.get('schema_fields', [])
        
        # 定义字段
        fields = [
            self.pymilvus.FieldSchema(name="id", dtype=self.pymilvus.DataType.INT64, is_primary=True, auto_id=False),
            self.pymilvus.FieldSchema(name="vector", dtype=self.pymilvus.DataType.FLOAT_VECTOR, dim=dimension)
        ]
        
        # 根据schema定义添加标量字段
        for field in schema_fields:
            field_name = field["name"]
            field_type = field["type"]
            
            # 跳过向量字段，因为我们已经定义了主向量字段
            if field.get("isVectorIndex"):
                continue
            
            # 根据字段类型添加字段
            if field_type == "text" or field_type == "keyword":
                fields.append(self.pymilvus.FieldSchema(name=field_name, dtype=self.pymilvus.DataType.VARCHAR, max_length=65535))
            elif field_type == "number":
                fields.append(self.pymilvus.FieldSchema(name=field_name, dtype=self.pymilvus.DataType.INT64))
            elif field_type == "boolean":
                fields.append(self.pymilvus.FieldSchema(name=field_name, dtype=self.pymilvus.DataType.BOOL))
            elif field_type == "array":
                # Milvus对数组的支持有限，我们将其作为VARCHAR存储
                fields.append(self.pymilvus.FieldSchema(name=field_name, dtype=self.pymilvus.DataType.VARCHAR, max_length=65535))
        
        # 创建集合schema
        schema = self.pymilvus.CollectionSchema(fields=fields, description=f"Collection for {collection_name}")
        
        # 创建集合
        collection = self.pymilvus.Collection(name=collection_name, schema=schema)
        
        # 为标量字段创建索引
        for field in schema_fields:
            if field.get("isIndexed") and not field.get("isVectorIndex"):
                field_name = field["name"]
                field_type = field["type"]
                
                # 为标量字段创建索引
                if field_type == "text" or field_type == "keyword":
                    # 为VARCHAR字段创建索引
                    index_params = {
                        "index_type": "Trie",
                        "metric_type": "HAMMING"
                    }
                    collection.create_index(field_name=field_name, index_params=index_params)
                elif field_type == "number":
                    # 为数值字段创建索引
                    index_params = {
                        "index_type": "STL_SORT",
                        "metric_type": "HAMMING"
                    }
                    collection.create_index(field_name=field_name, index_params=index_params)
        
        # 为向量字段创建索引
        index_params = {
            "index_type": "IVF_FLAT",
            "metric_type": "L2",
            "params": {"nlist": 128}
        }
        collection.create_index(field_name="vector", index_params=index_params)
        
        # 加载集合
        collection.load()
    
    async def delete_collection(self, collection_name: str):
        """删除集合"""
        if not self.MILVUS_AVAILABLE:
            raise ImportError("pymilvus is not installed. Please install it with: pip install pymilvus")
        
        try:
            if self.pymilvus.utility.has_collection(collection_name):
                self.pymilvus.utility.drop_collection(collection_name)
        except Exception:
            # 集合不存在或删除失败，忽略错误
            pass
    
    async def insert_vectors(
        self,
        collection_name: str,
        vectors: Sequence[Union[List[float], Dict[str, Any]]],  # 支持稠密向量和稀疏向量
        metadatas: List[Dict[str, Any]],
        ids: List[str]
    ):
        """插入向量"""
        if not self.MILVUS_AVAILABLE:
            raise ImportError("pymilvus is not installed. Please install it with: pip install pymilvus")
        
        # 获取集合
        collection = self.pymilvus.Collection(collection_name)
        
        # 准备数据
        data = []
        # ID字段
        int_ids = [int(hash(id) % (2**63 - 1)) for id in ids]  # Milvus需要int64类型的ID
        data.append(int_ids)
        # 向量字段 - 只处理稠密向量
        dense_vectors = []
        for vector in vectors:
            if isinstance(vector, list):
                dense_vectors.append(vector)
            elif isinstance(vector, dict) and "dense" in vector:
                dense_vectors.append(vector["dense"])
            else:
                # 如果不是稠密向量格式，添加一个空向量
                dense_vectors.append([])
        data.append(dense_vectors)
        
        # 获取schema中的字段定义
        schema = collection.schema
        field_names = [field.name for field in schema.fields if field.name not in ["id", "vector"]]
        
        # 为每个标量字段准备数据
        for field_name in field_names:
            field_data = []
            for metadata in metadatas:
                value = metadata.get(field_name, "")
                # 根据字段类型处理值
                field_schema = next((f for f in schema.fields if f.name == field_name), None)
                if field_schema:
                    if field_schema.dtype == self.pymilvus.DataType.INT64:
                        field_data.append(int(value) if isinstance(value, (int, float)) else 0)
                    elif field_schema.dtype == self.pymilvus.DataType.BOOL:
                        field_data.append(bool(value) if isinstance(value, bool) else False)
                    else:  # VARCHAR类型
                        field_data.append(str(value))
                else:
                    field_data.append(str(value))
            data.append(field_data)
        
        # 插入数据
        collection.insert(data)
        
        # 刷新集合
        collection.flush()
    
    async def search(
        self,
        collection_name: str,
        query_vector: List[float],
        top_k: int = 5,
        score_threshold: float = 0.0
    ) -> List[Dict[str, Any]]:
        """检索"""
        if not self.MILVUS_AVAILABLE:
            raise ImportError("pymilvus is not installed. Please install it with: pip install pymilvus")
        
        # 获取集合
        collection = self.pymilvus.Collection(collection_name)
        
        # 执行搜索
        search_params = {
            "metric_type": "L2",
            "params": {"nprobe": 10}
        }
        
        results = collection.search(
            data=[query_vector],
            anns_field="vector",
            param=search_params,
            limit=top_k,
            expr=None,
            output_fields=["id"] + [field.name for field in collection.schema.fields if field.name not in ["vector"]],
            consistency_level="Strong"
        )
        
        # 转换结果格式
        search_results = []
        for result in results:
            for hit in result:
                search_result = {
                    "id": hit.id,
                    "score": hit.score,
                    "payload": {}
                }
                # 添加其他字段
                for field_name in hit.fields:
                    if field_name != "vector":
                        search_result["payload"][field_name] = hit.fields[field_name]
                search_results.append(search_result)
        
        return search_results
    
    async def hybrid_search(
        self,
        collection_name: str,
        query_vector: List[float],
        query_sparse_vector: Optional[Dict[str, Any]] = None,
        top_k: int = 5,
        score_threshold: float = 0.0,
        fusion: str = "rrf"
    ) -> List[Dict[str, Any]]:
        """
        Milvus混合检索（默认实现回退到普通向量检索）
        Milvus目前不原生支持混合检索，需要通过RRF等方式实现
        """
        # Milvus目前不原生支持混合检索，回退到普通向量检索
        return await self.search(collection_name, query_vector, top_k, score_threshold)
    
    async def delete_vectors(self, collection_name: str, ids: List[str]):
        """删除向量"""
        if not self.MILVUS_AVAILABLE:
            raise ImportError("pymilvus is not installed. Please install it with: pip install pymilvus")
        
        # 获取集合
        collection = self.pymilvus.Collection(collection_name)
        
        # 转换ID为int64类型
        int_ids = [int(hash(id) % (2**63 - 1)) for id in ids]
        
        # 删除数据
        expr = f"id in {int_ids}"
        collection.delete(expr=expr)
        
        # 刷新集合
        collection.flush()


class VectorDBServiceFactory:
    """向量数据库服务工厂"""
    
    @staticmethod
    def create(db_type: VectorDBType) -> BaseVectorDBService:
        """
        创建向量数据库服务实例
        
        Args:
            db_type: 数据库类型
        
        Returns:
            向量数据库服务实例
        """
        if db_type == VectorDBType.ELASTICSEARCH:
            return ElasticsearchService()
        elif db_type == VectorDBType.QDRANT:
            return QdrantService()
        elif db_type == VectorDBType.MILVUS:
            return MilvusService()
        else:
            raise ValueError(f"不支持的向量数据库类型: {db_type}")
