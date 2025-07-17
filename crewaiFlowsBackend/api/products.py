# 产品品牌信息管理API
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database.database import get_db
from database.models import ProductDocument
from services.product_service import ProductService
from schemas.product_schemas import ProductDocumentCreate, ProductDocumentUpdate, ProductDocumentResponse

# 创建路由器 - 为了兼容现有的导航，使用 /api/products 路径
router = APIRouter(prefix="/api/products", tags=["产品品牌信息管理"])

# 依赖注入
def get_product_service(db: Session = Depends(get_db)) -> ProductService:
    return ProductService(db)

@router.get("/", response_model=List[ProductDocumentResponse])
async def get_products(
    product_category: Optional[str] = Query(None, description="产品类别筛选"),
    brand_name: Optional[str] = Query(None, description="品牌名称筛选"),
    price_range: Optional[str] = Query(None, description="价格区间筛选"),
    limit: int = Query(50, description="返回数量限制"),
    user_id: str = Query("default_user", description="用户ID"),
    product_service: ProductService = Depends(get_product_service)
):
    """获取产品文档列表"""
    return product_service.get_products(
        product_category=product_category, 
        brand_name=brand_name,
        price_range=price_range,
        limit=limit,
        user_id=user_id
    )

@router.get("/{product_id}", response_model=ProductDocumentResponse)
async def get_product(
    product_id: str,
    product_service: ProductService = Depends(get_product_service)
):
    """根据ID获取单个产品文档"""
    product = product_service.get_product_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="产品文档不存在")
    return product

@router.post("/", response_model=ProductDocumentResponse)
async def create_product(
    product_data: ProductDocumentCreate,
    product_service: ProductService = Depends(get_product_service)
):
    """创建新产品文档"""
    return product_service.create_product(product_data)

@router.put("/{product_id}", response_model=ProductDocumentResponse)
async def update_product(
    product_id: str,
    product_data: ProductDocumentUpdate,
    product_service: ProductService = Depends(get_product_service)
):
    """更新产品文档"""
    product = product_service.update_product(product_id, product_data)
    if not product:
        raise HTTPException(status_code=404, detail="产品文档不存在")
    return product

@router.delete("/{product_id}")
async def delete_product(
    product_id: str,
    product_service: ProductService = Depends(get_product_service)
):
    """删除产品文档"""
    success = product_service.delete_product(product_id)
    if not success:
        raise HTTPException(status_code=404, detail="产品文档不存在")
    return {"message": "产品文档删除成功"}

@router.get("/{product_id}/summary")
async def get_product_summary(
    product_id: str,
    product_service: ProductService = Depends(get_product_service)
):
    """获取产品文档摘要信息"""
    summary = product_service.get_product_summary(product_id)
    if not summary:
        raise HTTPException(status_code=404, detail="产品文档不存在")
    return summary

@router.get("/search/name/{product_name}")
async def search_products_by_name(
    product_name: str,
    user_id: str = Query("default_user", description="用户ID"),
    product_service: ProductService = Depends(get_product_service)
):
    """根据产品名称搜索产品文档"""
    return product_service.search_products_by_name(product_name, user_id)

@router.get("/search/brand/{brand_name}")
async def search_products_by_brand(
    brand_name: str,
    user_id: str = Query("default_user", description="用户ID"),
    product_service: ProductService = Depends(get_product_service)
):
    """根据品牌名称搜索产品文档"""
    return product_service.search_products_by_brand(brand_name, user_id)

@router.get("/category/{product_category}")
async def get_products_by_category(
    product_category: str,
    user_id: str = Query("default_user", description="用户ID"),
    product_service: ProductService = Depends(get_product_service)
):
    """根据产品类别获取产品文档"""
    return product_service.get_products_by_category(product_category, user_id) 