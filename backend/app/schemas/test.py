"""
测试相关的请求和响应Schema
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from app.models.test import TestType, TestStatus


class TestSetCreate(BaseModel):
    """创建测试集请求"""
    
    name: str = Field(..., description="测试集名称", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="测试集描述", max_length=500)
    kb_id: str = Field(..., description="关联知识库ID")
    test_type: TestType = Field(..., description="测试类型")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Python问答测试集",
                "description": "测试Python相关问题的检索效果",
                "kb_id": "kb_001",
                "test_type": "retrieval"
            }
        }


class TestSetUpdate(BaseModel):
    """更新测试集请求"""
    
    name: Optional[str] = Field(None, description="测试集名称", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="测试集描述", max_length=500)


class TestSetResponse(BaseModel):
    """测试集响应"""
    
    id: str
    name: str
    description: Optional[str]
    kb_id: str
    test_type: TestType
    case_count: int
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


class TestCaseCreate(BaseModel):
    """创建测试用例请求"""
    
    test_set_id: str = Field(..., description="所属测试集ID")
    query: str = Field(..., description="测试问题/查询", min_length=1)
    expected_chunks: Optional[List[str]] = Field(
        None,
        description="期望检索到的文档分块ID列表"
    )
    expected_answer: Optional[str] = Field(None, description="期望的答案")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="测试用例元数据")
    
    class Config:
        json_schema_extra = {
            "example": {
                "test_set_id": "ts_001",
                "query": "Python中如何定义一个类？",
                "expected_chunks": ["chunk_010", "chunk_011"],
                "expected_answer": "在Python中使用class关键字定义类..."
            }
        }


class TestCaseUpdate(BaseModel):
    """更新测试用例请求"""
    
    query: Optional[str] = Field(None, description="测试问题/查询", min_length=1)
    expected_chunks: Optional[List[str]] = Field(None, description="期望检索到的文档分块ID列表")
    expected_answer: Optional[str] = Field(None, description="期望的答案")
    metadata: Optional[Dict[str, Any]] = Field(None, description="测试用例元数据")


class TestCaseResponse(BaseModel):
    """测试用例响应"""
    
    id: str
    test_set_id: str
    kb_id: str
    query: str
    expected_chunks: Optional[List[str]]
    expected_answer: Optional[str]
    metadata: Dict[str, Any]
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


class RunRetrievalTestRequest(BaseModel):
    """执行检索测试请求"""
    
    test_case_id: Optional[str] = Field(None, description="单个测试用例ID")
    test_set_id: Optional[str] = Field(None, description="测试集ID（批量测试）")
    top_k: int = Field(10, description="检索返回的top-k数量", ge=1, le=100)
    score_threshold: Optional[float] = Field(None, description="相似度分数阈值")


class RetrievalTestResultResponse(BaseModel):
    """检索测试结果响应"""
    
    id: str
    test_case_id: str
    test_set_id: str
    kb_id: str
    query: str
    retrieved_chunks: List[Dict[str, Any]]
    retrieval_time: float
    precision: Optional[float]
    recall: Optional[float]
    f1_score: Optional[float]
    mrr: Optional[float]
    map_score: Optional[float]
    ndcg: Optional[float]
    hit_rate: Optional[float]
    status: TestStatus
    created_at: str
    
    class Config:
        from_attributes = True


class RunGenerationTestRequest(BaseModel):
    """执行生成测试请求"""
    
    test_case_id: Optional[str] = Field(None, description="单个测试用例ID")
    test_set_id: Optional[str] = Field(None, description="测试集ID（批量测试）")
    llm_model: Optional[str] = Field(None, description="使用的LLM模型")


class GenerationTestResultResponse(BaseModel):
    """生成测试结果响应"""
    
    id: str
    test_case_id: str
    test_set_id: str
    kb_id: str
    query: str
    retrieved_chunks: List[Dict[str, Any]]
    generated_answer: str
    generation_time: float
    relevance_score: Optional[float]
    coherence_score: Optional[float]
    faithfulness_score: Optional[float]
    llm_model: Optional[str]
    status: TestStatus
    created_at: str
    
    class Config:
        from_attributes = True


# ========== 检索器评估相关 ==========

class ImportT2RankingDatasetRequest(BaseModel):
    """导入T2Ranking数据集请求"""
    
    kb_id: str = Field(..., description="目标知识库ID")
    test_set_name: str = Field(..., description="测试集名称")
    collection_path: str = Field(..., description="文档集合文件路径")
    queries_path: str = Field(..., description="查询文件路径")
    qrels_path: str = Field(..., description="相关性标注文件路径")
    max_docs: Optional[int] = Field(None, description="最大文档数量限制", ge=1)
    max_queries: Optional[int] = Field(None, description="最大查询数量限制", ge=1)
    description: Optional[str] = Field(None, description="测试集描述")
    
    class Config:
        json_schema_extra = {
            "example": {
                "kb_id": "kb_t2ranking",
                "test_set_name": "T2Ranking检索测试集",
                "collection_path": "/path/to/collection.tsv",
                "queries_path": "/path/to/queries.dev.tsv",
                "qrels_path": "/path/to/qrels.dev.tsv",
                "max_docs": 10000,
                "max_queries": 100,
                "description": "T2Ranking数据集的开发集"
            }
        }


class RetrieverEvaluationRequest(BaseModel):
    """检索器评估请求"""
    
    kb_id: str = Field(..., description="知识库ID")
    test_set_id: str = Field(..., description="测试集ID")
    top_k: int = Field(10, description="检索返回的top-k数量", ge=1, le=100)
    vector_db_type: Optional[str] = Field(None, description="向量数据库类型")
    embedding_provider: Optional[str] = Field(None, description="向量模型提供商")
    embedding_model: Optional[str] = Field(None, description="向量模型名称")
    retrieval_algorithm: Optional[str] = Field(None, description="检索算法配置")
    
    class Config:
        json_schema_extra = {
            "example": {
                "kb_id": "kb_001",
                "test_set_id": "ts_001",
                "top_k": 10,
                "vector_db_type": "elasticsearch",
                "embedding_provider": "ollama",
                "embedding_model": "nomic-embed-text"
            }
        }


class RetrieverEvaluationResultResponse(BaseModel):
    """检索器评估结果响应"""
    
    evaluation_id: str
    kb_id: str
    test_set_id: str
    total_queries: int
    successful_queries: int
    failed_queries: int
    overall_metrics: Dict[str, float]
    config: Dict[str, Any]
    created_at: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "evaluation_id": "eval_001",
                "kb_id": "kb_001",
                "test_set_id": "ts_001",
                "total_queries": 100,
                "successful_queries": 98,
                "failed_queries": 2,
                "overall_metrics": {
                    "precision": 0.85,
                    "recall": 0.78,
                    "f1_score": 0.81,
                    "mrr": 0.89,
                    "map": 0.82,
                    "ndcg": 0.87,
                    "hit_rate": 0.95
                },
                "config": {
                    "top_k": 10,
                    "vector_db_type": "elasticsearch",
                    "embedding_model": "nomic-embed-text"
                },
                "created_at": "2025-11-07T10:00:00"
            }
        }


class DatasetStatisticsResponse(BaseModel):
    """数据集统计信息响应"""
    
    total_documents: int
    total_queries: int
    total_query_doc_pairs: int
    queries_with_relevant_docs: int
    avg_relevant_docs_per_query: float
    max_relevant_docs: int
    min_relevant_docs: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_documents": 8841,
                "total_queries": 367,
                "total_query_doc_pairs": 23573,
                "queries_with_relevant_docs": 367,
                "avg_relevant_docs_per_query": 64.23,
                "max_relevant_docs": 500,
                "min_relevant_docs": 1
            }
        }
