"""
AI辅助相关数据模型
"""
from pydantic import BaseModel, Field
from typing import Optional

class GenerateContentRequest(BaseModel):
    """生成内容请求"""
    existing_text: str = Field(..., description="已有内容")
    kb_content: str = Field(default="", description="知识库内容")
    section_text: str = Field(default="", description="章节参考内容")
    prompt_template: str = Field(..., description="Prompt模板")
    
    class Config:
        json_schema_extra = {
            "example": {
                "existing_text": "title = Introduction\n\ncontent{This is the introduction...}",
                "kb_content": "Some knowledge from database...",
                "section_text": "Related section content...",
                "prompt_template": "你是一个研究视频传输的专家...$$...$$...$$"
            }
        }

class ModifyContentRequest(BaseModel):
    """修改内容请求"""
    original_content: str = Field(..., description="原始内容")
    modification_instruction: str = Field(..., description="修改指令")
    
    class Config:
        json_schema_extra = {
            "example": {
                "original_content": "This is the original text...",
                "modification_instruction": "请将这段话改得更专业"
            }
        }

class SubmitRatingRequest(BaseModel):
    """提交用户评价和评分请求"""
    generated_id: str = Field(..., description="用户对ai生成内容的评价，id指的是本次生成在mongodb中的id")
    score: int = Field(..., description="用户评分")
    comment: str = Field(..., description="用户评价")

class GenerateContentResponse(BaseModel):
    """生成内容响应"""
    generated_content: str = Field(..., description="生成的内容")
    tokens_used: Optional[int] = Field(None, description="使用的token数量")
    generated_id: str = Field(..., description="每次生成后,都会向插入生成日志,此字段意味着mongodb插入后自动生成的id")

