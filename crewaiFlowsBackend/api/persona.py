# 人设构建API模块
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import uuid

from database.database import get_db
from database.models import PersonaDocument
from sqlalchemy.orm import Session

# 创建路由器
persona_router = APIRouter(prefix="/api/persona", tags=["persona"])

# 定义请求模型
class PersonaDocumentCreate(BaseModel):
    """人设构建文档创建模型"""
    account_name: str = Field(..., description="账号名称")
    document_content: str = Field(..., description="人设构建完整文档内容")
    account_type: Optional[str] = Field(None, description="账号类型")
    industry_field: Optional[str] = Field(None, description="行业领域")
    platform: str = Field("xiaohongshu", description="平台")
    tags: Optional[List[str]] = Field(None, description="标签列表")
    summary: Optional[str] = Field(None, description="简短摘要")
    user_id: str = Field("default_user", description="用户ID")

class PersonaDocumentResponse(BaseModel):
    """人设构建文档响应模型"""
    id: str
    account_name: str
    document_content: str
    account_type: Optional[str]
    industry_field: Optional[str]
    platform: str
    status: str
    created_at: datetime
    updated_at: datetime
    completed_at: datetime
    user_id: str
    tags: Optional[List[str]]
    summary: Optional[str]

    class Config:
        from_attributes = True

@persona_router.post("/documents", response_model=PersonaDocumentResponse)
async def create_persona_document(
    document_data: PersonaDocumentCreate,
    db: Session = Depends(get_db)
):
    """创建人设构建文档"""
    try:
        # 创建新的人设文档
        persona_doc = PersonaDocument(
            id=str(uuid.uuid4()),
            account_name=document_data.account_name,
            document_content=document_data.document_content,
            account_type=document_data.account_type,
            industry_field=document_data.industry_field,
            platform=document_data.platform,
            tags=document_data.tags,
            summary=document_data.summary,
            user_id=document_data.user_id,
            status="completed"
        )
        
        db.add(persona_doc)
        db.commit()
        db.refresh(persona_doc)
        
        return persona_doc
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建人设文档失败: {str(e)}")

@persona_router.get("/documents", response_model=List[PersonaDocumentResponse])
async def get_persona_documents(
    user_id: str = "default_user",
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """获取人设构建文档列表"""
    try:
        documents = db.query(PersonaDocument).filter(
            PersonaDocument.user_id == user_id
        ).order_by(
            PersonaDocument.created_at.desc()
        ).offset(offset).limit(limit).all()
        
        return documents
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取人设文档列表失败: {str(e)}")

@persona_router.get("/documents/{document_id}", response_model=PersonaDocumentResponse)
async def get_persona_document(
    document_id: str,
    db: Session = Depends(get_db)
):
    """获取单个人设构建文档"""
    try:
        document = db.query(PersonaDocument).filter(
            PersonaDocument.id == document_id
        ).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="人设文档不存在")
            
        return document
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取人设文档失败: {str(e)}")

@persona_router.put("/documents/{document_id}", response_model=PersonaDocumentResponse)
async def update_persona_document(
    document_id: str,
    document_data: PersonaDocumentCreate,
    db: Session = Depends(get_db)
):
    """更新人设构建文档"""
    try:
        document = db.query(PersonaDocument).filter(
            PersonaDocument.id == document_id
        ).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="人设文档不存在")
        
        # 更新文档信息
        document.account_name = document_data.account_name
        document.document_content = document_data.document_content
        document.account_type = document_data.account_type
        document.industry_field = document_data.industry_field
        document.platform = document_data.platform
        document.tags = document_data.tags
        document.summary = document_data.summary
        document.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(document)
        
        return document
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新人设文档失败: {str(e)}")

@persona_router.delete("/documents/{document_id}")
async def delete_persona_document(
    document_id: str,
    db: Session = Depends(get_db)
):
    """删除人设构建文档"""
    try:
        document = db.query(PersonaDocument).filter(
            PersonaDocument.id == document_id
        ).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="人设文档不存在")
        
        db.delete(document)
        db.commit()
        
        return {"message": "人设文档删除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除人设文档失败: {str(e)}")

@persona_router.get("/documents/search/{account_name}", response_model=List[PersonaDocumentResponse])
async def search_persona_documents_by_account(
    account_name: str,
    user_id: str = "default_user",
    db: Session = Depends(get_db)
):
    """根据账号名称搜索人设构建文档"""
    try:
        documents = db.query(PersonaDocument).filter(
            PersonaDocument.user_id == user_id,
            PersonaDocument.account_name.contains(account_name)
        ).order_by(
            PersonaDocument.created_at.desc()
        ).all()
        
        return documents
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索人设文档失败: {str(e)}") 