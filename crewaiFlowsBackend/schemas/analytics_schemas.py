# 数据分析数据模型

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class AnalyticsOverview(BaseModel):
    """数据分析总览模型"""
    total_accounts: int = Field(..., description="总账号数")
    total_contents: int = Field(..., description="总内容数")
    total_competitors: int = Field(..., description="总竞品数")
    total_schedules: int = Field(..., description="总计划数")
    total_tasks: int = Field(..., description="总任务数")
    
    # 增长数据
    accounts_growth: float = Field(..., description="账号增长率")
    contents_growth: float = Field(..., description="内容增长率")
    engagement_growth: float = Field(..., description="互动率增长率")
    
    # 性能指标
    avg_engagement_rate: float = Field(..., description="平均互动率")
    total_views: int = Field(..., description="总浏览量")
    total_likes: int = Field(..., description="总点赞数")
    total_comments: int = Field(..., description="总评论数")
    
    # 时间范围
    period_days: int = Field(..., description="统计天数")
    last_updated: datetime = Field(..., description="最后更新时间")


class ContentAnalytics(BaseModel):
    """内容数据分析模型"""
    total_contents: int = Field(..., description="总内容数")
    published_contents: int = Field(..., description="已发布内容数")
    draft_contents: int = Field(..., description="草稿内容数")
    
    # 性能指标
    avg_views: float = Field(..., description="平均浏览量")
    avg_likes: float = Field(..., description="平均点赞数")
    avg_comments: float = Field(..., description="平均评论数")
    avg_engagement_rate: float = Field(..., description="平均互动率")
    
    # 分类统计
    by_category: Dict[str, int] = Field(..., description="按分类统计")
    by_status: Dict[str, int] = Field(..., description="按状态统计")
    
    # 趋势数据
    daily_stats: List[Dict[str, Any]] = Field(..., description="每日统计")
    top_performing: List[Dict[str, Any]] = Field(..., description="最佳表现内容")


class AccountAnalytics(BaseModel):
    """账号数据分析模型"""
    account_id: str = Field(..., description="账号ID")
    account_name: str = Field(..., description="账号名称")
    platform: str = Field(..., description="平台")
    
    # 基础数据
    followers: int = Field(..., description="粉丝数")
    contents_count: int = Field(..., description="内容数量")
    
    # 性能指标
    engagement_rate: float = Field(..., description="互动率")
    avg_views: float = Field(..., description="平均浏览量")
    total_likes: int = Field(..., description="总点赞数")
    total_comments: int = Field(..., description="总评论数")
    
    # 增长数据
    followers_growth: float = Field(..., description="粉丝增长率")
    engagement_growth: float = Field(..., description="互动增长率")
    
    # 内容表现
    best_content: Optional[Dict[str, Any]] = Field(None, description="最佳内容")
    recent_performance: List[Dict[str, Any]] = Field(..., description="近期表现")


class CompetitorAnalytics(BaseModel):
    """竞品数据分析模型"""
    total_competitors: int = Field(..., description="竞品总数")
    by_category: Dict[str, int] = Field(..., description="按分类统计")
    by_tier: Dict[str, int] = Field(..., description="按层级统计")
    
    # 排行榜
    top_by_followers: List[Dict[str, Any]] = Field(..., description="粉丝数排行")
    top_by_engagement: List[Dict[str, Any]] = Field(..., description="互动率排行")
    trending_competitors: List[Dict[str, Any]] = Field(..., description="热门竞品")
    
    # 分析洞察
    market_insights: List[str] = Field(..., description="市场洞察")
    opportunities: List[str] = Field(..., description="机会点")


class TrendAnalytics(BaseModel):
    """趋势分析模型"""
    metric: str = Field(..., description="指标名称")
    period: str = Field(..., description="时间周期")
    
    # 趋势数据
    data_points: List[Dict[str, Any]] = Field(..., description="数据点")
    trend_direction: str = Field(..., description="趋势方向: up, down, stable")
    growth_rate: float = Field(..., description="增长率")
    
    # 预测数据
    forecast: Optional[List[Dict[str, Any]]] = Field(None, description="预测数据")
    confidence: Optional[float] = Field(None, description="预测置信度")


class PerformanceReport(BaseModel):
    """性能报告模型"""
    account_id: Optional[str] = Field(None, description="账号ID")
    report_period: str = Field(..., description="报告周期")
    generated_at: datetime = Field(..., description="生成时间")
    
    # 概览数据
    summary: Dict[str, Any] = Field(..., description="数据概览")
    
    # 详细指标
    metrics: Dict[str, Any] = Field(..., description="详细指标")
    
    # 内容表现
    content_performance: List[Dict[str, Any]] = Field(..., description="内容表现")
    
    # 竞品对比
    competitor_comparison: Optional[List[Dict[str, Any]]] = Field(None, description="竞品对比")
    
    # 建议和洞察
    insights: List[str] = Field(..., description="洞察分析")
    recommendations: List[str] = Field(..., description="优化建议")


class DashboardData(BaseModel):
    """仪表板数据模型"""
    overview: AnalyticsOverview = Field(..., description="总览数据")
    recent_activities: List[Dict[str, Any]] = Field(..., description="最近活动")
    quick_stats: Dict[str, Any] = Field(..., description="快速统计")
    alerts: List[Dict[str, Any]] = Field(..., description="提醒事项")
    performance_chart: List[Dict[str, Any]] = Field(..., description="性能图表数据")


class MetricsComparison(BaseModel):
    """指标对比模型"""
    metric: str = Field(..., description="对比指标")
    accounts: List[Dict[str, Any]] = Field(..., description="账号对比数据")
    chart_data: List[Dict[str, Any]] = Field(..., description="图表数据")
    best_performer: Dict[str, Any] = Field(..., description="最佳表现者")
    insights: List[str] = Field(..., description="对比洞察")


class InsightsRecommendations(BaseModel):
    """洞察和建议模型"""
    account_id: Optional[str] = Field(None, description="账号ID")
    generated_at: datetime = Field(..., description="生成时间")
    
    # 数据洞察
    performance_insights: List[str] = Field(..., description="性能洞察")
    content_insights: List[str] = Field(..., description="内容洞察")
    audience_insights: List[str] = Field(..., description="受众洞察")
    
    # 优化建议
    content_recommendations: List[str] = Field(..., description="内容建议")
    timing_recommendations: List[str] = Field(..., description="时机建议")
    strategy_recommendations: List[str] = Field(..., description="策略建议")
    
    # 行动计划
    action_items: List[Dict[str, Any]] = Field(..., description="行动项")
    priority_areas: List[str] = Field(..., description="优先改进领域") 