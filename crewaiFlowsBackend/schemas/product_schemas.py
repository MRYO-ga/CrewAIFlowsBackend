# 产品品牌信息schemas
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ProductDocumentBase(BaseModel):
    """产品文档基础模型"""
    product_name: str = Field(..., description="产品名称")
    document_content: str = Field(..., description="产品信息穿透完整文档内容")
    brand_name: Optional[str] = Field(None, description="品牌名称")
    product_category: Optional[str] = Field(None, description="产品类别")
    price_range: Optional[str] = Field(None, description="价格区间")
    target_audience: Optional[str] = Field(None, description="目标用户群体")
    tags: Optional[List[str]] = Field(None, description="标签列表")
    summary: Optional[str] = Field(None, description="简短摘要")
    user_id: str = Field("default_user", description="用户ID")


class ProductDocumentCreate(ProductDocumentBase):
    """创建产品文档模型"""
    pass


class ProductDocumentUpdate(BaseModel):
    """更新产品文档模型"""
    product_name: Optional[str] = Field(None, description="产品名称")
    document_content: Optional[str] = Field(None, description="产品信息穿透完整文档内容")
    brand_name: Optional[str] = Field(None, description="品牌名称")
    product_category: Optional[str] = Field(None, description="产品类别")
    price_range: Optional[str] = Field(None, description="价格区间")
    target_audience: Optional[str] = Field(None, description="目标用户群体")
    tags: Optional[List[str]] = Field(None, description="标签列表")
    summary: Optional[str] = Field(None, description="简短摘要")


class ProductDocumentResponse(ProductDocumentBase):
    """产品文档响应模型"""
    id: str
    status: str
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True 