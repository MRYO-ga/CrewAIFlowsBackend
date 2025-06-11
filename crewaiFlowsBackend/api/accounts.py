# 账号管理API
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database.database import get_db
from database.models import Account
from services.account_service import AccountService
from schemas.account_schemas import AccountCreate, AccountUpdate, AccountResponse

router = APIRouter(prefix="/api/accounts", tags=["账号管理"])

# 依赖注入
def get_account_service(db: Session = Depends(get_db)) -> AccountService:
    return AccountService(db)

@router.get("/", response_model=List[AccountResponse])
async def get_accounts(
    platform: Optional[str] = Query(None, description="平台筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    limit: int = Query(50, description="返回数量限制"),
    account_service: AccountService = Depends(get_account_service)
):
    """获取账号列表"""
    return account_service.get_accounts(platform=platform, status=status, limit=limit)

@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: str,
    account_service: AccountService = Depends(get_account_service)
):
    """根据ID获取单个账号信息"""
    account = account_service.get_account_by_id(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")
    return account

@router.post("/", response_model=AccountResponse)
async def create_account(
    account_data: AccountCreate,
    account_service: AccountService = Depends(get_account_service)
):
    """创建新账号"""
    return account_service.create_account(account_data)

@router.put("/{account_id}", response_model=AccountResponse)
async def update_account(
    account_id: str,
    account_data: AccountUpdate,
    account_service: AccountService = Depends(get_account_service)
):
    """更新账号信息"""
    account = account_service.update_account(account_id, account_data)
    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")
    return account

@router.delete("/{account_id}")
async def delete_account(
    account_id: str,
    account_service: AccountService = Depends(get_account_service)
):
    """删除账号"""
    success = account_service.delete_account(account_id)
    if not success:
        raise HTTPException(status_code=404, detail="账号不存在")
    return {"message": "账号删除成功"}

@router.get("/{account_id}/analytics")
async def get_account_analytics(
    account_id: str,
    days: int = Query(30, description="查询天数"),
    account_service: AccountService = Depends(get_account_service)
):
    """获取账号数据分析"""
    analytics = account_service.get_account_analytics(account_id, days)
    if not analytics:
        raise HTTPException(status_code=404, detail="账号不存在或无数据")
    return analytics 