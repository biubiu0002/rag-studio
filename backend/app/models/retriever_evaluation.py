"""
检索器评估相关数据模型
"""

from typing import Optional, Dict, Any
from pydantic import Field

from app.models.base import BaseModelMixin


class RetrieverEvaluationResult(BaseModelMixin):
    """检索器评估结果模型"""
    
    kb_id: str = Field(..., description="知识库ID")
    test_set_id: str = Field(..., description="测试集ID")
    
    # 评估统计
    total_queries: int = Field(..., description="总查询数")
    successful_queries: int = Field(..., description="成功执行的查询数")
    failed_queries: int = Field(..., description="失败的查询数")
    
    # 总体评估指标
    overall_metrics: Dict[str, float] = Field(
        default_factory=dict,
        description="总体评估指标（precision, recall, f1, mrr, map, ndcg, hit_rate）"
    )
    
    # 评估配置
    config: Dict[str, Any] = Field(
        default_factory=dict,
        description="评估配置（top_k, vector_db_type, embedding_model等）"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "eval_001",
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
                }
            }
        }

