"""
通用Schema
"""

from typing import Optional
from pydantic import BaseModel, Field


class PaginationParams(BaseModel):
    """分页参数"""
    
    page: int = Field(default=1, description="页码", ge=1)
    page_size: int = Field(default=20, description="每页大小", ge=1, le=100)
    
    @property
    def skip(self) -> int:
        """计算跳过的数量"""
        return (self.page - 1) * self.page_size
    
    @property
    def limit(self) -> int:
        """获取限制数量"""
        return self.page_size


class IDResponse(BaseModel):
    """ID响应"""
    
    id: str = Field(..., description="资源ID")


class MessageResponse(BaseModel):
    """消息响应"""
    
    message: str = Field(..., description="消息内容")

