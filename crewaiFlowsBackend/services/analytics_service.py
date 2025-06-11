# 数据分析服务层

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, text
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json

from database.models import Account, Content, Competitor, Schedule, Task
from schemas.analytics_schemas import (
    AnalyticsOverview,
    ContentAnalytics, 
    AccountAnalytics,
    CompetitorAnalytics,
    TrendAnalytics,
    PerformanceReport
)


class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_overview(self, days: int = 30) -> AnalyticsOverview:
        """获取数据分析总览"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # 基础统计
        total_accounts = self.db.query(Account).count()
        total_contents = self.db.query(Content).count()
        total_competitors = self.db.query(Competitor).count()
        total_schedules = self.db.query(Schedule).count()
        total_tasks = self.db.query(Task).count()
        
        # 计算增长率（与上一个周期对比）
        prev_start = start_date - timedelta(days=days)
        prev_accounts = self.db.query(Account).filter(
            Account.created_at >= prev_start,
            Account.created_at < start_date
        ).count()
        current_accounts = self.db.query(Account).filter(
            Account.created_at >= start_date
        ).count()
        
        accounts_growth = self._calculate_growth_rate(prev_accounts, current_accounts)
        
        # 内容增长率
        prev_contents = self.db.query(Content).filter(
            Content.created_at >= prev_start,
            Content.created_at < start_date
        ).count()
        current_contents = self.db.query(Content).filter(
            Content.created_at >= start_date
        ).count()
        
        contents_growth = self._calculate_growth_rate(prev_contents, current_contents)
        
        # 性能指标（从mock数据或实际计算）
        avg_engagement_rate = 5.2  # 可以从实际数据计算
        total_views = 125000
        total_likes = 8500
        total_comments = 1200
        engagement_growth = 12.5
        
        return AnalyticsOverview(
            total_accounts=total_accounts,
            total_contents=total_contents,
            total_competitors=total_competitors,
            total_schedules=total_schedules,
            total_tasks=total_tasks,
            accounts_growth=accounts_growth,
            contents_growth=contents_growth,
            engagement_growth=engagement_growth,
            avg_engagement_rate=avg_engagement_rate,
            total_views=total_views,
            total_likes=total_likes,
            total_comments=total_comments,
            period_days=days,
            last_updated=datetime.utcnow()
        )
    
    def get_content_analytics(self, account_id: Optional[str] = None, days: int = 30) -> ContentAnalytics:
        """获取内容数据分析"""
        query = self.db.query(Content)
        
        if account_id:
            query = query.filter(Content.account_id == account_id)
        
        total_contents = query.count()
        published_contents = query.filter(Content.status == 'published').count()
        draft_contents = query.filter(Content.status == 'draft').count()
        
        # 分类统计
        category_stats = {}
        category_results = query.with_entities(
            Content.category, func.count(Content.id)
        ).group_by(Content.category).all()
        
        for category, count in category_results:
            category_stats[category or "未分类"] = count
        
        # 状态统计
        status_stats = {}
        status_results = query.with_entities(
            Content.status, func.count(Content.id)
        ).group_by(Content.status).all()
        
        for status, count in status_results:
            status_stats[status] = count
        
        # 模拟性能数据
        avg_views = 2500.0
        avg_likes = 180.0
        avg_comments = 25.0
        avg_engagement_rate = 4.8
        
        # 模拟每日统计和最佳表现
        daily_stats = self._generate_daily_stats(days)
        top_performing = self._get_top_performing_content()
        
        return ContentAnalytics(
            total_contents=total_contents,
            published_contents=published_contents,
            draft_contents=draft_contents,
            avg_views=avg_views,
            avg_likes=avg_likes,
            avg_comments=avg_comments,
            avg_engagement_rate=avg_engagement_rate,
            by_category=category_stats,
            by_status=status_stats,
            daily_stats=daily_stats,
            top_performing=top_performing
        )
    
    def get_accounts_analytics(self, platform: Optional[str] = None, days: int = 30) -> List[AccountAnalytics]:
        """获取账号数据分析"""
        query = self.db.query(Account)
        
        if platform:
            query = query.filter(Account.platform == platform)
        
        accounts = query.all()
        analytics_list = []
        
        for account in accounts:
            # 获取账号的内容数量
            contents_count = self.db.query(Content).filter(
                Content.account_id == account.id
            ).count()
            
            # 模拟性能数据
            analytics = AccountAnalytics(
                account_id=account.id,
                account_name=account.name,
                platform=account.platform,
                followers=account.followers,
                contents_count=contents_count,
                engagement_rate=account.engagement,
                avg_views=account.avg_views,
                total_likes=5200,
                total_comments=680,
                followers_growth=8.5,
                engagement_growth=12.3,
                best_content=self._get_account_best_content(account.id),
                recent_performance=self._get_recent_performance(account.id)
            )
            analytics_list.append(analytics)
        
        return analytics_list
    
    def get_competitor_analytics(self, category: Optional[str] = None, days: int = 30) -> CompetitorAnalytics:
        """获取竞品数据分析"""
        query = self.db.query(Competitor)
        
        if category:
            query = query.filter(Competitor.category == category)
        
        total_competitors = query.count()
        
        # 分类统计
        category_stats = {}
        category_results = self.db.query(
            Competitor.category, func.count(Competitor.id)
        ).group_by(Competitor.category).all()
        
        for cat, count in category_results:
            category_stats[cat or "未分类"] = count
        
        # 层级统计（基于粉丝数模拟）
        tier_stats = {
            "头部KOL": 3,
            "中部KOL": 8,
            "腰部KOL": 15,
            "初级KOL": 25
        }
        
        # 排行榜数据（模拟）
        top_by_followers = self._get_top_competitors_by_followers()
        top_by_engagement = self._get_top_competitors_by_engagement()
        trending_competitors = self._get_trending_competitors()
        
        # 市场洞察
        market_insights = [
            "美妆类竞品在小红书平台表现活跃，平均互动率达6.8%",
            "护肤科普类内容更容易获得高转发率",
            "下午14:00-16:00是美妆类内容的黄金发布时间"
        ]
        
        opportunities = [
            "男性护肤市场仍有较大空白",
            "敏感肌护肤内容需求增长明显",
            "平价替代品测评内容互动率较高"
        ]
        
        return CompetitorAnalytics(
            total_competitors=total_competitors,
            by_category=category_stats,
            by_tier=tier_stats,
            top_by_followers=top_by_followers,
            top_by_engagement=top_by_engagement,
            trending_competitors=trending_competitors,
            market_insights=market_insights,
            opportunities=opportunities
        )
    
    def get_trend_analytics(self, metric: str, period: str) -> TrendAnalytics:
        """获取趋势分析"""
        # 根据周期确定天数
        period_days = {"7d": 7, "30d": 30, "90d": 90}.get(period, 30)
        
        # 生成趋势数据
        data_points = self._generate_trend_data(metric, period_days)
        
        # 计算趋势方向和增长率
        if len(data_points) >= 2:
            first_value = data_points[0]["value"]
            last_value = data_points[-1]["value"]
            growth_rate = ((last_value - first_value) / first_value) * 100 if first_value > 0 else 0
            
            if growth_rate > 5:
                trend_direction = "up"
            elif growth_rate < -5:
                trend_direction = "down"
            else:
                trend_direction = "stable"
        else:
            growth_rate = 0
            trend_direction = "stable"
        
        return TrendAnalytics(
            metric=metric,
            period=period,
            data_points=data_points,
            trend_direction=trend_direction,
            growth_rate=growth_rate,
            forecast=self._generate_forecast_data(data_points, 7),
            confidence=0.85
        )
    
    def get_performance_report(self, account_id: Optional[str] = None, 
                             start_date: Optional[datetime] = None,
                             end_date: Optional[datetime] = None) -> PerformanceReport:
        """获取性能报告"""
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        report_period = f"{start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}"
        
        # 生成报告数据
        summary = self._generate_performance_summary(account_id, start_date, end_date)
        metrics = self._generate_performance_metrics(account_id, start_date, end_date)
        content_performance = self._get_content_performance(account_id, start_date, end_date)
        
        insights = [
            "本期内容互动率较上期提升15%",
            "护肤类内容表现优于化妆类内容",
            "周末发布的内容平均浏览量更高"
        ]
        
        recommendations = [
            "建议增加护肤科普类内容比例",
            "优化发布时间至周五-周日",
            "加强与粉丝的互动回复"
        ]
        
        return PerformanceReport(
            account_id=account_id,
            report_period=report_period,
            generated_at=datetime.utcnow(),
            summary=summary,
            metrics=metrics,
            content_performance=content_performance,
            competitor_comparison=None,
            insights=insights,
            recommendations=recommendations
        )
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """获取仪表板数据"""
        overview = self.get_overview(30)
        
        recent_activities = [
            {"type": "content", "action": "发布", "title": "春季护肤指南", "time": "2小时前"},
            {"type": "account", "action": "粉丝突破", "title": "学生党美妆日记突破2.5w粉丝", "time": "5小时前"},
            {"type": "competitor", "action": "新增", "title": "添加竞品：小红薯护肤", "time": "1天前"}
        ]
        
        quick_stats = {
            "today_views": 8520,
            "today_likes": 342,
            "today_comments": 89,
            "pending_tasks": 5
        }
        
        alerts = [
            {"type": "warning", "message": "有2个任务即将超期", "time": "刚刚"},
            {"type": "info", "message": "系统将在今晚进行维护", "time": "1小时前"}
        ]
        
        performance_chart = self._generate_dashboard_chart_data()
        
        return {
            "overview": overview.dict(),
            "recent_activities": recent_activities,
            "quick_stats": quick_stats,
            "alerts": alerts,
            "performance_chart": performance_chart
        }
    
    def export_to_csv(self, type: str, start_date: Optional[datetime] = None,
                     end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """导出分析数据为CSV"""
        # 这里返回下载链接或者文件内容
        return {
            "download_url": f"/downloads/{type}_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv",
            "file_size": "2.5MB",
            "records_count": 150,
            "generated_at": datetime.utcnow().isoformat()
        }
    
    def get_insights_recommendations(self, account_id: Optional[str] = None) -> Dict[str, Any]:
        """获取智能洞察和建议"""
        return {
            "account_id": account_id,
            "generated_at": datetime.utcnow(),
            "performance_insights": [
                "您的账号在护肤类内容上表现突出，平均互动率达到7.2%",
                "最近7天的粉丝增长速度较上周提升了23%",
                "晚上19:00-21:00发布的内容获得最高的曝光量"
            ],
            "content_insights": [
                "测评类内容比教程类内容获得更多点赞",
                "包含'平价'关键词的内容转发率更高",
                "图文内容比纯文字内容表现更好"
            ],
            "audience_insights": [
                "您的粉丝主要集中在18-25岁年龄段",
                "女性粉丝占比85%，关注护肤和化妆内容",
                "一二线城市粉丝活跃度更高"
            ],
            "content_recommendations": [
                "增加平价好物测评内容",
                "制作更多新手化妆教程",
                "尝试季节性护肤话题"
            ],
            "timing_recommendations": [
                "周末发布内容获得更好效果",
                "晚上7-9点是最佳发布时间",
                "避免在工作日早晨发布"
            ],
            "strategy_recommendations": [
                "与其他博主建立合作关系",
                "参与平台热门话题讨论",
                "定期举办粉丝互动活动"
            ],
            "action_items": [
                {"task": "制作春季护肤专题", "priority": "high", "due_date": "2024-03-25"},
                {"task": "优化发布时间策略", "priority": "medium", "due_date": "2024-03-30"},
                {"task": "分析竞品最新动态", "priority": "low", "due_date": "2024-04-05"}
            ],
            "priority_areas": ["内容质量提升", "发布时机优化", "粉丝互动增强"]
        }
    
    def get_metrics_comparison(self, account_ids: List[str], metric: str, days: int = 30) -> Dict[str, Any]:
        """获取指标对比分析"""
        accounts_data = []
        chart_data = []
        
        for account_id in account_ids:
            account = self.db.query(Account).filter(Account.id == account_id).first()
            if account:
                # 模拟指标数据
                value = {
                    "engagement": account.engagement,
                    "followers": account.followers,
                    "views": account.avg_views,
                    "likes": 150
                }.get(metric, 0)
                
                accounts_data.append({
                    "account_id": account_id,
                    "account_name": account.name,
                    "metric_value": value,
                    "trend": "up"
                })
                
                chart_data.append({
                    "name": account.name,
                    "value": value
                })
        
        # 找出最佳表现者
        best_performer = max(accounts_data, key=lambda x: x["metric_value"]) if accounts_data else {}
        
        insights = [
            f"在{metric}指标上，{best_performer.get('account_name', '')}表现最佳",
            f"账号间{metric}差异较大，建议学习优秀账号的运营策略",
            f"整体{metric}水平处于行业中等水平"
        ]
        
        return {
            "metric": metric,
            "accounts": accounts_data,
            "chart_data": chart_data,
            "best_performer": best_performer,
            "insights": insights
        }
    
    # 辅助方法
    def _calculate_growth_rate(self, prev_value: int, current_value: int) -> float:
        """计算增长率"""
        if prev_value == 0:
            return 100.0 if current_value > 0 else 0.0
        return ((current_value - prev_value) / prev_value) * 100
    
    def _generate_daily_stats(self, days: int) -> List[Dict[str, Any]]:
        """生成每日统计数据"""
        stats = []
        base_date = datetime.utcnow() - timedelta(days=days)
        
        for i in range(days):
            date = base_date + timedelta(days=i)
            stats.append({
                "date": date.strftime('%Y-%m-%d'),
                "views": 2000 + (i * 50),
                "likes": 150 + (i * 5),
                "comments": 20 + (i * 2),
                "shares": 8 + i
            })
        
        return stats
    
    def _get_top_performing_content(self) -> List[Dict[str, Any]]:
        """获取最佳表现内容"""
        return [
            {"title": "平价控油散粉测评", "views": 5200, "likes": 380, "engagement_rate": 7.3},
            {"title": "学生党护肤步骤", "views": 4800, "likes": 420, "engagement_rate": 8.8},
            {"title": "新手化妆工具推荐", "views": 4200, "likes": 320, "engagement_rate": 7.6}
        ]
    
    def _get_account_best_content(self, account_id: str) -> Optional[Dict[str, Any]]:
        """获取账号最佳内容"""
        return {
            "title": "春季护肤必备单品",
            "views": 3200,
            "likes": 280,
            "engagement_rate": 8.8
        }
    
    def _get_recent_performance(self, account_id: str) -> List[Dict[str, Any]]:
        """获取近期表现"""
        return [
            {"date": "2024-03-20", "metric": "engagement_rate", "value": 6.5},
            {"date": "2024-03-19", "metric": "engagement_rate", "value": 5.8},
            {"date": "2024-03-18", "metric": "engagement_rate", "value": 7.2}
        ]
    
    def _get_top_competitors_by_followers(self) -> List[Dict[str, Any]]:
        """获取粉丝数排行"""
        # 由于followers字段是字符串类型（包含w、k等单位），这里按创建时间排序或分析次数排序
        competitors = self.db.query(Competitor).order_by(Competitor.analysis_count.desc()).limit(10).all()
        return [
            {
                "name": comp.name,
                "followers": comp.followers,
                "category": comp.category
            } for comp in competitors
        ]
    
    def _get_top_competitors_by_engagement(self) -> List[Dict[str, Any]]:
        """获取互动率排行"""
        return [
            {"name": "美妆情报局", "engagement_rate": 8.5, "category": "美妆"},
            {"name": "护肤小助手", "engagement_rate": 7.8, "category": "护肤"},
            {"name": "化妆师Lily", "engagement_rate": 7.2, "category": "化妆"}
        ]
    
    def _get_trending_competitors(self) -> List[Dict[str, Any]]:
        """获取热门竞品"""
        return [
            {"name": "新锐美妆博主", "trend": "rising", "growth_rate": 45.2},
            {"name": "护肤达人小王", "trend": "rising", "growth_rate": 32.8},
            {"name": "平价美妆分享", "trend": "stable", "growth_rate": 12.5}
        ]
    
    def _generate_trend_data(self, metric: str, days: int) -> List[Dict[str, Any]]:
        """生成趋势数据"""
        data = []
        base_date = datetime.utcnow() - timedelta(days=days)
        base_value = {"engagement": 5.0, "followers": 20000, "views": 2000, "likes": 150}.get(metric, 100)
        
        for i in range(days):
            date = base_date + timedelta(days=i)
            # 添加一些随机波动
            variation = (i % 7 - 3) * 0.1  # 模拟周期性变化
            value = base_value * (1 + (i * 0.01) + variation)  # 整体上升趋势
            
            data.append({
                "date": date.strftime('%Y-%m-%d'),
                "value": round(value, 2)
            })
        
        return data
    
    def _generate_forecast_data(self, historical_data: List[Dict[str, Any]], forecast_days: int) -> List[Dict[str, Any]]:
        """生成预测数据"""
        if not historical_data:
            return []
        
        last_value = historical_data[-1]["value"]
        last_date = datetime.strptime(historical_data[-1]["date"], '%Y-%m-%d')
        
        forecast = []
        for i in range(1, forecast_days + 1):
            date = last_date + timedelta(days=i)
            # 简单的线性预测
            predicted_value = last_value * (1 + 0.02 * i)  # 假设2%的日增长
            
            forecast.append({
                "date": date.strftime('%Y-%m-%d'),
                "value": round(predicted_value, 2),
                "type": "forecast"
            })
        
        return forecast
    
    def _generate_performance_summary(self, account_id: Optional[str], start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """生成性能摘要"""
        return {
            "period_days": (end_date - start_date).days,
            "total_content_published": 15,
            "total_views": 45000,
            "total_likes": 3200,
            "total_comments": 480,
            "avg_engagement_rate": 6.8,
            "follower_growth": 850,
            "best_performing_day": "2024-03-18"
        }
    
    def _generate_performance_metrics(self, account_id: Optional[str], start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """生成性能指标"""
        return {
            "reach": {"value": 125000, "change": "+15%"},
            "impressions": {"value": 89000, "change": "+8%"},
            "engagement_rate": {"value": 6.8, "change": "+12%"},
            "click_through_rate": {"value": 2.3, "change": "+5%"},
            "conversion_rate": {"value": 1.8, "change": "+20%"}
        }
    
    def _get_content_performance(self, account_id: Optional[str], start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """获取内容表现"""
        return [
            {"title": "春季护肤指南", "views": 5200, "likes": 380, "comments": 65, "engagement_rate": 8.5},
            {"title": "平价化妆品测评", "views": 4800, "likes": 420, "comments": 58, "engagement_rate": 9.9},
            {"title": "新手化妆教程", "views": 3900, "likes": 280, "comments": 45, "engagement_rate": 8.3}
        ]
    
    def _generate_dashboard_chart_data(self) -> List[Dict[str, Any]]:
        """生成仪表板图表数据"""
        return [
            {"date": "2024-03-15", "views": 2100, "likes": 180, "comments": 25},
            {"date": "2024-03-16", "views": 2300, "likes": 195, "comments": 28},
            {"date": "2024-03-17", "views": 2050, "likes": 170, "comments": 22},
            {"date": "2024-03-18", "views": 2800, "likes": 245, "comments": 35},
            {"date": "2024-03-19", "views": 2600, "likes": 220, "comments": 30},
            {"date": "2024-03-20", "views": 2900, "likes": 260, "comments": 38},
            {"date": "2024-03-21", "views": 3100, "likes": 285, "comments": 42}
        ] 