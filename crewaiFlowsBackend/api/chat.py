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
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from utils.myLLM import interact_with_intent_agent
from utils.smart_data_manager import smart_data_manager

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
    """智能聊天接口，集成MCP工具调用和任务拆解功能"""
    try:
        print(f"收到聊天请求，用户ID: {request.user_id}")
        print(f"用户输入: {request.user_input}")
        
        # 使用新的聊天服务
        from services.chat_service import ChatService
        
        chat_service = ChatService()
        
        # 处理用户消息
        response = await chat_service.process_message(
            user_input=request.user_input,
            user_id=request.user_id,
            conversation_history=request.conversation_history
        )
        
        # 转换为API响应格式
        result = {
            "status": "success",
            "message": "处理完成",
            "final_answer": response.final_answer,
            "data": {
                "task_decomposition": response.task_decomposition.dict() if response.task_decomposition else None,
                "steps_executed": [step.dict() for step in response.steps_executed],
                "metadata": response.metadata,
                "tools_used": response.metadata.get("tools_used", [])
            }
        }
        
        print(f"处理完成，步骤数: {response.metadata.get('steps_count', 0)}")
        print(f"使用的工具: {response.metadata.get('tools_used', [])}")
        
        return result
        
    except Exception as e:
        print(f"对话处理出错: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


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
    """流式聊天接口，实时展示任务执行步骤"""
    from fastapi.responses import StreamingResponse
    from services.chat_service import ChatService
    import json
    
    async def generate_stream():
        try:
            chat_service = ChatService()
            
            async for chunk in chat_service.stream_message(
                user_input=request.user_input,
                user_id=request.user_id,
                conversation_history=request.conversation_history
            ):
                # 将数据转换为JSON格式并发送
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
                
        except Exception as e:
            error_chunk = {
                "type": "error",
                "message": f"流式处理出错: {str(e)}",
                "error": str(e)
            }
            yield f"data: {json.dumps(error_chunk, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream"
        }
    )

@chat_router.post("/chat/analyze")
async def analyze_user_request(request: ChatRequest):
    """分析用户请求，返回任务拆解结果"""
    try:
        print(f"分析用户请求，用户ID: {request.user_id}")
        print(f"用户输入: {request.user_input}")
        
        from services.chat_service import ChatService
        
        chat_service = ChatService()
        
        # 分析用户请求
        task_decomposition = await chat_service.analyze_user_request(request.user_input)
        
        result = {
            "status": "success",
            "message": "分析完成",
            "data": {
                "task_decomposition": task_decomposition.dict(),
                "estimated_steps": len(task_decomposition.steps),
                "requires_tools": task_decomposition.requires_tools,
                "tool_names": task_decomposition.tool_names
            }
        }
        
        print(f"分析完成，拆解为 {len(task_decomposition.steps)} 个步骤")
        print(f"需要工具: {task_decomposition.requires_tools}")
        
        return result
        
    except Exception as e:
        print(f"分析请求出错: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@chat_router.get("/chat/tools")
async def get_available_tools():
    """获取当前可用的工具列表"""
    try:
        from services.chat_service import ChatService
        from services.mcp_server_manager import mcp_server_manager
        
        chat_service = ChatService()
        tools = await chat_service.get_available_tools()
        
        # 获取当前连接的服务器信息
        current_server = mcp_server_manager.get_current_server()
        
        return {
            "status": "success",
            "message": "获取工具列表成功",
            "data": {
                "tools": tools,
                "count": len(tools),
                "current_server": {
                    "name": current_server.name if current_server else None,
                    "description": current_server.description if current_server else None,
                    "tools_count": current_server.tools_count if current_server else 0,
                    "status": current_server.status.value if current_server else "unknown"
                }
            }
        }
        
    except Exception as e:
        print(f"获取工具列表出错: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@chat_router.get("/chat/context/{user_id}")
async def get_chat_context(user_id: str):
    """获取用户的聊天上下文"""
    try:
        from services.chat_service import ChatService
        
        chat_service = ChatService()
        context = await chat_service.get_chat_context(user_id)
        
        return {
            "status": "success",
            "message": "获取聊天上下文成功",
            "data": context
        }
        
    except Exception as e:
        print(f"获取聊天上下文出错: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@chat_router.get("/chat/history")
async def get_chat_history():
    """获取聊天历史"""
    return {"message": "聊天历史功能开发中"}


@chat_router.post("/chat/save")
async def save_message():
    """保存聊天消息"""
    return {"message": "聊天消息保存功能开发中"} 