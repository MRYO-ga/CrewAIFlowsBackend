# 竞品数据模式定义
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# 基础模式
class CompetitorBase(BaseModel):
    name: str = Field(..., description="竞品名称")
    account_id: Optional[str] = Field(None, description="账号ID")
    platform: str = Field(..., description="平台名称")
    tier: Optional[str] = Field(None, description="账号等级")
    category: Optional[str] = Field(None, description="账号类别")
    avatar: Optional[str] = Field(None, description="头像URL")
    profile_url: Optional[str] = Field(None, description="账号链接")
    tags: Optional[List[str]] = Field(None, description="标签列表")

# 竞品笔记基础模式
class CompetitorNoteBase(BaseModel):
    note_id: Optional[str] = Field(None, description="原平台笔记ID")
    title: str = Field(..., description="笔记标题")
    content_preview: Optional[str] = Field(None, description="内容预览")
    upload_time: Optional[str] = Field(None, description="发布时间")
    likes: int = Field(0, description="点赞数")
    collects: int = Field(0, description="收藏数")
    comments: int = Field(0, description="评论数")
    shares: int = Field(0, description="分享数")
    views: int = Field(0, description="浏览数")
    engagement_rate: float = Field(0.0, description="互动率")
    is_viral: bool = Field(False, description="是否爆款")
    viral_score: int = Field(0, description="爆款分数")
    content_type: Optional[str] = Field(None, description="内容类型")
    topics: Optional[List[str]] = Field(None, description="话题标签")
    performance_rank: int = Field(0, description="表现排名")
    analysis: Optional[str] = Field(None, description="分析文档")

# 创建竞品笔记模式
class CompetitorNoteCreate(CompetitorNoteBase):
    competitor_id: str = Field(..., description="竞品ID")

# 更新竞品笔记模式
class CompetitorNoteUpdate(BaseModel):
    title: Optional[str] = Field(None, description="笔记标题")
    content_preview: Optional[str] = Field(None, description="内容预览")
    likes: Optional[int] = Field(None, description="点赞数")
    collects: Optional[int] = Field(None, description="收藏数")
    comments: Optional[int] = Field(None, description="评论数")
    shares: Optional[int] = Field(None, description="分享数")
    views: Optional[int] = Field(None, description="浏览数")
    engagement_rate: Optional[float] = Field(None, description="互动率")
    is_viral: Optional[bool] = Field(None, description="是否爆款")
    viral_score: Optional[int] = Field(None, description="爆款分数")
    analysis: Optional[str] = Field(None, description="分析文档")

# 竞品笔记响应模式
class CompetitorNoteResponse(CompetitorNoteBase):
    id: str = Field(..., description="笔记ID")
    competitor_id: str = Field(..., description="竞品ID")
    created_at_timestamp: Optional[datetime] = Field(None, description="创建时间戳")
    updated_at_timestamp: Optional[datetime] = Field(None, description="更新时间戳")

    class Config:
        from_attributes = True

# 创建竞品模式
class CompetitorCreate(CompetitorBase):
    followers: Optional[str] = Field(None, description="粉丝数")
    explosion_rate: Optional[float] = Field(None, description="爆款率")
    analysis_count: Optional[int] = Field(0, description="分析次数")
    analysis_document: Optional[str] = Field(None, description="分析文档")

# 更新竞品模式
class CompetitorUpdate(BaseModel):
    name: Optional[str] = Field(None, description="竞品名称")
    tier: Optional[str] = Field(None, description="账号等级")
    category: Optional[str] = Field(None, description="账号类别")
    followers: Optional[str] = Field(None, description="粉丝数")
    explosion_rate: Optional[float] = Field(None, description="爆款率")
    avatar: Optional[str] = Field(None, description="头像URL")
    profile_url: Optional[str] = Field(None, description="账号链接")
    tags: Optional[List[str]] = Field(None, description="标签列表")
    analysis_document: Optional[str] = Field(None, description="分析文档")

# 竞品响应模式
class CompetitorResponse(CompetitorBase):
    id: str = Field(..., description="竞品ID")
    followers: Optional[str] = Field(None, description="粉丝数")
    explosion_rate: Optional[float] = Field(None, description="爆款率")
    last_update: Optional[str] = Field(None, description="最后更新时间")
    analysis_count: int = Field(0, description="分析次数")
    analysis_document: Optional[str] = Field(None, description="分析文档")
    created_at_timestamp: Optional[datetime] = Field(None, description="创建时间戳")
    updated_at_timestamp: Optional[datetime] = Field(None, description="更新时间戳")

    class Config:
        from_attributes = True 