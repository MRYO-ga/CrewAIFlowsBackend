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
    account_id: str = Field(..., description="小红书账号ID")
    account_name: str = Field(..., description="账号名称")
    profile_image: Optional[str] = Field(None, description="头像图片URL")
    bio: str = Field(..., description="账号简介")
    categories: List[str] = Field(..., description="账号分类标签")
    persona: Dict[str, Any] = Field(..., description="账号人设定义，包括性格、语调、风格等")
    target_audience: Dict[str, Any] = Field(..., description="目标受众群体定义")
    brand_values: List[str] = Field(..., description="品牌价值观")
    content_themes: List[str] = Field(..., description="内容主题方向")

class FansProfile(BaseModel):
    """粉丝画像模型"""
    account_id: str = Field(..., description="小红书账号ID")
    gender_ratio: Dict[str, float] = Field(..., description="性别比例，如{'female': 75, 'male': 25}")
    age_groups: Dict[str, float] = Field(..., description="年龄分布，如{'18-24': 30, '25-34': 45, '35+': 25}")
    geo_distribution: Dict[str, float] = Field(..., description="地理分布，如{'北京': 20, '上海': 15}")
    interests: List[str] = Field(..., description="兴趣偏好")
    active_time: List[str] = Field(..., description="活跃时间段")
    engagement_patterns: Dict[str, Any] = Field(..., description="互动模式分析")
    content_preferences: Dict[str, Any] = Field(..., description="内容偏好分析")

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
