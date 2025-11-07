"""
基础数据模型
定义所有模型的基类
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_serializer


class BaseModelMixin(BaseModel):
    """基础模型混入类"""
    
    id: str = Field(..., description="唯一标识符")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    
    class Config:
        # 允许从 ORM 模型创建
        from_attributes = True
    
    @field_serializer('created_at', 'updated_at')
    def serialize_datetime(self, value: datetime) -> str:
        """序列化datetime为ISO格式字符串"""
        return value.isoformat()
    
    def update_timestamp(self):
        """更新时间戳"""
        self.updated_at = datetime.now()

