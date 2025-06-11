# SOP相关的Pydantic模型
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

# SOP任务项模型
class SOPTaskItemBase(BaseModel):
    item_key: str = Field(..., description="任务项唯一标识")
    time: Optional[str] = Field(None, description="执行时间")
    action: str = Field(..., description="执行动作")
    content: str = Field(..., description="任务内容")
    example: Optional[str] = Field(None, description="示例")
    publish_time: Optional[str] = Field(None, description="发布时间")
    reason: Optional[str] = Field(None, description="执行原因")
    completed: bool = Field(False, description="是否完成")
    order_index: int = Field(0, description="排序索引")

class SOPTaskItemCreate(SOPTaskItemBase):
    pass

class SOPTaskItemUpdate(BaseModel):
    time: Optional[str] = None
    action: Optional[str] = None
    content: Optional[str] = None
    example: Optional[str] = None
    publish_time: Optional[str] = None
    reason: Optional[str] = None
    completed: Optional[bool] = None
    order_index: Optional[int] = None

class SOPTaskItemResponse(SOPTaskItemBase):
    id: str = Field(..., description="任务项ID")
    task_id: str = Field(..., description="所属任务ID")

    class Config:
        from_attributes = True

# SOP任务模型
class SOPTaskBase(BaseModel):
    task_key: str = Field(..., description="任务唯一标识")
    category: str = Field(..., description="任务分类")
    completed: bool = Field(False, description="是否完成")
    order_index: int = Field(0, description="排序索引")

class SOPTaskCreate(SOPTaskBase):
    items: List[SOPTaskItemCreate] = Field([], description="任务项列表")

class SOPTaskUpdate(BaseModel):
    category: Optional[str] = None
    completed: Optional[bool] = None
    order_index: Optional[int] = None

class SOPTaskResponse(SOPTaskBase):
    id: str = Field(..., description="任务ID")
    week_id: str = Field(..., description="所属周ID")
    items: List[SOPTaskItemResponse] = Field([], description="任务项列表")

    class Config:
        from_attributes = True

# SOP周模型
class SOPWeekBase(BaseModel):
    week_key: str = Field(..., description="周唯一标识")
    title: str = Field(..., description="周标题")
    status: str = Field("wait", description="状态")
    order_index: int = Field(0, description="排序索引")

class SOPWeekCreate(SOPWeekBase):
    tasks: List[SOPTaskCreate] = Field([], description="任务列表")

class SOPWeekUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None
    order_index: Optional[int] = None

class SOPWeekResponse(SOPWeekBase):
    id: str = Field(..., description="周ID")
    cycle_id: str = Field(..., description="所属周期ID")
    tasks: List[SOPTaskResponse] = Field([], description="任务列表")

    class Config:
        from_attributes = True

# SOP周期模型
class SOPCycleBase(BaseModel):
    cycle_key: str = Field(..., description="周期唯一标识")
    title: str = Field(..., description="周期标题")
    subtitle: Optional[str] = Field(None, description="副标题")
    duration: Optional[str] = Field(None, description="持续时间")
    status: str = Field("wait", description="状态")
    icon: Optional[str] = Field(None, description="图标")
    color: Optional[str] = Field(None, description="颜色")
    progress: int = Field(0, description="进度百分比")
    goal: Optional[str] = Field(None, description="目标")
    order_index: int = Field(0, description="排序索引")

class SOPCycleCreate(SOPCycleBase):
    weeks: List[SOPWeekCreate] = Field([], description="周列表")

class SOPCycleUpdate(BaseModel):
    title: Optional[str] = None
    subtitle: Optional[str] = None
    duration: Optional[str] = None
    status: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    progress: Optional[int] = None
    goal: Optional[str] = None
    order_index: Optional[int] = None

class SOPCycleResponse(SOPCycleBase):
    id: str = Field(..., description="周期ID")
    sop_id: str = Field(..., description="所属SOP ID")
    weeks: List[SOPWeekResponse] = Field([], description="周列表")

    class Config:
        from_attributes = True

# SOP主模型
class SOPBase(BaseModel):
    title: str = Field(..., description="SOP标题")
    type: str = Field(..., description="SOP类型")
    description: Optional[str] = Field(None, description="描述")
    status: str = Field("active", description="状态")

class SOPCreate(SOPBase):
    created_at: str = Field(..., description="创建时间")
    cycles: List[SOPCycleCreate] = Field([], description="周期列表")

class SOPUpdate(BaseModel):
    title: Optional[str] = None
    type: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    updated_at: Optional[str] = None

class SOPResponse(SOPBase):
    id: str = Field(..., description="SOP ID")
    created_at: str = Field(..., description="创建时间")
    updated_at: Optional[str] = Field(None, description="更新时间")
    cycles: List[SOPCycleResponse] = Field([], description="周期列表")

    class Config:
        from_attributes = True

# 简化的SOP列表响应模型
class SOPListResponse(BaseModel):
    id: str = Field(..., description="SOP ID")
    title: str = Field(..., description="SOP标题")
    type: str = Field(..., description="SOP类型")
    status: str = Field(..., description="状态")
    created_at: str = Field(..., description="创建时间")
    cycles_count: int = Field(0, description="周期数量")

    class Config:
        from_attributes = True 