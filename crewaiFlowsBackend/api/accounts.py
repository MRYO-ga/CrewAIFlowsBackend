# 人设管理API (替代原账号管理)
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database.database import get_db
from database.models import PersonaDocument
from services.persona_service import PersonaService
from schemas.persona_schemas import PersonaDocumentCreate, PersonaDocumentUpdate, PersonaDocumentResponse

router = APIRouter(prefix="/api/accounts", tags=["人设管理"])

# 依赖注入
def get_persona_service(db: Session = Depends(get_db)) -> PersonaService:
    return PersonaService(db)

@router.get("/", response_model=List[PersonaDocumentResponse])
async def get_personas(
    platform: Optional[str] = Query(None, description="平台筛选"),
    industry_field: Optional[str] = Query(None, description="行业领域筛选"),
    account_type: Optional[str] = Query(None, description="账号类型筛选"),
    limit: int = Query(50, description="返回数量限制"),
    user_id: str = Query("default_user", description="用户ID"),
    persona_service: PersonaService = Depends(get_persona_service)
):
    """获取人设文档列表"""
    return persona_service.get_personas(
        platform=platform, 
        industry_field=industry_field,
        account_type=account_type,
        limit=limit,
        user_id=user_id
    )

@router.get("/{persona_id}", response_model=PersonaDocumentResponse)
async def get_persona(
    persona_id: str,
    persona_service: PersonaService = Depends(get_persona_service)
):
    """根据ID获取单个人设文档"""
    persona = persona_service.get_persona_by_id(persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail="人设文档不存在")
    return persona

@router.post("/", response_model=PersonaDocumentResponse)
async def create_persona(
    persona_data: PersonaDocumentCreate,
    persona_service: PersonaService = Depends(get_persona_service)
):
    """创建新人设文档"""
    return persona_service.create_persona(persona_data)

@router.put("/{persona_id}", response_model=PersonaDocumentResponse)
async def update_persona(
    persona_id: str,
    persona_data: PersonaDocumentUpdate,
    persona_service: PersonaService = Depends(get_persona_service)
):
    """更新人设文档"""
    persona = persona_service.update_persona(persona_id, persona_data)
    if not persona:
        raise HTTPException(status_code=404, detail="人设文档不存在")
    return persona

@router.delete("/{persona_id}")
async def delete_persona(
    persona_id: str,
    persona_service: PersonaService = Depends(get_persona_service)
):
    """删除人设文档"""
    success = persona_service.delete_persona(persona_id)
    if not success:
        raise HTTPException(status_code=404, detail="人设文档不存在")
    return {"message": "人设文档删除成功"}

@router.get("/{persona_id}/summary")
async def get_persona_summary(
    persona_id: str,
    persona_service: PersonaService = Depends(get_persona_service)
):
    """获取人设文档摘要信息"""
    summary = persona_service.get_persona_summary(persona_id)
    if not summary:
        raise HTTPException(status_code=404, detail="人设文档不存在")
    return summary

@router.get("/search/{account_name}")
async def search_personas_by_account(
    account_name: str,
    user_id: str = Query("default_user", description="用户ID"),
    persona_service: PersonaService = Depends(get_persona_service)
):
    """根据账号名称搜索人设文档"""
    return persona_service.search_personas_by_account(account_name, user_id) 