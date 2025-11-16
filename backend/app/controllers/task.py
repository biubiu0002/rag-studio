"""
任务查询控制器
提供任务状态查询接口
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Optional

from app.core.response import success_response
from app.services.task_queue_service import TaskQueueService
from app.models.task_queue import TaskStatus

router = APIRouter(prefix="/tasks", tags=["任务管理"])


@router.get("/{task_id}", response_model=None, summary="获取任务详情")
async def get_task(task_id: str):
    """
    获取任务详情
    
    - **task_id**: 任务ID
    """
    try:
        task_service = TaskQueueService()
        task = await task_service.get_task(task_id)
        
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        return JSONResponse(
            content=success_response(
                data={
                    "id": task.id,
                    "task_type": task.task_type.value,
                    "status": task.status.value,
                    "payload": task.payload,
                    "progress": task.progress,
                    "result": task.result,
                    "error_message": task.error_message,
                    "retry_count": task.retry_count,
                    "max_retries": task.max_retries,
                    "created_at": task.created_at.isoformat() if task.created_at else None,
                    "started_at": task.started_at.isoformat() if task.started_at else None,
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                },
                message="获取成功"
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"获取任务详情失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("", response_model=None, summary="获取任务列表")
async def list_tasks(
    task_type: Optional[str] = Query(None, description="任务类型筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
):
    """
    获取任务列表
    
    - **task_type**: 任务类型筛选（document_write/evaluation）
    - **status**: 状态筛选（pending/running/completed/failed）
    - **page**: 页码
    - **page_size**: 每页大小
    """
    try:
        task_service = TaskQueueService()
        from app.repositories.factory import RepositoryFactory
        from app.models.task_queue import TaskQueue
        task_repo = RepositoryFactory.create_task_queue_repository()
        
        filters = {}
        if task_type:
            filters["task_type"] = task_type
        if status:
            filters["status"] = status
        
        skip = (page - 1) * page_size
        tasks = await task_repo.get_all(
            skip=skip,
            limit=page_size,
            filters=filters,
            order_by="-created_at"
        )
        total = await task_repo.count(filters=filters)
        
        tasks_data = [{
            "id": task.id,
            "task_type": task.task_type.value,
            "status": task.status.value,
            "progress": task.progress,
            "error_message": task.error_message,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        } for task in tasks]
        
        return JSONResponse(
            content={
                "success": True,
                "data": tasks_data,
                "total": total,
                "page": page,
                "page_size": page_size,
                "message": "获取成功"
            }
        )
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"获取任务列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")

