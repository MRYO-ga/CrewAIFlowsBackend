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

class ChatService:
    """简化的聊天服务类"""
    
    def __init__(self):
        """初始化聊天服务"""
        self.logger = logging.getLogger(__name__)
        
        # 使用全局MCP客户端实例（与MCPServerManager使用同一个）
        self.mcp_client = mcp_client_service
        
        # 初始化工具服务
        self.tool_service = ToolService(self.mcp_client)
        
        # 初始化LLM服务
        self.llm_service = LLMService(self.tool_service)
        
        # MCP连接状态标志
        self._mcp_initialized = False
        
        print("🎉 聊天服务初始化完成")
    
    async def _ensure_mcp_connected(self):
        """确保MCP已连接（延迟初始化）"""
        if not self._mcp_initialized:
            await self._auto_connect_mcp()
            self._mcp_initialized = True
    
    async def _auto_connect_mcp(self):
        """自动连接MCP服务器"""
        try:
            print("🔌 开始自动连接MCP服务器...")
            
            # 使用MCPServerManager进行自动连接
            success = await mcp_server_manager.auto_connect_best_server()
            
            if success:
                print("✅ MCP服务器自动连接成功")
            else:
                print("❌ MCP服务器自动连接失败")
            
        except Exception as e:
            print(f"❌ 自动连接MCP服务器失败: {e}")
    
    async def process_message_stream(self, user_input: str, user_id: str = "default", 
                                   conversation_history: Optional[List[Dict[str, Any]]] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式处理用户消息
        
        Args:
            user_input: 用户输入
            user_id: 用户ID
            conversation_history: 对话历史
            
        Yields:
            流式响应数据
        """
        try:
            print(f"📨 收到用户消息: {user_input[:50]}...")
            
            # 确保MCP已连接
            await self._ensure_mcp_connected()
            
            # 开始流式处理
            async for chunk in self.llm_service.process_message_stream(user_input, conversation_history):
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
                         conversation_history: Optional[List[Dict[str, Any]]] = None) -> str:
        """
        简单聊天接口（非流式）
        
        Args:
            user_input: 用户输入
            user_id: 用户ID
            conversation_history: 对话历史
            
        Returns:
            LLM回答
        """
        try:
            # 确保MCP已连接
            await self._ensure_mcp_connected()
            
            response = await self.llm_service.simple_chat(user_input, conversation_history)
            return response
            
        except Exception as error:
            self.logger.error(f"简单聊天失败: {error}")
            return f"抱歉，处理您的请求时发生了错误: {error}"
    
    async def get_mcp_status(self) -> Dict[str, Any]:
        """获取MCP连接状态"""
        try:
            # 确保MCP已连接
            await self._ensure_mcp_connected()
            
            is_connected = self.mcp_client.is_connected()
            tools = await self.tool_service.get_tools_for_llm() if is_connected else []
            
            return {
                "connected": is_connected,
                "tools_count": len(tools),
                "tools": [{"name": t["name"], "description": t["description"]} for t in tools]
            }
            
        except Exception as e:
            self.logger.error(f"获取MCP状态失败: {e}")
            return {
                "connected": False,
                "tools_count": 0,
                "tools": [],
                "error": str(e)
            }
    
    async def reconnect_mcp(self) -> bool:
        """重新连接MCP服务器"""
        try:
            print("🔄 重新连接MCP服务器...")
            # 重置初始化标志，强制重新连接
            self._mcp_initialized = False
            await self._ensure_mcp_connected()
            return self.mcp_client.is_connected()
            
        except Exception as e:
            self.logger.error(f"重新连接MCP失败: {e}")
            return False 