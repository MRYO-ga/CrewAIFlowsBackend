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
import sys
import asyncio
import uvicorn

# 在所有其他导入之前设置Windows事件循环策略
if sys.platform == "win32":
    # 设置ProactorEventLoopPolicy以支持子进程
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    print("🔧 已在模块导入时设置Windows Proactor事件循环策略")
# 导入第三方库
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi import Request
from pathlib import Path
# 数据库相关导入
from database.database import create_tables
# 导入所有模型以确保表被创建
from database.models import (
    Account, Content, Competitor, Task, Schedule, 
    ChatMessage, CompetitorNote, Analytics,
    SOP, SOPCycle, SOPWeek, SOPTask, SOPTaskItem
)
from api import (
    accounts_router, 
    contents_router, 
    competitors_router,
    schedules_router,
    chat_router,
    analytics_router,
    crew_router,
    tasks_router,
    sops_router
)
from api.mcp_router import router as mcp_router


# 服务访问的端口
PORT = 9000

# 配置模板
templates = Jinja2Templates(directory="templates")


# 定义了一个异步函数lifespan，它接收一个FastAPI应用实例app作为参数。这个函数将管理应用的生命周期，包括启动和关闭时的操作
# 函数在应用启动时执行一些初始化操作
# 函数在应用关闭时执行一些清理操作
# @asynccontextmanager 装饰器用于创建一个异步上下文管理器，它允许在yield之前和之后执行特定的代码块，分别表示启动和关闭时的操作
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时执行
    print("小红书多Agent自动化运营系统初始化中...")
    # 创建数据库表
    create_tables()
    print("数据库表创建完成")
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

# 注册API路由
app.include_router(accounts_router)
app.include_router(contents_router) 
app.include_router(competitors_router)
app.include_router(schedules_router)
app.include_router(chat_router)
app.include_router(analytics_router)
app.include_router(crew_router)
app.include_router(tasks_router)
app.include_router(sops_router)
app.include_router(mcp_router)

# MCP演示页面路由
@app.get("/mcp-demo")
async def mcp_demo(request: Request):
    """MCP聊天演示页面"""
    return templates.TemplateResponse("mcp_chat.html", {"request": request})


if __name__ == '__main__':
    from startup_check import full_startup_check
    
    # 运行启动检查
    print("🚀 运行系统启动检查...")
    try:
        check_result = asyncio.run(full_startup_check())
        if not check_result:
            print("💥 启动检查失败，请检查系统设置")
            sys.exit(1)
    except Exception as e:
        print(f"⚠️ 启动检查时出现异常: {e}")
        print("⚠️ 将继续启动，但可能遇到兼容性问题")
    
    print(f"在端口 {PORT} 上启动小红书多Agent自动化运营系统")
    print("🌐 MCP演示页面: http://localhost:9000/mcp-demo")
    
    # 直接使用标准启动方式，事件循环策略已在模块导入时设置
    uvicorn.run(app, host="0.0.0.0", port=PORT)
