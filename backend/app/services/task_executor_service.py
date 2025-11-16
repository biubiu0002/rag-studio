"""
任务执行服务
负责任务的实际执行逻辑
"""

import logging
from typing import Dict, Any

from app.models.task_queue import TaskQueue, TaskType, TaskStatus
from app.services.task_queue_service import TaskQueueService
from app.services.index_writing_service import IndexWritingService
from app.services.evaluation_task import EvaluationTaskService
from app.services.test_set_import_service import TestSetImportService

logger = logging.getLogger(__name__)


class TaskExecutorService:
    """任务执行服务"""
    
    def __init__(self):
        self.task_queue_service = TaskQueueService()
        self.index_writing_service = IndexWritingService()
        self.evaluation_service = EvaluationTaskService()
        self.test_set_import_service = TestSetImportService()
    
    async def execute_task(self, task: TaskQueue) -> None:
        """
        执行任务
        
        Args:
            task: 任务对象
        """
        task_id = task.id
        
        try:
            # 更新状态为running
            await self.task_queue_service.update_task_status(
                task_id, TaskStatus.RUNNING
            )
            
            # 根据任务类型执行
            if task.task_type == TaskType.DOCUMENT_WRITE:
                await self._execute_document_write_task(task)
            elif task.task_type == TaskType.EVALUATION:
                await self._execute_evaluation_task(task)
            elif task.task_type == TaskType.TEST_SET_IMPORT:
                await self._execute_test_set_import_task(task)
            else:
                raise ValueError(f"不支持的任务类型: {task.task_type}")
            
            logger.info(f"任务执行完成: task_id={task_id}")
            
        except Exception as e:
            logger.error(f"任务执行失败: task_id={task_id}, error={str(e)}", exc_info=True)
            await self.task_queue_service.mark_task_failed(
                task_id, str(e), retry=True
            )
            raise
    
    async def _execute_document_write_task(self, task: TaskQueue) -> None:
        """执行文档写入任务"""
        task_id = task.id
        payload = task.payload
        
        kb_id = payload.get("kb_id")
        chunks = payload.get("chunks", [])
        metadata_list = payload.get("metadata_list")
        dense_vectors = payload.get("dense_vectors")
        sparse_vectors = payload.get("sparse_vectors")
        
        if not kb_id:
            raise ValueError("payload中缺少kb_id")
        if not chunks:
            raise ValueError("payload中缺少chunks")
        
        # 执行写入
        result = await self.index_writing_service.write_chunks_to_index(
            kb_id=kb_id,
            chunks=chunks,
            metadata_list=metadata_list,
            dense_vectors=dense_vectors,
            sparse_vectors=sparse_vectors
        )
        
        # 标记任务完成
        await self.task_queue_service.mark_task_completed(
            task_id, result=result
        )
    
    async def _execute_evaluation_task(self, task: TaskQueue) -> None:
        """执行评估任务"""
        task_id = task.id
        payload = task.payload
        
        evaluation_task_id = payload.get("evaluation_task_id")
        save_detailed_results = payload.get("save_detailed_results", True)
        
        if not evaluation_task_id:
            raise ValueError("payload中缺少evaluation_task_id")
        
        # 执行评估（这里会更新评估任务的状态和进度）
        evaluation_task = await self.evaluation_service.execute_evaluation_task(
            task_id=evaluation_task_id,
            save_detailed_results=save_detailed_results
        )
        
        # 标记任务完成
        result = {
            "evaluation_task_id": evaluation_task_id,
            "status": evaluation_task.status.value,
            "total_cases": evaluation_task.total_cases,
            "completed_cases": evaluation_task.completed_cases,
            "failed_cases": evaluation_task.failed_cases
        }
        
        await self.task_queue_service.mark_task_completed(
            task_id, result=result
        )
    
    async def _execute_test_set_import_task(self, task: TaskQueue) -> None:
        """执行测试集导入任务"""
        task_id = task.id
        payload = task.payload
        
        import_task_id = payload.get("import_task_id")
        update_existing = payload.get("update_existing", False)
        
        if not import_task_id:
            raise ValueError("payload中缺少import_task_id")
        
        # 执行导入（这里会更新导入任务的状态和进度）
        # 注意：这里直接调用内部方法，因为导入逻辑已经在TestSetImportService中
        await self.test_set_import_service._execute_import_task(
            import_task_id, update_existing
        )
        
        # 获取导入任务的最新状态
        import_task = await self.test_set_import_service.get_import_task(import_task_id)
        
        # 标记任务完成
        result = {
            "import_task_id": import_task_id,
            "status": import_task.status if import_task else "unknown",
            "total_docs": import_task.total_docs if import_task else 0,
            "imported_docs": import_task.imported_docs if import_task else 0,
            "failed_docs": import_task.failed_docs if import_task else 0,
            "progress": import_task.progress if import_task else 0.0
        }
        
        if import_task and import_task.status == "completed":
            await self.task_queue_service.mark_task_completed(
                task_id, result=result
            )
        elif import_task and import_task.status == "failed":
            await self.task_queue_service.mark_task_failed(
                task_id, import_task.error_message or "导入失败", retry=True
            )
        else:
            # 如果导入任务还在运行中，等待完成（这种情况不应该发生）
            logger.warning(f"导入任务状态异常: import_task_id={import_task_id}, status={import_task.status if import_task else 'None'}")
            await self.task_queue_service.mark_task_completed(
                task_id, result=result
            )

