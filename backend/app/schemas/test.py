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
    kb_id: Optional[str] = Field(None, description="关联知识库ID（已废弃，创建时不需要）")
    test_type: TestType = Field(..., description="测试类型")
    
    # 配置快照（已废弃，不再使用）
    kb_config: Optional[Dict[str, Any]] = Field(None, description="知识库配置快照（已废弃）")
    chunking_config: Optional[Dict[str, Any]] = Field(None, description="分块策略配置（已废弃）")
    embedding_config: Optional[Dict[str, Any]] = Field(None, description="嵌入模型参数配置（已废弃）")
    sparse_vector_config: Optional[Dict[str, Any]] = Field(None, description="稀疏向量参数配置（已废弃）")
    index_config: Optional[Dict[str, Any]] = Field(None, description="索引配置（已废弃）")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "t2ranking_seed42_1000",
                "description": "T2Ranking数据集，随机种子42，前1000个问题",
                "kb_id": "kb_001",
                "test_type": "retrieval",
                "kb_config": {
                    "vector_db_type": "qdrant",
                    "embedding_provider": "ollama",
                    "embedding_model": "bge-m3:latest"
                },
                "chunking_config": {
                    "method": "fixed_size",
                    "chunk_size": 500,
                    "chunk_overlap": 50
                }
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
    kb_id: Optional[str]  # 改为可选
    test_type: TestType
    case_count: int
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


class ImportTestSetToKnowledgeBaseRequest(BaseModel):
    """导入测试集到知识库请求"""
    
    kb_id: str = Field(..., description="目标知识库ID")
    update_existing: bool = Field(True, description="是否更新已存在的文档")
    
    class Config:
        json_schema_extra = {
            "example": {
                "kb_id": "kb_001",
                "update_existing": True
            }
        }


class ImportPreviewResponse(BaseModel):
    """导入预览响应"""
    
    total_answers: int = Field(..., description="总答案数")
    new_docs: int = Field(..., description="将新增的文档数")
    existing_docs: int = Field(..., description="已存在的文档数")
    skipped_docs: int = Field(default=0, description="将跳过的文档数")


class ImportTaskResponse(BaseModel):
    """导入任务响应"""
    
    id: str
    test_set_id: str
    kb_id: str
    status: str
    progress: float
    total_docs: int
    imported_docs: int
    failed_docs: int
    error_message: Optional[str]
    started_at: Optional[str]
    completed_at: Optional[str]
    created_at: str
    
    class Config:
        from_attributes = True


class TestSetKnowledgeBaseResponse(BaseModel):
    """测试集-知识库关联响应"""
    
    id: str
    test_set_id: str
    kb_id: str
    imported_at: str
    import_config: Dict[str, Any]
    kb_deleted: bool
    test_set_deleted: bool
    
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


# ========== 新的检索器测试用例API Schemas ==========

class ExpectedAnswerCreate(BaseModel):
    """期望答案创建Schema"""
    
    answer_text: str = Field(..., description="答案文本", min_length=1)
    chunk_id: Optional[str] = Field(None, description="关联的文档分块ID")
    relevance_score: float = Field(1.0, description="关联度分数（0.0-4.0）", ge=0.0, le=4.0)
    
    class Config:
        json_schema_extra = {
            "example": {
                "answer_text": "Python使用class关键字定义类",
                "chunk_id": "chunk_010",
                "relevance_score": 1.0
            }
        }


class RetrieverTestCaseCreate(BaseModel):
    """创建检索器测试用例请求"""
    
    test_set_id: str = Field(..., description="所属测试集ID")
    question: str = Field(..., description="问题文本内容", min_length=1)
    expected_answers: List[ExpectedAnswerCreate] = Field(
        ...,
        description="期望答案列表",
        min_items=1
    )
    metadata: Dict[str, Any] = Field(default_factory=dict, description="用例元数据")
    
    class Config:
        json_schema_extra = {
            "example": {
                "test_set_id": "ts_001",
                "question": "Python中如何定义一个类？",
                "expected_answers": [
                    {
                        "answer_text": "Python使用class关键字定义类",
                        "chunk_id": "chunk_010",
                        "relevance_score": 1.0
                    },
                    {
                        "answer_text": "类定义语法：class ClassName:",
                        "chunk_id": "chunk_011",
                        "relevance_score": 0.9
                    }
                ],
                "metadata": {"difficulty": "easy"}
            }
        }


class RetrieverTestCaseUpdate(BaseModel):
    """更新检索器测试用例请求"""
    
    question: Optional[str] = Field(None, description="问题文本内容", min_length=1)
    expected_answers: Optional[List[ExpectedAnswerCreate]] = Field(
        None,
        description="期望答案列表",
        min_items=1
    )
    metadata: Optional[Dict[str, Any]] = Field(None, description="用例元数据")


class RetrieverTestCaseResponse(BaseModel):
    """检索器测试用例响应"""
    
    id: str
    test_set_id: str
    question: str
    expected_answers: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


class RetrieverTestCaseBatchCreate(BaseModel):
    """批量创建检索器测试用例请求"""
    
    test_set_id: str = Field(..., description="所属测试集ID")
    cases: List[Dict[str, Any]] = Field(
        ...,
        description="测试用例列表",
        min_items=1
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "test_set_id": "ts_001",
                "cases": [
                    {
                        "question": "Python中如何定义类？",
                        "expected_answers": [
                            {
                                "answer_text": "使用class关键字",
                                "chunk_id": "chunk_010",
                                "relevance_score": 1.0
                            }
                        ],
                        "metadata": {}
                    }
                ]
            }
        }


class BatchDeleteRequest(BaseModel):
    """批量删除请求"""
    
    case_ids: List[str] = Field(..., description="待删除的用例ID列表", min_items=1)


class BatchOperationResponse(BaseModel):
    """批量操作响应"""
    
    success_count: int = Field(..., description="成功数量")
    failed_count: int = Field(..., description="失败数量")
    failed_items: List[Dict[str, Any]] = Field(default_factory=list, description="失败记录")


# ========== 生成测试用例API Schemas ==========

class GenerationTestCaseCreate(BaseModel):
    """创建生成测试用例请求"""
    
    test_set_id: str = Field(..., description="所属测试集ID")
    question: str = Field(..., description="问题文本内容", min_length=1)
    reference_answer: str = Field(..., description="参考答案", min_length=1)
    reference_contexts: List[str] = Field(
        default_factory=list,
        description="参考上下文列表"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict, description="用例元数据")
    
    class Config:
        json_schema_extra = {
            "example": {
                "test_set_id": "ts_002",
                "question": "什么是面向对象编程？",
                "reference_answer": "面向对象编程是一种编程范式...",
                "reference_contexts": [
                    "面向对象编程的核心概念包括封装、继承和多态",
                    "OOP是一种将数据和操作数据的方法组合在一起的编程方式"
                ],
                "metadata": {"difficulty": "medium"}
            }
        }


class GenerationTestCaseUpdate(BaseModel):
    """更新生成测试用例请求"""
    
    question: Optional[str] = Field(None, description="问题文本内容", min_length=1)
    reference_answer: Optional[str] = Field(None, description="参考答案", min_length=1)
    reference_contexts: Optional[List[str]] = Field(None, description="参考上下文列表")
    metadata: Optional[Dict[str, Any]] = Field(None, description="用例元数据")


class GenerationTestCaseResponse(BaseModel):
    """生成测试用例响应"""
    
    id: str
    test_set_id: str
    question: str
    reference_answer: str
    reference_contexts: List[str]
    metadata: Dict[str, Any]
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


class GenerationTestCaseBatchCreate(BaseModel):
    """批量创建生成测试用例请求"""
    
    test_set_id: str = Field(..., description="所属测试集ID")
    cases: List[Dict[str, Any]] = Field(
        ...,
        description="测试用例列表",
        min_items=1
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "test_set_id": "ts_002",
                "cases": [
                    {
                        "question": "什么是面向对象编程？",
                        "reference_answer": "面向对象编程是...",
                        "reference_contexts": ["上下文1", "上下文2"],
                        "metadata": {}
                    }
                ]
            }
        }


# ========== 评估结果API Schemas ==========

class RetrieverEvaluationResultDetailResponse(BaseModel):
    """检索器评估结果详情响应"""
    
    id: str
    evaluation_task_id: str
    test_case_id: str
    question: str
    expected_answers: List[Dict[str, Any]]
    retrieved_results: List[Dict[str, Any]]
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


class GenerationEvaluationResultDetailResponse(BaseModel):
    """生成评估结果详情响应"""
    
    id: str
    evaluation_task_id: str
    test_case_id: str
    question: str
    retrieved_contexts: List[str]
    generated_answer: str
    reference_answer: str
    reference_contexts: List[str]
    retrieval_time: float
    generation_time: float
    ragas_metrics: Dict[str, Any]
    ragas_score: Optional[float]
    llm_model: Optional[str]
    status: TestStatus
    created_at: str
    
    class Config:
        from_attributes = True
