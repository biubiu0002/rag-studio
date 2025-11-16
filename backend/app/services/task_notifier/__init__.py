"""
任务通知组件
支持HTTP通知（当前）和MQ通知（后续扩展）
"""

from app.services.task_notifier.interface import TaskNotifierInterface
from app.services.task_notifier.http_notifier import HTTPTaskNotifier
from app.services.task_notifier.factory import TaskNotifierFactory

__all__ = [
    "TaskNotifierInterface",
    "HTTPTaskNotifier",
    "TaskNotifierFactory",
]

