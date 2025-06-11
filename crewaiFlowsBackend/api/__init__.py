# API模块初始化文件

from .accounts import router as accounts_router
from .contents import router as contents_router
from .competitors import router as competitors_router
from .schedules import schedules_router
from .chat import chat_router
from .analytics import analytics_router
from .crew import crew_router
from .tasks import tasks_router
from .sops import router as sops_router

# 导出所有路由器
__all__ = [
    "accounts_router",
    "contents_router", 
    "competitors_router",
    "schedules_router",
    "chat_router",
    "analytics_router",
    "crew_router",
    "tasks_router",
    "sops_router"
] 