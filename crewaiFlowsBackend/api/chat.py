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
    """智能聊天接口，集成MCP数据获取功能"""
    try:
        print(f"收到聊天请求，用户ID: {request.user_id}")
        print(f"用户输入: {request.user_input}")
        
        # 检查是否需要智能数据获取和优化
        if any(keyword in request.user_input.lower() for keyword in ["优化", "账号", "基础信息", "竞品", "内容", "发布"]):
            print("检测到优化需求，启动智能数据分析...")
            
            # 通过MCP获取用户相关数据
            user_context = smart_data_manager.get_user_data_context(request.user_id)
            print(f"获取用户上下文数据: {len(user_context)} 个模块")
            
            # 判断具体的优化类型
            optimization_target = "comprehensive"
            if "账号" in request.user_input or "基础信息" in request.user_input:
                optimization_target = "account_info"
            elif "内容" in request.user_input:
                optimization_target = "content_strategy"
            elif "发布" in request.user_input or "计划" in request.user_input:
                optimization_target = "publishing_plan"
            
            # 执行智能分析和优化
            optimization_result = smart_data_manager.analyze_and_optimize(
                request.user_id, 
                optimization_target, 
                user_context
            )
            
            # 构建包含优化建议的回复
            optimized_reply = f"""基于您的{optimization_target}优化需求，我已经分析了您的账号数据：

📊 **当前数据概览**：
• 账号名称：{user_context.get('account_info', {}).get('account_name', '未知')}
• 粉丝数量：{user_context.get('account_info', {}).get('profile_data', {}).get('followers_count', 0):,}
• 平均互动率：{user_context.get('account_info', {}).get('performance_metrics', {}).get('engagement_rate', 0)}%

🎯 **智能分析结果**："""

            if optimization_result.get('optimization_result'):
                opt_result = optimization_result['optimization_result']
                if isinstance(opt_result, dict):
                    if 'optimized_bio' in opt_result:
                        optimized_reply += f"\n\n**优化后的个人简介**：\n{opt_result['optimized_bio']}"
                    if 'recommended_tags' in opt_result:
                        optimized_reply += f"\n\n**建议标签**：{', '.join(opt_result['recommended_tags'])}"
                    if 'improvement_actions' in opt_result:
                        optimized_reply += f"\n\n**具体改进措施**：\n" + "\n".join([f"• {action}" for action in opt_result['improvement_actions']])
                else:
                    optimized_reply += f"\n{opt_result}"
            
            # 添加竞品参考信息
            if user_context.get('competitor_analysis'):
                competitors = user_context['competitor_analysis']
                optimized_reply += f"\n\n📈 **竞品参考**：\n"
                for comp in competitors[:2]:  # 只显示前2个竞品
                    optimized_reply += f"• {comp['name']}：{comp['follower_count']} 粉丝，擅长{comp['category']}\n"
            
            # 添加后续建议
            optimized_reply += f"\n\n💡 **下一步建议**：\n• 根据以上分析实施优化措施\n• 定期监控数据变化\n• 持续调整策略以获得最佳效果"
            
            return {
                "reply": optimized_reply,
                "data": {
                    "optimization_result": optimization_result,
                    "user_context_summary": {
                        "account_name": user_context.get('account_info', {}).get('account_name'),
                        "followers_count": user_context.get('account_info', {}).get('profile_data', {}).get('followers_count'),
                        "content_count": len(user_context.get('content_library', [])),
                        "competitor_count": len(user_context.get('competitor_analysis', []))
                    }
                }
            }
        
        # 如果不是优化需求，使用普通的意图解析Agent
        result = interact_with_intent_agent(
            request.user_input,
            request.conversation_history
        )
        
        # 如果意图解析完成且包含crew配置，也可以提供相关数据
        if result.get("data") and result["data"].get("crew"):
            print(f"意图解析完成，解析结果: {result['data']}")
            
            # 可以在这里添加相关的数据支持
            crew_config = result["data"].get("crew", {})
            if crew_config:
                # 获取相关的背景数据
                context_data = smart_data_manager.get_user_data_context(request.user_id)
                result["data"]["context_data"] = {
                    "account_summary": context_data.get('account_info', {}).get('account_name', ''),
                    "available_data": list(context_data.keys())
                }
        
        return result
        
    except Exception as e:
        print(f"对话处理出错: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@chat_router.post("/optimize")
async def optimize_user_data(request: OptimizationRequest):
    """专门的用户数据优化接口"""
    try:
        print(f"收到优化请求，用户ID: {request.user_id}, 优化类型: {request.optimization_type}")
        
        # 获取用户数据上下文
        user_context = smart_data_manager.get_user_data_context(request.user_id)
        
        # 执行智能分析和优化
        optimization_result = smart_data_manager.analyze_and_optimize(
            request.user_id,
            request.optimization_type,
            user_context
        )
        
        return {
            "status": "success",
            "user_id": request.user_id,
            "optimization_type": request.optimization_type,
            "result": optimization_result,
            "timestamp": optimization_result.get("timestamp")
        }
        
    except Exception as e:
        print(f"优化处理出错: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


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


@chat_router.get("/chat/history")
async def get_chat_history():
    """获取聊天历史"""
    return {"message": "聊天历史功能开发中"}


@chat_router.post("/chat/save")
async def save_message():
    """保存聊天消息"""
    return {"message": "聊天消息保存功能开发中"} 