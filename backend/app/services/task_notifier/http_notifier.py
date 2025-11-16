"""
HTTP任务通知实现
通过HTTP请求通知task_executor
"""

import logging
import httpx
from typing import Optional

from app.services.task_notifier.interface import TaskNotifierInterface

logger = logging.getLogger(__name__)


class HTTPTaskNotifier(TaskNotifierInterface):
    """HTTP任务通知器"""
    
    def __init__(self, executor_url: str, timeout: float = 5.0):
        """
        初始化HTTP通知器
        
        Args:
            executor_url: task_executor服务地址，如 http://localhost:8001
            timeout: 请求超时时间（秒）
        """
        self.executor_url = executor_url.rstrip('/')
        self.timeout = timeout
    
    async def notify(self, task_id: str) -> bool:
        """
        通过HTTP通知task_executor
        
        Args:
            task_id: 任务ID
        
        Returns:
            是否通知成功
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.executor_url}/internal/notify",
                    json={"task_id": task_id}
                )
                if response.status_code == 200:
                    logger.info(f"成功通知task_executor: task_id={task_id}")
                    return True
                else:
                    logger.warning(
                        f"通知task_executor失败: task_id={task_id}, "
                        f"status_code={response.status_code}, "
                        f"response={response.text}"
                    )
                    return False
        except httpx.TimeoutException:
            logger.warning(f"通知task_executor超时: task_id={task_id}")
            return False
        except Exception as e:
            logger.warning(f"通知task_executor异常: task_id={task_id}, error={str(e)}")
            return False

