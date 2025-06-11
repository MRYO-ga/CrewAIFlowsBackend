# 内容数据模式定义
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# 基础模式
class ContentBase(BaseModel):
    title: str = Field(..., description="内容标题")
    cover: Optional[str] = Field(None, description="封面图URL")
    description: Optional[str] = Field(None, description="内容描述")
    content: Optional[str] = Field(None, description="内容正文")
    category: Optional[str] = Field(None, description="内容分类")
    platform: str = Field("xiaohongshu", description="发布平台")
    account_id: str = Field(..., description="关联账号ID")
    tags: Optional[List[str]] = Field(None, description="标签列表")

# 创建内容模式
class ContentCreate(ContentBase):
    platform: Optional[str] = Field("xiaohongshu", description="发布平台")
    status: str = Field("draft", description="内容状态")
    created_at: Optional[str] = Field(None, description="创建时间")
    stats: Optional[Dict[str, Any]] = Field(None, description="统计数据")

# 更新内容模式
class ContentUpdate(BaseModel):
    title: Optional[str] = Field(None, description="内容标题")
    cover: Optional[str] = Field(None, description="封面图URL")
    description: Optional[str] = Field(None, description="内容描述")
    content: Optional[str] = Field(None, description="内容正文")
    category: Optional[str] = Field(None, description="内容分类")
    status: Optional[str] = Field(None, description="内容状态")
    tags: Optional[List[str]] = Field(None, description="标签列表")
    stats: Optional[Dict[str, Any]] = Field(None, description="统计数据")

# 内容响应模式
class ContentResponse(ContentBase):
    id: str = Field(..., description="内容ID")
    status: str = Field(..., description="内容状态")
    published_at: Optional[str] = Field(None, description="发布时间")
    created_at: Optional[str] = Field(None, description="创建时间")
    scheduled_at: Optional[str] = Field(None, description="计划时间")
    stats: Optional[Dict[str, Any]] = Field(None, description="统计数据")
    created_at_timestamp: Optional[datetime] = Field(None, description="创建时间戳")
    updated_at_timestamp: Optional[datetime] = Field(None, description="更新时间戳")

    class Config:
        from_attributes = True 