"""
知识库相关数据模型
"""
from pydantic import BaseModel, Field
from typing import List, Optional

class KnowledgeSearchRequest(BaseModel):
    """知识库检索请求"""
    query: str = Field(..., min_length=1, description="查询内容")
    k: int = Field(default=6, ge=1, le=20, description="返回结果数量")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "video streaming bandwidth prediction",
                "k": 6
            }
        }

class KnowledgeDocument(BaseModel):
    """知识文档"""
    content: str = Field(..., description="文档内容")
    source: str = Field(..., description="来源")
    metadata: Optional[dict] = Field(default_factory=dict, description="元数据")

class KnowledgeSearchResponse(BaseModel):
    """知识库检索响应"""
    documents: List[KnowledgeDocument] = Field(..., description="检索到的文档列表")
    total: int = Field(..., description="结果总数")

class KnowledgeSource(BaseModel):
    """知识来源"""
    source: str = Field(..., description="来源路径")
    doc_count: int = Field(..., description="文档块数量")

class DeleteKnowledgeRequest(BaseModel):
    """删除知识请求"""
    source: str = Field(..., description="要删除的来源")

