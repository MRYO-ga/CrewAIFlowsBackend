# 产品服务类
from sqlalchemy.orm import Session
from typing import List, Optional
from database.models import ProductDocument
from schemas.product_schemas import ProductDocumentCreate, ProductDocumentUpdate
import uuid
from datetime import datetime

class ProductService:
    def __init__(self, db: Session):
        self.db = db

    def get_products(
        self, 
        product_category: Optional[str] = None,
        brand_name: Optional[str] = None,
        price_range: Optional[str] = None,
        limit: int = 50,
        user_id: str = "default_user"
    ) -> List[ProductDocument]:
        """获取产品文档列表"""
        query = self.db.query(ProductDocument).filter(ProductDocument.user_id == user_id)
        
        if product_category:
            query = query.filter(ProductDocument.product_category == product_category)
        if brand_name:
            query = query.filter(ProductDocument.brand_name == brand_name)
        if price_range:
            query = query.filter(ProductDocument.price_range == price_range)
            
        return query.order_by(ProductDocument.created_at.desc()).limit(limit).all()

    def get_product_by_id(self, product_id: str) -> Optional[ProductDocument]:
        """根据ID获取产品文档"""
        return self.db.query(ProductDocument).filter(ProductDocument.id == product_id).first()

    def create_product(self, product_data: ProductDocumentCreate) -> ProductDocument:
        """创建新产品文档"""
        product = ProductDocument(
            id=str(uuid.uuid4()),
            product_name=product_data.product_name,
            document_content=product_data.document_content,
            brand_name=product_data.brand_name,
            product_category=product_data.product_category,
            price_range=product_data.price_range,
            target_audience=product_data.target_audience,
            tags=product_data.tags,
            summary=product_data.summary,
            user_id=product_data.user_id,
            status="completed"
        )
        
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        return product

    def update_product(self, product_id: str, product_data: ProductDocumentUpdate) -> Optional[ProductDocument]:
        """更新产品文档"""
        product = self.get_product_by_id(product_id)
        if not product:
            return None
            
        # 更新字段
        if product_data.product_name is not None:
            product.product_name = product_data.product_name
        if product_data.document_content is not None:
            product.document_content = product_data.document_content
        if product_data.brand_name is not None:
            product.brand_name = product_data.brand_name
        if product_data.product_category is not None:
            product.product_category = product_data.product_category
        if product_data.price_range is not None:
            product.price_range = product_data.price_range
        if product_data.target_audience is not None:
            product.target_audience = product_data.target_audience
        if product_data.tags is not None:
            product.tags = product_data.tags
        if product_data.summary is not None:
            product.summary = product_data.summary
            
        product.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(product)
        return product

    def delete_product(self, product_id: str) -> bool:
        """删除产品文档"""
        product = self.get_product_by_id(product_id)
        if not product:
            return False
            
        self.db.delete(product)
        self.db.commit()
        return True

    def get_product_summary(self, product_id: str) -> Optional[dict]:
        """获取产品文档摘要信息"""
        product = self.get_product_by_id(product_id)
        if not product:
            return None
            
        return {
            "id": product.id,
            "product_name": product.product_name,
            "brand_name": product.brand_name,
            "product_category": product.product_category,
            "price_range": product.price_range,
            "target_audience": product.target_audience,
            "summary": product.summary,
            "tags": product.tags,
            "created_at": product.created_at,
            "updated_at": product.updated_at,
            "status": product.status
        }

    def search_products_by_name(self, product_name: str, user_id: str = "default_user") -> List[ProductDocument]:
        """根据产品名称搜索产品文档"""
        return self.db.query(ProductDocument).filter(
            ProductDocument.user_id == user_id,
            ProductDocument.product_name.contains(product_name)
        ).order_by(ProductDocument.created_at.desc()).all()

    def get_products_by_tag(self, tag: str, user_id: str = "default_user") -> List[ProductDocument]:
        """根据标签搜索产品文档"""
        return self.db.query(ProductDocument).filter(
            ProductDocument.user_id == user_id,
            ProductDocument.tags.contains([tag])
        ).order_by(ProductDocument.created_at.desc()).all()

    def get_recent_products(self, days: int = 7, user_id: str = "default_user") -> List[ProductDocument]:
        """获取最近创建的产品文档"""
        from datetime import datetime, timedelta
        since_date = datetime.utcnow() - timedelta(days=days)
        
        return self.db.query(ProductDocument).filter(
            ProductDocument.user_id == user_id,
            ProductDocument.created_at >= since_date
        ).order_by(ProductDocument.created_at.desc()).all()

    def search_products_by_brand(self, brand_name: str, user_id: str = "default_user") -> List[ProductDocument]:
        """根据品牌名称搜索产品文档"""
        return self.db.query(ProductDocument).filter(
            ProductDocument.user_id == user_id,
            ProductDocument.brand_name.contains(brand_name)
        ).order_by(ProductDocument.created_at.desc()).all()

    def get_products_by_category(self, product_category: str, user_id: str = "default_user") -> List[ProductDocument]:
        """根据产品类别获取产品文档"""
        return self.db.query(ProductDocument).filter(
            ProductDocument.user_id == user_id,
            ProductDocument.product_category == product_category
        ).order_by(ProductDocument.created_at.desc()).all() 