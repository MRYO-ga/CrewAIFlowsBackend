# 竞品分析API
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database.database import get_db
from database.models import Competitor
from services.competitor_service import CompetitorService
from schemas.competitor_schemas import CompetitorCreate, CompetitorUpdate, CompetitorResponse, CompetitorNoteResponse

router = APIRouter(prefix="/api/competitors", tags=["竞品分析"])

# 依赖注入
def get_competitor_service(db: Session = Depends(get_db)) -> CompetitorService:
    return CompetitorService(db)

@router.get("/", response_model=List[CompetitorResponse])
async def get_competitors(
    platform: Optional[str] = Query(None, description="平台筛选"),
    tier: Optional[str] = Query(None, description="等级筛选"),
    category: Optional[str] = Query(None, description="类别筛选"),
    limit: int = Query(50, description="返回数量限制"),
    competitor_service: CompetitorService = Depends(get_competitor_service)
):
    """获取竞品列表"""
    return competitor_service.get_competitors(
        platform=platform, 
        tier=tier, 
        category=category, 
        limit=limit
    )

@router.get("/search")
async def search_competitors(
    keyword: str = Query(..., description="搜索关键词"),
    platform: Optional[str] = Query(None, description="平台筛选"),
    limit: int = Query(20, description="返回数量限制"),
    competitor_service: CompetitorService = Depends(get_competitor_service)
):
    """搜索竞品"""
    return competitor_service.search_competitors(keyword, platform, limit)

@router.get("/trending")
async def get_trending_competitors(
    platform: Optional[str] = Query(None, description="平台筛选"),
    limit: int = Query(10, description="返回数量限制"),
    competitor_service: CompetitorService = Depends(get_competitor_service)
):
    """获取热门竞品"""
    return competitor_service.get_trending_competitors(platform, limit)

@router.get("/{competitor_id}", response_model=CompetitorResponse)
async def get_competitor(
    competitor_id: str,
    competitor_service: CompetitorService = Depends(get_competitor_service)
):
    """根据ID获取单个竞品信息"""
    competitor = competitor_service.get_competitor_by_id(competitor_id)
    if not competitor:
        raise HTTPException(status_code=404, detail="竞品不存在")
    return competitor

@router.get("/{competitor_id}/notes", response_model=List[CompetitorNoteResponse])
async def get_competitor_notes(
    competitor_id: str,
    limit: int = Query(20, description="笔记数量限制"),
    competitor_service: CompetitorService = Depends(get_competitor_service)
):
    """获取竞品笔记分析数据"""
    # 先检查竞品是否存在
    competitor = competitor_service.get_competitor_by_id(competitor_id)
    if not competitor:
        raise HTTPException(status_code=404, detail="竞品不存在")
    
    # 获取或初始化笔记数据
    notes = competitor_service.init_sample_notes(competitor_id)
    return notes

@router.post("/", response_model=CompetitorResponse)
async def create_competitor(
    competitor_data: CompetitorCreate,
    competitor_service: CompetitorService = Depends(get_competitor_service)
):
    """创建新竞品分析"""
    return competitor_service.create_competitor(competitor_data)

@router.put("/{competitor_id}", response_model=CompetitorResponse)
async def update_competitor(
    competitor_id: str,
    competitor_data: CompetitorUpdate,
    competitor_service: CompetitorService = Depends(get_competitor_service)
):
    """更新竞品信息"""
    competitor = competitor_service.update_competitor(competitor_id, competitor_data)
    if not competitor:
        raise HTTPException(status_code=404, detail="竞品不存在")
    return competitor

@router.delete("/{competitor_id}")
async def delete_competitor(
    competitor_id: str,
    competitor_service: CompetitorService = Depends(get_competitor_service)
):
    """删除竞品分析"""
    success = competitor_service.delete_competitor(competitor_id)
    if not success:
        raise HTTPException(status_code=404, detail="竞品不存在")
    return {"message": "竞品分析删除成功"} 