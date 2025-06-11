# 内容管理API
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database.database import get_db
from database.models import Content
from services.content_service import ContentService
from schemas.content_schemas import ContentCreate, ContentUpdate, ContentResponse

router = APIRouter(prefix="/api/contents", tags=["内容管理"])

# 依赖注入
def get_content_service(db: Session = Depends(get_db)) -> ContentService:
    return ContentService(db)

@router.get("/", response_model=List[ContentResponse])
async def get_contents(
    account_id: Optional[str] = Query(None, description="账号ID筛选"),
    category: Optional[str] = Query(None, description="内容类型筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    platform: Optional[str] = Query(None, description="平台筛选"),
    limit: int = Query(50, description="返回数量限制"),
    content_service: ContentService = Depends(get_content_service)
):
    """获取内容列表"""
    return content_service.get_contents(
        account_id=account_id, 
        category=category, 
        status=status,
        platform=platform,
        limit=limit
    )

@router.get("/{content_id}", response_model=ContentResponse)
async def get_content(
    content_id: str,
    content_service: ContentService = Depends(get_content_service)
):
    """根据ID获取单个内容信息"""
    content = content_service.get_content_by_id(content_id)
    if not content:
        raise HTTPException(status_code=404, detail="内容不存在")
    return content

@router.post("/", response_model=ContentResponse)
async def create_content(
    content_data: ContentCreate,
    content_service: ContentService = Depends(get_content_service)
):
    """创建新内容"""
    return content_service.create_content(content_data)

@router.put("/{content_id}", response_model=ContentResponse)
async def update_content(
    content_id: str,
    content_data: ContentUpdate,
    content_service: ContentService = Depends(get_content_service)
):
    """更新内容信息"""
    content = content_service.update_content(content_id, content_data)
    if not content:
        raise HTTPException(status_code=404, detail="内容不存在")
    return content

@router.delete("/{content_id}")
async def delete_content(
    content_id: str,
    content_service: ContentService = Depends(get_content_service)
):
    """删除内容"""
    success = content_service.delete_content(content_id)
    if not success:
        raise HTTPException(status_code=404, detail="内容不存在")
    return {"message": "内容删除成功"}

@router.put("/{content_id}/status")
async def update_content_status(
    content_id: str,
    status: str = Query(..., description="新状态"),
    content_service: ContentService = Depends(get_content_service)
):
    """更新内容状态"""
    content = content_service.update_content_status(content_id, status)
    if not content:
        raise HTTPException(status_code=404, detail="内容不存在")
    return content

@router.get("/account/{account_id}/stats")
async def get_account_content_stats(
    account_id: str,
    content_service: ContentService = Depends(get_content_service)
):
    """获取账号内容统计数据"""
    stats = content_service.get_account_content_stats(account_id)
    return stats 