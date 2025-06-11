# 发布计划数据模型

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ScheduleBase(BaseModel):
    """发布计划基础模型"""
    title: str = Field(..., description="计划标题")
    description: Optional[str] = Field(None, description="计划描述")
    type: str = Field(default="single", description="计划类型: single, batch, ab_test, recurring")
    account_id: Optional[str] = Field(None, description="关联账号ID")
    content_id: Optional[str] = Field(None, description="关联内容ID")
    platform: Optional[str] = Field(None, description="发布平台")
    publish_datetime: Optional[datetime] = Field(None, description="计划发布时间")
    note: Optional[str] = Field(None, description="备注")


class ScheduleCreate(ScheduleBase):
    """创建发布计划请求模型"""
    test_config: Optional[Dict[str, Any]] = Field(None, description="A/B测试配置")
    recurring_config: Optional[Dict[str, Any]] = Field(None, description="循环发布配置")


class ScheduleUpdate(BaseModel):
    """更新发布计划请求模型"""
    title: Optional[str] = Field(None, description="计划标题")
    description: Optional[str] = Field(None, description="计划描述")
    status: Optional[str] = Field(None, description="状态")
    publish_datetime: Optional[datetime] = Field(None, description="计划发布时间")
    note: Optional[str] = Field(None, description="备注")
    test_config: Optional[Dict[str, Any]] = Field(None, description="A/B测试配置")
    recurring_config: Optional[Dict[str, Any]] = Field(None, description="循环发布配置")


class ScheduleResponse(ScheduleBase):
    """发布计划响应模型"""
    id: str = Field(..., description="计划ID")
    status: str = Field(..., description="状态")
    published_at: Optional[datetime] = Field(None, description="实际发布时间")
    test_config: Optional[Dict[str, Any]] = Field(None, description="A/B测试配置")
    recurring_config: Optional[Dict[str, Any]] = Field(None, description="循环发布配置")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class ScheduleWithDetails(ScheduleResponse):
    """带详情的发布计划响应模型"""
    account: Optional[Dict[str, Any]] = Field(None, description="关联账号信息")
    content: Optional[Dict[str, Any]] = Field(None, description="关联内容信息")


class ScheduleStats(BaseModel):
    """发布计划统计模型"""
    total: int = Field(..., description="总数")
    pending: int = Field(..., description="待发布")
    running: int = Field(..., description="进行中")
    published: int = Field(..., description="已发布")
    completed: int = Field(..., description="已完成")
    cancelled: int = Field(..., description="已取消")


class PublishResult(BaseModel):
    """发布结果模型"""
    schedule_id: str = Field(..., description="计划ID")
    status: str = Field(..., description="发布状态")
    published_at: datetime = Field(..., description="发布时间")
    content_updated: bool = Field(..., description="内容是否已更新")
    message: str = Field(..., description="结果消息") 