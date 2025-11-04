"""
论文相关数据模型
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class PaperSection(BaseModel):
    """论文章节"""
    id: str = Field(..., description="章节ID")
    title: str = Field(..., description="章节标题")
    content: str = Field(default="", description="章节内容")
    children: List['PaperSection'] = Field(default_factory=list, description="子章节")

class PaperBase(BaseModel):
    """论文基础信息"""
    paper_title: str = Field(..., description="论文标题")
    uid: str = Field(..., description="用户ID")

class PaperCreate(PaperBase):
    """创建论文"""
    sections: List[PaperSection] = Field(default_factory=list, description="章节列表")

class PaperUpdate(BaseModel):
    """更新论文"""
    paper_title: Optional[str] = Field(None, description="论文标题")
    sections: Optional[List[PaperSection]] = Field(None, description="章节列表")

class PaperResponse(PaperBase):
    """论文响应"""
    sections: List[PaperSection] = Field(default_factory=list, description="章节列表")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")

class PaperListItem(BaseModel):
    """论文列表项"""
    paper_title: str = Field(..., description="论文标题")
    uid: str = Field(..., description="用户ID")
    created_at: Optional[datetime] = Field(None, description="创建时间")

class DeletePaperRequest(BaseModel):
    """删除论文请求"""
    paper_title: str = Field(..., description="论文标题")
    uid: str = Field(..., description="用户ID")

