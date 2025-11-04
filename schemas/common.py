"""
通用响应模型和数据模型
"""
from pydantic import BaseModel, Field
from typing import Optional, Any, Generic, TypeVar

T = TypeVar('T')

class Response(BaseModel, Generic[T]):
    """统一响应格式"""
    success: bool = Field(description="请求是否成功")
    message: str = Field(description="响应消息")
    data: Optional[T] = Field(default=None, description="响应数据")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "操作成功",
                "data": {}
            }
        }

class PaginationParams(BaseModel):
    """分页参数"""
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=10, ge=1, le=100, description="每页数量")

class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应"""
    success: bool
    message: str
    data: Optional[T] = None
    total: int = Field(description="总数")
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页数量")

