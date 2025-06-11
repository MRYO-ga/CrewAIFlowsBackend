# 账号数据模式定义
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# 基础模式
class AccountBase(BaseModel):
    name: str = Field(..., description="账号名称")
    platform: str = Field(..., description="平台名称")
    account_id: str = Field(..., description="账号ID")
    avatar: Optional[str] = Field(None, description="头像URL")
    status: str = Field("active", description="账号状态")
    bio: Optional[str] = Field(None, description="个人简介")
    tags: Optional[List[str]] = Field(None, description="标签列表")

# 创建账号模式
class AccountCreate(AccountBase):
    created_at: Optional[str] = Field(None, description="创建时间")
    followers: Optional[int] = Field(0, description="粉丝数")
    notes: Optional[int] = Field(0, description="笔记数")
    engagement: Optional[float] = Field(0.0, description="互动率")
    avg_views: Optional[int] = Field(0, description="平均浏览量")
    verified: Optional[bool] = Field(False, description="是否认证")
    content_count: Optional[int] = Field(0, description="内容数量")
    target_audience: Optional[Dict[str, Any]] = Field(None, description="目标受众信息")
    positioning: Optional[Dict[str, Any]] = Field(None, description="账号定位")
    content_strategy: Optional[Dict[str, Any]] = Field(None, description="内容策略")
    monetization: Optional[Dict[str, Any]] = Field(None, description="变现信息")

# 更新账号模式
class AccountUpdate(BaseModel):
    name: Optional[str] = Field(None, description="账号名称")
    avatar: Optional[str] = Field(None, description="头像URL")
    status: Optional[str] = Field(None, description="账号状态")
    bio: Optional[str] = Field(None, description="个人简介")
    tags: Optional[List[str]] = Field(None, description="标签列表")
    followers: Optional[int] = Field(None, description="粉丝数")
    notes: Optional[int] = Field(None, description="笔记数")
    engagement: Optional[float] = Field(None, description="互动率")
    avg_views: Optional[int] = Field(None, description="平均浏览量")
    verified: Optional[bool] = Field(None, description="是否认证")
    content_count: Optional[int] = Field(None, description="内容数量")
    target_audience: Optional[Dict[str, Any]] = Field(None, description="目标受众信息")
    positioning: Optional[Dict[str, Any]] = Field(None, description="账号定位")
    content_strategy: Optional[Dict[str, Any]] = Field(None, description="内容策略")
    monetization: Optional[Dict[str, Any]] = Field(None, description="变现信息")

# 账号响应模式
class AccountResponse(AccountBase):
    id: str = Field(..., description="账号主键ID")
    created_at: Optional[str] = Field(None, description="创建时间")
    last_updated: Optional[str] = Field(None, description="最后更新时间")
    followers: int = Field(0, description="粉丝数")
    notes: int = Field(0, description="笔记数")
    engagement: float = Field(0.0, description="互动率")
    avg_views: int = Field(0, description="平均浏览量")
    verified: bool = Field(False, description="是否认证")
    content_count: int = Field(0, description="内容数量")
    target_audience: Optional[Dict[str, Any]] = Field(None, description="目标受众信息")
    positioning: Optional[Dict[str, Any]] = Field(None, description="账号定位")
    content_strategy: Optional[Dict[str, Any]] = Field(None, description="内容策略")
    monetization: Optional[Dict[str, Any]] = Field(None, description="变现信息")
    created_at_timestamp: Optional[datetime] = Field(None, description="创建时间戳")
    updated_at_timestamp: Optional[datetime] = Field(None, description="更新时间戳")

    class Config:
        from_attributes = True

# 账号分析响应模式
class AccountAnalyticsResponse(BaseModel):
    account_id: str = Field(..., description="账号ID")
    account_name: str = Field(..., description="账号名称")
    total_views: int = Field(0, description="总浏览量")
    total_likes: int = Field(0, description="总点赞数")
    total_comments: int = Field(0, description="总评论数")
    total_shares: int = Field(0, description="总分享数")
    followers_growth: int = Field(0, description="粉丝增长")
    avg_engagement_rate: float = Field(0.0, description="平均互动率")
    content_published: int = Field(0, description="发布内容数")
    best_performing_content: Optional[Dict[str, Any]] = Field(None, description="最佳表现内容")
    content_type_breakdown: Optional[Dict[str, Any]] = Field(None, description="内容类型分布")
    growth_trend: Optional[List[Dict[str, Any]]] = Field(None, description="增长趋势")

    class Config:
        from_attributes = True 