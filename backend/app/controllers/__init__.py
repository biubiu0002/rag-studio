"""
控制器模块（MVC中的C）
处理HTTP请求和响应
"""

from app.controllers import knowledge_base, document, test_management, debug_pipeline

__all__ = [
    "knowledge_base",
    "document",
    "test_management",
    "debug_pipeline",
]
