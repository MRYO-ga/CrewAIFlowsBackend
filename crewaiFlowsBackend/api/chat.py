# 聊天API（简化版）
from fastapi import APIRouter

router = APIRouter(prefix="/api/chat-db", tags=["聊天数据库"])

@router.get("/messages")
async def get_chat_messages():
    """获取聊天消息列表"""
    return {"message": "聊天数据库功能开发中"}

@router.post("/messages")
async def save_chat_message():
    """保存聊天消息"""
    return {"message": "聊天消息保存功能开发中"}

# chat API路由模块 - 处理智能对话和优化相关的API接口

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import json
from utils.myLLM import interact_with_intent_agent
from utils.smart_data_manager import smart_data_manager

# 创建全局聊天服务实例
from services.chat_service import ChatService
chat_service = ChatService()

# 创建路由器
chat_router = APIRouter(prefix="/api", tags=["chat"])

# 定义对话请求模型
class ChatRequest(BaseModel):
    """对话请求模型"""
    user_input: str = Field(..., description="用户输入的消息")
    conversation_history: Optional[List[Dict[str, Any]]] = Field(None, description="对话历史")
    user_id: Optional[str] = Field("default_user", description="用户ID")


# 定义智能优化请求模型
class OptimizationRequest(BaseModel):
    """智能优化请求模型"""
    user_id: str = Field(..., description="用户ID")
    optimization_type: str = Field(..., description="优化类型：account_info, content_strategy, publishing_plan")
    target_area: Optional[str] = Field(None, description="具体优化区域")


@chat_router.post("/chat")
async def chat_with_agent(request: ChatRequest):
    """简单聊天接口（非流式）"""
    try:
        print(f"收到非流式聊天请求，用户ID: {request.user_id}")
        print(f"用户输入: {request.user_input}")
        
        response = await chat_service.simple_chat(
            user_input=request.user_input,
            user_id=request.user_id,
            conversation_history=request.conversation_history
        )
        
        return {
            "status": "success",
            "reply": response,
            "final_answer": response,
            "data": {
                "type": "simple_chat"
            }
        }
        
    except Exception as e:
        print(f"非流式聊天处理出错: {str(e)}")
        return {
            "status": "error",
            "reply": f"抱歉，处理您的请求时发生了错误: {str(e)}",
            "error": str(e)
        }


# @chat_router.post("/optimize")
# async def optimize_user_data(request: OptimizationRequest):
#     """专门的用户数据优化接口"""
#     try:
#         print(f"收到优化请求，用户ID: {request.user_id}, 优化类型: {request.optimization_type}")
        
#         # 获取用户数据上下文
#         user_context = smart_data_manager.get_user_data_context(request.user_id)
        
#         # 执行智能分析和优化
#         optimization_result = smart_data_manager.analyze_and_optimize(
#             request.user_id,
#             request.optimization_type,
#             user_context
#         )
        
#         return {
#             "status": "success",
#             "user_id": request.user_id,
#             "optimization_type": request.optimization_type,
#             "result": optimization_result,
#             "timestamp": optimization_result.get("timestamp")
#         }
        
#     except Exception as e:
#         print(f"优化处理出错: {str(e)}")
#         raise HTTPException(status_code=500, detail=str(e))


@chat_router.get("/user-context/{user_id}")
async def get_user_context(user_id: str, data_type: str = "all"):
    """获取用户的数据上下文"""
    try:
        print(f"获取用户上下文，用户ID: {user_id}, 数据类型: {data_type}")
        
        # 通过MCP获取用户数据
        user_context = smart_data_manager.get_user_data_context(user_id, data_type)
        
        return {
            "status": "success",
            "user_id": user_id,
            "data_type": data_type,
            "context": user_context,
            "summary": {
                "modules_count": len(user_context),
                "available_modules": list(user_context.keys())
            }
        }
        
    except Exception as e:
        print(f"获取用户上下文出错: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@chat_router.post("/chat/stream")
async def stream_chat_with_agent(request: ChatRequest):
    """流式聊天接口，实时展示对话过程"""
    
    async def generate_stream():
        try:
            print(f"收到流式聊天请求，用户ID: {request.user_id}")
            print(f"用户输入: {request.user_input}")
            
            async for chunk in chat_service.process_message_stream(
                user_input=request.user_input,
                user_id=request.user_id,
                conversation_history=request.conversation_history
            ):
                # 发送服务器发送事件格式
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
                
        except Exception as e:
            error_chunk = {
                "type": "error",
                "content": f"流式处理出错: {str(e)}",
                "data": {"error": str(e)},
                "timestamp": ""
            }
            yield f"data: {json.dumps(error_chunk, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type"
        }
    )

@chat_router.post("/chat/analyze")
async def analyze_user_request(request: ChatRequest):
    """分析用户请求，返回任务拆解结果"""
    try:
        print(f"分析用户请求，用户ID: {request.user_id}")
        print(f"用户输入: {request.user_input}")
        
        # 使用全局的chat_service实例，不要创建新的
        # 分析用户请求 (这个方法可能需要添加到ChatService中)
        # task_decomposition = await chat_service.analyze_user_request(request.user_input)
        
        # 暂时返回简单响应，因为analyze_user_request方法可能不存在
        result = {
            "status": "success",
            "message": "分析功能开发中",
            "data": {
                "task_decomposition": {"steps": [], "requires_tools": False, "tool_names": []},
                "estimated_steps": 0,
                "requires_tools": False,
                "tool_names": []
            }
        }
        
        print("分析功能开发中")
        
        return result
        
    except Exception as e:
        print(f"分析请求出错: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@chat_router.get("/chat/mcp-status")
async def get_mcp_status():
    """获取MCP连接状态和可用工具"""
    try:
        status = await chat_service.get_mcp_status()
        return {
            "status": "success",
            "data": status
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "data": {
                "connected": False,
                "tools_count": 0,
                "tools": []
            }
        }

@chat_router.post("/chat/mcp-reconnect")
async def reconnect_mcp():
    """重新连接MCP服务器"""
    try:
        success = await chat_service.reconnect_mcp()
        if success:
            status = await chat_service.get_mcp_status()
            return {
                "status": "success",
                "message": "MCP重新连接成功",
                "data": status
            }
        else:
            return {
                "status": "error",
                "message": "MCP重新连接失败",
                "data": {
                    "connected": False,
                    "tools_count": 0,
                    "tools": []
                }
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"MCP重新连接失败: {str(e)}",
            "error": str(e)
        }

# 兼容性接口 - 保持原有API接口
@chat_router.get("/chat/tools")
async def get_available_tools():
    """获取可用工具列表（兼容性接口）"""
    try:
        status = await chat_service.get_mcp_status()
        return {
            "status": "success",
            "tools": status.get("tools", []),
            "count": status.get("tools_count", 0)
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "tools": [],
            "count": 0
        }

@chat_router.get("/chat/context/{user_id}")
async def get_chat_context(user_id: str):
    """获取聊天上下文（兼容性接口）"""
    try:
        status = await chat_service.get_mcp_status()
        return {
            "status": "success",
            "user_id": user_id,
            "context": {
                "mcp_connected": status.get("connected", False),
                "available_tools": status.get("tools", []),
                "tools_count": status.get("tools_count", 0)
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "context": {}
        }

# 占位符接口
@chat_router.get("/chat/history")
async def get_chat_history():
    """获取聊天历史（待实现）"""
    return {"message": "聊天历史功能开发中"}

@chat_router.post("/chat/save")
async def save_message():
    """保存聊天消息（待实现）"""
    return {"message": "消息保存功能开发中"} 