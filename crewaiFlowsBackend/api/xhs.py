#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小红书数据管理API
提供小红书笔记、评论、用户等数据的查询和管理接口
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import JSONResponse
from typing import Dict, List, Any, Optional
import logging

from services.xhs_service import XhsService
from database.database import get_db
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/xhs", tags=["小红书数据管理"])

xhs_service = XhsService()


@router.get("/notes", summary="获取笔记列表")
async def get_notes(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    source: Optional[str] = Query(None, description="数据来源筛选"),
    search_keyword: Optional[str] = Query(None, description="搜索关键词筛选"),
    user_id: Optional[str] = Query(None, description="用户ID筛选")
):
    """获取小红书笔记列表"""
    try:
        result = await xhs_service.get_notes(
            page=page,
            page_size=page_size,
            source=source,
            search_keyword=search_keyword,
            user_id=user_id
        )
        
        return JSONResponse(content={
            "success": True,
            "data": result,
            "message": "获取笔记列表成功"
        })
        
    except Exception as e:
        logger.error(f"获取笔记列表失败: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": f"获取笔记列表失败: {str(e)}"
            }
        )


@router.get("/notes/{note_id}", summary="获取笔记详情")
async def get_note_detail(note_id: str):
    """获取指定笔记的详细信息，包括评论"""
    try:
        note_detail = await xhs_service.get_note_detail(note_id)
        
        if not note_detail:
            return JSONResponse(
                status_code=404,
                content={
                    "success": False,
                    "message": "笔记不存在"
                }
            )
        
        return JSONResponse(content={
            "success": True,
            "data": note_detail,
            "message": "获取笔记详情成功"
        })
        
    except Exception as e:
        logger.error(f"获取笔记详情失败: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": f"获取笔记详情失败: {str(e)}"
            }
        )


@router.get("/statistics", summary="获取统计信息")
async def get_statistics():
    """获取小红书数据统计信息"""
    try:
        stats = await xhs_service.get_statistics()
        
        return JSONResponse(content={
            "success": True,
            "data": stats,
            "message": "获取统计信息成功"
        })
        
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": f"获取统计信息失败: {str(e)}"
            }
        )


@router.get("/search-records", summary="获取搜索记录")
async def get_search_records(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db)
):
    """获取小红书搜索记录"""
    try:
        from database.models import XhsSearchRecord
        from sqlalchemy import desc
        
        # 获取总数
        total = db.query(XhsSearchRecord).count()
        
        # 分页查询
        records = db.query(XhsSearchRecord).order_by(
            desc(XhsSearchRecord.search_time)
        ).offset((page - 1) * page_size).limit(page_size).all()
        
        record_list = []
        for record in records:
            record_dict = {
                'id': record.id,
                'keyword': record.keyword,
                'search_type': record.search_type,
                'result_count': record.result_count,
                'page': record.page,
                'page_size': record.page_size,
                'sort': record.sort,
                'total_results': record.total_results,
                'has_more': record.has_more,
                'search_time': record.search_time.isoformat() if record.search_time else None,
                'created_at': record.created_at.isoformat() if record.created_at else None
            }
            record_list.append(record_dict)
        
        return JSONResponse(content={
            "success": True,
            "data": {
                "records": record_list,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size
            },
            "message": "获取搜索记录成功"
        })
        
    except Exception as e:
        logger.error(f"获取搜索记录失败: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": f"获取搜索记录失败: {str(e)}"
            }
        )


@router.get("/api-logs", summary="获取API调用日志")
async def get_api_logs(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    api_name: Optional[str] = Query(None, description="API名称筛选"),
    success: Optional[bool] = Query(None, description="成功状态筛选"),
    db: Session = Depends(get_db)
):
    """获取小红书API调用日志"""
    try:
        from database.models import XhsApiLog
        from sqlalchemy import desc, and_
        
        query = db.query(XhsApiLog)
        
        # 添加筛选条件
        if api_name:
            query = query.filter(XhsApiLog.api_name == api_name)
        if success is not None:
            query = query.filter(XhsApiLog.success == success)
        
        # 获取总数
        total = query.count()
        
        # 分页查询
        logs = query.order_by(desc(XhsApiLog.call_time)).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        
        log_list = []
        for log in logs:
            log_dict = {
                'id': log.id,
                'api_name': log.api_name,
                'method': log.method,
                'endpoint': log.endpoint,
                'request_params': log.request_params,
                'response_code': log.response_code,
                'response_time': log.response_time,
                'response_size': log.response_size,
                'success': log.success,
                'error_message': log.error_message,
                'data_count': log.data_count,
                'call_time': log.call_time.isoformat() if log.call_time else None,
                'created_at': log.created_at.isoformat() if log.created_at else None
            }
            log_list.append(log_dict)
        
        return JSONResponse(content={
            "success": True,
            "data": {
                "logs": log_list,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size
            },
            "message": "获取API日志成功"
        })
        
    except Exception as e:
        logger.error(f"获取API日志失败: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": f"获取API日志失败: {str(e)}"
            }
        )


@router.delete("/notes/{note_id}", summary="删除笔记")
async def delete_note(note_id: str, db: Session = Depends(get_db)):
    """删除指定笔记及其评论"""
    try:
        from database.models import XhsNote
        
        # 查找笔记
        note = db.query(XhsNote).filter(XhsNote.id == note_id).first()
        if not note:
            return JSONResponse(
                status_code=404,
                content={
                    "success": False,
                    "message": "笔记不存在"
                }
            )
        
        # 删除笔记（评论功能已移除）
        db.delete(note)
        db.commit()
        
        return JSONResponse(content={
            "success": True,
            "message": "删除笔记成功"
        })
        
    except Exception as e:
        logger.error(f"删除笔记失败: {e}")
        db.rollback()
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": f"删除笔记失败: {str(e)}"
            }
        )


@router.post("/test-mcp", summary="测试小红书MCP功能")
async def test_xhs_mcp(action: str = Query(..., description="测试动作: home_feed, search, note_detail")):
    """测试小红书MCP功能"""
    try:
        from services.multi_mcp_client_service import multi_mcp_client_service
        
        # 确保MCP已连接
        if not multi_mcp_client_service.is_connected():
            await multi_mcp_client_service.connect_to_all_servers()
        
        result = None
        
        if action == "home_feed":
            # 测试首页推荐
            result = await multi_mcp_client_service.call_tool("home_feed", {})
            
        elif action == "search":
            # 测试搜索功能
            result = await multi_mcp_client_service.call_tool("search_notes", {"keywords": "美食"})
            
        elif action == "note_detail":
            # 先获取一个笔记，然后获取详情
            home_result = await multi_mcp_client_service.call_tool("home_feed", {})
            # 这里需要解析结果获取笔记URL，简化处理
            result = {"message": "需要先从首页获取笔记URL，然后调用详情接口"}
            
        else:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message": "不支持的测试动作"
                }
            )
        
        return JSONResponse(content={
            "success": True,
            "data": {
                "action": action,
                "result": result.content if hasattr(result, 'content') else result
            },
            "message": f"MCP测试 {action} 完成"
        })
        
    except Exception as e:
        logger.error(f"MCP测试失败: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": f"MCP测试失败: {str(e)}"
            }
        ) 