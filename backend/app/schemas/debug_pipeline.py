"""
链路调试相关的请求和响应Schema
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


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
    provider: str = Field("ollama", description="Embedding服务提供商: ollama, custom")
    service_url: Optional[str] = Field(None, description="自定义服务地址（用于Ollama或自定义提供商）")
    api_key: Optional[str] = Field(None, description="API密钥（用于自定义提供商）")


class UnifiedSearchRequest(BaseModel):
    """统一检索请求"""
    kb_id: str = Field(..., description="知识库ID")
    query: str = Field(..., description="查询文本")
    retrieval_mode: str = Field("hybrid", description="检索模式: semantic, keyword, hybrid")
    top_k: int = Field(10, description="返回数量")
    fusion_method: str = Field("rrf", description="混合检索融合方法: rrf, weighted")
    rrf_k: int = Field(60, description="RRF参数k", ge=1)
    semantic_weight: float = Field(0.7, description="语义向量权重（加权平均时使用）", ge=0, le=1)
    keyword_weight: float = Field(0.3, description="关键词权重（加权平均时使用）", ge=0, le=1)
    score_threshold: float = Field(0.0, description="分数阈值", ge=0, le=1)


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


class QdrantHybridSearchRequest(BaseModel):
    """Qdrant混合检索请求"""
    kb_id: str = Field(..., description="知识库ID")
    query: str = Field(..., description="查询文本")
    query_vector: Optional[List[float]] = Field(None, description="查询向量（如果提供则直接使用）")
    query_sparse_vector: Optional[Dict[str, Any]] = Field(None, description="稀疏查询向量（indices和values）")
    top_k: int = Field(10, description="返回数量")
    score_threshold: float = Field(0.0, description="分数阈值", ge=0, le=1)
    fusion: str = Field("rrf", description="融合方法: rrf, dbsf")
    embedding_model: str = Field("bge-m3:latest", description="Embedding模型")
    generate_sparse_vector: bool = Field(True, description="是否自动生成稀疏向量（使用SPLADE等模型）")


class SparseVectorRequest(BaseModel):
    """稀疏向量生成请求"""
    kb_id: str = Field(..., description="知识库ID")
    text: str = Field(..., description="输入文本")
    method: str = Field("bm25", description="稀疏向量生成方法: bm25, tf-idf, simple, splade")


class WriteVectorIndexRequest(BaseModel):
    """写入向量索引请求"""
    kb_id: str = Field(..., description="知识库ID")
    chunks: List[Dict[str, Any]] = Field(..., description="分块数据列表")
    vectors: List[List[float]] = Field(..., description="向量列表")
    fields: Optional[List[str]] = Field(None, description="要写入的字段列表")


class WriteKeywordIndexRequest(BaseModel):
    """写入关键词索引请求"""
    kb_id: str = Field(..., description="知识库ID")
    chunks: List[Dict[str, Any]] = Field(..., description="分块数据列表")
    tokens_list: List[List[str]] = Field(..., description="分词结果列表")
    fields: Optional[List[str]] = Field(None, description="要写入的字段列表")


class WriteSparseVectorIndexRequest(BaseModel):
    """写入稀疏向量索引请求"""
    kb_id: str = Field(..., description="知识库ID")
    chunks: List[Dict[str, Any]] = Field(..., description="分块数据列表")
    sparse_vectors: List[Dict[str, Any]] = Field(..., description="稀疏向量列表，每个元素包含indices和values")
    fields: Optional[List[str]] = Field(None, description="要写入的字段列表")


class WriteHybridIndexRequest(BaseModel):
    """写入混合索引请求（同时支持稠密向量和稀疏向量）"""
    kb_id: str = Field(..., description="知识库ID")
    chunks: List[Dict[str, Any]] = Field(..., description="分块数据列表")
    dense_vectors: Optional[List[List[float]]] = Field(None, description="稠密向量列表")
    sparse_vectors: Optional[List[Dict[str, Any]]] = Field(None, description="稀疏向量列表，每个元素包含indices和values")
    fields: Optional[List[str]] = Field(None, description="要写入的字段列表")


class SaveDebugResultRequest(BaseModel):
    """保存调试结果请求"""
    name: str = Field(..., description="结果名称")
    type: str = Field(..., description="结果类型: chunks, embeddings, tokens, index_data, schemas, knowledge_bases")
    data: Dict[str, Any] = Field(..., description="结果数据")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")


class GenerationRequest(BaseModel):
    """生成请求"""
    query: str = Field(..., description="查询问题")
    context: Optional[str] = Field(None, description="上下文（可选，如果提供则直接使用）")
    kb_id: Optional[str] = Field(None, description="知识库ID（如果需要自动检索上下文）")
    stream: bool = Field(False, description="是否启用流式输出")
    llm_provider: str = Field("ollama", description="LLM服务提供商")
    llm_model: str = Field("deepseek-r1:1.5b", description="LLM模型")
    temperature: float = Field(0.7, description="生成参数：温度", ge=0, le=1)
    max_tokens: Optional[int] = Field(None, description="最大生成token数")


class GenerationResponse(BaseModel):
    """生成响应"""
    query: str = Field(..., description="查询问题")
    context: Optional[str] = Field(None, description="使用的上下文")
    answer: str = Field(..., description="生成的答案")
    generation_time: float = Field(..., description="生成耗时(秒)")
    llm_model: str = Field(..., description="使用的LLM模型")
    tokens_used: Optional[int] = Field(None, description="消耗的token数")

