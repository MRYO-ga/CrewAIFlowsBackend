# crew API路由模块 - 处理crew流程相关的API接口

import json
from uuid import uuid4
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from utils.jobManager import append_event, get_job_by_id
from tasks import app as celery_app

# 创建路由器
crew_router = APIRouter(prefix="/api", tags=["crew"])


# 定义子Agent配置模型
class AgentConfig(BaseModel):
    account_info_writer: Optional[bool] = Field(None, description="账号基础信息撰写Agent")
    unique_persona_builder: Optional[bool] = Field(None, description="独特人设定位构建Agent")
    content_direction_planner: Optional[bool] = Field(None, description="主题内容方向规划Agent")


# 定义内容创作配置模型
class ContentCreationConfig(BaseModel):
    content_creator: Optional[bool] = Field(None, description="内容创作Agent")


# 定义竞品分析配置模型
class CompetitorAnalysisConfig(BaseModel):
    platform_trend_decoder: Optional[bool] = Field(None, description="平台趋势解析Agent")
    content_style_analyst: Optional[bool] = Field(None, description="内容风格分析Agent")


# 定义Crew配置模型
class CrewConfig(BaseModel):
    persona_management: Optional[Union[Dict[str, bool], AgentConfig, str]] = Field(None, description="人设管理模块配置，支持对象或字符串")
    competitor_analysis: Optional[Union[Dict[str, bool], CompetitorAnalysisConfig, str]] = Field(None, description="竞品分析模块配置，支持对象或字符串")
    content_creation: Optional[Union[Dict[str, bool], ContentCreationConfig, str]] = Field(None, description="内容创作模块配置，支持对象或字符串")
    compliance_check: Optional[str] = Field(None, description="合规检测模块配置")
    publication: Optional[str] = Field(None, description="发布互动模块配置")


# 定义输入数据模型 - 小红书自动化运营系统请求
class XiaoHongShuRequest(BaseModel):
    """小红书自动化运营系统请求模型"""
    requirements: str = Field(..., description="详细需求描述")
    reference_urls: Optional[List[str]] = Field(None, description="参考链接")
    additional_data: Optional[Dict[str, Any]] = Field(None, description="其他附加数据")
    crew: Optional[CrewConfig] = Field(None, description="子Agent配置")


@crew_router.post("/crew")
async def run_flow(request: XiaoHongShuRequest):
    """开启一次作业运行flow"""
    try:
        job_id = str(uuid4())
        print(f"生成作业ID: {job_id}")
        
        # 构建输入数据
        input_data = {
            "requirements": request.requirements,
            "reference_urls": request.reference_urls,
            "additional_data": request.additional_data
        }
        
        # 添加crew配置
        if request.crew:
            # 转换为字典格式以便于JSON序列化
            crew_dict = request.crew.dict(exclude_none=True)
            
            # 为了兼容性，检查每个模块的配置格式
            for module, config in crew_dict.items():
                # 如果是字典，保持原样
                if isinstance(config, dict):
                    print(f"模块 {module} 使用对象配置: {config}")
                # 如果是字符串或其它类型，不做处理
                else:
                    print(f"模块 {module} 使用字符串配置: {config}")
            
            input_data["crew"] = crew_dict
            print(f"完整的crew配置: {json.dumps(crew_dict, ensure_ascii=False)}")
        
        # 记录初始事件
        initial_event = {
            "event_type": "job_created",
            "requirements": request.requirements,
            "input_data": input_data
        }
        append_event(job_id, json.dumps(initial_event, ensure_ascii=False))
        
        # 使用 Celery 调用 kickoff_flow 任务
        print(f"准备调用 Celery 任务")
        print(f"输入数据: {json.dumps(input_data, ensure_ascii=False)}")
        celery_app.send_task('tasks.kickoff_flow', args=[job_id, input_data])
        print(f"任务已分发，作业ID: {job_id}")
        
        return {
            "job_id": job_id, 
            "message": "任务已提交，正在处理中",
            "input_data": input_data
        }
        
    except Exception as e:
        print(f"启动作业时出错:\n\n {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@crew_router.get("/crew/{job_id}")
async def get_status(job_id: str):
    """查询特定作业状态"""
    job = get_job_by_id(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="未找到该作业")

    # 尝试解析作业结果为JSON格式
    try:
        result_json = json.loads(str(job.result))
    except json.JSONDecodeError:
        result_json = str(job.result)

    # 返回作业ID、状态、结果和事件的JSON响应
    return {
        "job_id": job_id,
        "status": job.status,
        "result": result_json,
        "events": [{"timestamp": event.timestamp.isoformat(), "data": event.data} for event in job.events]
    }


@crew_router.get("/agent-types")
async def get_agent_types():
    """返回系统支持的所有Agent类型及其功能描述"""
    return {
        "agent_types": [
            {
                "type": "account_persona_agent",
                "name": "账号人设管理Agent",
                "description": "管理账号档案、分组、粉丝画像等，为内容生成和运营策略提供基础数据。"
            },
            {
                "type": "competitor_analysis_agent",
                "name": "竞品分析Agent",
                "description": "自动筛选竞品、提取爆款策略、输出分析报告，为市场洞察提供支持。"
            },
            {
                "type": "content_creation_agent",
                "name": "内容生成Agent",
                "description": "结合人设和竞品策略，自动生成多风格内容，支持素材智能匹配。"
            },
            {
                "type": "compliance_check_agent",
                "name": "合规检测Agent",
                "description": "内容合规性检测与敏感词过滤，保障所有内容符合平台规范。"
            },
            {
                "type": "publication_agent",
                "name": "发布互动Agent",
                "description": "自动发布内容、收集互动数据、优化发布策略，提高内容曝光和互动效果。"
            }
        ]
    }


@crew_router.get("/capabilities")
async def get_capabilities():
    """返回系统支持的核心能力和功能"""
    return {
        "capabilities": [
            {
                "name": "账号人设管理",
                "description": "管理多个小红书账号的人设定位、粉丝画像分析和内容策略规划",
                "features": ["账号建档与验证", "多账号分组管理", "粉丝画像动态更新", "内容风格定制"]
            },
            {
                "name": "竞品分析",
                "description": "自动分析小红书平台上的竞品账号和爆款内容",
                "features": ["竞品筛选与监控", "爆款要素拆解", "趋势分析", "竞品策略报告"]
            },
            {
                "name": "内容生成",
                "description": "基于账号人设和竞品分析自动生成小红书内容",
                "features": ["多模板生成", "素材智能匹配", "标题优化", "合规预处理"]
            },
            {
                "name": "合规检测",
                "description": "确保内容符合小红书平台规则和行业法规",
                "features": ["敏感词检测", "原创度检测", "违规内容过滤", "修改建议生成"]
            },
            {
                "name": "内容发布与互动",
                "description": "自动调度发布内容并收集互动数据",
                "features": ["定时发布", "评论自动回复", "互动数据分析", "策略优化建议"]
            },
            {
                "name": "智能数据分析",
                "description": "通过MCP协议智能获取和分析用户数据，提供个性化优化建议",
                "features": ["智能数据获取", "AI驱动分析", "个性化优化", "实时策略调整"]
            }
        ]
    } 