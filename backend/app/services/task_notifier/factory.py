"""
任务通知器工厂
根据配置创建相应的通知器实例
"""

from app.config import settings
from app.services.task_notifier.interface import TaskNotifierInterface
from app.services.task_notifier.http_notifier import HTTPTaskNotifier


class TaskNotifierFactory:
    """任务通知器工厂类"""
    
    @staticmethod
    def create() -> TaskNotifierInterface:
        """
        创建通知器实例
        
        Returns:
            通知器实例
        
        Raises:
            ValueError: 不支持的通知器类型
        """
        notifier_type = getattr(settings, 'TASK_NOTIFIER_TYPE', 'http').lower()
        executor_url = getattr(settings, 'TASK_EXECUTOR_URL', 'http://localhost:8001')
        
        if notifier_type == "http":
            return HTTPTaskNotifier(executor_url)
        elif notifier_type == "mq":
            # 后续实现MQ通知器
            raise NotImplementedError("MQ通知器尚未实现")
        else:
            raise ValueError(
                f"不支持的通知器类型: {notifier_type}，"
                f"支持的类型: http, mq"
            )

