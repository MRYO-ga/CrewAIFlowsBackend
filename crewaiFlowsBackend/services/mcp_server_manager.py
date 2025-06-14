"""
MCP服务器管理器
负责自动发现、启动和管理本地MCP服务器
"""

import asyncio
import json
import os
import subprocess
import sys
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set

from pydantic import BaseModel
from services.mcp_client_service import mcp_client_service


class ServerStatus(Enum):
    """服务器状态枚举"""
    UNKNOWN = "unknown"
    AVAILABLE = "available"
    CONNECTED = "connected"
    ERROR = "error"
    DISABLED = "disabled"


class MCPServerInfo(BaseModel):
    """MCP服务器信息"""
    name: str
    description: str
    script_path: str
    script_type: str  # "python" or "javascript"
    status: ServerStatus = ServerStatus.UNKNOWN
    tools_count: int = 0
    last_connected: Optional[datetime] = None
    error_message: Optional[str] = None
    auto_connect: bool = True
    priority: int = 1  # 优先级，数字越小优先级越高


class MCPServerManager:
    """MCP服务器管理器"""
    
    def __init__(self):
        self.servers: Dict[str, MCPServerInfo] = {}
        self.current_server: Optional[str] = None
        self.mcp_directory = Path(__file__).parent.parent / "mcp"
        self.config_file = self.mcp_directory / "servers_config.json"
        self._discover_servers()
        self._load_config()
    
    def _discover_servers(self):
        """自动发现MCP目录中的服务器"""
        print(f"🔍 扫描MCP服务器目录: {self.mcp_directory}")
        
        if not self.mcp_directory.exists():
            print(f"❌ MCP目录不存在: {self.mcp_directory}")
            return
        
        # 扫描Python服务器
        for py_file in self.mcp_directory.glob("*.py"):
            if py_file.name.startswith("__"):
                continue
            
            server_info = self._analyze_python_server(py_file)
            if server_info:
                self.servers[server_info.name] = server_info
                print(f"✅ 发现Python MCP服务器: {server_info.name}")
        
        # 扫描JavaScript服务器
        for js_file in self.mcp_directory.glob("*.js"):
            server_info = self._analyze_javascript_server(js_file)
            if server_info:
                self.servers[server_info.name] = server_info
                print(f"✅ 发现JavaScript MCP服务器: {server_info.name}")
        
        print(f"🎯 总共发现 {len(self.servers)} 个MCP服务器")
    
    def _analyze_python_server(self, file_path: Path) -> Optional[MCPServerInfo]:
        """分析Python MCP服务器文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 简单的启发式分析
            if 'mcp.server' in content or 'FastMCP' in content or 'Server(' in content:
                name = file_path.stem
                description = self._extract_description(content)
                
                return MCPServerInfo(
                    name=name,
                    description=description,
                    script_path=str(file_path.absolute()),
                    script_type="python",
                    status=ServerStatus.AVAILABLE
                )
        except Exception as e:
            print(f"⚠️ 分析Python服务器失败 {file_path}: {e}")
        
        return None
    
    def _analyze_javascript_server(self, file_path: Path) -> Optional[MCPServerInfo]:
        """分析JavaScript MCP服务器文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 简单的启发式分析
            if '@modelcontextprotocol' in content or 'mcp' in content.lower():
                name = file_path.stem
                description = self._extract_description(content)
                
                return MCPServerInfo(
                    name=name,
                    description=description,
                    script_path=str(file_path.absolute()),
                    script_type="javascript",
                    status=ServerStatus.AVAILABLE
                )
        except Exception as e:
            print(f"⚠️ 分析JavaScript服务器失败 {file_path}: {e}")
        
        return None
    
    def _extract_description(self, content: str) -> str:
        """从文件内容中提取描述"""
        lines = content.split('\n')
        
        # 查找文档字符串或注释中的描述
        for i, line in enumerate(lines[:20]):  # 只检查前20行
            line = line.strip()
            if line.startswith('"""') or line.startswith("'''"):
                # Python文档字符串
                desc_lines = []
                for j in range(i + 1, min(i + 10, len(lines))):
                    desc_line = lines[j].strip()
                    if desc_line.endswith('"""') or desc_line.endswith("'''"):
                        break
                    if desc_line and not desc_line.startswith('#'):
                        desc_lines.append(desc_line)
                return ' '.join(desc_lines)[:200]
            elif line.startswith('/*') or line.startswith('//'):
                # JavaScript注释
                return line.replace('/*', '').replace('//', '').replace('*/', '').strip()[:200]
        
        # 默认描述
        return f"MCP服务器"
    
    def _load_config(self):
        """加载服务器配置"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                for server_name, server_config in config.get('servers', {}).items():
                    if server_name in self.servers:
                        # 更新服务器配置
                        server = self.servers[server_name]
                        server.auto_connect = server_config.get('auto_connect', True)
                        server.priority = server_config.get('priority', 1)
                        server.description = server_config.get('description', server.description)
                        server.tools_count = server_config.get('tools_count', 0)
                        server.error_message = server_config.get('error_message', None)
                        
                        # 加载上次连接时间
                        if server_config.get('last_connected'):
                            try:
                                from datetime import datetime
                                server.last_connected = datetime.fromisoformat(server_config['last_connected'])
                            except Exception:
                                server.last_connected = None
                        
                        # 加载状态 - 修复：将之前CONNECTED状态重置为AVAILABLE
                        if server_config.get('disabled', False):
                            server.status = ServerStatus.DISABLED
                        elif server_config.get('status'):
                            try:
                                config_status = ServerStatus(server_config['status'])
                                # 重要修复：应用重启时，之前CONNECTED的服务器应该是AVAILABLE状态
                                if config_status == ServerStatus.CONNECTED:
                                    server.status = ServerStatus.AVAILABLE
                                else:
                                    server.status = config_status
                            except ValueError:
                                server.status = ServerStatus.AVAILABLE
                        else:
                            server.status = ServerStatus.AVAILABLE
                
                print(f"📋 加载服务器配置: {self.config_file}")
            except Exception as e:
                print(f"⚠️ 加载配置文件失败: {e}")
    
    def _save_config(self):
        """保存服务器配置"""
        config = {
            'servers': {
                name: {
                    'auto_connect': server.auto_connect,
                    'priority': server.priority,
                    'description': server.description,
                    'disabled': server.status == ServerStatus.DISABLED,
                    'tools_count': server.tools_count,
                    'last_connected': server.last_connected.isoformat() if server.last_connected else None,
                    'status': server.status.value,
                    'error_message': server.error_message
                }
                for name, server in self.servers.items()
            }
        }
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            print(f"💾 保存服务器配置: {self.config_file}")
        except Exception as e:
            print(f"⚠️ 保存配置文件失败: {e}")
    
    async def auto_connect_best_server(self) -> bool:
        """自动连接到最佳的MCP服务器"""
        print("🔄 开始自动连接到最佳MCP服务器...")
        
        # 如果已经连接，跳过
        if mcp_client_service.is_connected():
            print("✅ 已经连接到MCP服务器，跳过自动连接")
            return True
        
        # 获取可用的服务器，按优先级排序
        available_servers = [
            server for server in self.servers.values()
            if server.status == ServerStatus.AVAILABLE and server.auto_connect
        ]
        
        if not available_servers:
            print("❌ 没有可用的MCP服务器")
            return False
        
        # 按优先级排序，SQLite服务器优先
        available_servers.sort(key=lambda s: (
            0 if 'sqlite' in s.name.lower() else s.priority,
            s.name
        ))
        
        print(f"🎯 发现 {len(available_servers)} 个可用服务器")
        
        # 尝试连接到最佳服务器
        for server in available_servers:
            print(f"🔗 尝试连接到服务器: {server.name}")
            
            try:
                success = await mcp_client_service.connect_to_server(server.script_path)
                
                if success:
                    server.status = ServerStatus.CONNECTED
                    server.last_connected = datetime.now()
                    server.error_message = None
                    self.current_server = server.name
                    
                    # 获取工具数量
                    try:
                        tools = await mcp_client_service.get_tools()
                        server.tools_count = len(tools)
                        print(f"✅ 成功连接到 {server.name}，发现 {server.tools_count} 个工具")
                    except Exception as e:
                        print(f"⚠️ 获取工具列表失败: {e}")
                        server.tools_count = 0
                    
                    self._save_config()
                    return True
                else:
                    server.status = ServerStatus.ERROR
                    server.error_message = "连接失败"
                    print(f"❌ 连接失败: {server.name}")
                    
            except Exception as e:
                server.status = ServerStatus.ERROR
                server.error_message = str(e)
                print(f"❌ 连接异常 {server.name}: {e}")
        
        print("❌ 所有服务器连接失败")
        return False
    
    async def connect_to_server(self, server_name: str) -> bool:
        """连接到指定的服务器"""
        if server_name not in self.servers:
            print(f"❌ 服务器不存在: {server_name}")
            return False
        
        server = self.servers[server_name]
        
        if server.status == ServerStatus.DISABLED:
            print(f"❌ 服务器已禁用: {server_name}")
            return False
        
        print(f"🔗 正在连接到服务器: {server_name}")
        
        try:
            # 先断开当前连接
            if mcp_client_service.is_connected():
                await mcp_client_service.close()
            
            success = await mcp_client_service.connect_to_server(server.script_path)
            
            if success:
                # 更新所有服务器状态
                for name, srv in self.servers.items():
                    if name == server_name:
                        srv.status = ServerStatus.CONNECTED
                        srv.last_connected = datetime.now()
                        srv.error_message = None
                    elif srv.status == ServerStatus.CONNECTED:
                        srv.status = ServerStatus.AVAILABLE
                
                self.current_server = server_name
                
                # 获取工具数量
                try:
                    tools = await mcp_client_service.get_tools()
                    server.tools_count = len(tools)
                    print(f"✅ 成功连接到 {server_name}，发现 {server.tools_count} 个工具")
                except Exception as e:
                    print(f"⚠️ 获取工具列表失败: {e}")
                    server.tools_count = 0
                
                self._save_config()
                return True
            else:
                server.status = ServerStatus.ERROR
                server.error_message = "连接失败"
                print(f"❌ 连接失败: {server_name}")
                return False
                
        except Exception as e:
            server.status = ServerStatus.ERROR
            server.error_message = str(e)
            print(f"❌ 连接异常 {server_name}: {e}")
            return False
    
    def get_servers_list(self) -> List[MCPServerInfo]:
        """获取服务器列表"""
        return list(self.servers.values())
    
    def get_current_server(self) -> Optional[MCPServerInfo]:
        """获取当前连接的服务器"""
        if self.current_server and self.current_server in self.servers:
            return self.servers[self.current_server]
        return None
    
    def enable_server(self, server_name: str) -> bool:
        """启用服务器"""
        if server_name in self.servers:
            server = self.servers[server_name]
            if server.status == ServerStatus.DISABLED:
                server.status = ServerStatus.AVAILABLE
                self._save_config()
                print(f"✅ 已启用服务器: {server_name}")
                return True
        return False
    
    def disable_server(self, server_name: str) -> bool:
        """禁用服务器"""
        if server_name in self.servers:
            server = self.servers[server_name]
            if server.status != ServerStatus.DISABLED:
                server.status = ServerStatus.DISABLED
                
                # 如果当前连接的就是这个服务器，断开连接
                if self.current_server == server_name:
                    asyncio.create_task(mcp_client_service.close())
                    self.current_server = None
                
                self._save_config()
                print(f"❌ 已禁用服务器: {server_name}")
                return True
        return False
    
    def set_server_priority(self, server_name: str, priority: int) -> bool:
        """设置服务器优先级"""
        if server_name in self.servers:
            self.servers[server_name].priority = priority
            self._save_config()
            print(f"📊 设置服务器 {server_name} 优先级为: {priority}")
            return True
        return False
    
    def refresh_servers(self):
        """重新扫描并刷新服务器列表"""
        print("🔄 重新扫描MCP服务器...")
        old_servers = set(self.servers.keys())
        
        # 重新发现服务器
        self.servers.clear()
        self._discover_servers()
        self._load_config()
        
        new_servers = set(self.servers.keys())
        
        # 报告变化
        added = new_servers - old_servers
        removed = old_servers - new_servers
        
        if added:
            print(f"➕ 新增服务器: {', '.join(added)}")
        
        if removed:
            print(f"➖ 移除服务器: {', '.join(removed)}")
        
        print(f"✅ 刷新完成，当前有 {len(self.servers)} 个服务器")


# 创建全局实例
mcp_server_manager = MCPServerManager() 