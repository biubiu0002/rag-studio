"""
评估相关数据模型
"""

from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import Field
from datetime import datetime

from app.models.base import BaseModelMixin


class EvaluationType(str, Enum):
    """评估类型"""
    RETRIEVAL = "retrieval"    # 检索器评估
    GENERATION = "generation"  # 生成器评估


class EvaluationStatus(str, Enum):
    """评估状态"""
    PENDING = "pending"        # 待执行
    RUNNING = "running"        # 执行中
    COMPLETED = "completed"    # 已完成
    FAILED = "failed"          # 失败
    ARCHIVED = "archived"      # 已归档


class EvaluationTask(BaseModelMixin):
    """评估任务模型"""
    
    test_set_id: str = Field(..., description="测试集ID")
    kb_id: str = Field(..., description="知识库ID")
    evaluation_type: EvaluationType = Field(..., description="评估类型")
    task_name: Optional[str] = Field(None, description="任务名称", max_length=100)
    status: EvaluationStatus = Field(default=EvaluationStatus.PENDING, description="任务状态")
    
    # 配置信息
    retrieval_config: Dict[str, Any] = Field(
        default_factory=dict, 
        description="检索配置，包含 retrieval_mode, top_k, score_threshold, fusion_method, rrf_k, semantic_weight, keyword_weight"
    )
    generation_config: Dict[str, Any] = Field(default_factory=dict, description="生成配置")
    
    # 统计信息
    total_cases: int = Field(default=0, description="总测试用例数")
    completed_cases: int = Field(default=0, description="已完成用例数")
    failed_cases: int = Field(default=0, description="失败用例数")
    
    # 时间信息
    started_at: Optional[datetime] = Field(None, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "eval_task_001",
                "test_set_id": "ts_001",
                "kb_id": "kb_001",
                "evaluation_type": "retrieval",
                "task_name": "检索器评估-2025-01-15",
                "status": "completed",
                "retrieval_config": {
                    "retrieval_mode": "hybrid",
                    "top_k": 10,
                    "score_threshold": 0.0,
                    "fusion_method": "rrf",
                    "rrf_k": 60,
                    "semantic_weight": 0.7,
                    "keyword_weight": 0.3
                },
                "total_cases": 100,
                "completed_cases": 98,
                "failed_cases": 2
            }
        }


class EvaluationCaseResult(BaseModelMixin):
    """评估用例结果模型"""
    
    evaluation_task_id: str = Field(..., description="评估任务ID")
    test_case_id: str = Field(..., description="测试用例ID")
    query: str = Field(..., description="查询文本")
    
    # 检索结果
    retrieved_chunks: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="检索到的分块列表"
    )
    retrieval_time: Optional[float] = Field(None, description="检索耗时(秒)")
    
    # 生成结果
    generated_answer: Optional[str] = Field(None, description="生成的答案")
    generation_time: Optional[float] = Field(None, description="生成耗时(秒)")
    
    # 评估指标
    retrieval_metrics: Dict[str, float] = Field(
        default_factory=dict,
        description="检索评估指标（precision, recall, f1, mrr, map, ndcg, hit_rate等）"
    )
    ragas_retrieval_metrics: Dict[str, float] = Field(
        default_factory=dict,
        description="RAGAS检索指标（context_precision, context_recall, context_relevancy等）"
    )
    ragas_generation_metrics: Dict[str, float] = Field(
        default_factory=dict,
        description="RAGAS生成指标（faithfulness, answer_relevancy等）"
    )
    ragas_score: Optional[float] = Field(None, description="RAGAS综合评分", ge=0.0, le=1.0)
    
    # 状态
    status: EvaluationStatus = Field(default=EvaluationStatus.PENDING, description="状态")
    error_message: Optional[str] = Field(None, description="错误信息")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "eval_result_001",
                "evaluation_task_id": "eval_task_001",
                "test_case_id": "tc_001",
                "query": "Python中如何定义一个类？",
                "retrieved_chunks": [
                    {"chunk_id": "chunk_010", "score": 0.95, "content": "..."}
                ],
                "retrieval_time": 0.15,
                "retrieval_metrics": {
                    "precision": 0.9,
                    "recall": 0.85,
                    "f1_score": 0.87
                },
                "ragas_retrieval_metrics": {
                    "context_precision": 0.88,
                    "context_recall": 0.82
                },
                "ragas_score": 0.85
            }
        }


class EvaluationSummary(BaseModelMixin):
    """评估汇总模型"""
    
    evaluation_task_id: str = Field(..., description="评估任务ID")
    
    # 总体指标
    overall_retrieval_metrics: Dict[str, float] = Field(
        default_factory=dict,
        description="总体检索指标（平均值）"
    )
    overall_ragas_retrieval_metrics: Dict[str, float] = Field(
        default_factory=dict,
        description="总体RAGAS检索指标"
    )
    overall_ragas_generation_metrics: Dict[str, float] = Field(
        default_factory=dict,
        description="总体RAGAS生成指标"
    )
    overall_ragas_score: Optional[float] = Field(None, description="总体RAGAS综合评分", ge=0.0, le=1.0)
    
    # 指标分布
    metrics_distribution: Dict[str, Any] = Field(
        default_factory=dict,
        description="指标分布（最大值、最小值、标准差等）"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "eval_summary_001",
                "evaluation_task_id": "eval_task_001",
                "overall_retrieval_metrics": {
                    "precision": 0.85,
                    "recall": 0.78,
                    "f1_score": 0.81
                },
                "overall_ragas_retrieval_metrics": {
                    "context_precision": 0.82,
                    "context_recall": 0.75
                },
                "overall_ragas_score": 0.80,
                "metrics_distribution": {
                    "precision": {"min": 0.5, "max": 1.0, "std": 0.15}
                }
            }
        }

