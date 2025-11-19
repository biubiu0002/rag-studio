"""
评估相关的请求和响应Schema
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class CreateEvaluationTaskRequest(BaseModel):
    """创建评估任务请求"""
    test_set_id: str = Field(..., description="测试集ID")
    kb_id: str = Field(..., description="知识库ID")
    evaluation_type: str = Field(..., description="评估类型: retrieval, generation")
    task_name: Optional[str] = Field(None, description="任务名称")
    retrieval_config: Optional[Dict[str, Any]] = Field(None, description="检索配置")
    generation_config: Optional[Dict[str, Any]] = Field(None, description="生成配置")


class ExecuteEvaluationTaskRequest(BaseModel):
    """执行评估任务请求"""
    save_detailed_results: bool = Field(True, description="是否保存详细结果")

