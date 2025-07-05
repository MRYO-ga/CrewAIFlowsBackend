# 数据分析API
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from database.database import get_db
from database.models import PersonaDocument, Content, Competitor, Schedule, Task
from services.analytics_service import AnalyticsService
from schemas.analytics_schemas import (
    AnalyticsOverview, 
    ContentAnalytics, 
    AccountAnalytics, 
    CompetitorAnalytics,
    TrendAnalytics,
    PerformanceReport
)

# 创建路由器
analytics_router = APIRouter(prefix="/api/analytics", tags=["数据分析"])

# 依赖注入
def get_analytics_service(db: Session = Depends(get_db)) -> AnalyticsService:
    return AnalyticsService(db)

@analytics_router.get("/overview", response_model=AnalyticsOverview)
async def get_analytics_overview(
    days: int = Query(30, description="分析天数"),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """获取数据分析总览"""
    return analytics_service.get_overview(days)

@analytics_router.get("/content", response_model=ContentAnalytics)
async def get_content_analytics(
    account_id: Optional[str] = Query(None, description="账号ID筛选"),
    days: int = Query(30, description="分析天数"),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """获取内容数据分析"""
    return analytics_service.get_content_analytics(account_id, days)

@analytics_router.get("/accounts", response_model=List[AccountAnalytics])
async def get_accounts_analytics(
    platform: Optional[str] = Query(None, description="平台筛选"),
    days: int = Query(30, description="分析天数"),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """获取账号数据分析"""
    return analytics_service.get_accounts_analytics(platform, days)

@analytics_router.get("/competitors", response_model=CompetitorAnalytics)
async def get_competitor_analytics(
    category: Optional[str] = Query(None, description="分类筛选"),
    days: int = Query(30, description="分析天数"),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """获取竞品数据分析"""
    return analytics_service.get_competitor_analytics(category, days)

@analytics_router.get("/trends", response_model=TrendAnalytics)
async def get_trend_analytics(
    metric: str = Query("engagement", description="指标类型: engagement, followers, views, likes"),
    period: str = Query("7d", description="时间周期: 7d, 30d, 90d"),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """获取趋势分析"""
    return analytics_service.get_trend_analytics(metric, period)

@analytics_router.get("/performance/report", response_model=PerformanceReport)
async def get_performance_report(
    account_id: Optional[str] = Query(None, description="账号ID"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """获取性能报告"""
    return analytics_service.get_performance_report(account_id, start_date, end_date)

@analytics_router.get("/dashboard/data")
async def get_dashboard_data(
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """获取仪表板数据"""
    return analytics_service.get_dashboard_data()

@analytics_router.get("/export/csv")
async def export_analytics_csv(
    type: str = Query(..., description="导出类型: accounts, contents, competitors, schedules, tasks"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """导出分析数据为CSV"""
    return analytics_service.export_to_csv(type, start_date, end_date)

@analytics_router.get("/insights/recommendations")
async def get_insights_recommendations(
    account_id: Optional[str] = Query(None, description="账号ID"),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """获取智能洞察和建议"""
    return analytics_service.get_insights_recommendations(account_id)

@analytics_router.get("/metrics/comparison")
async def get_metrics_comparison(
    account_ids: List[str] = Query(..., description="账号ID列表"),
    metric: str = Query("engagement", description="对比指标"),
    days: int = Query(30, description="对比天数"),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """获取指标对比分析"""
    return analytics_service.get_metrics_comparison(account_ids, metric, days) 