"""
统一响应格式模块
"""

from typing import Any, Generic, Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class SuccessResponse(BaseModel, Generic[T]):
    """成功响应模型"""
    
    success: bool = Field(default=True, description="请求是否成功")
    data: Optional[T] = Field(default=None, description="响应数据")
    message: Optional[str] = Field(default=None, description="响应消息")


class PageResponse(BaseModel, Generic[T]):
    """分页响应模型"""
    
    success: bool = Field(default=True, description="请求是否成功")
    data: list[T] = Field(default_factory=list, description="数据列表")
    total: int = Field(default=0, description="总记录数")
    page: int = Field(default=1, description="当前页码")
    page_size: int = Field(default=20, description="每页大小")
    total_pages: int = Field(default=0, description="总页数")
    
    @classmethod
    def create(
        cls,
        data: list[T],
        total: int,
        page: int = 1,
        page_size: int = 20,
    ) -> "PageResponse[T]":
        """
        创建分页响应
        
        Args:
            data: 数据列表
            total: 总记录数
            page: 当前页码
            page_size: 每页大小
        
        Returns:
            分页响应对象
        """
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        
        return cls(
            data=data,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )


class ErrorResponse(BaseModel):
    """错误响应模型"""
    
    success: bool = Field(default=False, description="请求是否成功")
    message: str = Field(..., description="错误消息")
    data: Optional[Any] = Field(default=None, description="错误详情（可选）")


def success_response(data: Any = None, message: Optional[str] = None) -> dict:
    """
    创建成功响应
    
    Args:
        data: 响应数据
        message: 响应消息
    
    Returns:
        响应字典
    """
    return SuccessResponse(data=data, message=message).model_dump()


def page_response(
    data: list,
    total: int,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    """
    创建分页响应
    
    Args:
        data: 数据列表
        total: 总记录数
        page: 当前页码
        page_size: 每页大小
    
    Returns:
        分页响应字典
    """
    return PageResponse.create(
        data=data,
        total=total,
        page=page,
        page_size=page_size,
    ).model_dump()


def error_response(message: str, data: Any = None) -> dict:
    """
    创建错误响应
    
    Args:
        message: 错误消息
        data: 错误详情（可选）
    
    Returns:
        错误响应字典
    """
    return ErrorResponse(message=message, data=data).model_dump()

