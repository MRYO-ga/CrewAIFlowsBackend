# 任务管理API
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database.database import get_db
from database.models import Task
from services.task_service import TaskService
from schemas.task_schemas import TaskCreate, TaskUpdate, TaskResponse, TaskStats

# 创建路由器
tasks_router = APIRouter(prefix="/api/tasks", tags=["任务管理"])

# 依赖注入
def get_task_service(db: Session = Depends(get_db)) -> TaskService:
    return TaskService(db)

@tasks_router.get("/", response_model=List[TaskResponse])
async def get_tasks(
    status: Optional[str] = Query(None, description="按状态筛选"),
    type: Optional[str] = Query(None, description="按类型筛选"),
    assignee: Optional[str] = Query(None, description="按负责人筛选"),
    priority: Optional[str] = Query(None, description="按优先级筛选"),
    search_term: Optional[str] = Query(None, description="搜索关键词"),
    limit: int = Query(50, description="返回数量限制"),
    task_service: TaskService = Depends(get_task_service)
):
    """获取任务列表"""
    tasks = task_service.get_tasks(
        status=status,
        type=type,
        assignee=assignee,
        priority=priority,
        search_term=search_term,
        limit=limit
    )
    return tasks

@tasks_router.get("/stats", response_model=TaskStats)
async def get_task_stats(
    task_service: TaskService = Depends(get_task_service)
):
    """获取任务统计信息"""
    return task_service.get_task_stats()

@tasks_router.get("/{task_id}", response_model=TaskResponse)
async def get_task_detail(
    task_id: str,
    task_service: TaskService = Depends(get_task_service)
):
    """获取单个任务详情"""
    task = task_service.get_task_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="未找到该任务")
    return task

@tasks_router.post("/", response_model=TaskResponse)
async def create_task(
    task_data: TaskCreate,
    task_service: TaskService = Depends(get_task_service)
):
    """创建任务"""
    return task_service.create_task(task_data)

@tasks_router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str,
    task_data: TaskUpdate,
    task_service: TaskService = Depends(get_task_service)
):
    """更新任务"""
    task = task_service.update_task(task_id, task_data)
    if not task:
        raise HTTPException(status_code=404, detail="未找到该任务")
    return task

@tasks_router.delete("/{task_id}")
async def delete_task(
    task_id: str,
    task_service: TaskService = Depends(get_task_service)
):
    """删除任务"""
    success = task_service.delete_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="未找到该任务")
    return {"message": "任务删除成功"}

@tasks_router.post("/{task_id}/complete")
async def complete_task(
    task_id: str,
    task_service: TaskService = Depends(get_task_service)
):
    """完成任务"""
    task = task_service.complete_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="未找到该任务")
    return task

@tasks_router.post("/{task_id}/start")
async def start_task(
    task_id: str,
    task_service: TaskService = Depends(get_task_service)
):
    """开始任务"""
    task = task_service.start_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="未找到该任务")
    return task

@tasks_router.put("/{task_id}/progress")
async def update_task_progress(
    task_id: str,
    progress: int = Query(..., ge=0, le=100, description="任务进度(0-100)"),
    task_service: TaskService = Depends(get_task_service)
):
    """更新任务进度"""
    task = task_service.update_task_progress(task_id, progress)
    if not task:
        raise HTTPException(status_code=404, detail="未找到该任务")
    return task

@tasks_router.get("/overdue/list")
async def get_overdue_tasks(
    task_service: TaskService = Depends(get_task_service)
):
    """获取超时任务列表"""
    return task_service.get_overdue_tasks() 