# 账号服务层
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid

from database.models import Account, Content, Analytics
from schemas.account_schemas import AccountCreate, AccountUpdate, AccountResponse, AccountAnalyticsResponse

class AccountService:
    def __init__(self, db: Session):
        self.db = db

    def get_accounts(
        self, 
        platform: Optional[str] = None,
        status: Optional[str] = None, 
        limit: int = 50
    ) -> List[AccountResponse]:
        """获取账号列表"""
        query = self.db.query(Account)
        
        # 添加筛选条件
        if platform:
            query = query.filter(Account.platform == platform)
        if status:
            query = query.filter(Account.status == status)
            
        # 排序和限制
        accounts = query.order_by(desc(Account.updated_at_timestamp)).limit(limit).all()
        
        return [AccountResponse.model_validate(account) for account in accounts]

    def get_account_by_id(self, account_id: str) -> Optional[AccountResponse]:
        """根据ID获取账号"""
        account = self.db.query(Account).filter(Account.id == account_id).first()
        if account:
            return AccountResponse.model_validate(account)
        return None

    def create_account(self, account_data: AccountCreate) -> AccountResponse:
        """创建新账号"""
        # 生成唯一ID
        account_id = str(uuid.uuid4())[:8]
        
        # 创建账号对象
        db_account = Account(
            id=account_id,
            name=account_data.name,
            platform=account_data.platform,
            account_id=account_data.account_id,
            avatar=account_data.avatar,
            status=account_data.status,
            created_at=account_data.created_at or datetime.now().strftime('%Y-%m-%d'),
            last_updated=datetime.now().strftime('%Y-%m-%d'),
            followers=account_data.followers or 0,
            notes=account_data.notes or 0,
            engagement=account_data.engagement or 0.0,
            avg_views=account_data.avg_views or 0,
            verified=account_data.verified or False,
            content_count=account_data.content_count or 0,
            bio=account_data.bio,
            tags=account_data.tags or [],
            target_audience=account_data.target_audience or {},
            positioning=account_data.positioning or {},
            content_strategy=account_data.content_strategy or {},
            monetization=account_data.monetization or {}
        )
        
        self.db.add(db_account)
        self.db.commit()
        self.db.refresh(db_account)
        
        return AccountResponse.model_validate(db_account)

    def update_account(self, account_id: str, account_data: AccountUpdate) -> Optional[AccountResponse]:
        """更新账号信息"""
        db_account = self.db.query(Account).filter(Account.id == account_id).first()
        if not db_account:
            return None

        # 更新字段
        update_data = account_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(db_account, field):
                setattr(db_account, field, value)
        
        # 更新最后修改时间
        db_account.last_updated = datetime.now().strftime('%Y-%m-%d')
        
        self.db.commit()
        self.db.refresh(db_account)
        
        return AccountResponse.model_validate(db_account)

    def delete_account(self, account_id: str) -> bool:
        """删除账号"""
        db_account = self.db.query(Account).filter(Account.id == account_id).first()
        if not db_account:
            return False
            
        self.db.delete(db_account)
        self.db.commit()
        return True

    def get_account_analytics(self, account_id: str, days: int = 30) -> Optional[AccountAnalyticsResponse]:
        """获取账号数据分析"""
        # 检查账号是否存在
        account = self.db.query(Account).filter(Account.id == account_id).first()
        if not account:
            return None

        # 计算日期范围
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # 获取内容统计
        contents = self.db.query(Content).filter(
            and_(
                Content.account_id == account_id,
                Content.created_at_timestamp >= start_date
            )
        ).all()

        # 计算总览数据
        total_views = sum(content.stats.get('views', 0) if content.stats else 0 for content in contents)
        total_likes = sum(content.stats.get('likes', 0) if content.stats else 0 for content in contents)
        total_comments = sum(content.stats.get('comments', 0) if content.stats else 0 for content in contents)
        total_shares = sum(content.stats.get('shares', 0) if content.stats else 0 for content in contents)

        # 找出最佳表现内容
        best_content = None
        if contents:
            best_content = max(contents, key=lambda x: x.stats.get('likes', 0) if x.stats else 0)
            best_content = {
                'id': best_content.id,
                'title': best_content.title,
                'likes': best_content.stats.get('likes', 0) if best_content.stats else 0,
                'views': best_content.stats.get('views', 0) if best_content.stats else 0
            }

        # 内容类型分布
        content_type_breakdown = {}
        for content in contents:
            category = content.category or 'other'
            content_type_breakdown[category] = content_type_breakdown.get(category, 0) + 1

        return AccountAnalyticsResponse(
            account_id=account_id,
            account_name=account.name,
            total_views=total_views,
            total_likes=total_likes,
            total_comments=total_comments,
            total_shares=total_shares,
            followers_growth=0,  # 这里可以根据历史数据计算
            avg_engagement_rate=account.engagement,
            content_published=len(contents),
            best_performing_content=best_content,
            content_type_breakdown=content_type_breakdown,
            growth_trend=[]  # 可以根据需要计算增长趋势
        )

    def search_accounts(self, keyword: str, platform: Optional[str] = None, limit: int = 20) -> List[AccountResponse]:
        """搜索账号"""
        query = self.db.query(Account).filter(
            or_(
                Account.name.contains(keyword),
                Account.bio.contains(keyword),
                Account.account_id.contains(keyword)
            )
        )
        
        if platform:
            query = query.filter(Account.platform == platform)
            
        accounts = query.order_by(desc(Account.followers)).limit(limit).all()
        return [AccountResponse.model_validate(account) for account in accounts]

    def get_platform_stats(self) -> Dict[str, Any]:
        """获取平台统计信息"""
        stats = {}
        
        # 按平台统计账号数量
        platform_counts = self.db.query(Account.platform, Account.status).all()
        
        for platform, status in platform_counts:
            if platform not in stats:
                stats[platform] = {'total': 0, 'active': 0, 'inactive': 0}
            stats[platform]['total'] += 1
            if status == 'active':
                stats[platform]['active'] += 1
            else:
                stats[platform]['inactive'] += 1
                
        return stats 