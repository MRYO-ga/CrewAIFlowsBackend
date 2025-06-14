"""
工具服务模块 - Python版本
负责处理与MCP工具相关的逻辑，对应Node.js版本的ToolService
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from pathlib import Path

from .mcp_client_service import MCPClientService, OpenAITool, MCPToolResult, LogType

class ToolService:
    """
    工具服务类 - Python版本
    提供工具列表获取和工具调用功能
    """
    
    def __init__(self, mcp_client: MCPClientService):
        """
        构造函数
        
        Args:
            mcp_client: MCP客户端实例
        """
        self.mcp_client = mcp_client
        self.logger = logging.getLogger(__name__)
        
    async def get_tools(self) -> List[OpenAITool]:
        """
        获取服务器提供的工具列表
        
        Returns:
            转换后的OpenAI工具格式数组
        """
        print("🔧 [工具服务] 开始获取工具列表...")
        
        try:
            # 从MCP服务器获取工具列表
            print("📞 [工具服务] 调用MCP客户端获取工具...")
            tools = await self.mcp_client.get_tools()
            print(f"✅ [工具服务] MCP客户端返回 {len(tools)} 个工具")
            
            # 记录工具信息
            tool_info = [
                {"name": tool.function["name"], "description": tool.function["description"]}
                for tool in tools
            ]
            
            # print("📋 [工具服务] 工具详细信息:")
            # for i, info in enumerate(tool_info, 1):
            #     print(f"   {i}. {info['name']}: {info['description']}")
            
            # self.mcp_client.add_logs(tool_info, LogType.GET_TOOLS)
            
            print(f"🎉 [工具服务] 工具列表获取完成，共 {len(tools)} 个工具")
            return tools
            
        except Exception as error:
            print(f"❌ [工具服务] 获取工具列表失败: {error}")
            # self.mcp_client.add_logs(str(error), LogType.GET_TOOLS_ERROR)
            self.logger.error(f"获取工具列表失败: {error}")
            raise Exception(f"获取工具列表失败: {error}")
    
    async def call_tool(self, tool_name: str, tool_args: Dict[str, Any]) -> MCPToolResult:
        """
        调用MCP工具
        
        Args:
            tool_name: 工具名称
            tool_args: 工具参数
            
        Returns:
            工具调用结果
        """
        print(f"🔧 [工具服务] 开始调用工具: {tool_name}")
        print(f"📝 [工具服务] 工具参数: {json.dumps(tool_args, ensure_ascii=False, indent=2)}")
        
        try:
            # 记录工具调用
            call_info = {
                "name": tool_name,
                "arguments": tool_args,
                "timestamp": datetime.now().isoformat()
            }
            # self.mcp_client.add_logs(call_info, LogType.TOOL_CALL)
            self.logger.info(f"调用工具: {tool_name}")
            
            # 执行工具调用
            print("📞 [工具服务] 调用MCP客户端执行工具...")
            result = await self.mcp_client.call_tool(tool_name, tool_args)
            print(f"✅ [工具服务] MCP客户端调用成功，结果类型: {type(result)}")
            
            # 记录调用结果
            # self.mcp_client.add_logs(result.content, LogType.TOOL_CALL_RESPONSE)
            self.logger.info(f"工具 {tool_name} 调用成功")
            
            print(f"🎉 [工具服务] 工具 {tool_name} 调用完成")
            return result
            
        except Exception as error:
            print(f"❌ [工具服务] 调用工具 {tool_name} 失败: {error}")
            # self.mcp_client.add_logs(str(error), LogType.TOOL_CALL_ERROR)
            self.logger.error(f"调用工具 {tool_name} 失败: {error}")
            raise Exception(f"调用工具 {tool_name} 失败: {error}")
    
    async def get_tool_by_name(self, tool_name: str) -> Optional[OpenAITool]:
        """
        根据名称获取特定工具
        
        Args:
            tool_name: 工具名称
            
        Returns:
            工具对象或None
        """
        try:
            tools = await self.get_tools()
            for tool in tools:
                if tool.function["name"] == tool_name:
                    return tool
            return None
        except Exception as error:
            self.logger.error(f"获取工具 {tool_name} 失败: {error}")
            return None
    
    async def batch_call_tools(self, tool_calls: List[Dict[str, Any]]) -> List[MCPToolResult]:
        """
        批量调用工具
        
        Args:
            tool_calls: 工具调用列表，每个元素包含name和arguments
            
        Returns:
            工具调用结果列表
        """
        results = []
        
        for tool_call in tool_calls:
            try:
                tool_name = tool_call.get("name")
                tool_args = tool_call.get("arguments", {})
                
                if not tool_name:
                    continue
                    
                result = await self.call_tool(tool_name, tool_args)
                results.append(result)
                
            except Exception as error:
                self.logger.error(f"批量调用工具失败: {error}")
                # 创建错误结果
                error_result = MCPToolResult(
                    content=f"工具调用失败: {error}",
                    isError=True
                )
                results.append(error_result)
        
        return results
    
    def format_tool_result(self, result: MCPToolResult) -> Dict[str, Any]:
        """
        格式化工具调用结果
        
        Args:
            result: 工具调用结果
            
        Returns:
            格式化后的结果字典
        """
        print(f"🔧 [工具服务] 开始格式化工具结果, 类型: {type(result)}")
        
        try:
            print(f"📦 [工具服务] 原始结果内容类型: {type(result.content)}")
            print(f"🔍 [工具服务] 原始结果内容: {result.content}")
            
            # 安全地处理MCP返回的内容
            def safe_serialize(obj):
                """安全序列化对象，处理TextContent等特殊类型"""
                print(f"🔄 [工具服务] safe_serialize 处理对象类型: {type(obj)}")
                
                if hasattr(obj, '__dict__'):
                    # 如果是对象，转换为字典
                    if hasattr(obj, 'text'):
                        # 处理TextContent类型
                        print(f"📄 [工具服务] 检测到TextContent对象，提取text属性: {obj.text}")
                        return obj.text
                    elif hasattr(obj, 'content'):
                        # 递归处理content属性
                        print(f"📦 [工具服务] 对象有content属性，递归处理...")
                        return safe_serialize(obj.content)
                    else:
                        # 通用对象转字典
                        print(f"🔧 [工具服务] 通用对象转字典，属性: {list(obj.__dict__.keys())}")
                        return {k: safe_serialize(v) for k, v in obj.__dict__.items()}
                elif isinstance(obj, list):
                    # 处理列表
                    print(f"📋 [工具服务] 处理列表，长度: {len(obj)}")
                    return [safe_serialize(item) for item in obj]
                elif isinstance(obj, dict):
                    # 处理字典
                    print(f"📚 [工具服务] 处理字典，键: {list(obj.keys())}")
                    return {k: safe_serialize(v) for k, v in obj.items()}
                else:
                    # 基本类型直接返回
                    print(f"✨ [工具服务] 基本类型直接返回: {type(obj)}")
                    return obj
            
            # 安全处理result.content
            print("🔄 [工具服务] 开始安全序列化...")
            safe_content = safe_serialize(result.content)
            print(f"✅ [工具服务] 安全序列化完成，结果类型: {type(safe_content)}")
            print(f"📄 [工具服务] 序列化结果: {safe_content}")
            
            # 如果处理后的内容是字符串，尝试解析为JSON
            if isinstance(safe_content, str):
                print("📝 [工具服务] 内容是字符串，尝试JSON解析...")
                try:
                    parsed_content = json.loads(safe_content)
                    print(f"✅ [工具服务] JSON解析成功: {parsed_content}")
                    formatted_result = {
                        "success": True,
                        "data": parsed_content,
                        "raw_content": safe_content
                    }
                    print(f"🎉 [工具服务] 格式化完成 (JSON): {formatted_result}")
                    return formatted_result
                except json.JSONDecodeError as e:
                    print(f"⚠️ [工具服务] JSON解析失败: {e}, 返回原始字符串")
                    formatted_result = {
                        "success": True,
                        "data": safe_content,
                        "raw_content": safe_content
                    }
                    print(f"🎉 [工具服务] 格式化完成 (字符串): {formatted_result}")
                    return formatted_result
            else:
                print("📦 [工具服务] 内容不是字符串，直接使用序列化结果")
                formatted_result = {
                    "success": True,
                    "data": safe_content,
                    "raw_content": str(safe_content)
                }
                print(f"🎉 [工具服务] 格式化完成 (对象): {formatted_result}")
                return formatted_result
                
        except Exception as error:
            print(f"❌ [工具服务] 格式化工具结果失败: {error}")
            self.logger.error(f"格式化工具结果失败: {error}")
            error_result = {
                "success": False,
                "error": str(error),
                "raw_content": str(result.content) if result else None
            }
            print(f"🔧 [工具服务] 返回错误结果: {error_result}")
            return error_result
    
    async def get_tools_for_llm(self, filter_tools: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        获取适合LLM使用的工具列表格式
        
        Args:
            filter_tools: 可选的工具名称过滤列表
            
        Returns:
            适合LLM使用的工具描述列表
        """
        try:
            tools = await self.get_tools()
            
            llm_tools = []
            for tool in tools:
                tool_name = tool.function["name"]
                
                # 如果有过滤器，只包含指定的工具
                if filter_tools and tool_name not in filter_tools:
                    continue
                
                llm_tool = {
                    "name": tool_name,
                    "description": tool.function["description"],
                    "parameters": tool.function.get("parameters", {}),
                    "type": "function"
                }
                llm_tools.append(llm_tool)
            
            return llm_tools
            
        except Exception as error:
            self.logger.error(f"获取LLM工具列表失败: {error}")
            return []
    
    async def validate_tool_args(self, tool_name: str, tool_args: Dict[str, Any]) -> bool:
        """
        验证工具参数是否符合要求
        
        Args:
            tool_name: 工具名称
            tool_args: 工具参数
            
        Returns:
            验证结果
        """
        try:
            tool = await self.get_tool_by_name(tool_name)
            if not tool:
                return False
            
            # 获取参数模式
            parameters = tool.function.get("parameters", {})
            required = parameters.get("required", [])
            properties = parameters.get("properties", {})
            
            # 检查必需参数
            for param in required:
                if param not in tool_args:
                    self.logger.warning(f"工具 {tool_name} 缺少必需参数: {param}")
                    return False
            
            # 检查参数类型（简单验证）
            for param, value in tool_args.items():
                if param in properties:
                    expected_type = properties[param].get("type")
                    if expected_type == "string" and not isinstance(value, str):
                        self.logger.warning(f"工具 {tool_name} 参数 {param} 类型错误，期望字符串")
                        return False
                    elif expected_type == "number" and not isinstance(value, (int, float)):
                        self.logger.warning(f"工具 {tool_name} 参数 {param} 类型错误，期望数字")
                        return False
                    elif expected_type == "boolean" and not isinstance(value, bool):
                        self.logger.warning(f"工具 {tool_name} 参数 {param} 类型错误，期望布尔值")
                        return False
            
            return True
            
        except Exception as error:
            self.logger.error(f"验证工具参数失败: {error}")
            return False
    
    async def close(self):
        """关闭工具服务"""
        try:
            if self.mcp_client:
                await self.mcp_client.close()
            self.logger.info("工具服务已关闭")
        except Exception as error:
            self.logger.error(f"关闭工具服务失败: {error}") 