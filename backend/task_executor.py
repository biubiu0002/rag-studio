"""
任务执行器主程序
独立进程，接收HTTP通知并并发执行任务
"""

import asyncio
import logging
from typing import Dict
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.config import settings
from app.models.task_queue import TaskQueue, TaskStatus
from app.repositories.factory import RepositoryFactory
from app.services.task_executor_service import TaskExecutorService

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="RAG Studio Task Executor",
    version=settings.APP_VERSION,
    description="任务执行器服务 - 处理文档写入和评估任务"
)


class NotifyRequest(BaseModel):
    """通知请求模型"""
    task_id: str


class TaskExecutor:
    """任务执行器"""
    
    def __init__(self, max_concurrent: int = 5):
        """
        初始化任务执行器
        
        Args:
            max_concurrent: 最大并发数
        """
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.task_repo = RepositoryFactory.create_task_queue_repository()
        self.executor_service = TaskExecutorService()
    
    async def process_task(self, task_id: str) -> None:
        """
        处理单个任务（带并发控制）
        
        Args:
            task_id: 任务ID
        """
        async with self.semaphore:  # 获取信号量，控制并发
            try:
                # 从数据库获取任务
                task = await self.task_repo.get_by_id(task_id)
                if not task:
                    logger.warning(f"任务不存在: task_id={task_id}")
                    return
                
                # 检查任务状态，避免重复执行
                if task.status != TaskStatus.PENDING:
                    logger.info(
                        f"任务状态不是pending，跳过执行: "
                        f"task_id={task_id}, status={task.status.value}"
                    )
                    return
                
                # 执行任务
                await self.executor_service.execute_task(task)
                
            except Exception as e:
                logger.error(
                    f"任务执行异常: task_id={task_id}, error={str(e)}",
                    exc_info=True
                )
    
    async def handle_notify(self, task_id: str) -> None:
        """
        接收HTTP通知，异步执行任务
        
        Args:
            task_id: 任务ID
        """
        # 检查任务是否已在运行
        if task_id in self.running_tasks:
            logger.info(f"任务已在执行中，跳过: task_id={task_id}")
            return
        
        # 创建异步任务（不阻塞）
        task = asyncio.create_task(self.process_task(task_id))
        self.running_tasks[task_id] = task
        
        # 任务完成后清理
        def cleanup(t):
            self.running_tasks.pop(task_id, None)
        
        task.add_done_callback(cleanup)
        logger.info(f"已接收任务通知: task_id={task_id}")


# 全局executor实例
_executor: TaskExecutor = None


def get_executor() -> TaskExecutor:
    """获取全局executor实例"""
    global _executor
    if _executor is None:
        max_concurrent = getattr(settings, 'TASK_EXECUTOR_MAX_CONCURRENT', 5)
        _executor = TaskExecutor(max_concurrent=max_concurrent)
    return _executor


@app.on_event("startup")
async def startup_event():
    """启动事件"""
    logger.info("="*60)
    logger.info(f"🚀 启动 {settings.APP_NAME} Task Executor v{settings.APP_VERSION}")
    logger.info(f"📍 地址: http://{settings.HOST}:8001")
    logger.info(f"🔄 最大并发数: {getattr(settings, 'TASK_EXECUTOR_MAX_CONCURRENT', 5)}")
    logger.info("="*60)


@app.get("/health")
async def health_check():
    """健康检查接口"""
    executor = get_executor()
    return JSONResponse(
        content={
            "status": "healthy",
            "service": "task_executor",
            "max_concurrent": executor.semaphore._value,
            "running_tasks": len(executor.running_tasks)
        }
    )


@app.post("/internal/notify")
async def notify_handler(request: NotifyRequest):
    """
    接收任务通知接口
    
    Args:
        request: 通知请求，包含task_id
    """
    task_id = request.task_id
    
    if not task_id:
        raise HTTPException(status_code=400, detail="task_id不能为空")
    
    executor = get_executor()
    await executor.handle_notify(task_id)
    
    return JSONResponse(
        content={
            "status": "accepted",
            "task_id": task_id,
            "message": "任务已接收"
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    print(f"🚀 启动任务执行器服务")
    print(f"📍 地址: http://{settings.HOST}:8001")
    print(f"📚 API文档: http://{settings.HOST}:8001/docs")
    print()
    
    uvicorn.run(
        "task_executor:app",
        host=settings.HOST,
        port=8001,
        reload=settings.DEBUG,
        log_level="info",
    )

