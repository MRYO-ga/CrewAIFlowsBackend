# 人设服务类
from sqlalchemy.orm import Session
from typing import List, Optional
from database.models import PersonaDocument
from schemas.persona_schemas import PersonaDocumentCreate, PersonaDocumentUpdate
import uuid
from datetime import datetime

class PersonaService:
    def __init__(self, db: Session):
        self.db = db

    def get_personas(
        self, 
        platform: Optional[str] = None,
        industry_field: Optional[str] = None,
        account_type: Optional[str] = None,
        limit: int = 50,
        user_id: str = "default_user"
    ) -> List[PersonaDocument]:
        """获取人设文档列表"""
        query = self.db.query(PersonaDocument).filter(PersonaDocument.user_id == user_id)
        
        if platform:
            query = query.filter(PersonaDocument.platform == platform)
        if industry_field:
            query = query.filter(PersonaDocument.industry_field == industry_field)
        if account_type:
            query = query.filter(PersonaDocument.account_type == account_type)
            
        return query.order_by(PersonaDocument.created_at.desc()).limit(limit).all()

    def get_persona_by_id(self, persona_id: str) -> Optional[PersonaDocument]:
        """根据ID获取人设文档"""
        return self.db.query(PersonaDocument).filter(PersonaDocument.id == persona_id).first()

    def create_persona(self, persona_data: PersonaDocumentCreate) -> PersonaDocument:
        """创建新人设文档"""
        persona = PersonaDocument(
            id=str(uuid.uuid4()),
            account_name=persona_data.account_name,
            document_content=persona_data.document_content,
            account_type=persona_data.account_type,
            industry_field=persona_data.industry_field,
            platform=persona_data.platform,
            tags=persona_data.tags,
            summary=persona_data.summary,
            user_id=persona_data.user_id,
            status="completed"
        )
        
        self.db.add(persona)
        self.db.commit()
        self.db.refresh(persona)
        return persona

    def update_persona(self, persona_id: str, persona_data: PersonaDocumentUpdate) -> Optional[PersonaDocument]:
        """更新人设文档"""
        persona = self.get_persona_by_id(persona_id)
        if not persona:
            return None
            
        # 更新字段
        if persona_data.account_name is not None:
            persona.account_name = persona_data.account_name
        if persona_data.document_content is not None:
            persona.document_content = persona_data.document_content
        if persona_data.account_type is not None:
            persona.account_type = persona_data.account_type
        if persona_data.industry_field is not None:
            persona.industry_field = persona_data.industry_field
        if persona_data.platform is not None:
            persona.platform = persona_data.platform
        if persona_data.tags is not None:
            persona.tags = persona_data.tags
        if persona_data.summary is not None:
            persona.summary = persona_data.summary
            
        persona.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(persona)
        return persona

    def delete_persona(self, persona_id: str) -> bool:
        """删除人设文档"""
        persona = self.get_persona_by_id(persona_id)
        if not persona:
            return False
            
        self.db.delete(persona)
        self.db.commit()
        return True

    def get_persona_summary(self, persona_id: str) -> Optional[dict]:
        """获取人设文档摘要信息"""
        persona = self.get_persona_by_id(persona_id)
        if not persona:
            return None
            
        return {
            "id": persona.id,
            "account_name": persona.account_name,
            "account_type": persona.account_type,
            "industry_field": persona.industry_field,
            "platform": persona.platform,
            "summary": persona.summary,
            "tags": persona.tags,
            "created_at": persona.created_at,
            "updated_at": persona.updated_at,
            "status": persona.status
        }

    def search_personas_by_account(self, account_name: str, user_id: str = "default_user") -> List[PersonaDocument]:
        """根据账号名称搜索人设文档"""
        return self.db.query(PersonaDocument).filter(
            PersonaDocument.user_id == user_id,
            PersonaDocument.account_name.contains(account_name)
        ).order_by(PersonaDocument.created_at.desc()).all()

    def get_personas_by_tag(self, tag: str, user_id: str = "default_user") -> List[PersonaDocument]:
        """根据标签搜索人设文档"""
        return self.db.query(PersonaDocument).filter(
            PersonaDocument.user_id == user_id,
            PersonaDocument.tags.contains([tag])
        ).order_by(PersonaDocument.created_at.desc()).all()

    def get_recent_personas(self, days: int = 7, user_id: str = "default_user") -> List[PersonaDocument]:
        """获取最近创建的人设文档"""
        from datetime import datetime, timedelta
        since_date = datetime.utcnow() - timedelta(days=days)
        
        return self.db.query(PersonaDocument).filter(
            PersonaDocument.user_id == user_id,
            PersonaDocument.created_at >= since_date
        ).order_by(PersonaDocument.created_at.desc()).all() 