# SOP相关API
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import json

from database.database import get_db
from services.sop_service import SOPService
from schemas.sop_schemas import (
    SOPCreate, SOPUpdate, SOPResponse, SOPListResponse,
    SOPTaskItemUpdate, SOPTaskItemResponse
)

router = APIRouter(prefix="/api/sops", tags=["SOP管理"])

# 依赖注入
def get_sop_service(db: Session = Depends(get_db)) -> SOPService:
    return SOPService(db)

@router.get("/", response_model=List[SOPListResponse])
async def get_sops(
    sop_type: Optional[str] = Query(None, description="SOP类型筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    limit: int = Query(50, description="返回数量限制"),
    sop_service: SOPService = Depends(get_sop_service)
):
    """获取SOP列表"""
    return sop_service.get_sops(sop_type=sop_type, status=status, limit=limit)

@router.get("/{sop_id}", response_model=SOPResponse)
async def get_sop(
    sop_id: str,
    sop_service: SOPService = Depends(get_sop_service)
):
    """根据ID获取完整SOP数据"""
    sop = sop_service.get_sop_by_id(sop_id)
    if not sop:
        raise HTTPException(status_code=404, detail="SOP不存在")
    return sop

@router.post("/", response_model=SOPResponse)
async def create_sop(
    sop_data: SOPCreate,
    sop_service: SOPService = Depends(get_sop_service)
):
    """创建新SOP"""
    return sop_service.create_sop(sop_data)

@router.put("/{sop_id}", response_model=SOPResponse)
async def update_sop(
    sop_id: str,
    sop_data: SOPUpdate,
    sop_service: SOPService = Depends(get_sop_service)
):
    """更新SOP信息"""
    sop = sop_service.update_sop(sop_id, sop_data)
    if not sop:
        raise HTTPException(status_code=404, detail="SOP不存在")
    return sop

@router.delete("/{sop_id}")
async def delete_sop(
    sop_id: str,
    sop_service: SOPService = Depends(get_sop_service)
):
    """删除SOP"""
    success = sop_service.delete_sop(sop_id)
    if not success:
        raise HTTPException(status_code=404, detail="SOP不存在")
    return {"message": "SOP删除成功"}

@router.put("/task-items/{item_id}/status", response_model=SOPTaskItemResponse)
async def update_task_item_status(
    item_id: str,
    completed: bool = Query(..., description="完成状态"),
    sop_service: SOPService = Depends(get_sop_service)
):
    """更新任务项完成状态"""
    item = sop_service.update_task_item_status(item_id, completed)
    if not item:
        raise HTTPException(status_code=404, detail="任务项不存在")
    return item

@router.get("/{sop_id}/progress")
async def get_sop_progress(
    sop_id: str,
    sop_service: SOPService = Depends(get_sop_service)
):
    """获取SOP整体进度"""
    progress = sop_service.get_sop_progress(sop_id)
    if not progress:
        raise HTTPException(status_code=404, detail="SOP不存在")
    return progress

@router.post("/import-json", response_model=SOPResponse)
async def import_sop_from_json(
    json_data: Dict[str, Any],
    sop_service: SOPService = Depends(get_sop_service)
):
    """从JSON数据导入SOP"""
    try:
        return sop_service.import_sop_from_json(json_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"导入失败: {str(e)}")

@router.post("/import-file", response_model=SOPResponse)
async def import_sop_from_file(
    file: UploadFile = File(..., description="JSON文件"),
    sop_service: SOPService = Depends(get_sop_service)
):
    """从JSON文件导入SOP"""
    try:
        # 读取文件内容
        content = await file.read()
        json_data = json.loads(content.decode('utf-8'))
        
        return sop_service.import_sop_from_json(json_data)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="无效的JSON文件")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"导入失败: {str(e)}")

@router.get("/types/available")
async def get_available_sop_types():
    """获取可用的SOP类型"""
    return {
        "types": [
            {
                "key": "operation_sop",
                "name": "运营SOP",
                "description": "账号运营标准操作程序"
            },
            {
                "key": "content_sop",
                "name": "内容创作SOP",
                "description": "内容创作标准流程"
            },
            {
                "key": "publishing_sop",
                "name": "发布SOP",
                "description": "内容发布标准流程"
            },
            {
                "key": "analysis_sop",
                "name": "分析SOP",
                "description": "数据分析标准流程"
            }
        ]
    } 