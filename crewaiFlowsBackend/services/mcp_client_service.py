"""
MCP客户端服务模块
负责处理与MCP服务器的连接和工具调用
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from enum import Enum
from pathlib import Path

from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

# 在Windows上修复事件循环策略
if sys.platform == "win32":
    # 在模块导入时就设置正确的事件循环策略
    try:
        import asyncio
        # 检查当前策略
        current_policy = asyncio.get_event_loop_policy()
        if not isinstance(current_policy, asyncio.WindowsProactorEventLoopPolicy):
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
            print("🔧 MCP客户端已设置Windows Proactor事件循环策略")
    except Exception as e:
        print(f"⚠️ 设置MCP事件循环策略失败: {e}")

class LogType(Enum):
    """日志类型枚举"""
    GET_TOOLS = "GET_Tools"
    GET_TOOLS_ERROR = "GET_Tools_Error"
    CONNECT_TO_SERVER = "Connect_To_Server"
    LLM_REQUEST = "LLM_Request"
    LLM_RESPONSE = "LLM_Response"
    LLM_ERROR = "LLM_Error"
    LLM_STREAM = "LLM_Stream"
    TOOL_CALL = "Tool_Call"
    TOOL_CALL_RESPONSE = "Tool_Call_Response"
    TOOL_CALL_ERROR = "Tool_Call_Error"


class MCPToolResult:
    """工具调用结果"""
    def __init__(self, content: Any, **kwargs):
        self.content = content
        for key, value in kwargs.items():
            setattr(self, key, value)


class MCPTool:
    """MCP工具定义"""
    def __init__(self, name: str, description: str, input_schema: Dict[str, Any]):
        self.name = name
        self.description = description
        self.input_schema = input_schema


class OpenAITool:
    """OpenAI工具格式"""
    def __init__(self, type: str, function: Dict[str, Any]):
        self.type = type
        self.function = function


class MCPClientService:
    """MCP客户端服务类"""
    
    def __init__(self, logs_dir: str = "logs"):
        self.client: Optional[ClientSession] = None
        self._connection_context = None
        self._session_context = None
        self.logs_dir = Path(logs_dir)
        self.log_index = 0
        self._connection_lock = asyncio.Lock()  # 添加连接锁
        self._last_connection_path = None  # 记录最后连接的路径
        self.setup_logging()
        
    def setup_logging(self):
        """设置日志目录"""
        self.logs_dir.mkdir(exist_ok=True)
        
        # 清空旧日志文件
        for log_file in self.logs_dir.glob("*.json"):
            try:
                log_file.unlink()
                print(f"已删除历史日志文件 {log_file.name}")
            except Exception as e:
                print(f"删除文件 {log_file} 失败: {e}")
    
    def add_logs(self, log_data: Any, log_type: LogType):
        """添加日志"""
        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
        
        # 创建安全的文件名
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
                print(f"尝试写入路径: {self.logs_dir}")
                print(f"文件名: {log_filename}")
        
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
    
    def _patch_schema_arrays(self, schema: Dict[str, Any], 
                           default_items: Dict[str, Any] = None) -> Dict[str, Any]:
        """修补Schema中缺少items的数组类型"""
        if default_items is None:
            default_items = {"type": "object"}
        
        import copy
        new_schema = copy.deepcopy(schema)
        
        def process_object(node: Dict[str, Any], path: List[str]):
            # 处理对象的所有属性
            if node.get('properties'):
                for key, prop in node['properties'].items():
                    if isinstance(prop.get('type'), list) and len(prop['type']) > 1:
                        # 兼容豆包，type 不能为数组
                        prop['type'] = prop['type'][0]
                    
                    if prop.get('type') == 'array' and 'items' not in prop:
                        # 发现缺少items的数组属性
                        prop['items'] = default_items
                        print(f"[SimplePatcher] 修补属性: {'.'.join(path + [key])}")
                    
                    # 递归处理子对象
                    if prop.get('type') == 'object':
                        process_object(prop, path + [key])
            
            # 处理数组的items
            if (node.get('items') and 
                node['items'].get('type') == 'array' and 
                'items' not in node['items']):
                node['items']['items'] = default_items
                print(f"[SimplePatcher] 修补嵌套数组: {'.'.join(path)}.items")
        
        # 从根对象开始处理
        if new_schema.get('type') == 'object':
            process_object(new_schema, [])
        
        return new_schema
    
    async def connect_to_server(self, server_script_path: str, server_args: List[str] = None):
        """连接到MCP服务器"""
        # 使用锁确保同时只有一个连接操作
        async with self._connection_lock:
            try:
                print(f"🔒 获取连接锁，开始连接到: {server_script_path}")
                
                # Windows兼容性处理
                if sys.platform == "win32":
                    # 确保使用正确的事件循环
                    try:
                        current_loop = asyncio.get_running_loop()
                        loop_type = type(current_loop).__name__
                        print(f"🔧 当前事件循环类型: {loop_type}")
                        
                        # 如果不是ProactorEventLoop，给出警告但继续尝试
                        if not isinstance(current_loop, asyncio.ProactorEventLoop):
                            print("⚠️ 检测到非Proactor事件循环，可能在子进程创建时遇到问题")
                            print("💡 如果连接失败，请重启应用")
                    except Exception as e:
                        print(f"⚠️ 检查事件循环时出现警告: {e}")
                    
                    # 设置Windows特定的环境变量
                    import os
                    os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
                
                # 如果已经连接到相同的服务器，直接返回成功
                if (self.client and self._last_connection_path == server_script_path and 
                    self.is_connected()):
                    print(f"✅ 已连接到相同服务器: {server_script_path}")
                    return True
                
                # 先关闭已有连接
                if self.client:
                    print("🔄 关闭现有连接")
                    await self._cleanup_connection()
                
                # 判断服务器脚本类型
                if server_script_path.endswith('.js'):
                    command = "node"
                elif server_script_path.endswith('.py'):
                    # 使用当前Python解释器的完整路径
                    command = sys.executable
                    print(f"🐍 使用Python解释器: {command}")
                else:
                    raise ValueError("服务器脚本必须是 .js 或 .py 文件")
                
                # 设置服务器参数
                args = [server_script_path]
                if server_args:
                    args.extend(server_args)
                
                server_params = StdioServerParameters(
                    command=command,
                    args=args,
                    env=None
                )
                
                # self.add_logs({
                #     "command": command,
                #     "args": args,
                #     "server_path": server_script_path
                # }, LogType.CONNECT_TO_SERVER)
                
                print(f"📡 连接到服务器: {command} {' '.join(args)}")
                
                # 连接到服务器并保持连接，添加超时和重试
                max_retries = 2
                for attempt in range(max_retries + 1):
                    try:
                        if attempt > 0:
                            print(f"🔄 第 {attempt + 1} 次尝试连接...")
                            await asyncio.sleep(1)  # 等待1秒后重试
                        
                        print("🔗 步骤1: 创建stdio客户端连接...")
                        self._connection_context = stdio_client(server_params)
                        
                        print("🔗 步骤2: 启动连接上下文...")
                        # 添加超时
                        read_stream, write_stream = await asyncio.wait_for(
                            self._connection_context.__aenter__(),
                            timeout=30.0  # 30秒超时
                        )
                        print(f"📝 读写流已建立: read={read_stream is not None}, write={write_stream is not None}")
                        
                        print("🔗 步骤3: 创建客户端会话...")
                        self._session_context = ClientSession(read_stream, write_stream)
                        
                        print("🔗 步骤4: 启动会话上下文...")
                        session = await asyncio.wait_for(
                            self._session_context.__aenter__(),
                            timeout=15.0  # 15秒超时
                        )
                        print(f"💼 会话已创建: {session is not None}")
                        
                        print("🔗 步骤5: 初始化会话...")
                        await asyncio.wait_for(
                            session.initialize(),
                            timeout=10.0  # 10秒超时
                        )
                        print("✅ 会话初始化完成")
                        
                        print("🔗 步骤6: 测试连接 - 获取工具列表...")
                        tools_result = await asyncio.wait_for(
                            session.list_tools(),
                            timeout=10.0  # 10秒超时
                        )
                        print(f"✅ 连接测试成功，获取到 {len(tools_result.tools)} 个工具")
                        
                        self.client = session
                        self._last_connection_path = server_script_path
                        print(f"✅ 成功连接到MCP服务器: {server_script_path}")
                        return True
                        
                    except asyncio.TimeoutError:
                        print(f"⏰ 连接超时 (尝试 {attempt + 1}/{max_retries + 1})")
                        await self._cleanup_connection()
                        if attempt == max_retries:
                            raise Exception("连接超时，已达到最大重试次数")
                    except (NotImplementedError, OSError) as subprocess_error:
                        print(f"💥 子进程创建失败 (尝试 {attempt + 1}/{max_retries + 1}): {subprocess_error}")
                        await self._cleanup_connection()
                        if attempt == max_retries:
                            raise Exception(f"Windows子进程创建失败: {subprocess_error}. 请确保已正确设置事件循环策略。")
                    except Exception as retry_error:
                        print(f"🚫 连接失败 (尝试 {attempt + 1}/{max_retries + 1}): {retry_error}")
                        await self._cleanup_connection()
                        if attempt == max_retries:
                            raise retry_error
                        
            except Exception as e:
                import traceback
                error_msg = f"连接MCP服务器失败: {str(e)}"
                error_details = traceback.format_exc()
                print(f"❌ 详细错误信息:")
                print(f"错误类型: {type(e).__name__}")
                print(f"错误消息: {str(e)}")
                print(f"完整堆栈:")
                print(error_details)
                
                # 安全地记录日志，避免引用未定义的变量
                log_data = {
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "traceback": error_details,
                    "server_path": server_script_path
                }
                # 只有在变量已定义时才添加
                try:
                    if 'command' in locals():
                        log_data["command"] = command
                    if 'args' in locals():
                        log_data["args"] = args
                except NameError:
                    pass  # 变量未定义，跳过
                
                # self.add_logs(log_data, LogType.GET_TOOLS_ERROR)
                
                # 清理失败的连接
                await self._cleanup_connection()
                return False
    
    async def _cleanup_connection(self):
        """清理连接"""
        try:
            if self._session_context:
                try:
                    # 使用更安全的清理方式，避免跨任务问题
                    if hasattr(self._session_context, '__aexit__'):
                        await self._session_context.__aexit__(None, None, None)
                except Exception as e:
                    print(f"清理session失败: {e}")
                finally:
                    self._session_context = None
        except Exception as e:
            print(f"清理session外层失败: {e}")
            self._session_context = None
        
        try:
            if self._connection_context:
                try:
                    # 使用更安全的清理方式，避免跨任务问题
                    if hasattr(self._connection_context, '__aexit__'):
                        await self._connection_context.__aexit__(None, None, None)
                except Exception as e:
                    print(f"清理connection失败: {e}")
                finally:
                    self._connection_context = None
        except Exception as e:
            print(f"清理connection外层失败: {e}")
            self._connection_context = None
        
        # 强制重置所有状态
        self.client = None
        self._session_context = None
        self._connection_context = None
        self._last_connection_path = None
    
    async def get_tools(self) -> List[OpenAITool]:
        """获取服务器提供的工具列表"""
        print("🔍 [MCP工具获取] 开始获取工具列表...")
        
        if not self.client:
            print("❌ [MCP工具获取] 客户端未连接")
            raise RuntimeError("未连接到MCP服务器")
        
        try:
            print("📞 [MCP工具获取] 正在调用 client.list_tools()...")
            # 从MCP服务器获取工具列表
            tools_result = await self.client.list_tools()
            print(f"✅ [MCP工具获取] 成功获取 {len(tools_result.tools)} 个原始工具:")
            
            # for i, tool in enumerate(tools_result.tools, 1):
            #     print(f"   {i}. {tool.name}: {tool.description}")
            #     print(f"      输入参数结构: {json.dumps(tool.inputSchema, ensure_ascii=False, indent=2)}")
            
            log_info = [
                {"name": tool.name, "description": tool.description}
                for tool in tools_result.tools
            ]
            # self.add_logs(log_info, LogType.GET_TOOLS)
            
            # 转换为OpenAI工具格式
            print("🔄 [MCP工具获取] 正在转换为OpenAI工具格式...")
            openai_tools = []
            for tool in tools_result.tools:
                # print(f"🔧 [MCP工具获取] 转换工具: {tool.name}")
                
                # 修补schema数组
                patched_schema = self._patch_schema_arrays(tool.inputSchema) if tool.inputSchema else {}
                # print(f"   修补后的schema: {json.dumps(patched_schema, ensure_ascii=False, indent=2)}")
                
                openai_tool = OpenAITool(
                    type="function",
                    function={
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": patched_schema
                    }
                )
                openai_tools.append(openai_tool)
                # print(f"   ✅ 转换完成")
            
            print(f"🎉 [MCP工具获取] 成功转换 {len(openai_tools)} 个工具为OpenAI格式")
            return openai_tools
            
        except Exception as error:
            error_msg = f"获取工具列表失败: {str(error)}"
            print(error_msg)
            # self.add_logs(error_msg, LogType.GET_TOOLS_ERROR)
            raise RuntimeError(error_msg)
    
    async def call_tool(self, tool_name: str, tool_args: Dict[str, Any]) -> MCPToolResult:
        """调用MCP工具"""
        print(f"🛠️ [MCP工具调用] 开始调用工具: {tool_name}")
        print(f"📝 [MCP工具调用] 工具参数: {json.dumps(tool_args, ensure_ascii=False, indent=2)}")
        
        if not self.client:
            print("❌ [MCP工具调用] 客户端未连接")
            raise RuntimeError("未连接到MCP服务器")
        
        try:
            print("📞 [MCP工具调用] 正在调用 client.call_tool()...")
            
            # self.add_logs({
            #     "name": tool_name,
            #     "arguments": tool_args
            # }, LogType.TOOL_CALL)
            
            # 执行工具调用
            result = await self.client.call_tool(tool_name, tool_args)
            # print(f"📦 [MCP工具调用] 原始调用结果类型: {type(result)}")
            # print(f"🔍 [MCP工具调用] 结果内容: {result}")
            
            # 检查结果的内容
            if hasattr(result, 'content'):
                print(f"📄 [MCP工具调用] 结果内容类型: {type(result.content)}")
                if hasattr(result.content, '__iter__') and not isinstance(result.content, str):
                    print(f"📋 [MCP工具调用] 内容列表长度: {len(result.content)}")
                    for i, item in enumerate(result.content):
                        print(f"   项目{i}: {type(item)} - {item}")
                else:
                    print(f"📄 [MCP工具调用] 内容详情: {result.content}")
            
            # self.add_logs(result.__dict__ if hasattr(result, '__dict__') else str(result), 
            #              LogType.TOOL_CALL_RESPONSE)
            
            mcp_result = MCPToolResult(content=result.content)
            print(f"✅ [MCP工具调用] 工具调用成功完成")
            return mcp_result
            
        except Exception as error:
            error_msg = f"调用工具 {tool_name} 失败: {str(error)}"
            print(f"❌ [MCP工具调用] {error_msg}")
            print(f"🔍 [MCP工具调用] 错误详情: {type(error).__name__}: {str(error)}")
            # self.add_logs(error_msg, LogType.TOOL_CALL_ERROR)
            raise RuntimeError(error_msg)
    
    def is_connected(self) -> bool:
        """检查是否已连接到MCP服务器"""
        try:
            is_connected = (self.client is not None and 
                          self._session_context is not None and 
                          self._connection_context is not None)
            print(f"MCP连接状态检查: client={self.client is not None}, session={self._session_context is not None}, connection={self._connection_context is not None}")
            return is_connected
        except Exception as e:
            print(f"检查连接状态时出错: {e}")
            return False
    
    async def close(self):
        """关闭连接"""
        async with self._connection_lock:
            await self._cleanup_connection()


# 创建全局实例
mcp_client_service = MCPClientService() 