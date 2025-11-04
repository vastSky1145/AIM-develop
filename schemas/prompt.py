"""
Prompt模板相关数据模型
"""
from pydantic import BaseModel, Field
from typing import Optional

class PromptTemplateCreate(BaseModel):
    """创建Prompt模板"""
    ppt_id: str = Field(..., description="PPT章节ID")
    prompt_json: str = Field(..., description="Prompt模板内容")
    
    class Config:
        json_schema_extra = {
            "example": {
                "ppt_id": "ppt1.1",
                "prompt_json": "你是一个研究视频传输的专家..."
            }
        }

class PromptTemplateResponse(BaseModel):
    """Prompt模板响应"""
    ppt_id: str = Field(..., description="PPT章节ID")
    prompt_json: str = Field(..., description="Prompt模板内容")

