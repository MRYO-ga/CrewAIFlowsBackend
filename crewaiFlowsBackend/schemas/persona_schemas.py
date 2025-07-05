# 人设文档Schema定义
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class PersonaDocumentBase(BaseModel):
    """人设文档基础模型"""
    account_name: str = Field(..., description="账号名称")
    document_content: str = Field(..., description="人设构建完整文档内容")
    account_type: Optional[str] = Field(None, description="账号类型")
    industry_field: Optional[str] = Field(None, description="行业领域")
    platform: str = Field("xiaohongshu", description="平台")
    tags: Optional[List[str]] = Field(None, description="标签列表")
    summary: Optional[str] = Field(None, description="简短摘要")
    user_id: str = Field("default_user", description="用户ID")

class PersonaDocumentCreate(PersonaDocumentBase):
    """创建人设文档的请求模型"""
    pass

class PersonaDocumentUpdate(BaseModel):
    """更新人设文档的请求模型"""
    account_name: Optional[str] = Field(None, description="账号名称")
    document_content: Optional[str] = Field(None, description="人设构建完整文档内容")
    account_type: Optional[str] = Field(None, description="账号类型")
    industry_field: Optional[str] = Field(None, description="行业领域")
    platform: Optional[str] = Field(None, description="平台")
    tags: Optional[List[str]] = Field(None, description="标签列表")
    summary: Optional[str] = Field(None, description="简短摘要")

class PersonaDocumentResponse(PersonaDocumentBase):
    """人设文档响应模型"""
    id: str
    status: str
    created_at: datetime
    updated_at: datetime
    completed_at: datetime

    class Config:
        from_attributes = True

class PersonaDocumentSummary(BaseModel):
    """人设文档摘要模型"""
    id: str
    account_name: str
    account_type: Optional[str]
    industry_field: Optional[str]
    platform: str
    summary: Optional[str]
    tags: Optional[List[str]]
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PersonaSearchResponse(BaseModel):
    """人设搜索响应模型"""
    total: int
    personas: List[PersonaDocumentSummary]
    
class PersonaStatsResponse(BaseModel):
    """人设统计响应模型"""
    total_personas: int
    by_platform: dict
    by_industry: dict
    by_account_type: dict
    recent_count: int 