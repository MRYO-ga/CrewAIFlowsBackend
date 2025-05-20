# 核心功能:实现了一个基于FastAPI的API后端服务，主要功能包括:
# (1)创建FastAPI应用：实例化FastAPI应用并启用CORS，以支持跨域请求
# (2)环境变量设置：设置API_KEY环境变量，用于LLM和搜索引擎API的访问
# (3)作业管理：通过jobs字典管理并存储作业的状态和事件，确保在多线程环境中安全访问
# (4)启动Flow:
# kickoff_flow函数接受作业ID和输入参数并调用其kickoff方法启动flow
# 在执行过程中捕获异常并更新作业状态
# 使用线程异步执行作业，允许同时处理多个请求
# (5)POST接口 /api/crew：接收客户请求，验证输入数据，生成作业ID，启动kickoff_flow函数，并返回作业ID和HTTP状态码202
# (6)GET接口 /api/crew/<job_id>：根据作业ID查询作业状态，返回作业的状态、结果和相关事件


# 导入标准库
import json
from uuid import uuid4
from threading import Thread
import os
import uvicorn
# 导入第三方库
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from utils.jobManager import append_event, get_job_by_id, update_job_by_id
from utils.myLLM import create_llm, interact_with_intent_agent
from tasks import app as celery_app
# from utils.manager_agent import create_manager_agent


# 服务访问的端口
PORT = 8012


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


# 定义对话请求模型
class ChatRequest(BaseModel):
    """对话请求模型"""
    user_input: str = Field(..., description="用户输入的消息")
    conversation_history: Optional[List[Dict[str, Any]]] = Field(None, description="对话历史")


# 定义了一个异步函数lifespan，它接收一个FastAPI应用实例app作为参数。这个函数将管理应用的生命周期，包括启动和关闭时的操作
# 函数在应用启动时执行一些初始化操作
# 函数在应用关闭时执行一些清理操作
# @asynccontextmanager 装饰器用于创建一个异步上下文管理器，它允许在yield之前和之后执行特定的代码块，分别表示启动和关闭时的操作
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时执行
    print("小红书多Agent自动化运营系统初始化完成")
    # yield 关键字将控制权交还给FastAPI框架，使应用开始运行
    # 分隔了启动和关闭的逻辑。在yield 之前的代码在应用启动时运行，yield 之后的代码在应用关闭时运行
    yield
    # 关闭时执行
    print("正在关闭系统...")


# 实例化一个FastAPI实例
# lifespan 参数用于在应用程序生命周期的开始和结束时执行一些初始化或清理工作
app = FastAPI(
    title="小红书多Agent自动化运营系统",
    description="基于多Agent协作的小红书自动化运营系统，支持账号管理、竞品分析、内容生成、合规检测、发布与互动",
    version="1.0.0",
    lifespan=lifespan
)

# 启用CORS，允许任何来源访问以 /api/ 开头的接口
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# POST接口 /api/chat，与意图解析Agent进行对话
@app.post("/api/chat")
async def chat_with_agent(request: ChatRequest):
    try:
        # 调用意图解析Agent
        result = interact_with_intent_agent(
            request.user_input,
            request.conversation_history
        )
        
        # 如果data非空且包含完整信息，则表示对话已完成
        if result.get("data") and result["data"].get("crew"):
            print(f"对话完成，解析结果: {result['data']}")
        
        return result
        
    except Exception as e:
        print(f"对话处理出错: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# POST接口 /api/crew，开启一次作业运行flow
@app.post("/api/crew")
async def run_flow(request: XiaoHongShuRequest):
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


# GET接口 /api/crew/{job_id}，查询特定作业状态
@app.get("/api/crew/{job_id}")
async def get_status(job_id: str):
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

# 获取支持的Agent类型
@app.get("/api/agent-types")
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

# 获取系统能力
@app.get("/api/capabilities")
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
            }
        ]
    }

if __name__ == '__main__':
    print(f"在端口 {PORT} 上启动小红书多Agent自动化运营系统")
    # uvicorn是一个用于运行ASGI应用的轻量级、超快速的ASGI服务器实现
    # 用于部署基于FastAPI框架的异步PythonWeb应用程序
    uvicorn.run(app, host="0.0.0.0", port=PORT)
