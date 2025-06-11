# 任务管理服务层

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid

from database.models import Task, Account, Content, Schedule
from schemas.task_schemas import TaskCreate, TaskUpdate, TaskStats


class TaskService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_tasks(self, status: Optional[str] = None, type: Optional[str] = None,
                 assignee: Optional[str] = None, priority: Optional[str] = None,
                 search_term: Optional[str] = None, limit: int = 50) -> List[Task]:
        """获取任务列表"""
        query = self.db.query(Task)
        
        # 应用筛选条件
        if status:
            query = query.filter(Task.status == status)
        if type:
            query = query.filter(Task.type == type)
        if assignee:
            query = query.filter(Task.assignee == assignee)
        if priority:
            query = query.filter(Task.priority == priority)
        if search_term:
            query = query.filter(
                or_(
                    Task.title.ilike(f"%{search_term}%"),
                    Task.description.ilike(f"%{search_term}%")
                )
            )
        
        # 按创建时间倒序排列
        query = query.order_by(Task.created_at.desc())
        
        # 限制返回数量
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    def get_task_by_id(self, task_id: str) -> Optional[Task]:
        """根据ID获取任务"""
        return self.db.query(Task).filter(Task.id == task_id).first()
    
    def create_task(self, task_data: TaskCreate) -> Task:
        """创建任务"""
        # 生成UUID
        task_id = str(uuid.uuid4())
        
        # 验证关联的数据是否存在
        if task_data.account_id:
            account = self.db.query(Account).filter(Account.id == task_data.account_id).first()
            if not account:
                raise ValueError(f"账号ID {task_data.account_id} 不存在")
        
        if task_data.content_id:
            content = self.db.query(Content).filter(Content.id == task_data.content_id).first()
            if not content:
                raise ValueError(f"内容ID {task_data.content_id} 不存在")
        
        if task_data.schedule_id:
            schedule = self.db.query(Schedule).filter(Schedule.id == task_data.schedule_id).first()
            if not schedule:
                raise ValueError(f"计划ID {task_data.schedule_id} 不存在")
        
        # 创建任务
        db_task = Task(
            id=task_id,
            title=task_data.title,
            description=task_data.description,
            type=task_data.type,
            priority=task_data.priority,
            assignee=task_data.assignee,
            deadline=task_data.deadline,
            account_id=task_data.account_id,
            content_id=task_data.content_id,
            schedule_id=task_data.schedule_id,
            notes=task_data.notes,
            tags=task_data.tags,
            attachments=task_data.attachments,
            status="pending",
            progress=0
        )
        
        self.db.add(db_task)
        self.db.commit()
        self.db.refresh(db_task)
        
        return db_task
    
    def update_task(self, task_id: str, task_data: TaskUpdate) -> Optional[Task]:
        """更新任务"""
        db_task = self.get_task_by_id(task_id)
        if not db_task:
            return None
        
        # 更新字段
        update_data = task_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_task, field, value)
        
        db_task.updated_at = datetime.utcnow()
        
        # 如果进度达到100%，自动设置为已完成
        if hasattr(db_task, 'progress') and db_task.progress == 100 and db_task.status != 'completed':
            db_task.status = 'completed'
            db_task.completed_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(db_task)
        
        return db_task
    
    def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        db_task = self.get_task_by_id(task_id)
        if not db_task:
            return False
        
        self.db.delete(db_task)
        self.db.commit()
        
        return True
    
    def complete_task(self, task_id: str) -> Optional[Task]:
        """完成任务"""
        db_task = self.get_task_by_id(task_id)
        if not db_task:
            return None
        
        db_task.status = "completed"
        db_task.progress = 100
        db_task.completed_at = datetime.utcnow()
        db_task.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(db_task)
        
        return db_task
    
    def start_task(self, task_id: str) -> Optional[Task]:
        """开始任务"""
        db_task = self.get_task_by_id(task_id)
        if not db_task:
            return None
        
        if db_task.status == 'pending':
            db_task.status = "inProgress"
            db_task.started_at = datetime.utcnow()
            db_task.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(db_task)
        
        return db_task
    
    def update_task_progress(self, task_id: str, progress: int) -> Optional[Task]:
        """更新任务进度"""
        db_task = self.get_task_by_id(task_id)
        if not db_task:
            return None
        
        db_task.progress = progress
        db_task.updated_at = datetime.utcnow()
        
        # 自动更新状态
        if progress == 0 and db_task.status != 'pending':
            db_task.status = 'pending'
        elif 0 < progress < 100 and db_task.status != 'inProgress':
            db_task.status = 'inProgress'
            if not db_task.started_at:
                db_task.started_at = datetime.utcnow()
        elif progress == 100 and db_task.status != 'completed':
            db_task.status = 'completed'
            db_task.completed_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(db_task)
        
        return db_task
    
    def get_task_stats(self) -> TaskStats:
        """获取任务统计信息"""
        base_query = self.db.query(Task)
        
        # 基本状态统计
        total = base_query.count()
        pending = base_query.filter(Task.status == 'pending').count()
        in_progress = base_query.filter(Task.status == 'inProgress').count()
        completed = base_query.filter(Task.status == 'completed').count()
        cancelled = base_query.filter(Task.status == 'cancelled').count()
        
        # 计算超时任务
        overdue = base_query.filter(
            and_(
                Task.deadline < datetime.utcnow(),
                Task.status.in_(['pending', 'inProgress'])
            )
        ).count()
        
        # 按类型统计
        type_stats = {}
        type_results = self.db.query(
            Task.type, func.count(Task.id)
        ).group_by(Task.type).all()
        for type_name, count in type_results:
            type_stats[type_name] = count
        
        # 按优先级统计
        priority_stats = {}
        priority_results = self.db.query(
            Task.priority, func.count(Task.id)
        ).group_by(Task.priority).all()
        for priority, count in priority_results:
            priority_stats[priority] = count
        
        # 按负责人统计
        assignee_stats = {}
        assignee_results = self.db.query(
            Task.assignee, func.count(Task.id)
        ).filter(Task.assignee.isnot(None)).group_by(Task.assignee).all()
        for assignee, count in assignee_results:
            assignee_stats[assignee] = count
        
        return TaskStats(
            total=total,
            pending=pending,
            in_progress=in_progress,
            completed=completed,
            overdue=overdue,
            cancelled=cancelled,
            by_type=type_stats,
            by_priority=priority_stats,
            by_assignee=assignee_stats
        )
    
    def get_overdue_tasks(self) -> List[Task]:
        """获取超时任务列表"""
        return self.db.query(Task).filter(
            and_(
                Task.deadline < datetime.utcnow(),
                Task.status.in_(['pending', 'inProgress'])
            )
        ).order_by(Task.deadline).all()
    
    def get_tasks_by_assignee(self, assignee: str) -> List[Task]:
        """获取指定负责人的任务"""
        return self.db.query(Task).filter(
            Task.assignee == assignee
        ).order_by(Task.created_at.desc()).all()
    
    def batch_update_status(self, task_ids: List[str], status: str) -> int:
        """批量更新任务状态"""
        updated_count = self.db.query(Task).filter(
            Task.id.in_(task_ids)
        ).update(
            {"status": status, "updated_at": datetime.utcnow()},
            synchronize_session=False
        )
        
        self.db.commit()
        return updated_count
    
    def assign_tasks(self, task_ids: List[str], assignee: str) -> int:
        """批量分配任务"""
        updated_count = self.db.query(Task).filter(
            Task.id.in_(task_ids)
        ).update(
            {"assignee": assignee, "updated_at": datetime.utcnow()},
            synchronize_session=False
        )
        
        self.db.commit()
        return updated_count 