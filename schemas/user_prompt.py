"""
用户Prompt管理相关数据模型
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# ============ 收藏夹相关模型 ============

class FolderCreate(BaseModel):
    """创建收藏夹"""
    folder_name: str = Field(..., description="收藏夹名称", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="收藏夹描述", max_length=500)
    
    class Config:
        json_schema_extra = {
            "example": {
                "folder_name": "学术写作",
                "description": "用于学术论文写作的Prompt模板"
            }
        }

class FolderUpdate(BaseModel):
    """更新收藏夹"""
    folder_name: Optional[str] = Field(None, description="收藏夹名称", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="收藏夹描述", max_length=500)
    
    class Config:
        json_schema_extra = {
            "example": {
                "folder_name": "学术写作（更新）",
                "description": "更新后的描述"
            }
        }

class FolderResponse(BaseModel):
    """收藏夹响应"""
    id: str = Field(..., description="收藏夹ID")
    user_id: str = Field(..., description="用户ID")
    folder_name: str = Field(..., description="收藏夹名称")
    description: Optional[str] = Field(None, description="收藏夹描述")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    prompt_count: int = Field(0, description="包含的Prompt数量")

# ============ Prompt相关模型 ============

class PromptCreate(BaseModel):
    """创建Prompt"""
    folder_id: str = Field(..., description="所属收藏夹ID")
    prompt_name: str = Field(..., description="Prompt名称", min_length=1, max_length=100)
    prompt_content: str = Field(..., description="Prompt内容", min_length=1)
    description: Optional[str] = Field(None, description="Prompt描述", max_length=500)
    tags: List[str] = Field(default_factory=list, description="标签列表")
    
    class Config:
        json_schema_extra = {
            "example": {
                "folder_id": "507f1f77bcf86cd799439011",
                "prompt_name": "论文引言生成",
                "prompt_content": "你是一个研究专家，请根据以下内容生成论文引言...",
                "description": "用于生成论文引言部分",
                "tags": ["引言", "学术"]
            }
        }

class PromptUpdate(BaseModel):
    """更新Prompt"""
    folder_id: Optional[str] = Field(None, description="所属收藏夹ID")
    prompt_name: Optional[str] = Field(None, description="Prompt名称", min_length=1, max_length=100)
    prompt_content: Optional[str] = Field(None, description="Prompt内容", min_length=1)
    description: Optional[str] = Field(None, description="Prompt描述", max_length=500)
    tags: Optional[List[str]] = Field(None, description="标签列表")
    
    class Config:
        json_schema_extra = {
            "example": {
                "prompt_name": "论文引言生成（更新）",
                "prompt_content": "更新后的Prompt内容...",
                "tags": ["引言", "学术", "优化"]
            }
        }

class PromptResponse(BaseModel):
    """Prompt响应"""
    id: str = Field(..., description="Prompt ID")
    user_id: str = Field(..., description="用户ID")
    folder_id: str = Field(..., description="所属收藏夹ID")
    prompt_name: str = Field(..., description="Prompt名称")
    prompt_content: str = Field(..., description="Prompt内容")
    description: Optional[str] = Field(None, description="Prompt描述")
    tags: List[str] = Field(default_factory=list, description="标签列表")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

# ============ 组合模型 ============

class FolderWithPromptsResponse(BaseModel):
    """收藏夹及其下的Prompts"""
    folder: FolderResponse
    prompts: List[PromptResponse]

