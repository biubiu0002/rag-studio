"""
任务队列数据模型
"""

from typing import Optional, Dict, Any
from enum import Enum
from pydantic import Field
from datetime import datetime

from app.models.base import BaseModelMixin


class TaskType(str, Enum):
    """任务类型"""
    DOCUMENT_WRITE = "document_write"  # 文档写入任务
    EVALUATION = "evaluation"          # 评估任务
    TEST_SET_IMPORT = "test_set_import"  # 测试集导入任务


class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"    # 待执行
    RUNNING = "running"    # 执行中
    COMPLETED = "completed" # 已完成
    FAILED = "failed"      # 失败


class TaskQueue(BaseModelMixin):
    """任务队列模型"""
    
    task_type: TaskType = Field(..., description="任务类型")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="任务状态")
    payload: Dict[str, Any] = Field(default_factory=dict, description="任务参数（JSON格式）")
    progress: float = Field(default=0.0, ge=0.0, le=1.0, description="进度（0.0-1.0）")
    result: Optional[Dict[str, Any]] = Field(None, description="执行结果（JSON格式）")
    error_message: Optional[str] = Field(None, description="错误信息")
    retry_count: int = Field(default=0, ge=0, description="重试次数")
    max_retries: int = Field(default=3, ge=0, description="最大重试次数")
    
    # 时间信息
    started_at: Optional[datetime] = Field(None, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "task_001",
                "task_type": "document_write",
                "status": "pending",
                "payload": {
                    "kb_id": "kb_001",
                    "chunks": ["chunk1", "chunk2"],
                    "metadata_list": []
                },
                "progress": 0.0,
                "result": None,
                "error_message": None,
                "retry_count": 0,
                "max_retries": 3,
                "created_at": "2025-01-15T10:00:00",
                "started_at": None,
                "completed_at": None
            }
        }

