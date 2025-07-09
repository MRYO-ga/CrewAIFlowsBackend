# 数据库模型定义
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, JSON, ForeignKey, Index, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from .database import Base

# 人设构建文档模型
class PersonaDocument(Base):
    __tablename__ = "persona_documents"

    id = Column(String(50), primary_key=True)
    account_name = Column(String(100), nullable=False, comment="账号名称")
    document_content = Column(Text, nullable=False, comment="人设构建完整文档内容")
    
    # 基本信息（从文档中体现，不单独存储）
    account_type = Column(String(50), comment="账号类型")
    industry_field = Column(String(50), comment="行业领域")
    platform = Column(String(20), default="xiaohongshu", comment="平台")
    
    # 状态信息
    status = Column(String(20), default="completed", comment="状态: completed, archived")
    
    # 时间信息
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
    completed_at = Column(DateTime, default=func.now(), comment="完成时间")
    
    # 用户信息
    user_id = Column(String(50), default="default_user", comment="用户ID")
    
    # 扩展信息
    tags = Column(JSON, comment="标签列表")
    summary = Column(Text, comment="简短摘要")

    # 索引
    __table_args__ = (
        Index('idx_persona_user_created', 'user_id', 'created_at'),
        Index('idx_persona_account_name', 'account_name'),
    )

# 内容管理模型
class Content(Base):
    __tablename__ = "contents"

    id = Column(String(50), primary_key=True)
    title = Column(String(200), nullable=False)
    cover = Column(String(500))
    description = Column(Text)
    content = Column(Text)
    category = Column(String(50))  # review, tutorial, recommendation, knowledge
    status = Column(String(20), default="draft")  # draft, reviewing, published, scheduled
    
    # 发布信息
    published_at = Column(String(50))
    created_at = Column(String(50))
    scheduled_at = Column(String(50))
    
    # 关联信息
    platform = Column(String(20))
    account_name = Column(String(100), comment="账号名称")
    
    # 数据统计
    stats = Column(JSON)  # 包含views, likes, comments, shares, favorites
    
    # 标签
    tags = Column(JSON)
    
    # 时间戳
    created_at_timestamp = Column(DateTime, default=func.now())
    updated_at_timestamp = Column(DateTime, default=func.now(), onupdate=func.now())

    # 关系
    schedules = relationship("Schedule", back_populates="content")
    tasks = relationship("Task", back_populates="content")

# 竞品分析模型
class Competitor(Base):
    __tablename__ = "competitors"

    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    account_id = Column(String(100))
    platform = Column(String(20), nullable=False)
    tier = Column(String(20))  # top, mid, rising
    category = Column(String(50))
    followers = Column(String(20))  # 粉丝数（可能包含w、k等单位）
    explosion_rate = Column(Float, default=0.0)
    last_update = Column(String(50))
    analysis_count = Column(Integer, default=0)
    avatar = Column(String(500))
    profile_url = Column(String(500))
    tags = Column(JSON)
    analysis_document = Column(Text)  # 详细分析文档
    
    # 时间戳
    created_at_timestamp = Column(DateTime, default=func.now())
    updated_at_timestamp = Column(DateTime, default=func.now(), onupdate=func.now())

    # 关系
    notes = relationship("CompetitorNote", back_populates="competitor")

# 竞品笔记模型
class CompetitorNote(Base):
    __tablename__ = "competitor_notes"

    id = Column(String(50), primary_key=True)
    competitor_id = Column(String(50), ForeignKey("competitors.id"), nullable=False)
    note_id = Column(String(100), nullable=False)
    title = Column(String(200), nullable=False)
    content_preview = Column(Text)
    upload_time = Column(String(50))
    likes = Column(Integer, default=0)
    collects = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    views = Column(Integer, default=0)
    engagement_rate = Column(Float, default=0.0)
    is_viral = Column(Boolean, default=False)
    viral_score = Column(Integer, default=0)
    content_type = Column(String(50))
    topics = Column(JSON)  # 存储话题数组
    performance_rank = Column(Integer, default=0)
    analysis = Column(Text)  # 存储分析文档

    # 关系
    competitor = relationship("Competitor", back_populates="notes")

# 发布计划模型
class Schedule(Base):
    """发布计划模型"""
    __tablename__ = "schedules"

    id = Column(String(50), primary_key=True, index=True)
    title = Column(String(200), nullable=False, comment="计划标题")
    description = Column(Text, comment="计划描述")
    type = Column(String(50), nullable=False, default="single", comment="计划类型: single, batch, ab_test, recurring")
    status = Column(String(50), nullable=False, default="pending", comment="状态: pending, running, published, completed, cancelled")
    
    # 关联信息
    account_name = Column(String(100), comment="账号名称")
    content_id = Column(String(50), ForeignKey("contents.id"), comment="关联内容ID")
    platform = Column(String(50), comment="发布平台")
    
    # 发布时间
    publish_datetime = Column(DateTime, comment="计划发布时间")
    published_at = Column(DateTime, comment="实际发布时间")
    
    # 配置信息（JSON格式存储）
    test_config = Column(JSON, comment="A/B测试配置")
    recurring_config = Column(JSON, comment="循环发布配置")
    
    # 其他信息
    note = Column(Text, comment="备注")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    # 关系
    content = relationship("Content", back_populates="schedules")
    tasks = relationship("Task", back_populates="schedule")

# 聊天对话模型
class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(String(50), primary_key=True)
    content = Column(Text, nullable=False)
    sender = Column(String(20), nullable=False)  # ai, user
    timestamp = Column(String(50))
    status = Column(String(20), default="received")  # sent, received, read
    
    # 会话相关
    user_id = Column(String(50), default="default_user")
    session_id = Column(String(50))
    
    # AI相关
    intent = Column(String(50))  # 意图识别结果
    references = Column(JSON)    # 参考信息
    
    # 时间戳
    created_at_timestamp = Column(DateTime, default=func.now())

# 任务管理模型
class Task(Base):
    """任务管理模型"""
    __tablename__ = "tasks"

    id = Column(String(50), primary_key=True, index=True)
    title = Column(String(200), nullable=False, comment="任务标题")
    description = Column(Text, comment="任务描述")
    type = Column(String(50), nullable=False, comment="任务类型: content, analysis, schedule, operation")
    status = Column(String(50), nullable=False, default="pending", comment="状态: pending, inProgress, completed, overdue, cancelled")
    priority = Column(String(20), nullable=False, default="medium", comment="优先级: low, medium, high, urgent")
    
    # 任务详情
    assignee = Column(String(100), comment="负责人")
    deadline = Column(DateTime, comment="截止时间")
    progress = Column(Integer, default=0, comment="完成进度(0-100)")
    
    # 关联信息
    account_name = Column(String(100), comment="账号名称")
    content_id = Column(String(50), ForeignKey("contents.id"), nullable=True, comment="关联内容ID")
    schedule_id = Column(String(50), ForeignKey("schedules.id"), nullable=True, comment="关联计划ID")
    
    # 扩展信息
    tags = Column(JSON, comment="标签列表")
    attachments = Column(JSON, comment="附件列表")
    notes = Column(Text, comment="备注")
    
    # 时间信息
    started_at = Column(DateTime, comment="开始时间")
    completed_at = Column(DateTime, comment="完成时间")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    # 关系
    content = relationship("Content", back_populates="tasks")
    schedule = relationship("Schedule", back_populates="tasks")

# 添加索引
Index('idx_content_status', Content.status)
Index('idx_content_category', Content.category)
Index('idx_competitor_platform', Competitor.platform)
Index('idx_competitor_tier', Competitor.tier)
Index('idx_schedule_status', Schedule.status)
Index('idx_chat_user_id', ChatMessage.user_id)

# SOP模型 - 标准操作程序
class SOP(Base):
    __tablename__ = "sops"
    
    id = Column(String(50), primary_key=True)
    title = Column(String(200), nullable=False)
    type = Column(String(50), nullable=False)  # operation_sop, content_sop等
    description = Column(Text)
    status = Column(String(20), default='active')  # active, inactive, archived
    created_at = Column(String(50), nullable=False)
    updated_at = Column(String(50))
    
    # 关系
    cycles = relationship("SOPCycle", back_populates="sop", cascade="all, delete-orphan")

# SOP周期模型
class SOPCycle(Base):
    __tablename__ = "sop_cycles"
    
    id = Column(String(50), primary_key=True)
    sop_id = Column(String(50), ForeignKey('sops.id'), nullable=False)
    cycle_key = Column(String(50), nullable=False)  # cold-start, growth, mature
    title = Column(String(200), nullable=False)
    subtitle = Column(String(300))
    duration = Column(String(50))
    status = Column(String(20), default='wait')  # wait, process, finish
    icon = Column(String(50))
    color = Column(String(20))
    progress = Column(Integer, default=0)
    goal = Column(Text)
    order_index = Column(Integer, default=0)
    
    # 关系
    sop = relationship("SOP", back_populates="cycles")
    weeks = relationship("SOPWeek", back_populates="cycle", cascade="all, delete-orphan")

# SOP周模型
class SOPWeek(Base):
    __tablename__ = "sop_weeks"
    
    id = Column(String(50), primary_key=True)
    cycle_id = Column(String(50), ForeignKey('sop_cycles.id'), nullable=False)
    week_key = Column(String(50), nullable=False)  # week-1, week-2-3等
    title = Column(String(300), nullable=False)
    status = Column(String(20), default='wait')  # wait, process, finish
    order_index = Column(Integer, default=0)
    
    # 关系
    cycle = relationship("SOPCycle", back_populates="weeks")
    tasks = relationship("SOPTask", back_populates="week", cascade="all, delete-orphan")

# SOP任务模型
class SOPTask(Base):
    __tablename__ = "sop_tasks"
    
    id = Column(String(50), primary_key=True)
    week_id = Column(String(50), ForeignKey('sop_weeks.id'), nullable=False)
    task_key = Column(String(50), nullable=False)
    category = Column(String(200), nullable=False)
    completed = Column(Boolean, default=False)
    order_index = Column(Integer, default=0)
    
    # 关系
    week = relationship("SOPWeek", back_populates="tasks")
    items = relationship("SOPTaskItem", back_populates="task", cascade="all, delete-orphan")

# SOP任务项模型
class SOPTaskItem(Base):
    __tablename__ = "sop_task_items"
    
    id = Column(String(50), primary_key=True)
    task_id = Column(String(50), ForeignKey('sop_tasks.id'), nullable=False)
    item_key = Column(String(50), nullable=False)
    time = Column(String(100))
    action = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    example = Column(Text)
    publish_time = Column(String(100))
    reason = Column(Text)
    completed = Column(Boolean, default=False)
    order_index = Column(Integer, default=0)
    
    # 关系
    task = relationship("SOPTask", back_populates="items")

# 更新Competitor模型，添加notes关系
Competitor.notes = relationship("CompetitorNote", back_populates="competitor")

# 小红书数据模型

class XhsNote(Base):
    """小红书笔记表"""
    __tablename__ = "xhs_notes"
    
    id = Column(String(50), primary_key=True)  # 笔记ID
    model_type = Column(String(50), nullable=True)  # 模型类型
    xsec_token = Column(String(500), nullable=True)  # 安全令牌
    note_url = Column(String(500), nullable=True)  # 笔记URL
    
    # 笔记基本信息
    type = Column(String(50), nullable=True)  # 笔记类型（video, normal等）
    display_title = Column(String(500), nullable=True)  # 显示标题
    desc = Column(Text, nullable=True)  # 描述
    ip_location = Column(String(100), nullable=True)  # IP位置
    
    # 时间信息
    time = Column(String(50), nullable=True)  # 发布时间（格式化）
    timestamp = Column(BigInteger, nullable=True)  # 时间戳
    last_update_time = Column(String(50), nullable=True)  # 最后更新时间
    
    # 用户信息
    user_id = Column(String(50), nullable=True)  # 用户ID
    user_nickname = Column(String(200), nullable=True)  # 用户昵称
    user_avatar = Column(String(500), nullable=True)  # 用户头像
    user_xsec_token = Column(String(500), nullable=True)  # 用户安全令牌
    
    # 互动数据 - 使用字符串类型保存，以便保留原始格式（如"1.9万"）
    liked_count = Column(String(50), default="0")  # 点赞数
    comment_count = Column(String(50), default="0")  # 评论数
    collected_count = Column(String(50), default="0")  # 收藏数
    share_count = Column(String(50), default="0")  # 分享数
    
    # 图片信息
    cover_image = Column(String(500), nullable=True)  # 封面图片URL
    images = Column(JSON, nullable=True)  # 图片URL列表
    
    # 评论数据
    comments_json = Column(JSON, nullable=True)  # 评论数据JSON
    
    # 数据来源
    source = Column(String(50), nullable=True)  # 数据来源（home_feed, search等）
    search_keyword = Column(String(200), nullable=True)  # 搜索关键词
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.now)  # 创建时间
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)  # 更新时间


class XhsSearchRecord(Base):
    """小红书搜索记录模型"""
    __tablename__ = "xhs_search_records"

    id = Column(String(50), primary_key=True, comment="记录ID")
    keyword = Column(String(200), nullable=False, comment="搜索关键词")
    search_type = Column(String(50), default="notes", comment="搜索类型：notes, users")
    result_count = Column(Integer, default=0, comment="搜索结果数量")
    
    # 搜索参数
    page = Column(Integer, default=1, comment="页码")
    page_size = Column(Integer, default=20, comment="每页数量")
    sort = Column(String(50), default="general", comment="排序方式")
    
    # 搜索结果统计
    total_results = Column(Integer, default=0, comment="总结果数")
    has_more = Column(Boolean, default=False, comment="是否还有更多")
    
    # 时间信息
    search_time = Column(DateTime, default=func.now(), comment="搜索时间")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")


class XhsApiLog(Base):
    """小红书API调用日志模型"""
    __tablename__ = "xhs_api_logs"

    id = Column(String(50), primary_key=True, comment="日志ID")
    api_name = Column(String(100), nullable=False, comment="API接口名称")
    method = Column(String(20), comment="请求方法")
    endpoint = Column(String(200), comment="请求端点")
    
    # 请求参数
    request_params = Column(JSON, comment="请求参数")
    
    # 响应信息
    response_code = Column(Integer, comment="响应状态码")
    response_time = Column(Float, comment="响应时间（秒）")
    response_size = Column(Integer, comment="响应大小（字节）")
    
    # 结果统计
    success = Column(Boolean, default=True, comment="是否成功")
    error_message = Column(Text, comment="错误信息")
    data_count = Column(Integer, default=0, comment="返回数据条数")
    
    # 时间信息
    call_time = Column(DateTime, default=func.now(), comment="调用时间")
    created_at = Column(DateTime, default=func.now(), comment="创建时间") 