# 发布计划服务层

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid

from database.models import Schedule, PersonaDocument, Content
from schemas.schedule_schemas import ScheduleCreate, ScheduleUpdate, PublishResult, ScheduleStats


class ScheduleService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_schedules(self, account_id: Optional[str] = None, status: Optional[str] = None, 
                     platform: Optional[str] = None, limit: int = 50) -> List[Schedule]:
        """获取发布计划列表"""
        query = self.db.query(Schedule)
        
        # 应用筛选条件
        if account_id:
            query = query.filter(Schedule.account_id == account_id)
        if status:
            query = query.filter(Schedule.status == status)
        if platform:
            query = query.filter(Schedule.platform == platform)
        
        # 按创建时间倒序排列
        query = query.order_by(Schedule.created_at.desc())
        
        # 限制返回数量
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    def get_schedule_by_id(self, schedule_id: str) -> Optional[Schedule]:
        """根据ID获取发布计划"""
        return self.db.query(Schedule).filter(Schedule.id == schedule_id).first()
    
    def create_schedule(self, schedule_data: ScheduleCreate) -> Schedule:
        """创建发布计划"""
        # 生成UUID
        schedule_id = str(uuid.uuid4())
        
        # 验证关联的账号和内容是否存在
        if schedule_data.account_id:
            account = self.db.query(Account).filter(Account.id == schedule_data.account_id).first()
            if not account:
                raise ValueError(f"账号ID {schedule_data.account_id} 不存在")
        
        if schedule_data.content_id:
            content = self.db.query(Content).filter(Content.id == schedule_data.content_id).first()
            if not content:
                raise ValueError(f"内容ID {schedule_data.content_id} 不存在")
        
        # 创建发布计划
        db_schedule = Schedule(
            id=schedule_id,
            title=schedule_data.title,
            description=schedule_data.description,
            type=schedule_data.type,
            account_id=schedule_data.account_id,
            content_id=schedule_data.content_id,
            platform=schedule_data.platform,
            publish_datetime=schedule_data.publish_datetime,
            note=schedule_data.note,
            test_config=schedule_data.test_config,
            recurring_config=schedule_data.recurring_config,
            status="pending"
        )
        
        self.db.add(db_schedule)
        self.db.commit()
        self.db.refresh(db_schedule)
        
        return db_schedule
    
    def update_schedule(self, schedule_id: str, schedule_data: ScheduleUpdate) -> Optional[Schedule]:
        """更新发布计划"""
        db_schedule = self.get_schedule_by_id(schedule_id)
        if not db_schedule:
            return None
        
        # 更新字段
        update_data = schedule_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_schedule, field, value)
        
        db_schedule.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(db_schedule)
        
        return db_schedule
    
    def delete_schedule(self, schedule_id: str) -> bool:
        """删除发布计划"""
        db_schedule = self.get_schedule_by_id(schedule_id)
        if not db_schedule:
            return False
        
        self.db.delete(db_schedule)
        self.db.commit()
        
        return True
    
    def publish_schedule(self, schedule_id: str) -> Optional[PublishResult]:
        """立即发布计划"""
        db_schedule = self.get_schedule_by_id(schedule_id)
        if not db_schedule:
            return None
        
        # 检查是否已经发布
        if db_schedule.status in ['published', 'completed']:
            return PublishResult(
                schedule_id=schedule_id,
                status=db_schedule.status,
                published_at=db_schedule.published_at or datetime.utcnow(),
                content_updated=False,
                message="该计划已经发布"
            )
        
        # 更新计划状态
        db_schedule.status = "published"
        db_schedule.published_at = datetime.utcnow()
        
        # 更新关联内容状态
        content_updated = False
        if db_schedule.content_id:
            content = self.db.query(Content).filter(Content.id == db_schedule.content_id).first()
            if content and content.status != 'published':
                content.status = 'published'
                content.published_at = datetime.utcnow()
                content_updated = True
        
        self.db.commit()
        self.db.refresh(db_schedule)
        
        return PublishResult(
            schedule_id=schedule_id,
            status="published",
            published_at=db_schedule.published_at,
            content_updated=content_updated,
            message="发布成功"
        )
    
    def get_schedule_stats(self, days: int = 30) -> ScheduleStats:
        """获取发布计划统计信息"""
        # 计算日期范围
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # 查询指定时间范围内的计划
        base_query = self.db.query(Schedule).filter(
            Schedule.created_at >= start_date,
            Schedule.created_at <= end_date
        )
        
        # 统计各状态的数量
        total = base_query.count()
        pending = base_query.filter(Schedule.status == 'pending').count()
        running = base_query.filter(Schedule.status == 'running').count()
        published = base_query.filter(Schedule.status == 'published').count()
        completed = base_query.filter(Schedule.status == 'completed').count()
        cancelled = base_query.filter(Schedule.status == 'cancelled').count()
        
        return ScheduleStats(
            total=total,
            pending=pending,
            running=running,
            published=published,
            completed=completed,
            cancelled=cancelled
        )
    
    def get_upcoming_schedules(self, hours: int = 24) -> List[Schedule]:
        """获取即将发布的计划"""
        end_time = datetime.utcnow() + timedelta(hours=hours)
        
        return self.db.query(Schedule).filter(
            and_(
                Schedule.status == 'pending',
                Schedule.publish_datetime <= end_time,
                Schedule.publish_datetime >= datetime.utcnow()
            )
        ).order_by(Schedule.publish_datetime).all()
    
    def batch_update_status(self, schedule_ids: List[str], status: str) -> int:
        """批量更新计划状态"""
        updated_count = self.db.query(Schedule).filter(
            Schedule.id.in_(schedule_ids)
        ).update(
            {"status": status, "updated_at": datetime.utcnow()},
            synchronize_session=False
        )
        
        self.db.commit()
        return updated_count 