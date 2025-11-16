"""
任务队列服务
负责任务的创建、查询和管理
"""

import uuid
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from app.models.task_queue import TaskQueue, TaskType, TaskStatus
from app.repositories.factory import RepositoryFactory
from app.services.task_notifier.factory import TaskNotifierFactory

logger = logging.getLogger(__name__)


class TaskQueueService:
    """任务队列服务"""
    
    def __init__(self):
        self.task_repo = RepositoryFactory.create_task_queue_repository()
        self.notifier = TaskNotifierFactory.create()
    
    async def create_task(
        self,
        task_type: TaskType,
        payload: Dict[str, Any],
        max_retries: int = 3
    ) -> TaskQueue:
        """
        创建任务
        
        Args:
            task_type: 任务类型
            payload: 任务参数
            max_retries: 最大重试次数
        
        Returns:
            创建的任务对象
        """
        task_id = f"task_{uuid.uuid4().hex[:12]}"
        
        task = TaskQueue(
            id=task_id,
            task_type=task_type,
            status=TaskStatus.PENDING,
            payload=payload,
            progress=0.0,
            max_retries=max_retries,
            retry_count=0
        )
        
        # 保存到数据库
        task = await self.task_repo.create(task)
        
        # 通知task_executor
        notify_success = await self.notifier.notify(task_id)
        if not notify_success:
            logger.warning(f"任务创建成功但通知失败: task_id={task_id}，task_executor可能通过轮询获取")
        
        logger.info(f"创建任务: task_id={task_id}, task_type={task_type.value}")
        
        return task
    
    async def get_task(self, task_id: str) -> Optional[TaskQueue]:
        """
        获取任务
        
        Args:
            task_id: 任务ID
        
        Returns:
            任务对象，不存在返回None
        """
        return await self.task_repo.get_by_id(task_id)
    
    async def update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        error_message: Optional[str] = None
    ) -> Optional[TaskQueue]:
        """
        更新任务状态
        
        Args:
            task_id: 任务ID
            status: 新状态
            error_message: 错误信息（如果状态为failed）
        
        Returns:
            更新后的任务对象
        """
        task = await self.task_repo.get_by_id(task_id)
        if not task:
            return None
        
        task.status = status
        if error_message:
            task.error_message = error_message
        
        if status == TaskStatus.RUNNING and not task.started_at:
            task.started_at = datetime.now()
        elif status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
            task.completed_at = datetime.now()
        
        return await self.task_repo.update(task_id, task)
    
    async def update_task_progress(
        self,
        task_id: str,
        progress: float,
        result: Optional[Dict[str, Any]] = None
    ) -> Optional[TaskQueue]:
        """
        更新任务进度
        
        Args:
            task_id: 任务ID
            progress: 进度（0.0-1.0）
            result: 部分结果（可选）
        
        Returns:
            更新后的任务对象
        """
        task = await self.task_repo.get_by_id(task_id)
        if not task:
            return None
        
        task.progress = max(0.0, min(1.0, progress))
        if result:
            task.result = result
        
        return await self.task_repo.update(task_id, task)
    
    async def mark_task_completed(
        self,
        task_id: str,
        result: Optional[Dict[str, Any]] = None
    ) -> Optional[TaskQueue]:
        """
        标记任务完成
        
        Args:
            task_id: 任务ID
            result: 执行结果
        
        Returns:
            更新后的任务对象
        """
        task = await self.task_repo.get_by_id(task_id)
        if not task:
            return None
        
        task.status = TaskStatus.COMPLETED
        task.progress = 1.0
        task.completed_at = datetime.now()
        if result:
            task.result = result
        
        return await self.task_repo.update(task_id, task)
    
    async def mark_task_failed(
        self,
        task_id: str,
        error_message: str,
        retry: bool = False
    ) -> Optional[TaskQueue]:
        """
        标记任务失败
        
        Args:
            task_id: 任务ID
            error_message: 错误信息
            retry: 是否重试
        
        Returns:
            更新后的任务对象
        """
        task = await self.task_repo.get_by_id(task_id)
        if not task:
            return None
        
        task.retry_count += 1
        
        # 如果未超过最大重试次数且需要重试，重置为pending
        if retry and task.retry_count <= task.max_retries:
            task.status = TaskStatus.PENDING
            task.error_message = None
            task.started_at = None
            
            # 通知task_executor重试
            await self.notifier.notify(task_id)
            logger.info(f"任务重试: task_id={task_id}, retry_count={task.retry_count}")
        else:
            task.status = TaskStatus.FAILED
            task.error_message = error_message
            task.completed_at = datetime.now()
            logger.error(f"任务失败: task_id={task_id}, error={error_message}")
        
        return await self.task_repo.update(task_id, task)

