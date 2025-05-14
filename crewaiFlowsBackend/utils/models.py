# 核心功能:定义数据模型，使用Pydantic库来进行数据验证和类型检查


from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class MarketStrategy(BaseModel):
	"""Market strategy model"""
	name: str = Field(..., description="市场战略名称")
	tatics: List[str] = Field(..., description="市场战略中使用的战术清单")
	channels: List[str] = Field(..., description="市场战略中使用的渠道清单")
	KPIs: List[str] = Field(..., description="市场战略中使用的关键绩效指标清单")

class CampaignIdea(BaseModel):
	"""Campaign idea model"""
	name: str = Field(..., description="活动创意名称")
	description: str = Field(..., description="Description of the campaign idea")
	audience: str = Field(..., description="活动创意说明")
	channel: str = Field(..., description="活动创意渠道")

class Copy(BaseModel):
	"""Copy model"""
	title: str = Field(..., description="副本标题")
	body: str = Field(..., description="正文")

# 账号人设管理Agent模型
class AccountProfile(BaseModel):
    """账号档案模型"""
    account_name: str = Field(..., description="账号名称")
    bio: str = Field(..., description="账号简介")
    avatar_style: str = Field(..., description="头像风格描述")
    key_tags: List[str] = Field(..., description="关键标签列表")
    tone_style: str = Field(..., description="语言风格")

class FansProfile(BaseModel):
    """粉丝画像模型"""
    demographic: Dict[str, Any] = Field(..., description="人口统计学特征")
    interests: List[str] = Field(..., description="兴趣爱好")
    behavior_patterns: Dict[str, Any] = Field(..., description="平台行为模式")
    content_preferences: List[str] = Field(..., description="内容偏好")
    interaction_habits: Dict[str, Any] = Field(..., description="互动习惯")

# 竞品分析Agent模型
class CompetitorAnalysis(BaseModel):
    """竞品分析模型"""
    category: str = Field(..., description="分析品类")
    competitors: List[Dict[str, Any]] = Field(..., description="竞品账号列表及基本信息")
    content_strategies: Dict[str, Any] = Field(..., description="竞品内容策略分析")
    engagement_tactics: Dict[str, Any] = Field(..., description="竞品互动策略分析")
    market_positioning: Dict[str, Any] = Field(..., description="市场定位分析")
    audience_overlap: Dict[str, Any] = Field(..., description="受众重合度分析")
    strengths_weaknesses: Dict[str, Any] = Field(..., description="优势与不足分析")
    actionable_insights: List[str] = Field(..., description="可操作的洞察")

class HotContentTemplate(BaseModel):
    """爆款内容模板模型"""
    category: str = Field(..., description="内容品类")
    title_patterns: List[Dict[str, Any]] = Field(..., description="标题模式列表")
    content_structures: List[Dict[str, Any]] = Field(..., description="内容结构模板")
    image_styles: List[Dict[str, Any]] = Field(..., description="图片风格建议")
    hashtag_strategies: List[Dict[str, Any]] = Field(..., description="标签策略")
    engagement_hooks: List[str] = Field(..., description="互动钩子")
    example_notes: List[Dict[str, Any]] = Field(..., description="示例笔记")

# 内容生成Agent模型
class ContentStructure(BaseModel):
    """内容结构模型"""
    topic: str = Field(..., description="内容主题")
    target_audience: Dict[str, Any] = Field(..., description="目标受众")
    sections: List[Dict[str, Any]] = Field(..., description="内容分节结构")
    image_placement: List[Dict[str, Any]] = Field(..., description="图片放置建议")
    engagement_points: List[Dict[str, Any]] = Field(..., description="互动点建议")
    estimated_length: int = Field(..., description="估计内容长度")
    key_messages: List[str] = Field(..., description="核心信息点")

class ContentTitle(BaseModel):
    """内容标题模型"""
    main_title: str = Field(..., description="主标题")
    alternative_titles: List[str] = Field(..., description="备选标题列表")
    title_analysis: Dict[str, Any] = Field(..., description="标题分析，包括吸引点、情感诉求等")
    keywords: List[str] = Field(..., description="包含的关键词")
    seo_score: float = Field(..., description="SEO评分(0-10)")
    engagement_prediction: float = Field(..., description="互动预测评分(0-10)")

class ContentDraft(BaseModel):
    """内容草稿模型"""
    title: str = Field(..., description="标题")
    sections: List[Dict[str, Any]] = Field(..., description="内容分节，包括文本和图片建议")
    tags: List[str] = Field(..., description="标签列表")
    cover_image_suggestion: Dict[str, Any] = Field(..., description="封面图建议")
    call_to_action: str = Field(..., description="互动召唤语")
    total_length: int = Field(..., description="总字数")
    reading_time: str = Field(..., description="预计阅读时间")
    target_emotions: List[str] = Field(..., description="目标情绪反应")

# 合规检测Agent模型
class ComplianceReport(BaseModel):
    """合规报告模型"""
    content_id: str = Field(..., description="内容ID")
    is_compliant: bool = Field(..., description="是否合规")
    detected_issues: List[Dict[str, Any]] = Field(..., description="检测到的问题")
    risk_level: str = Field(..., description="风险等级：低、中、高")
    platform_policies: List[Dict[str, Any]] = Field(..., description="相关平台政策")
    sensitivity_analysis: Dict[str, Any] = Field(..., description="敏感度分析")
    recommendation: str = Field(..., description="处理建议")
    suggested_revisions: Optional[Dict[str, Any]] = Field(None, description="修改建议")

# 发布互动Agent模型
class PublicationResult(BaseModel):
    """发布结果模型"""
    publication_id: str = Field(..., description="发布ID")
    account_id: str = Field(..., description="账号ID")
    content_id: str = Field(..., description="内容ID")
    publish_time: str = Field(..., description="发布时间")
    status: str = Field(..., description="发布状态：待发布、已发布、失败")
    platform_url: Optional[str] = Field(None, description="内容平台URL")
    tags_applied: List[str] = Field(..., description="应用的标签")
    technical_details: Dict[str, Any] = Field(..., description="技术细节记录")

class InteractionStats(BaseModel):
    """互动数据统计模型"""
    publication_id: str = Field(..., description="发布ID")
    collection_time: str = Field(..., description="数据采集时间")
    time_since_publication: str = Field(..., description="发布后经过时间")
    metrics: Dict[str, Any] = Field(..., description="核心指标：浏览、点赞、评论、收藏等")
    growth_rate: Dict[str, float] = Field(..., description="增长率数据")
    audience_engagement: Dict[str, Any] = Field(..., description="受众互动分析")
    performance_assessment: str = Field(..., description="表现评估")
    optimization_recommendations: List[str] = Field(..., description="优化建议")

class ContentPlan(BaseModel):
    """内容规划模型"""
    main_topics: List[str] = Field(..., description="主要内容主题")
    content_ratio: Dict[str, int] = Field(..., description="内容类型占比(%)")
    posting_schedule: str = Field(..., description="发布时间策略")
    interaction_strategy: str = Field(..., description="互动策略")
    trending_topics: List[str] = Field(..., description="推荐结合的热点话题")

class TrendReport(BaseModel):
    """平台趋势报告模型"""
    hot_topics: List[Dict[str, Any]] = Field(..., description="热门话题及增长趋势")
    content_forms: Dict[str, int] = Field(..., description="内容形式占比(%)")
    language_features: List[str] = Field(..., description="高互动内容语言特征")
    opportunity_topics: List[str] = Field(..., description="潜在机会点话题")
    trend_prediction: str = Field(..., description="未来趋势预测")

class CompetitorMatrix(BaseModel):
    """竞品策略矩阵模型"""
    topic_coverage: Dict[str, List[str]] = Field(..., description="各竞品主题覆盖情况")
    format_innovation: Dict[str, List[str]] = Field(..., description="各竞品内容形式创新点")
    style_positioning: Dict[str, Dict[str, int]] = Field(..., description="各竞品风格定位坐标")
    strengths_weaknesses: Dict[str, Dict[str, List[str]]] = Field(..., description="各竞品优劣势")
    differentiation_suggestion: str = Field(..., description="差异化策略建议")

class ContentCreation(BaseModel):
    """内容创作模型"""
    title: str = Field(..., description="内容标题")
    content_type: str = Field(..., description="内容类型(图文/视频)")
    content_body: str = Field(..., description="内容正文")
    visual_suggestion: str = Field(..., description="视觉呈现建议")
    interaction_guide: str = Field(..., description="互动引导语")
    hashtags: List[str] = Field(..., description="推荐话题标签")
