"""
简化的聊天服务
负责处理聊天流程，自动连接MCP，并提供流式输出
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, AsyncGenerator
from datetime import datetime
from pathlib import Path

from .llm_service import LLMService, StreamChunk
from .tool_service import ToolService
from .mcp_client_service import mcp_client_service  # 使用全局实例
from .mcp_server_manager import mcp_server_manager
from .multi_mcp_client_service import multi_mcp_client_service  # 多服务器MCP客户端

class ChatService:
    """简化的聊天服务类"""
    
    def __init__(self):
        """初始化聊天服务"""
        self.logger = logging.getLogger(__name__)
        
        # 使用多服务器MCP客户端实例
        self.multi_mcp_client = multi_mcp_client_service
        
        # 保留单服务器MCP客户端作为备用
        self.mcp_client = mcp_client_service
        
        # 初始化工具服务（优先使用多服务器客户端）
        self.tool_service = ToolService(self.multi_mcp_client)
        
        # 初始化LLM服务
        self.llm_service = LLMService(self.tool_service)
        
        # MCP连接状态标志
        self._mcp_initialized = False
        
        print("🎉 聊天服务初始化完成（支持多MCP服务器）")
    
    async def _ensure_mcp_connected(self):
        """确保MCP已连接（延迟初始化）"""
        if not self._mcp_initialized:
            await self._auto_connect_mcp()
            self._mcp_initialized = True
    
    async def _auto_connect_mcp(self):
        """自动连接MCP服务器（优先使用多服务器连接）"""
        try:
            print("🔌 开始自动连接所有MCP服务器...")
            
            # 首先尝试连接到所有服务器（SQL + 小红书）
            success = await self.multi_mcp_client.connect_to_all_servers()
            
            if success:
                print("✅ 多服务器MCP连接成功")
                return True
            else:
                print("⚠️ 多服务器MCP连接失败，尝试单服务器模式...")
                
                # 如果多服务器连接失败，回退到单服务器模式
                fallback_success = await mcp_server_manager.auto_connect_best_server()
                
                if fallback_success:
                    print("✅ 单服务器MCP连接成功（回退模式）")
                    # 切换工具服务到单服务器客户端
                    self.tool_service = ToolService(self.mcp_client)
                    return True
                else:
                    print("❌ 所有MCP连接方式都失败")
                    return False
            
        except Exception as e:
            print(f"❌ 自动连接MCP服务器失败: {e}")
            return False
    
    async def process_message_stream(self, user_input: str, user_id: str = "default", 
                                   model: str = "gpt-4o-mini",
                                   conversation_history: Optional[List[Dict[str, Any]]] = None,
                                   attached_data: Optional[List[Dict[str, Any]]] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式处理用户消息
        
        Args:
            user_input: 用户输入
            user_id: 用户ID
            model: 使用的AI模型
            conversation_history: 对话历史
            attached_data: 附加的引用数据
            
        Yields:
            流式响应数据
        """
        try:
            print(f"📨 收到用户消息: {user_input[:50]}...")
            
            # 记录附加数据信息
            if attached_data and len(attached_data) > 0:
                print(f"📎 检测到附加数据: {len(attached_data)} 项")
                for i, data in enumerate(attached_data, 1):
                    data_type = data.get('type', 'unknown')
                    data_name = data.get('data', {}).get('name', '未知')
                    print(f"   {i}. 【{data_type}】{data_name}")
            
            # 确保MCP已连接
            await self._ensure_mcp_connected()
            
            # 开始流式处理
            async for chunk in self.llm_service.process_message_stream(user_input, conversation_history, model):
                # 转换为API响应格式
                yield {
                    "type": chunk.type,
                    "content": chunk.content,
                    "data": chunk.data,
                    "timestamp": chunk.timestamp
                }
                
        except Exception as error:
            self.logger.error(f"流式处理消息失败: {error}")
            yield {
                "type": "error",
                "content": f"处理消息时发生错误: {error}",
                "data": {"error": str(error)},
                "timestamp": datetime.now().isoformat()
            }
    
    async def simple_chat(self, user_input: str, user_id: str = "default", 
                         model: str = "gpt-4o-mini",
                         conversation_history: Optional[List[Dict[str, Any]]] = None) -> str:
        """
        简单聊天接口（非流式）
        
        Args:
            user_input: 用户输入
            user_id: 用户ID
            model: 使用的AI模型
            conversation_history: 对话历史
            
        Returns:
            LLM回答
        """
        try:
            # 确保MCP已连接
            await self._ensure_mcp_connected()
            
            response = await self.llm_service.simple_chat(user_input, conversation_history, model)
            return response
            
        except Exception as error:
            self.logger.error(f"简单聊天失败: {error}")
            return f"抱歉，处理您的请求时发生了错误: {error}"
    
    async def simple_chat_with_persona(self, user_input: str, user_id: str = "default", 
                                     model: str = "gpt-4o-mini",
                                     conversation_history: Optional[List[Dict[str, Any]]] = None,
                                     persona_prompt: str = "") -> str:
        """
        带人设的简单聊天接口（非流式）
        
        Args:
            user_input: 用户输入
            user_id: 用户ID
            model: 使用的AI模型
            conversation_history: 对话历史
            persona_prompt: 人设系统提示词
            
        Returns:
            LLM回答
        """
        try:
            # 确保MCP已连接
            await self._ensure_mcp_connected()
            
            response = await self.llm_service.simple_chat_with_persona(
                user_input, 
                conversation_history, 
                model, 
                persona_prompt
            )
            return response
            
        except Exception as error:
            self.logger.error(f"人设聊天失败: {error}")
            return f"抱歉，处理您的请求时发生了错误: {error}"
    
    async def get_mcp_status(self) -> Dict[str, Any]:
        """获取MCP连接状态"""
        try:
            # 确保MCP已连接
            await self._ensure_mcp_connected()
            
            # 优先检查多服务器连接状态
            multi_connected = self.multi_mcp_client.is_connected()
            single_connected = self.mcp_client.is_connected()
            
            is_connected = multi_connected or single_connected
            
            if multi_connected:
                # 使用多服务器客户端的工具
                tools = await self.multi_mcp_client.get_tools()
                connected_servers = self.multi_mcp_client.get_connected_servers()
                tool_list = [{"name": t.function["name"], "description": t.function["description"]} for t in tools]
                
                return {
                    "connected": True,
                    "tools_count": len(tools),
                    "tools": tool_list,
                    "connected_servers": connected_servers,
                    "connection_type": "multi_server"
                }
            elif single_connected:
                # 使用单服务器客户端的工具
                tools = await self.tool_service.get_tools_for_llm()
                tool_list = [{"name": t["name"], "description": t["description"]} for t in tools]
                
                return {
                    "connected": True,
                    "tools_count": len(tools),
                    "tools": tool_list,
                    "connected_servers": ["single_server"],
                    "connection_type": "single_server"
                }
            else:
                return {
                    "connected": False,
                    "tools_count": 0,
                    "tools": [],
                    "connected_servers": [],
                    "connection_type": "none"
                }
            
        except Exception as e:
            self.logger.error(f"获取MCP状态失败: {e}")
            return {
                "connected": False,
                "tools_count": 0,
                "tools": [],
                "connected_servers": [],
                "error": str(e)
            }
    
    async def reconnect_mcp(self) -> bool:
        """重新连接MCP服务器"""
        try:
            print("🔄 重新连接所有MCP服务器...")
            # 重置初始化标志，强制重新连接
            self._mcp_initialized = False
            
            # 关闭现有连接
            if self.multi_mcp_client.is_connected():
                await self.multi_mcp_client.close()
            
            # 重新连接
            await self._ensure_mcp_connected()
            
            # 检查连接状态
            return self.multi_mcp_client.is_connected() or self.mcp_client.is_connected()
            
        except Exception as e:
            self.logger.error(f"重新连接MCP失败: {e}")
            return False 