# 发布计划API
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database.database import get_db
from database.models import Schedule
from services.schedule_service import ScheduleService
from schemas.schedule_schemas import ScheduleCreate, ScheduleUpdate, ScheduleResponse

# 创建路由器
schedules_router = APIRouter(prefix="/api/schedules", tags=["发布计划"])

# 依赖注入
def get_schedule_service(db: Session = Depends(get_db)) -> ScheduleService:
    return ScheduleService(db)

@schedules_router.get("/", response_model=List[ScheduleResponse])
async def get_schedules(
    account_id: Optional[str] = Query(None, description="按账号ID筛选"),
    status: Optional[str] = Query(None, description="按状态筛选"),
    platform: Optional[str] = Query(None, description="按平台筛选"),
    limit: int = Query(50, description="返回数量限制"),
    schedule_service: ScheduleService = Depends(get_schedule_service)
):
    """获取发布计划列表"""
    schedules = schedule_service.get_schedules(
        account_id=account_id,
        status=status,
        platform=platform,
        limit=limit
    )
    return schedules

@schedules_router.get("/{schedule_id}", response_model=ScheduleResponse)
async def get_schedule_detail(
    schedule_id: str,
    schedule_service: ScheduleService = Depends(get_schedule_service)
):
    """获取单个发布计划详情"""
    schedule = schedule_service.get_schedule_by_id(schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="未找到该发布计划")
    return schedule

@schedules_router.post("/", response_model=ScheduleResponse)
async def create_schedule(
    schedule_data: ScheduleCreate,
    schedule_service: ScheduleService = Depends(get_schedule_service)
):
    """创建发布计划"""
    return schedule_service.create_schedule(schedule_data)

@schedules_router.put("/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(
    schedule_id: str,
    schedule_data: ScheduleUpdate,
    schedule_service: ScheduleService = Depends(get_schedule_service)
):
    """更新发布计划"""
    schedule = schedule_service.update_schedule(schedule_id, schedule_data)
    if not schedule:
        raise HTTPException(status_code=404, detail="未找到该发布计划")
    return schedule

@schedules_router.delete("/{schedule_id}")
async def delete_schedule(
    schedule_id: str,
    schedule_service: ScheduleService = Depends(get_schedule_service)
):
    """删除发布计划"""
    success = schedule_service.delete_schedule(schedule_id)
    if not success:
        raise HTTPException(status_code=404, detail="未找到该发布计划")
    return {"message": "发布计划删除成功"}

@schedules_router.post("/{schedule_id}/publish")
async def publish_now(
    schedule_id: str,
    schedule_service: ScheduleService = Depends(get_schedule_service)
):
    """立即发布计划"""
    result = schedule_service.publish_schedule(schedule_id)
    if not result:
        raise HTTPException(status_code=404, detail="未找到该发布计划")
    return result

@schedules_router.get("/stats/summary")
async def get_schedule_stats(
    days: int = Query(30, description="统计天数"),
    schedule_service: ScheduleService = Depends(get_schedule_service)
):
    """获取发布计划统计信息"""
    return schedule_service.get_schedule_stats(days) 