"""
测试相关数据模型
"""

from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import Field
from datetime import datetime

from app.models.base import BaseModelMixin


class TestType(str, Enum):
    """测试类型"""
    RETRIEVAL = "retrieval"    # 检索测试
    GENERATION = "generation"  # 生成测试


class TestStatus(str, Enum):
    """测试状态"""
    PENDING = "pending"        # 待执行
    RUNNING = "running"        # 执行中
    COMPLETED = "completed"    # 已完成
    FAILED = "failed"          # 失败


class TestSet(BaseModelMixin):
    """测试集模型"""
    
    name: str = Field(..., description="测试集名称", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="测试集描述", max_length=500)
    
    kb_id: Optional[str] = Field(None, description="关联知识库ID（已废弃，保留用于兼容）")
    test_type: TestType = Field(..., description="测试类型")
    
    # 统计信息
    case_count: int = Field(default=0, description="测试用例数量")
    
    # 配置快照（已废弃，现在保存在TestSetKnowledgeBase中）
    kb_config: Dict[str, Any] = Field(
        default_factory=dict,
        description="知识库配置快照（已废弃）"
    )
    chunking_config: Dict[str, Any] = Field(
        default_factory=dict,
        description="分块策略配置（已废弃）"
    )
    embedding_config: Dict[str, Any] = Field(
        default_factory=dict,
        description="嵌入模型参数配置（已废弃）"
    )
    sparse_vector_config: Dict[str, Any] = Field(
        default_factory=dict,
        description="稀疏向量参数配置（已废弃）"
    )
    index_config: Dict[str, Any] = Field(
        default_factory=dict,
        description="索引配置（已废弃）"
    )


class TestSetKnowledgeBase(BaseModelMixin):
    """测试集-知识库关联模型"""
    
    test_set_id: str = Field(..., description="测试集ID")
    kb_id: str = Field(..., description="知识库ID")
    imported_at: datetime = Field(..., description="导入时间")
    import_config: Dict[str, Any] = Field(
        default_factory=dict,
        description="导入时的配置快照（知识库完整配置）"
    )
    kb_deleted: bool = Field(default=False, description="知识库是否已删除")
    test_set_deleted: bool = Field(default=False, description="测试集是否已删除")


class ImportTask(BaseModelMixin):
    """导入任务模型"""
    
    test_set_id: str = Field(..., description="测试集ID")
    kb_id: str = Field(..., description="知识库ID")
    status: str = Field(default="pending", description="任务状态：pending/running/completed/failed")
    progress: float = Field(default=0.0, description="进度（0.0-1.0）", ge=0.0, le=1.0)
    total_docs: int = Field(default=0, description="总文档数")
    imported_docs: int = Field(default=0, description="已导入文档数")
    failed_docs: int = Field(default=0, description="失败文档数")
    error_message: Optional[str] = Field(None, description="错误信息")
    import_config: Dict[str, Any] = Field(default_factory=dict, description="导入配置")
    started_at: Optional[datetime] = Field(None, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "ts_001",
                "name": "t2ranking_seed42_1000",
                "description": "T2Ranking数据集，随机种子42，前1000个问题",
                "kb_id": "kb_001",
                "test_type": "retrieval",
                "case_count": 1000,
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


class TestCase(BaseModelMixin):
    """测试用例模型（已废弃，保留用于兼容性）"""
    
    test_set_id: str = Field(..., description="所属测试集ID")
    kb_id: str = Field(..., description="关联知识库ID")
    
    # 测试输入
    query: str = Field(..., description="测试问题/查询", min_length=1)
    
    # 期望输出（用于评估）
    expected_chunks: Optional[List[str]] = Field(
        None,
        description="期望检索到的文档分块ID列表"
    )
    expected_answer: Optional[str] = Field(None, description="期望的答案")
    
    # 元数据
    metadata: Dict[str, Any] = Field(default_factory=dict, description="测试用例元数据")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "tc_001",
                "test_set_id": "ts_001",
                "kb_id": "kb_001",
                "query": "Python中如何定义一个类？",
                "expected_chunks": ["chunk_010", "chunk_011"],
                "expected_answer": "在Python中使用class关键字定义类..."
            }
        }


class ExpectedAnswer(BaseModelMixin):
    """期望答案模型（嵌套在RetrieverTestCase中）"""
    
    answer_text: str = Field(..., description="答案文本内容")
    chunk_id: Optional[str] = Field(None, description="关联的分块ID")
    relevance_score: float = Field(1.0, description="关联度分数（0.0-1.0）", ge=0.0, le=1.0)
    
    class Config:
        json_schema_extra = {
            "example": {
                "answer_text": "在Python中使用class关键字定义类",
                "chunk_id": "chunk_001",
                "relevance_score": 1.0
            }
        }


class RetrieverTestCase(BaseModelMixin):
    """检索器测试用例模型"""
    
    test_set_id: str = Field(..., description="所属测试集ID")
    question: str = Field(..., description="问题文本内容", min_length=1)
    expected_answers: List[Dict[str, Any]] = Field(
        ...,
        description="期望答案列表",
        min_items=1
    )
    metadata: Dict[str, Any] = Field(default_factory=dict, description="用例元数据")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "rtc_abc123",
                "test_set_id": "ts_001",
                "question": "Python中如何定义一个类？",
                "expected_answers": [
                    {
                        "answer_text": "在Python中使用class关键字定义类",
                        "chunk_id": "chunk_001",
                        "relevance_score": 1.0
                    },
                    {
                        "answer_text": "类是面向对象编程的基础",
                        "chunk_id": "chunk_002",
                        "relevance_score": 0.8
                    }
                ],
                "metadata": {"source": "tutorial", "difficulty": "easy"}
            }
        }


class GenerationTestCase(BaseModelMixin):
    """生成测试用例模型"""
    
    test_set_id: str = Field(..., description="所属测试集ID")
    question: str = Field(..., description="测试问题", min_length=1)
    reference_answer: str = Field(..., description="参考答案（用于RAGAS评估）")
    reference_contexts: List[str] = Field(
        default_factory=list,
        description="参考上下文列表（golden contexts）"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict, description="用例元数据")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "gtc_xyz789",
                "test_set_id": "ts_002",
                "question": "如何定义Python类？",
                "reference_answer": "在Python中使用class关键字...",
                "reference_contexts": ["上下文1", "上下文2"],
                "metadata": {"difficulty": "easy"}
            }
        }


class RetrieverEvaluationResult(BaseModelMixin):
    """检索器评估结果模型"""
    
    evaluation_task_id: str = Field(..., description="评估任务ID")
    test_case_id: str = Field(..., description="测试用例ID（RetrieverTestCase）")
    question: str = Field(..., description="问题文本（冗余存储便于查询）")
    expected_answers: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="期望答案列表（结构同测试用例）"
    )
    retrieved_results: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="检索到的结果列表"
    )
    retrieval_time: float = Field(..., description="检索耗时（秒）")
    
    # 评估指标
    precision: Optional[float] = Field(None, description="精确率", ge=0.0, le=1.0)
    recall: Optional[float] = Field(None, description="召回率", ge=0.0, le=1.0)
    f1_score: Optional[float] = Field(None, description="F1分数", ge=0.0, le=1.0)
    mrr: Optional[float] = Field(None, description="平均倒数排名", ge=0.0, le=1.0)
    map_score: Optional[float] = Field(None, description="平均精度均值", ge=0.0, le=1.0)
    ndcg: Optional[float] = Field(None, description="归一化折损累积增益", ge=0.0, le=1.0)
    hit_rate: Optional[float] = Field(None, description="命中率", ge=0.0, le=1.0)
    
    status: TestStatus = Field(default=TestStatus.COMPLETED, description="评估状态")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "rer_001",
                "evaluation_task_id": "et_001",
                "test_case_id": "rtc_abc123",
                "question": "Python中如何定义一个类？",
                "expected_answers": [
                    {"answer_text": "在Python中使用class关键字定义类", "chunk_id": "chunk_001", "relevance_score": 1.0}
                ],
                "retrieved_results": [
                    {"chunk_id": "chunk_001", "chunk_text": "...", "score": 0.95, "rank": 1, "matched": True}
                ],
                "retrieval_time": 0.15,
                "precision": 0.9,
                "recall": 0.85,
                "f1_score": 0.87
            }
        }


class GenerationEvaluationResult(BaseModelMixin):
    """生成评估结果模型"""
    
    evaluation_task_id: str = Field(..., description="评估任务ID")
    test_case_id: str = Field(..., description="测试用例ID（GenerationTestCase）")
    question: str = Field(..., description="问题（冗余存储便于查询）")
    
    # 检索上下文
    retrieved_contexts: List[str] = Field(
        default_factory=list,
        description="检索到的上下文列表"
    )
    
    # 生成结果
    generated_answer: str = Field(..., description="生成的答案")
    
    # 时间统计
    retrieval_time: float = Field(..., description="检索耗时（秒）")
    generation_time: float = Field(..., description="生成耗时（秒）")
    
    # RAGAS评估指标
    ragas_metrics: Dict[str, Any] = Field(
        default_factory=dict,
        description="RAGAS评估指标集合（faithfulness, answer_relevancy, context_precision等）"
    )
    
    # LLM配置
    llm_model: Optional[str] = Field(None, description="使用的LLM模型")
    
    # 状态
    status: TestStatus = Field(default=TestStatus.COMPLETED, description="评估状态")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "ger_001",
                "evaluation_task_id": "et_002",
                "test_case_id": "gtc_xyz789",
                "question": "如何定义Python类？",
                "retrieved_contexts": ["上下文1", "上下文2"],
                "generated_answer": "在Python中使用class关键字...",
                "retrieval_time": 0.12,
                "generation_time": 2.5,
                "ragas_metrics": {
                    "faithfulness": 0.85,
                    "answer_relevancy": 0.80,
                    "context_precision": 0.83,
                    "context_recall": 0.78,
                    "context_relevancy": 0.82,
                    "answer_similarity": 0.88,
                    "answer_correctness": 0.86
                },
                "llm_model": "qwen2:7b",
                "status": "completed"
            }
        }



