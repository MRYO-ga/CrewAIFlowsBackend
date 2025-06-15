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
        # 先加载配置文件中的服务器
        self._load_config()
        # 然后扫描目录补充发现其他服务器
        self._discover_servers()
    
    def _discover_servers(self):
        """自动发现MCP目录中的服务器（作为配置文件的补充）"""
        print(f"🔍 补充扫描MCP服务器目录: {self.mcp_directory}")
        
        if not self.mcp_directory.exists():
            print(f"❌ MCP目录不存在: {self.mcp_directory}")
            return
        
        discovered_count = 0
        
        # 扫描Python服务器
        for py_file in self.mcp_directory.glob("**/main.py"):  # 支持子目录
            if py_file.name.startswith("__"):
                continue
            
            # 排除虚拟环境和包目录
            path_parts = py_file.parts
            if any(part in ['.venv', 'venv', 'site-packages', 'node_modules', '__pycache__'] for part in path_parts):
                continue
            
            # 从路径获取服务器名称（使用父目录名）
            server_name = py_file.parent.name
            
            # 如果配置文件中已经有这个服务器，跳过
            if server_name in self.servers:
                continue
            
            server_info = self._analyze_python_server(py_file, server_name)
            if server_info:
                self.servers[server_info.name] = server_info
                print(f"✅ 发现新的Python MCP服务器: {server_info.name}")
                discovered_count += 1
        
        print(f"🎯 补充发现 {discovered_count} 个新MCP服务器")
    
    def _analyze_python_server(self, file_path: Path, server_name: str = None) -> Optional[MCPServerInfo]:
        """分析Python MCP服务器文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 简单的启发式分析
            if 'mcp.server' in content or 'FastMCP' in content or 'Server(' in content:
                name = server_name or file_path.stem
                description = self._extract_description(content)
                
                return MCPServerInfo(
                    name=name,
                    description=description,
                    script_path=str(file_path.absolute()),
                    script_type="python",
                    status=ServerStatus.AVAILABLE,
                    auto_connect=False,  # 新发现的服务器默认不自动连接
                    priority=99  # 新发现的服务器优先级较低
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
        """加载服务器配置 - 适配ReActMCP格式"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # 直接从根级别读取服务器配置，跳过settings
                for server_name, server_config in config.items():
                    if server_name == 'settings':  # 跳过设置项
                        continue
                    
                    # 如果是新格式的服务器配置
                    if isinstance(server_config, dict) and 'script' in server_config:
                        # 创建或更新服务器信息
                        server_info = MCPServerInfo(
                            name=server_name,
                            description=server_config.get('description', f"{server_name} MCP服务器"),
                            script_path=server_config.get('script', ''),
                            script_type="python",  # 默认为python
                            status=ServerStatus.AVAILABLE if server_config.get('active', True) else ServerStatus.DISABLED,
                            auto_connect=server_config.get('active', True),
                            priority=0 if server_name == 'xhs-mcp' else 1  # xhs-mcp优先级更高
                        )
                        
                        self.servers[server_name] = server_info
                        print(f"✅ 加载服务器配置: {server_name}")
                
                print(f"📋 从配置文件加载了 {len([k for k in config.keys() if k != 'settings'])} 个MCP服务器")
            except Exception as e:
                print(f"⚠️ 加载配置文件失败: {e}")
    
    def _save_config(self):
        """保存服务器配置 - 适配ReActMCP格式"""
        config = {}
        
        # 保存每个服务器的配置
        for name, server in self.servers.items():
            config[name] = {
                'script': server.script_path,
                'encoding_error_handler': 'ignore',
                'description': server.description,
                'required_env_vars': [],
                'active': server.status != ServerStatus.DISABLED
            }
        
        # 添加设置项
        config['settings'] = {
            'model': 'gpt-4o',
            'system_prompt_path': ''
        }
        
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False, default=str)
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