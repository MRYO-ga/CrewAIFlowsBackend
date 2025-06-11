# 竞品服务层
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from database.models import Competitor, CompetitorNote
from schemas.competitor_schemas import CompetitorCreate, CompetitorUpdate, CompetitorResponse, CompetitorNoteCreate, CompetitorNoteResponse

class CompetitorService:
    def __init__(self, db: Session):
        self.db = db

    def get_competitors(
        self, 
        platform: Optional[str] = None,
        tier: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 50
    ) -> List[CompetitorResponse]:
        """获取竞品列表"""
        query = self.db.query(Competitor)
        
        # 添加筛选条件
        if platform:
            query = query.filter(Competitor.platform == platform)
        if tier:
            query = query.filter(Competitor.tier == tier)
        if category:
            query = query.filter(Competitor.category == category)
            
        # 排序和限制
        competitors = query.order_by(desc(Competitor.explosion_rate)).limit(limit).all()
        
        return [CompetitorResponse.model_validate(competitor) for competitor in competitors]

    def get_competitor_by_id(self, competitor_id: str) -> Optional[CompetitorResponse]:
        """根据ID获取竞品"""
        competitor = self.db.query(Competitor).filter(Competitor.id == competitor_id).first()
        if competitor:
            return CompetitorResponse.model_validate(competitor)
        return None

    def create_competitor(self, competitor_data: CompetitorCreate) -> CompetitorResponse:
        """创建新竞品分析"""
        # 生成唯一ID
        competitor_id = str(uuid.uuid4())[:8]
        
        # 创建竞品对象
        db_competitor = Competitor(
            id=competitor_id,
            name=competitor_data.name,
            account_id=competitor_data.account_id,
            platform=competitor_data.platform,
            tier=competitor_data.tier,
            category=competitor_data.category,
            followers=competitor_data.followers,
            explosion_rate=competitor_data.explosion_rate or 0.0,
            last_update=datetime.now().strftime('%Y-%m-%d'),
            analysis_count=competitor_data.analysis_count or 0,
            avatar=competitor_data.avatar,
            profile_url=competitor_data.profile_url,
            tags=competitor_data.tags or [],
            analysis_document=competitor_data.analysis_document
        )
        
        self.db.add(db_competitor)
        self.db.commit()
        self.db.refresh(db_competitor)
        
        return CompetitorResponse.model_validate(db_competitor)

    def update_competitor(self, competitor_id: str, competitor_data: CompetitorUpdate) -> Optional[CompetitorResponse]:
        """更新竞品信息"""
        db_competitor = self.db.query(Competitor).filter(Competitor.id == competitor_id).first()
        if not db_competitor:
            return None

        # 更新字段
        update_data = competitor_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(db_competitor, field):
                setattr(db_competitor, field, value)
        
        # 更新最后修改时间
        db_competitor.last_update = datetime.now().strftime('%Y-%m-%d')
        
        self.db.commit()
        self.db.refresh(db_competitor)
        
        return CompetitorResponse.model_validate(db_competitor)

    def delete_competitor(self, competitor_id: str) -> bool:
        """删除竞品分析"""
        db_competitor = self.db.query(Competitor).filter(Competitor.id == competitor_id).first()
        if not db_competitor:
            return False
            
        self.db.delete(db_competitor)
        self.db.commit()
        return True

    def search_competitors(self, keyword: str, platform: Optional[str] = None, limit: int = 20) -> List[CompetitorResponse]:
        """搜索竞品"""
        query = self.db.query(Competitor).filter(
            or_(
                Competitor.name.contains(keyword),
                Competitor.category.contains(keyword),
                Competitor.account_id.contains(keyword)
            )
        )
        
        if platform:
            query = query.filter(Competitor.platform == platform)
            
        competitors = query.order_by(desc(Competitor.explosion_rate)).limit(limit).all()
        return [CompetitorResponse.model_validate(competitor) for competitor in competitors]

    def get_trending_competitors(self, platform: Optional[str] = None, limit: int = 10) -> List[CompetitorResponse]:
        """获取热门竞品"""
        query = self.db.query(Competitor)
        
        if platform:
            query = query.filter(Competitor.platform == platform)
            
        # 按爆款率排序
        competitors = query.order_by(desc(Competitor.explosion_rate)).limit(limit).all()
        return [CompetitorResponse.model_validate(competitor) for competitor in competitors]

    # ===== 竞品笔记相关方法 =====
    
    def get_competitor_notes(self, competitor_id: str, limit: int = 20) -> List[CompetitorNoteResponse]:
        """获取竞品笔记列表"""
        notes = self.db.query(CompetitorNote).filter(
            CompetitorNote.competitor_id == competitor_id
        ).order_by(desc(CompetitorNote.viral_score)).limit(limit).all()
        
        return [CompetitorNoteResponse.model_validate(note) for note in notes]
    
    def create_competitor_note(self, note_data: CompetitorNoteCreate) -> CompetitorNoteResponse:
        """创建竞品笔记"""
        note_id = str(uuid.uuid4())[:12]
        
        db_note = CompetitorNote(
            id=note_id,
            competitor_id=note_data.competitor_id,
            note_id=note_data.note_id,
            title=note_data.title,
            content_preview=note_data.content_preview,
            upload_time=note_data.upload_time,
            likes=note_data.likes,
            collects=note_data.collects,
            comments=note_data.comments,
            shares=note_data.shares,
            views=note_data.views,
            engagement_rate=note_data.engagement_rate,
            is_viral=note_data.is_viral,
            viral_score=note_data.viral_score,
            content_type=note_data.content_type,
            topics=note_data.topics or [],
            performance_rank=note_data.performance_rank,
            analysis=note_data.analysis or {}
        )
        
        self.db.add(db_note)
        self.db.commit()
        self.db.refresh(db_note)
        
        return CompetitorNoteResponse.model_validate(db_note)
        
    def init_sample_notes(self, competitor_id: str) -> List[CompetitorNoteResponse]:
        """为竞品初始化示例笔记数据"""
        # 检查是否已经有笔记数据
        existing_notes = self.db.query(CompetitorNote).filter(
            CompetitorNote.competitor_id == competitor_id
        ).count()
        
        if existing_notes > 0:
            return self.get_competitor_notes(competitor_id)
        
        # 创建示例笔记数据
        sample_notes = [
            {
                "note_id": "676e9cde000000001300b211",
                "title": "2024年终回顾｜INFJ重新出发",
                "content_preview": "这一年过得很快，也很慢。作为一个INFJ，我总是习惯在年末的时候...",
                "upload_time": "2024-03-18 20:30",
                "likes": 12580,
                "collects": 8960,
                "comments": 456,
                "shares": 123,
                "views": 156789,
                "engagement_rate": 14.2,
                "is_viral": True,
                "viral_score": 85,
                "content_type": "图文",
                "topics": ["年终总结", "个人成长", "情感"],
                "performance_rank": 1,
                "analysis": {
                    "爆款原因": "时机恰当（年终）+ 情感共鸣 + 身份标签精准",
                    "内容特点": "真实感强，情感表达细腻，结构完整",
                    "可复制点": "年终回顾模板，INFJ人群定位，情感共鸣写法"
                }
            },
            {
                "note_id": "67171e4f0000000021007009",
                "title": "24岁生日感悟｜成年人的崩溃与重建",
                "content_preview": "昨天是我24岁生日，没有蛋糕没有派对，就是很平常的一天...",
                "upload_time": "2024-03-15 19:45",
                "likes": 8965,
                "collects": 6234,
                "comments": 289,
                "shares": 87,
                "views": 89456,
                "engagement_rate": 17.8,
                "is_viral": True,
                "viral_score": 78,
                "content_type": "图文",
                "topics": ["生日感悟", "成长", "青春"],
                "performance_rank": 2,
                "analysis": {
                    "爆款原因": "生日节点 + 年龄焦虑 + 真实感受分享",
                    "内容特点": "平实的语言，真挚的情感，引发共鸣",
                    "可复制点": "生日感悟模板，年龄焦虑话题，真实感表达"
                }
            },
            {
                "note_id": "670d8f2a00000000210078a5",
                "title": "换季护肤攻略｜敏感肌的秋冬救星",
                "content_preview": "最近天气转凉，敏感肌的姐妹们是不是又开始担心换季烂脸了...",
                "upload_time": "2024-03-12 21:15",
                "likes": 15680,
                "collects": 12890,
                "comments": 678,
                "shares": 234,
                "views": 198765,
                "engagement_rate": 14.8,
                "is_viral": True,
                "viral_score": 82,
                "content_type": "图文",
                "topics": ["护肤", "敏感肌", "换季"],
                "performance_rank": 3,
                "analysis": {
                    "爆款原因": "季节性需求 + 痛点精准 + 解决方案实用",
                    "内容特点": "专业性强，实用性高，产品推荐具体",
                    "可复制点": "换季护肤模板，敏感肌定位，产品推荐逻辑"
                }
            }
        ]
        
        # 创建笔记记录
        created_notes = []
        for note_data in sample_notes:
            note_create = CompetitorNoteCreate(
                competitor_id=competitor_id,
                **note_data
            )
            created_note = self.create_competitor_note(note_create)
            created_notes.append(created_note)
        
        return created_notes 