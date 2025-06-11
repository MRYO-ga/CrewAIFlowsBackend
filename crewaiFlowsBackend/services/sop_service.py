# SOP服务层
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
import json

from database.models import SOP, SOPCycle, SOPWeek, SOPTask, SOPTaskItem
from schemas.sop_schemas import (
    SOPCreate, SOPUpdate, SOPResponse, SOPListResponse,
    SOPCycleCreate, SOPCycleUpdate, SOPCycleResponse,
    SOPWeekCreate, SOPWeekUpdate, SOPWeekResponse,
    SOPTaskCreate, SOPTaskUpdate, SOPTaskResponse,
    SOPTaskItemCreate, SOPTaskItemUpdate, SOPTaskItemResponse
)

class SOPService:
    def __init__(self, db: Session):
        self.db = db

    def get_sops(self, sop_type: Optional[str] = None, status: Optional[str] = None, limit: int = 50) -> List[SOPListResponse]:
        """获取SOP列表"""
        query = self.db.query(SOP)
        
        if sop_type:
            query = query.filter(SOP.type == sop_type)
        if status:
            query = query.filter(SOP.status == status)
            
        sops = query.order_by(desc(SOP.created_at)).limit(limit).all()
        
        # 转换为列表响应格式
        result = []
        for sop in sops:
            cycles_count = self.db.query(SOPCycle).filter(SOPCycle.sop_id == sop.id).count()
            result.append(SOPListResponse(
                id=sop.id,
                title=sop.title,
                type=sop.type,
                status=sop.status,
                created_at=sop.created_at,
                cycles_count=cycles_count
            ))
        
        return result

    def get_sop_by_id(self, sop_id: str) -> Optional[SOPResponse]:
        """根据ID获取完整SOP数据"""
        sop = self.db.query(SOP).filter(SOP.id == sop_id).first()
        if not sop:
            return None
            
        return SOPResponse.model_validate(sop)

    def create_sop(self, sop_data: SOPCreate) -> SOPResponse:
        """创建新SOP"""
        sop_id = str(uuid.uuid4())
        
        # 创建SOP主记录
        db_sop = SOP(
            id=sop_id,
            title=sop_data.title,
            type=sop_data.type,
            description=sop_data.description,
            status=sop_data.status,
            created_at=sop_data.created_at
        )
        
        self.db.add(db_sop)
        self.db.flush()  # 获取ID
        
        # 创建周期数据
        for cycle_index, cycle_data in enumerate(sop_data.cycles):
            cycle_id = str(uuid.uuid4())[:12]
            
            db_cycle = SOPCycle(
                id=cycle_id,
                sop_id=sop_id,
                cycle_key=cycle_data.cycle_key,
                title=cycle_data.title,
                subtitle=cycle_data.subtitle,
                duration=cycle_data.duration,
                status=cycle_data.status,
                icon=cycle_data.icon,
                color=cycle_data.color,
                progress=cycle_data.progress,
                goal=cycle_data.goal,
                order_index=cycle_index
            )
            
            self.db.add(db_cycle)
            self.db.flush()
            
            # 创建周数据
            for week_index, week_data in enumerate(cycle_data.weeks):
                week_id = str(uuid.uuid4())[:12]
                
                db_week = SOPWeek(
                    id=week_id,
                    cycle_id=cycle_id,
                    week_key=week_data.week_key,
                    title=week_data.title,
                    status=week_data.status,
                    order_index=week_index
                )
                
                self.db.add(db_week)
                self.db.flush()
                
                # 创建任务数据
                for task_index, task_data in enumerate(week_data.tasks):
                    task_id = str(uuid.uuid4())[:12]
                    
                    db_task = SOPTask(
                        id=task_id,
                        week_id=week_id,
                        task_key=task_data.task_key,
                        category=task_data.category,
                        completed=task_data.completed,
                        order_index=task_index
                    )
                    
                    self.db.add(db_task)
                    self.db.flush()
                    
                    # 创建任务项数据
                    for item_index, item_data in enumerate(task_data.items):
                        item_id = str(uuid.uuid4())[:12]
                        
                        db_item = SOPTaskItem(
                            id=item_id,
                            task_id=task_id,
                            item_key=item_data.item_key,
                            time=item_data.time,
                            action=item_data.action,
                            content=item_data.content,
                            example=item_data.example,
                            publish_time=item_data.publish_time,
                            reason=item_data.reason,
                            completed=item_data.completed,
                            order_index=item_index
                        )
                        
                        self.db.add(db_item)
        
        self.db.commit()
        self.db.refresh(db_sop)
        
        return SOPResponse.model_validate(db_sop)

    def update_sop(self, sop_id: str, sop_data: SOPUpdate) -> Optional[SOPResponse]:
        """更新SOP信息"""
        db_sop = self.db.query(SOP).filter(SOP.id == sop_id).first()
        if not db_sop:
            return None

        # 更新字段
        update_data = sop_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(db_sop, field):
                setattr(db_sop, field, value)
        
        if not db_sop.updated_at:
            db_sop.updated_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        self.db.commit()
        self.db.refresh(db_sop)
        
        return SOPResponse.model_validate(db_sop)

    def delete_sop(self, sop_id: str) -> bool:
        """删除SOP"""
        db_sop = self.db.query(SOP).filter(SOP.id == sop_id).first()
        if not db_sop:
            return False
            
        self.db.delete(db_sop)
        self.db.commit()
        return True

    def update_task_item_status(self, item_id: str, completed: bool) -> Optional[SOPTaskItemResponse]:
        """更新任务项完成状态"""
        # 首先尝试通过ID查找
        db_item = self.db.query(SOPTaskItem).filter(SOPTaskItem.id == item_id).first()
        
        # 如果通过ID找不到，尝试通过item_key查找
        if not db_item:
            db_item = self.db.query(SOPTaskItem).filter(SOPTaskItem.item_key == item_id).first()
        
        if not db_item:
            return None
            
        db_item.completed = completed
        self.db.commit()
        self.db.refresh(db_item)
        
        return SOPTaskItemResponse.model_validate(db_item)

    def get_sop_progress(self, sop_id: str) -> Dict[str, Any]:
        """获取SOP整体进度"""
        sop = self.db.query(SOP).filter(SOP.id == sop_id).first()
        if not sop:
            return {}
        
        # 统计任务项完成情况
        total_items = 0
        completed_items = 0
        
        for cycle in sop.cycles:
            for week in cycle.weeks:
                for task in week.tasks:
                    for item in task.items:
                        total_items += 1
                        if item.completed:
                            completed_items += 1
        
        progress_percentage = (completed_items / total_items * 100) if total_items > 0 else 0
        
        return {
            'sop_id': sop_id,
            'total_items': total_items,
            'completed_items': completed_items,
            'progress_percentage': round(progress_percentage, 1),
            'cycles_progress': [
                {
                    'cycle_id': cycle.id,
                    'cycle_key': cycle.cycle_key,
                    'title': cycle.title,
                    'progress': cycle.progress
                }
                for cycle in sop.cycles
            ]
        }

    def import_sop_from_json(self, json_data: Dict[str, Any]) -> SOPResponse:
        """从JSON数据导入SOP"""
        # 解析JSON数据并创建SOP
        sop_create_data = {
            'title': json_data['title'],
            'type': json_data['type'],
            'description': f"导入于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            'status': 'active',
            'created_at': json_data['created_at'],
            'cycles': []
        }
        
        # 解析周期数据
        for cycle_data in json_data['cycles']:
            cycle_create = {
                'cycle_key': cycle_data['id'],
                'title': cycle_data['title'],
                'subtitle': cycle_data['subtitle'],
                'duration': cycle_data['duration'],
                'status': cycle_data['status'],
                'icon': cycle_data['icon'],
                'color': cycle_data['color'],
                'progress': cycle_data['progress'],
                'goal': cycle_data['goal'],
                'order_index': 0,
                'weeks': []
            }
            
            # 解析周数据
            if 'weeks' in cycle_data:
                for week_data in cycle_data['weeks']:
                    week_create = {
                        'week_key': week_data['id'],
                        'title': week_data['title'],
                        'status': week_data['status'],
                        'order_index': 0,
                        'tasks': []
                    }
                    
                    # 解析任务数据
                    if 'tasks' in week_data:
                        for task_data in week_data['tasks']:
                            task_create = {
                                'task_key': task_data['id'],
                                'category': task_data['category'],
                                'completed': task_data.get('completed', False),
                                'order_index': 0,
                                'items': []
                            }
                            
                            # 解析任务项数据
                            if 'items' in task_data:
                                for item_data in task_data['items']:
                                    item_create = {
                                        'item_key': item_data['id'],
                                        'time': item_data.get('time'),
                                        'action': item_data['action'],
                                        'content': item_data['content'],
                                        'example': item_data.get('example'),
                                        'publish_time': item_data.get('publishTime'),
                                        'reason': item_data.get('reason'),
                                        'completed': item_data.get('completed', False),
                                        'order_index': 0
                                    }
                                    task_create['items'].append(item_create)
                            
                            week_create['tasks'].append(task_create)
                    
                    cycle_create['weeks'].append(week_create)
            
            sop_create_data['cycles'].append(cycle_create)
        
        # 创建SOP
        sop_create = SOPCreate(**sop_create_data)
        return self.create_sop(sop_create) 