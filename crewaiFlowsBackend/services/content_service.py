# 内容服务层
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from database.models import Content, Account
from schemas.content_schemas import ContentCreate, ContentUpdate, ContentResponse

class ContentService:
    def __init__(self, db: Session):
        self.db = db

    def get_contents(
        self, 
        account_id: Optional[str] = None,
        category: Optional[str] = None,
        status: Optional[str] = None,
        platform: Optional[str] = None,
        limit: int = 50
    ) -> List[ContentResponse]:
        """获取内容列表"""
        query = self.db.query(Content)
        
        # 添加筛选条件
        if account_id:
            query = query.filter(Content.account_id == account_id)
        if category:
            query = query.filter(Content.category == category)
        if status:
            query = query.filter(Content.status == status)
        if platform:
            query = query.filter(Content.platform == platform)
            
        # 排序和限制
        contents = query.order_by(desc(Content.updated_at_timestamp)).limit(limit).all()
        
        return [ContentResponse.model_validate(content) for content in contents]

    def get_content_by_id(self, content_id: str) -> Optional[ContentResponse]:
        """根据ID获取内容"""
        content = self.db.query(Content).filter(Content.id == content_id).first()
        if content:
            return ContentResponse.model_validate(content)
        return None

    def create_content(self, content_data: ContentCreate) -> ContentResponse:
        """创建新内容"""
        # 生成唯一ID
        content_id = str(uuid.uuid4())[:8]
        
        # 创建内容对象
        db_content = Content(
            id=content_id,
            title=content_data.title,
            cover=content_data.cover,
            description=content_data.description,
            content=content_data.content,
            category=content_data.category,
            status=content_data.status,
            created_at=content_data.created_at or datetime.now().strftime('%Y-%m-%d %H:%M'),
            platform=content_data.platform or "xiaohongshu",
            account_id=content_data.account_id,
            stats=content_data.stats or {},
            tags=content_data.tags or []
        )
        
        self.db.add(db_content)
        self.db.commit()
        self.db.refresh(db_content)
        
        return ContentResponse.model_validate(db_content)

    def update_content(self, content_id: str, content_data: ContentUpdate) -> Optional[ContentResponse]:
        """更新内容信息"""
        db_content = self.db.query(Content).filter(Content.id == content_id).first()
        if not db_content:
            return None

        # 更新字段
        update_data = content_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(db_content, field):
                setattr(db_content, field, value)
        
        self.db.commit()
        self.db.refresh(db_content)
        
        return ContentResponse.model_validate(db_content)

    def delete_content(self, content_id: str) -> bool:
        """删除内容"""
        db_content = self.db.query(Content).filter(Content.id == content_id).first()
        if not db_content:
            return False
            
        self.db.delete(db_content)
        self.db.commit()
        return True

    def update_content_status(self, content_id: str, status: str) -> Optional[ContentResponse]:
        """更新内容状态"""
        db_content = self.db.query(Content).filter(Content.id == content_id).first()
        if not db_content:
            return None
            
        db_content.status = status
        if status == 'published':
            db_content.published_at = datetime.now().strftime('%Y-%m-%d %H:%M')
        
        self.db.commit()
        self.db.refresh(db_content)
        
        return ContentResponse.model_validate(db_content)

    def get_account_content_stats(self, account_id: str) -> Dict[str, Any]:
        """获取账号内容统计数据"""
        contents = self.db.query(Content).filter(Content.account_id == account_id).all()
        
        # 按状态统计
        status_stats = {}
        category_stats = {}
        total_views = 0
        total_likes = 0
        
        for content in contents:
            # 状态统计
            status = content.status or 'unknown'
            status_stats[status] = status_stats.get(status, 0) + 1
            
            # 分类统计
            category = content.category or 'other'
            category_stats[category] = category_stats.get(category, 0) + 1
            
            # 数据统计
            if content.stats:
                total_views += content.stats.get('views', 0)
                total_likes += content.stats.get('likes', 0)
        
        return {
            'total_content': len(contents),
            'status_breakdown': status_stats,
            'category_breakdown': category_stats,
            'total_views': total_views,
            'total_likes': total_likes,
            'avg_views_per_content': total_views / len(contents) if contents else 0,
            'avg_likes_per_content': total_likes / len(contents) if contents else 0
        } 