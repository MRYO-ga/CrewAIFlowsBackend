"""
聊天服务模块
整合MCP客户端、工具服务和LLM服务，提供完整的智能对话功能
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, AsyncGenerator
from pathlib import Path

from .mcp_client_service import MCPClientService, mcp_client_service
from .mcp_server_manager import mcp_server_manager
from .tool_service import ToolService
from .llm_service import LLMService, LLMResponse, TaskDecomposition

class ChatService:
    """聊天服务类"""
    
    def __init__(self):
        """初始化聊天服务"""
        self.logger = logging.getLogger(__name__)
        # 使用全局的MCP客户端服务，而不是创建新的
        self.mcp_client = mcp_client_service
        self.tool_service = None
        self.llm_service = None
        self._initialized = False
    
    async def initialize(self, openai_api_key: str = None, model: str = "gpt-4o-mini"):
        """
        初始化聊天服务
        
        Args:
            openai_api_key: OpenAI API密钥
            model: 使用的LLM模型
        """
        try:
            if self._initialized:
                return
            
            self.logger.info("正在初始化聊天服务...")
            
            # 1. 检查是否已有MCP连接，如果没有则自动连接
            if not self.mcp_client.is_connected():
                self.logger.info("MCP未连接，尝试自动连接到最佳服务器...")
                success = await mcp_server_manager.auto_connect_best_server()
                if not success:
                    self.logger.warning("自动连接MCP服务器失败，聊天功能可能受限")
            else:
                current_server = mcp_server_manager.get_current_server()
                self.logger.info(f"使用已连接的MCP服务器: {current_server.name if current_server else '未知'}")
            
            # 2. 初始化工具服务
            self.tool_service = ToolService(self.mcp_client)
            
            # 3. 初始化LLM服务，使用配置好的LLM类型
            self.llm_service = LLMService(
                self.tool_service, 
                openai_api_key, 
                model, 
                llm_type="openai"  # 使用myLLM.py中配置的代理服务
            )
            
            self._initialized = True
            self.logger.info("聊天服务初始化完成")
            
        except Exception as error:
            self.logger.error(f"初始化聊天服务失败: {error}")
            raise error
    

    
    async def process_message(self, user_input: str, user_id: str = "default", conversation_history: Optional[List[Dict[str, Any]]] = None) -> LLMResponse:
        """
        处理用户消息
        
        Args:
            user_input: 用户输入
            user_id: 用户ID
            conversation_history: 对话历史
            
        Returns:
            LLM响应结果
        """
        try:
            if not self._initialized:
                await self.initialize()
            
            self.logger.info(f"处理用户 {user_id} 的消息: {user_input}")
            
            # 检查MCP连接状态
            current_server = mcp_server_manager.get_current_server()
            if current_server:
                self.logger.info(f"使用MCP服务器: {current_server.name}")
            else:
                self.logger.warning("没有可用的MCP服务器")
            
            # 处理用户输入
            response = await self.llm_service.process_user_input(user_input, conversation_history)
            
            # 添加用户ID到元数据
            response.metadata["user_id"] = user_id
            response.metadata["timestamp"] = response.metadata.get("execution_time")
            
            return response
            
        except Exception as error:
            self.logger.error(f"处理用户消息失败: {error}")
            return LLMResponse(
                content=f"处理消息时发生错误: {error}",
                final_answer=f"抱歉，处理您的消息时发生了错误: {error}",
                metadata={"error": str(error), "user_id": user_id}
            )
    
    async def stream_message(self, user_input: str, user_id: str = "default", conversation_history: Optional[List[Dict[str, Any]]] = None) -> AsyncGenerator[Dict[str, Any], None]:
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
            if not self._initialized:
                await self.initialize()
            
            self.logger.info(f"流式处理用户 {user_id} 的消息: {user_input}")
            
            # 检查MCP连接状态
            current_server = mcp_server_manager.get_current_server()
            if current_server:
                self.logger.info(f"使用MCP服务器: {current_server.name}")
            
            # 流式处理用户输入
            async for chunk in self.llm_service.stream_response(user_input, conversation_history):
                # 添加用户ID到每个块
                chunk["user_id"] = user_id
                yield chunk
                
        except Exception as error:
            self.logger.error(f"流式处理用户消息失败: {error}")
            yield {
                "type": "error",
                "message": f"处理消息时发生错误: {error}",
                "error": str(error),
                "user_id": user_id
            }
    

    
    async def get_available_tools(self) -> List[Dict[str, Any]]:
        """
        获取当前可用的工具列表
        
        Returns:
            工具列表
        """
        try:
            if not self._initialized:
                await self.initialize()
            
            return await self.tool_service.get_tools_for_llm()
            
        except Exception as error:
            self.logger.error(f"获取工具列表失败: {error}")
            return []
    
    async def get_chat_context(self, user_id: str) -> Dict[str, Any]:
        """
        获取用户的聊天上下文
        
        Args:
            user_id: 用户ID
            
        Returns:
            聊天上下文信息
        """
        try:
            if not self._initialized:
                await self.initialize()
            
            # 获取可用工具
            tools = await self.get_available_tools()
            
            # 构建上下文
            context = {
                "user_id": user_id,
                "available_tools": tools,
                "mcp_servers": list(self.mcp_servers.keys()),
                "current_server": getattr(self.mcp_client, "_last_connection_path", None),
                "initialized": self._initialized
            }
            
            return context
            
        except Exception as error:
            self.logger.error(f"获取聊天上下文失败: {error}")
            return {"error": str(error)}
    
    async def analyze_user_request(self, user_input: str) -> TaskDecomposition:
        """
        分析用户请求
        
        Args:
            user_input: 用户输入
            
        Returns:
            任务拆解结果
        """
        try:
            if not self._initialized:
                await self.initialize()
            
            # 根据用户输入选择服务器
            await self._select_mcp_server(user_input)
            
            # 分析用户输入
            return await self.llm_service.analyze_user_input(user_input)
            
        except Exception as error:
            self.logger.error(f"分析用户请求失败: {error}")
            # 返回简单的错误任务拆解
            from .llm_service import TaskType, TaskStep
            return TaskDecomposition(
                task_type=TaskType.SIMPLE_QUERY,
                task_description=f"分析失败: {error}",
                steps=[TaskStep(
                    step_id=1,
                    step_name="错误处理",
                    step_description=f"处理错误: {error}",
                    tool_name=None,
                    tool_args=None
                )],
                requires_tools=False,
                tool_names=[]
            )
    
    async def close(self):
        """关闭聊天服务"""
        try:
            if self.llm_service:
                # LLM服务没有特定的关闭方法
                pass
            
            if self.tool_service:
                await self.tool_service.close()
            
            if self.mcp_client:
                await self.mcp_client.close()
            
            self._initialized = False
            self.logger.info("聊天服务已关闭")
            
        except Exception as error:
            self.logger.error(f"关闭聊天服务失败: {error}")
    
    def __del__(self):
        """析构函数"""
        if self._initialized:
            try:
                # 异步关闭服务
                asyncio.create_task(self.close())
            except:
                pass 