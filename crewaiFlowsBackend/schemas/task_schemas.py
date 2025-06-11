# 任务管理数据模型

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class TaskBase(BaseModel):
    """任务基础模型"""
    title: str = Field(..., description="任务标题")
    description: Optional[str] = Field(None, description="任务描述")
    type: str = Field(..., description="任务类型: content, analysis, schedule, operation")
    priority: str = Field(default="medium", description="优先级: low, medium, high, urgent")
    assignee: Optional[str] = Field(None, description="负责人")
    deadline: Optional[datetime] = Field(None, description="截止时间")
    account_id: Optional[str] = Field(None, description="关联账号ID")
    content_id: Optional[str] = Field(None, description="关联内容ID")
    schedule_id: Optional[str] = Field(None, description="关联计划ID")
    notes: Optional[str] = Field(None, description="备注")


class TaskCreate(TaskBase):
    """创建任务请求模型"""
    tags: Optional[List[str]] = Field(None, description="标签列表")
    attachments: Optional[List[Dict[str, Any]]] = Field(None, description="附件列表")


class TaskUpdate(BaseModel):
    """更新任务请求模型"""
    title: Optional[str] = Field(None, description="任务标题")
    description: Optional[str] = Field(None, description="任务描述")
    status: Optional[str] = Field(None, description="状态")
    priority: Optional[str] = Field(None, description="优先级")
    assignee: Optional[str] = Field(None, description="负责人")
    deadline: Optional[datetime] = Field(None, description="截止时间")
    progress: Optional[int] = Field(None, ge=0, le=100, description="进度(0-100)")
    notes: Optional[str] = Field(None, description="备注")
    tags: Optional[List[str]] = Field(None, description="标签列表")
    attachments: Optional[List[Dict[str, Any]]] = Field(None, description="附件列表")


class TaskResponse(TaskBase):
    """任务响应模型"""
    id: str = Field(..., description="任务ID")
    status: str = Field(..., description="状态")
    progress: int = Field(..., description="完成进度")
    tags: Optional[List[str]] = Field(None, description="标签列表")
    attachments: Optional[List[Dict[str, Any]]] = Field(None, description="附件列表")
    started_at: Optional[datetime] = Field(None, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class TaskWithDetails(TaskResponse):
    """带详情的任务响应模型"""
    account: Optional[Dict[str, Any]] = Field(None, description="关联账号信息")
    content: Optional[Dict[str, Any]] = Field(None, description="关联内容信息")
    schedule: Optional[Dict[str, Any]] = Field(None, description="关联计划信息")


class TaskStats(BaseModel):
    """任务统计模型"""
    total: int = Field(..., description="总数")
    pending: int = Field(..., description="待处理")
    in_progress: int = Field(..., description="进行中")
    completed: int = Field(..., description="已完成")
    overdue: int = Field(..., description="超时")
    cancelled: int = Field(..., description="已取消")
    
    # 按类型统计
    by_type: Dict[str, int] = Field(..., description="按类型统计")
    # 按优先级统计
    by_priority: Dict[str, int] = Field(..., description="按优先级统计")
    # 按负责人统计
    by_assignee: Dict[str, int] = Field(..., description="按负责人统计")


class TaskProgress(BaseModel):
    """任务进度模型"""
    task_id: str = Field(..., description="任务ID")
    progress: int = Field(..., ge=0, le=100, description="进度(0-100)")
    updated_at: datetime = Field(..., description="更新时间")


class TaskAssignment(BaseModel):
    """任务分配模型"""
    task_ids: List[str] = Field(..., description="任务ID列表")
    assignee: str = Field(..., description="负责人")


class TaskBatchOperation(BaseModel):
    """批量操作模型"""
    task_ids: List[str] = Field(..., description="任务ID列表")
    operation: str = Field(..., description="操作类型: complete, cancel, delete, assign")
    params: Optional[Dict[str, Any]] = Field(None, description="操作参数") 