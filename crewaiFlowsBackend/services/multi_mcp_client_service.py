"""
多服务器MCP客户端服务模块
使用MultiServerMCPClient同时连接多个MCP服务器
"""

import asyncio
import json
import logging
import sys
import os
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from pathlib import Path

from langchain_mcp_adapters.client import MultiServerMCPClient
from services.mcp_client_service import MCPTool, OpenAITool, MCPToolResult, LogType

# Windows兼容性处理
if sys.platform == "win32":
    try:
        import asyncio
        current_policy = asyncio.get_event_loop_policy()
        if not isinstance(current_policy, asyncio.WindowsProactorEventLoopPolicy):
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
            print("🔧 多服务器MCP客户端已设置Windows Proactor事件循环策略")
    except Exception as e:
        print(f"⚠️ 设置多服务器MCP事件循环策略失败: {e}")


class MultiMCPClientService:
    """多服务器MCP客户端服务类"""
    
    def __init__(self, logs_dir: str = "logs"):
        self.client: Optional[MultiServerMCPClient] = None
        self.connected_servers: Dict[str, bool] = {}
        self.logs_dir = Path(logs_dir)
        self.log_index = 0
        self._connection_lock = asyncio.Lock()
        self.config_file = Path(__file__).parent.parent / "mcp" / "servers_config.json"
        self.setup_logging()
        
    def setup_logging(self):
        """设置日志目录"""
        self.logs_dir.mkdir(exist_ok=True)
        
    def add_logs(self, log_data: Any, log_type: LogType):
        """添加日志"""
        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
        
        log_filename = f"{self.log_index}_{log_type.value}_{timestamp}.json"
        log_filename = self._sanitize_filename(log_filename)
        
        print(f"{self.log_index} {log_type.value} {now.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if log_data:
            try:
                log_file_path = self.logs_dir / log_filename
                with open(log_file_path, 'w', encoding='utf-8') as f:
                    json.dump(log_data, f, ensure_ascii=False, indent=2, default=str)
            except Exception as error:
                print(f"写入日志文件失败: {error}")
        
        self.log_index += 1
    
    def _sanitize_filename(self, filename: str) -> str:
        """清理文件名中的特殊字符"""
        return (filename
                .replace('[', '').replace(']', '')
                .replace('<', '_').replace('>', '_')
                .replace(':', '_').replace('"', '_')
                .replace('/', '_').replace('\\', '_')
                .replace('|', '_').replace('?', '_')
                .replace('*', '_')
                .replace(' ', '_')
                .replace('__', '_'))
    
    def load_mcp_config(self) -> Dict[str, Any]:
        """加载MCP配置文件"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Error: Configuration file '{self.config_file}' not found.")
            return {}
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in configuration file '{self.config_file}'.")
            return {}
    
    async def connect_to_all_servers(self) -> bool:
        """连接到所有活跃的MCP服务器"""
        async with self._connection_lock:
            try:
                print("🔒 获取连接锁，开始连接到所有MCP服务器")
                
                # 1. 加载配置
                mcp_config = self.load_mcp_config()
                if not mcp_config:
                    print("❌ 无法加载MCP配置")
                    return False
                
                # 2. 创建多服务器客户端
                self.client = MultiServerMCPClient()
                
                # 3. 遍历配置，连接每个活跃的服务器
                connected_count = 0
                for server_name, server_config in mcp_config.items():
                    if server_name == "settings":
                        continue
                    
                    if not server_config.get("active", False):
                        print(f"⏭️ 跳过未激活的服务器: {server_name}")
                        continue
                    
                    try:
                        script_path = server_config.get("script", "")
                        if not script_path or not os.path.exists(script_path):
                            print(f"❌ 服务器脚本不存在: {server_name} -> {script_path}")
                            self.connected_servers[server_name] = False
                            continue
                        
                        print(f"🔗 连接到服务器: {server_name}")
                        
                        # 4. 启动子进程运行MCP服务器
                        await self.client.connect_to_server(
                            server_name,
                            transport="stdio",
                            command=sys.executable,  # Python解释器路径
                            args=[script_path],      # MCP服务器脚本路径
                            encoding_error_handler=server_config.get("encoding_error_handler", "ignore")
                        )
                        
                        self.connected_servers[server_name] = True
                        connected_count += 1
                        print(f"✅ 成功连接到服务器: {server_name}")
                        
                    except Exception as e:
                        print(f"❌ 连接服务器失败 {server_name}: {str(e)}")
                        self.connected_servers[server_name] = False
                
                if connected_count > 0:
                    print(f"🎉 成功连接到 {connected_count} 个MCP服务器")
                    self.add_logs({
                        "connected_servers": list(self.connected_servers.keys()),
                        "connected_count": connected_count
                    }, LogType.CONNECT_TO_SERVER)
                    return True
                else:
                    print("❌ 没有成功连接到任何MCP服务器")
                    return False
                    
            except Exception as e:
                print(f"❌ 连接所有服务器失败: {str(e)}")
                self.add_logs({
                    "error": str(e),
                    "error_type": type(e).__name__
                }, LogType.GET_TOOLS_ERROR)
                return False
    
    async def get_tools(self) -> List[OpenAITool]:
        """获取所有连接服务器的工具列表"""
        if not self.client:
            print("❌ 客户端未连接")
            return []
        
        try:
            print("🔍 获取所有可用工具...")
            
            # 5. 获取所有可用工具
            tools = self.client.get_tools()
            
            # 转换为OpenAI工具格式
            openai_tools = []
            for tool in tools:
                # 确保input_schema是可序列化的字典
                input_schema = tool.input_schema
                
                # 检查是否是Pydantic模型实例
                if hasattr(input_schema, 'model_dump') and callable(getattr(input_schema, 'model_dump')):
                    try:
                        input_schema = input_schema.model_dump()
                    except Exception as e:
                        print(f"⚠️ model_dump失败: {e}")
                        input_schema = {}
                elif hasattr(input_schema, 'dict') and callable(getattr(input_schema, 'dict')):
                    try:
                        input_schema = input_schema.dict()
                    except Exception as e:
                        print(f"⚠️ dict失败: {e}")
                        input_schema = {}
                elif not isinstance(input_schema, dict):
                    # 如果不是字典，尝试转换为字典
                    try:
                        input_schema = dict(input_schema) if input_schema else {}
                    except Exception:
                        input_schema = {}
                
                openai_tool = OpenAITool(
                    type="function",
                    function={
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": input_schema
                    }
                )
                openai_tools.append(openai_tool)
            
            print(f"✅ 成功获取 {len(openai_tools)} 个工具")
            self.add_logs({
                "tools_count": len(openai_tools),
                "tools": [{"name": tool.function["name"], "description": tool.function["description"]} for tool in openai_tools]
            }, LogType.GET_TOOLS)
            
            return openai_tools
            
        except Exception as e:
            print(f"❌ 获取工具列表失败: {str(e)}")
            import traceback
            print(f"详细错误: {traceback.format_exc()}")
            self.add_logs({
                "error": str(e),
                "error_type": type(e).__name__,
                "traceback": traceback.format_exc()
            }, LogType.GET_TOOLS_ERROR)
            return []
    
    async def call_tool(self, tool_name: str, tool_args: Dict[str, Any]) -> MCPToolResult:
        """调用指定的工具"""
        if not self.client:
            raise Exception("客户端未连接")
        
        try:
            print(f"🔧 调用工具: {tool_name}")
            print(f"📝 参数: {tool_args}")
            
            # 获取所有工具
            tools = self.client.get_tools()
            
            # 查找指定的工具
            target_tool = None
            for tool in tools:
                if tool.name == tool_name:
                    target_tool = tool
                    break
            
            if not target_tool:
                raise Exception(f"工具 {tool_name} 未找到")
            
            # 使用工具的ainvoke方法调用
            result = await target_tool.ainvoke(tool_args)
            
            print(f"✅ 工具调用成功: {tool_name}")
            self.add_logs({
                "tool_name": tool_name,
                "tool_args": tool_args,
                "result": result
            }, LogType.TOOL_CALL_RESPONSE)
            
            return MCPToolResult(content=result)
            
        except Exception as e:
            print(f"❌ 工具调用失败 {tool_name}: {str(e)}")
            self.add_logs({
                "tool_name": tool_name,
                "tool_args": tool_args,
                "error": str(e),
                "error_type": type(e).__name__
            }, LogType.TOOL_CALL_ERROR)
            raise e
    
    def is_connected(self) -> bool:
        """检查是否已连接到任何服务器"""
        return self.client is not None and any(self.connected_servers.values())
    
    def get_connected_servers(self) -> List[str]:
        """获取已连接的服务器列表"""
        return [name for name, connected in self.connected_servers.items() if connected]
    
    async def close(self):
        """关闭所有连接"""
        if self.client:
            try:
                await self.client.close()
                print("✅ 已关闭所有MCP服务器连接")
            except Exception as e:
                print(f"⚠️ 关闭连接时出现错误: {e}")
            finally:
                self.client = None
                self.connected_servers.clear()


# 创建全局实例
multi_mcp_client_service = MultiMCPClientService() 