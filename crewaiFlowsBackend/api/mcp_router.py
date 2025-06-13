"""
MCP客户端API路由
提供MCP客户端连接、工具调用等功能的API接口
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import asyncio
import os

from services.mcp_client_service import mcp_client_service, MCPClientService
from services.mcp_server_manager import mcp_server_manager, MCPServerManager, MCPServerInfo, ServerStatus

router = APIRouter(prefix="/api/mcp", tags=["MCP客户端"])


class ConnectServerRequest(BaseModel):
    """连接服务器请求模型"""
    server_script_path: str
    server_args: Optional[List[str]] = None


class ToolCallRequest(BaseModel):
    """工具调用请求模型"""
    tool_name: str
    tool_args: Dict[str, Any] = {}


class ServerConnectionResponse(BaseModel):
    """服务器连接响应模型"""
    success: bool
    message: str


class ToolsResponse(BaseModel):
    """工具列表响应模型"""
    tools: List[Dict[str, Any]]
    total: int


class ToolCallResponse(BaseModel):
    """工具调用响应模型"""
    success: bool
    result: Any
    message: str


class ServersListResponse(BaseModel):
    """服务器列表响应模型"""
    servers: List[Dict[str, Any]]
    current_server: Optional[str]
    total: int


class AutoConnectRequest(BaseModel):
    """自动连接请求模型"""
    force_reconnect: bool = False


class ConnectServerByNameRequest(BaseModel):
    """按名称连接服务器请求模型"""
    server_name: str


def _get_fallback_tools():
    """获取后备工具列表（硬编码）"""
    return [
        {
            "type": "function",
            "function": {
                "name": "get_alerts",
                "description": "获取美国各州的天气警报",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "state": {
                            "type": "string",
                            "description": "美国州的两字母代码（例如 CA, NY）"
                        }
                    },
                    "required": ["state"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_forecast",
                "description": "获取某个位置的天气预报",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "latitude": {
                            "type": "number",
                            "description": "位置的纬度"
                        },
                        "longitude": {
                            "type": "number",
                            "description": "位置的经度"
                        }
                    },
                    "required": ["latitude", "longitude"]
                }
            }
        }
    ]


def get_mcp_service() -> MCPClientService:
    """获取MCP客户端服务实例"""
    # 使用全局单例实例，保持连接状态
    return mcp_client_service


@router.post("/connect", response_model=ServerConnectionResponse)
async def connect_to_server(
    request: ConnectServerRequest,
    mcp_service: MCPClientService = Depends(get_mcp_service)
):
    """
    连接到MCP服务器
    
    Args:
        request: 连接请求参数，包含服务器脚本路径和参数
        
    Returns:
        ServerConnectionResponse: 连接结果
    """
    try:
        # 检查服务器脚本文件是否存在
        if not os.path.exists(request.server_script_path):
            # 如果是相对路径或默认路径，尝试从mcp目录查找
            if not os.path.isabs(request.server_script_path):
                default_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "mcp", request.server_script_path)
                if os.path.exists(default_path):
                    request.server_script_path = default_path
                else:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"服务器脚本文件不存在: {request.server_script_path}"
                    )
            else:
                raise HTTPException(
                    status_code=400, 
                    detail=f"服务器脚本文件不存在: {request.server_script_path}"
                )
        
        # 连接到服务器
        success = await mcp_service.connect_to_server(
            request.server_script_path,
            request.server_args
        )
        
        if success:
            return ServerConnectionResponse(
                success=True,
                message=f"成功连接到MCP服务器: {request.server_script_path}"
            )
        else:
            return ServerConnectionResponse(
                success=False,
                message="连接MCP服务器失败"
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"连接服务器时发生错误: {str(e)}")


@router.get("/tools", response_model=ToolsResponse)
async def get_available_tools(
    mcp_service: MCPClientService = Depends(get_mcp_service)
):
    """
    获取可用的工具列表
    
    Returns:
        ToolsResponse: 工具列表
    """
    try:
        print(f"检查MCP连接状态: {mcp_service.is_connected()}")
        
        # 如果没有连接，尝试自动连接到最佳服务器
        if not mcp_service.is_connected():
            print("🔄 尝试自动连接到最佳MCP服务器...")
            try:
                success = await mcp_server_manager.auto_connect_best_server()
                if not success:
                    # 连接失败，使用硬编码的工具列表作为后备方案
                    print("⚠️ 自动连接失败，使用硬编码工具列表作为后备方案")
                    return ToolsResponse(
                        tools=_get_fallback_tools(),
                        total=len(_get_fallback_tools())
                    )
            except Exception as connect_error:
                import traceback
                error_details = traceback.format_exc()
                print(f"❌ 自动连接过程中出现异常:")
                print(f"异常类型: {type(connect_error).__name__}")
                print(f"异常消息: {str(connect_error)}")
                print(f"完整堆栈:")
                print(error_details)
                
                # 连接异常，使用硬编码的工具列表作为后备方案
                print("⚠️ 自动连接异常，使用硬编码工具列表作为后备方案")
                return ToolsResponse(
                    tools=_get_fallback_tools(),
                    total=len(_get_fallback_tools())
                )
            else:
                print("⚠️ 天气服务器文件不存在，使用硬编码工具列表作为后备方案")
                return ToolsResponse(
                    tools=_get_fallback_tools(),
                    total=len(_get_fallback_tools())
                )
        
        print("尝试获取工具列表...")
        tools = await mcp_service.get_tools()
        print(f"获取到工具数量: {len(tools)}")
        
        # 转换为字典格式
        tools_data = []
        for tool in tools:
            tools_data.append({
                "type": tool.type,
                "function": tool.function
            })
        
        print(f"成功转换工具数据: {len(tools_data)}")
        return ToolsResponse(
            tools=tools_data,
            total=len(tools_data)
        )
        
    except RuntimeError as e:
        print(f"运行时错误: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"未知错误: {str(e)}")
        import traceback
        print(f"错误堆栈: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"获取工具列表时发生错误: {str(e)}")


@router.post("/tools/call", response_model=ToolCallResponse)
async def call_tool(
    request: ToolCallRequest,
    mcp_service: MCPClientService = Depends(get_mcp_service)
):
    """
    调用MCP工具
    
    Args:
        request: 工具调用请求，包含工具名称和参数
        
    Returns:
        ToolCallResponse: 工具调用结果
    """
    try:
        result = await mcp_service.call_tool(
            request.tool_name,
            request.tool_args
        )
        
        return ToolCallResponse(
            success=True,
            result=result.content,
            message=f"成功调用工具 {request.tool_name}"
        )
        
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"调用工具时发生错误: {str(e)}")


@router.post("/disconnect")
async def disconnect_from_server(
    mcp_service: MCPClientService = Depends(get_mcp_service)
):
    """
    断开与MCP服务器的连接
    
    Returns:
        dict: 断开连接结果
    """
    try:
        await mcp_service.close()
        return {
            "success": True,
            "message": "已断开与MCP服务器的连接"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"断开连接时发生错误: {str(e)}")


@router.get("/status")
async def get_connection_status(
    mcp_service: MCPClientService = Depends(get_mcp_service)
):
    """
    获取MCP客户端连接状态
    
    Returns:
        dict: 连接状态信息
    """
    is_connected = mcp_service.is_connected()
    current_server = mcp_server_manager.get_current_server()
    tools_count = 0
    
    # 如果已连接，尝试获取工具数量
    if is_connected:
        try:
            tools = await mcp_service.get_tools()
            tools_count = len(tools)
        except Exception as e:
            print(f"获取工具数量失败: {e}")
    
    return {
        "connected": is_connected,
        "current_server": current_server.name if current_server else None,
        "tools_count": tools_count,
        "logs_dir": str(mcp_service.logs_dir),
        "log_count": mcp_service.log_index,
        "message": f"已连接到MCP服务器: {current_server.name}" if is_connected and current_server else "未连接到MCP服务器"
    }


@router.get("/servers", response_model=ServersListResponse)
async def get_servers_list():
    """
    获取所有可用的MCP服务器列表
    
    Returns:
        ServersListResponse: 服务器列表
    """
    try:
        servers = mcp_server_manager.get_servers_list()
        current_server = mcp_server_manager.get_current_server()
        
        servers_data = []
        for server in servers:
            server_dict = {
                "name": server.name,
                "description": server.description,
                "script_type": server.script_type,
                "status": server.status.value,
                "tools_count": server.tools_count,
                "last_connected": server.last_connected.isoformat() if server.last_connected else None,
                "error_message": server.error_message,
                "auto_connect": server.auto_connect,
                "priority": server.priority,
                "enabled": server.status != ServerStatus.DISABLED,
                "path": server.script_path,
                "error": server.error_message
            }
            servers_data.append(server_dict)
        
        return ServersListResponse(
            servers=servers_data,
            current_server=current_server.name if current_server else None,
            total=len(servers_data)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取服务器列表失败: {str(e)}")


@router.post("/auto-connect", response_model=ServerConnectionResponse)
async def auto_connect_best_server(request: AutoConnectRequest):
    """
    自动连接到最佳的MCP服务器
    
    Args:
        request: 自动连接请求参数
        
    Returns:
        ServerConnectionResponse: 连接结果
    """
    try:
        # 如果强制重连，先断开当前连接
        if request.force_reconnect and mcp_client_service.is_connected():
            await mcp_client_service.close()
        
        success = await mcp_server_manager.auto_connect_best_server()
        
        if success:
            current_server = mcp_server_manager.get_current_server()
            return ServerConnectionResponse(
                success=True,
                message=f"成功自动连接到服务器: {current_server.name if current_server else '未知'}"
            )
        else:
            return ServerConnectionResponse(
                success=False,
                message="自动连接失败，没有可用的服务器"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"自动连接失败: {str(e)}")


@router.post("/connect-by-name", response_model=ServerConnectionResponse)
async def connect_server_by_name(request: ConnectServerByNameRequest):
    """
    按名称连接到指定的MCP服务器
    
    Args:
        request: 连接请求参数
        
    Returns:
        ServerConnectionResponse: 连接结果
    """
    try:
        success = await mcp_server_manager.connect_to_server(request.server_name)
        
        if success:
            return ServerConnectionResponse(
                success=True,
                message=f"成功连接到服务器: {request.server_name}"
            )
        else:
            return ServerConnectionResponse(
                success=False,
                message=f"连接服务器失败: {request.server_name}"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"连接服务器失败: {str(e)}")


@router.post("/servers/{server_name}/enable")
async def enable_server(server_name: str):
    """
    启用指定的MCP服务器
    
    Args:
        server_name: 服务器名称
        
    Returns:
        dict: 操作结果
    """
    try:
        success = mcp_server_manager.enable_server(server_name)
        return {
            "success": success,
            "message": f"服务器 {server_name} 已{'启用' if success else '启用失败'}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启用服务器失败: {str(e)}")


@router.post("/servers/{server_name}/disable")
async def disable_server(server_name: str):
    """
    禁用指定的MCP服务器
    
    Args:
        server_name: 服务器名称
        
    Returns:
        dict: 操作结果
    """
    try:
        success = mcp_server_manager.disable_server(server_name)
        return {
            "success": success,
            "message": f"服务器 {server_name} 已{'禁用' if success else '禁用失败'}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"禁用服务器失败: {str(e)}")


@router.post("/refresh-servers")
async def refresh_servers():
    """
    重新扫描并刷新MCP服务器列表
    
    Returns:
        dict: 操作结果
    """
    try:
        mcp_server_manager.refresh_servers()
        servers = mcp_server_manager.get_servers_list()
        return {
            "success": True,
            "message": f"刷新成功，发现 {len(servers)} 个服务器",
            "servers_count": len(servers)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"刷新服务器列表失败: {str(e)}")