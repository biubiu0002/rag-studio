"""
任务通知接口
定义通知task_executor的抽象接口
"""

from abc import ABC, abstractmethod


class TaskNotifierInterface(ABC):
    """任务通知接口"""
    
    @abstractmethod
    async def notify(self, task_id: str) -> bool:
        """
        通知task_executor有新任务
        
        Args:
            task_id: 任务ID
        
        Returns:
            是否通知成功
        """
        pass

