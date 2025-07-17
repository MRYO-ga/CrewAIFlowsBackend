"""
简化的LLM服务模块
让LLM直接决定是否使用MCP工具，支持流式输出
"""

import asyncio
import json
import logging
import re
from typing import Dict, List, Any, Optional, AsyncGenerator
from datetime import datetime
import sys
import os
from pathlib import Path

# 添加utils路径到sys.path
utils_path = Path(__file__).parent.parent / "utils"
if str(utils_path) not in sys.path:
    sys.path.append(str(utils_path))

from myLLM import chat_with_llm
from persona_prompts import get_persona_prompt
from pydantic import BaseModel

from .tool_service import ToolService
from .mcp_client_service import MCPClientService, LogType
from utils.persona_prompts import persona_manager

class ChatMessage(BaseModel):
    """聊天消息模型"""
    role: str
    content: str

class StreamChunk(BaseModel):
    """流式输出数据块"""
    type: str  # message, tool_call, tool_result, complete, error
    content: str = ""
    data: Optional[Dict[str, Any]] = None
    timestamp: str = ""

class LLMService:
    """简化的LLM服务类"""
    
    def __init__(self, tool_service: ToolService, api_key: str = None, model: str = "gpt-4o-mini", llm_type: str = "openai"):
        """
        初始化LLM服务
        
        Args:
            tool_service: 工具服务实例
            api_key: API密钥
            model: 模型名称
            llm_type: LLM类型
        """
        self.tool_service = tool_service
        self.api_key = api_key
        self.model = model
        self.llm_type = llm_type
        self.logger = logging.getLogger(__name__)
        
        # 基础系统提示词，工具信息将在运行时动态添加
        self.base_system_prompt = """
作为专家，你可以：
- 查询和分析数据库中的数据
- 执行数据库的增删改查操作
- 提供数据结构和架构信息
- 协助数据分析和洞察生成
- 处理用户的开发需求和技术问题

**工具调用关键规则（必须严格遵循）：**
1. 当需要数据库操作时，立即调用相应工具，不要承诺稍后调用
2. 工具调用必须严格按照JSON格式：{"tool_call": {"name": "工具名", "args": {...}}}
3. 工具调用必须放在```json代码块中
4. 验证参数格式后再发送调用，不确定时询问澄清而非猜测
5. 每次只调用一个工具
6. 如果任务需要多个步骤，持续使用工具直到完成，不要在第一次失败时停止

**工具使用边界：**
使用工具的情况：
- 用户询问数据库表结构、数据内容
- 用户要求查询、插入、更新、删除数据
- 用户需要数据分析或统计信息
- 用户要求执行任何SQL操作
- 用户询问具体的数据库架构信息

不使用工具的情况：
- 用户询问一般性的编程概念或理论问题
- 用户要求代码示例（非数据库操作）
- 用户寻求技术建议或最佳实践
- 用户进行简单的问候或闲聊

**数据库操作执行顺序：**
1. 查看表结构前，先列出所有表
2. 插入数据前，确认表结构和字段要求
3. 复杂查询前，了解相关表的关系
4. 修改数据前，先查询确认现有数据

**重要格式规范：**
- sqlite_insert_data工具的data参数必须是JSON字符串格式，如："{\"name\": \"张三\", \"age\": 25}"
- UPDATE/DELETE操作使用sqlite_query工具
- 所有SELECT查询使用sqlite_query工具
- 表结构查询使用sqlite_describe_table工具

**工具调用示例：**
```json
{
  "tool_call": {
    "name": "sqlite_list_tables",
    "args": {}
  }
}
```

```json
{
  "tool_call": {
    "name": "sqlite_insert_data",
    "args": {
      "table_name": "accounts",
      "data": "{\"name\": \"新用户\", \"status\": \"active\"}"
    }
  }
}
```

**禁止行为：**
- 不要说"我将为您调用工具"或"稍后我会查询数据库"，需要工具时立即调用
- 不要猜测参数值，不确定时请要求用户澄清
- 不要在单次响应中承诺多个工具调用，按需逐个执行
- 不要使用除了指定JSON格式外的任何工具调用格式"""
        
    async def process_message_stream(self, user_input: str, 
                                   conversation_history: Optional[List[Dict[str, Any]]] = None, 
                                   model: str = None,
                                   attached_data: Optional[List[Dict[str, Any]]] = None) -> AsyncGenerator[StreamChunk, None]:
        """
        流式处理用户消息，支持工具调用和动态agent切换
        
        Args:
            user_input: 用户输入
            conversation_history: 对话历史
            model: 使用的模型（如果为None则使用默认模型）
            attached_data: 附加数据，包含persona_context等信息
            
        Yields:
            StreamChunk: 流式输出数据块
        """
        try:
            # 获取可用工具并构建完整的系统提示词
            available_tools = await self.tool_service.get_tools_for_llm()
            tools_text = self._format_tools_for_llm(available_tools)
            
            # 检查是否有persona_context，用于动态切换agent
            agent_prompt = self.base_system_prompt
            enhanced_user_input = user_input
            
            if attached_data:
                # 处理agent切换 - 优先查找包含agent字段的persona_context
                for data_item in attached_data:
                    if (data_item.get("type") == "persona_context" and 
                        data_item.get("data") and 
                        data_item.get("data", {}).get("agent")):
                        persona_data = data_item["data"]
                        # 使用persona_manager获取对应的agent提示词
                        agent_prompt = persona_manager.get_persona_by_context(persona_data)
                        print(f"🤖 检测到agent切换: {persona_data.get('agent', '未知')}")
                        break
                
                # 处理附加的数据内容，将其添加到用户输入中
                context_data_list = []
                for data_item in attached_data:
                    data_type = data_item.get("type", "")
                    data_content = data_item.get("data", {})
                    data_name = data_item.get("name", "")
                    
                    # 跳过用于agent选择的persona_context数据
                    if (data_type == "persona_context" and 
                        data_content.get("agent") is not None):
                        continue
                    
                    # 处理persona_context数据
                    if data_type == "persona_context" and data_content:
                        context_data_list.append({
                            "type": "账号人设信息",
                            "name": data_name,
                            "content": data_content
                        })
                        print(f"📋 处理引用数据: 类型=persona_context, 名称={data_name}")
                    
                    # 处理product_context数据  
                    elif data_type == "product_context" and data_content:
                        context_data_list.append({
                            "type": "产品信息",
                            "name": data_name,
                            "content": data_content
                        })
                        print(f"📋 处理引用数据: 类型=product_context, 名称={data_name}")
                    
                    # 处理其他类型的数据
                    elif data_type in ["xiaohongshu_note", "xiaohongshu_search"] and data_content:
                        context_data_list.append({
                            "type": "小红书数据",
                            "name": data_name,
                            "content": data_content
                        })
                        print(f"📋 处理引用数据: 类型={data_type}, 名称={data_name}")
                
                # 如果有数据内容，添加到用户输入中
                if context_data_list:
                    context_text = "\n\n📎 以下是我提供的相关数据：\n"
                    for i, context_item in enumerate(context_data_list, 1):
                        context_text += f"\n{i}. 【{context_item['type']}】{context_item['name']}\n"
                        context_text += f"   数据内容：{str(context_item['content'])}\n"
                    
                    enhanced_user_input = user_input + context_text
                    print(f"✅ 增强输入长度: {len(enhanced_user_input)}")
                    print(f"📎 发现附加数据: {len(context_data_list)} 项")
                    for i, item in enumerate(context_data_list, 1):
                        print(f"   {i}. 【{item['type']}】{item['name']}")
            
            system_prompt = f"""
                            {agent_prompt}
                            {self.base_system_prompt}
                            {tools_text}
                            """

            # 构建对话历史
            messages = [{"role": "system", "content": system_prompt}]
            print(f"🔍 构建的系统提示词: {system_prompt[:]}...")
            
            # 添加历史对话
            if conversation_history:
                for msg in conversation_history[-5:]:  # 只保留最近5轮对话
                    if msg.get("role") in ["user", "assistant"]:
                        messages.append({
                            "role": msg["role"],
                            "content": msg["content"]
                        })
            
            # 添加当前用户输入（使用增强后的输入）
            messages.append({"role": "user", "content": enhanced_user_input})
            
            # 发送开始处理消息
            yield StreamChunk(
                type="start",
                content="开始处理您的问题...",
                timestamp=datetime.now().isoformat()
            )
            
            # 开始LLM对话循环
            max_iterations = 5  # 最大工具调用迭代次数
            iteration = 0
            
            while iteration < max_iterations:
                iteration += 1
                
                # 调用LLM
                yield StreamChunk(
                    type="llm_thinking",
                    content=f"LLM正在思考... (第{iteration}轮)",
                    timestamp=datetime.now().isoformat()
                )
                
                # 使用指定的模型（如果提供了的话）
                current_model = model if model else self.model
                llm_response = await self._call_llm(messages, current_model)
                
                # 检查是否包含工具调用
                tool_call = self._extract_tool_call(llm_response)
                
                if tool_call:
                    # 提取工具调用前的文本内容
                    tool_call_text = ""
                    json_pattern = r'```json.*?```'
                    text_before_tool = re.split(json_pattern, llm_response, flags=re.DOTALL | re.IGNORECASE)
                    
                    if text_before_tool and text_before_tool[0].strip():
                        # 有工具调用前的说明文字，先显示这部分
                        explanation_text = text_before_tool[0].strip()
                        yield StreamChunk(
                            type="ai_message",
                            content=explanation_text,
                            timestamp=datetime.now().isoformat()
                        )
                    
                    # 显示工具调用信息
                    yield StreamChunk(
                        type="tool_call",
                        content=f"调用工具: {tool_call['name']}",
                        data=tool_call,
                        timestamp=datetime.now().isoformat()
                    )
                    
                    # 执行工具调用
                    try:
                        # 修复特定工具的参数格式
                        fixed_args = self._fix_tool_args(tool_call["name"], tool_call["args"])
                        
                        tool_result = await self.tool_service.call_tool(
                            tool_call["name"], 
                            fixed_args
                        )
                        
                        # 处理工具结果
                        result_content = self._format_tool_result(tool_result)
                        
                        yield StreamChunk(
                            type="tool_result",
                            content=f"工具 {tool_call['name']} 执行完成",
                            data={"result": result_content, "success": True},
                            timestamp=datetime.now().isoformat()
                        )
                        
                        # 将工具调用和结果添加到对话历史
                        messages.append({
                            "role": "assistant", 
                            "content": f"我调用了工具 {tool_call['name']}，参数: {json.dumps(tool_call['args'], ensure_ascii=False)}"
                        })
                        messages.append({
                            "role": "user", 
                            "content": f"工具执行结果：{result_content}"
                        })
                        
                        # 继续下一轮循环，让LLM基于工具结果继续处理
                        continue
                        
                    except Exception as e:
                        # 工具调用失败
                        yield StreamChunk(
                            type="tool_error",
                            content=f"工具 {tool_call['name']} 执行失败: {str(e)}",
                            data={"error": str(e)},
                            timestamp=datetime.now().isoformat()
                        )
                        
                        # 告诉LLM工具调用失败
                        messages.append({
                            "role": "assistant", 
                            "content": f"我尝试调用工具 {tool_call['name']}，但执行失败了。"
                        })
                        messages.append({
                            "role": "user", 
                            "content": f"工具调用失败：{str(e)}。请不要再使用这个工具，直接回答问题。"
                        })
                        
                        # 继续下一轮循环
                        continue
                        
                else:
                    # 没有工具调用，直接返回答案
                    yield StreamChunk(
                        type="final_answer",
                        content=llm_response,
                        timestamp=datetime.now().isoformat()
                    )
                    yield StreamChunk(
                        type="complete",
                        content="对话完成",
                        timestamp=datetime.now().isoformat()
                    )
                    return
            
            # 如果达到最大迭代次数，强制结束
            yield StreamChunk(
                type="max_iterations",
                content="已达到最大工具调用次数，请告诉我您需要什么帮助。",
                timestamp=datetime.now().isoformat()
            )
            yield StreamChunk(
                type="complete",
                content="对话完成",
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as error:
            self.logger.error(f"流式处理消息失败: {error}")
            yield StreamChunk(
                type="error",
                content=f"处理消息时发生错误: {error}",
                data={"error": str(error)},
                timestamp=datetime.now().isoformat()
            )
    
    def _format_tools_for_llm(self, tools: List[Dict[str, Any]]) -> str:
        """格式化工具信息给LLM，重要信息前置"""
        if not tools:
            return "当前没有可用的工具。"
        
        tools_text = f"可用工具清单 ({len(tools)}个):\n\n"
        
        # 按工具重要性排序，数据库相关工具优先
        priority_order = {
            'sqlite_list_tables': 1,
            'sqlite_describe_table': 2, 
            'sqlite_query': 3,
            'sqlite_insert_data': 4,
            'sqlite_get_schema': 5
        }
        
        sorted_tools = sorted(tools, key=lambda x: priority_order.get(x['name'], 999))
        
        for i, tool in enumerate(sorted_tools, 1):
            tools_text += f"{i}. **{tool['name']}**\n"
            tools_text += f"   功能: {tool['description']}\n"
            
            # 添加参数信息（如果有）
            if tool.get('parameters') and tool['parameters'].get('properties'):
                props = tool['parameters']['properties']
                required = tool['parameters'].get('required', [])
                
                tools_text += "   参数:\n"
                for param_name, param_info in props.items():
                    param_type = param_info.get('type', 'unknown')
                    is_required = " (必需)" if param_name in required else " (可选)"
                    tools_text += f"     - {param_name} ({param_type}){is_required}\n"
            else:
                tools_text += "   参数: 无\n"
            
            tools_text += "\n"
        
        return tools_text
    
    def _fix_tool_args(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """修复工具参数格式"""
        fixed_args = args.copy()
        
        # 修复sqlite_insert_data的data参数
        if tool_name == "sqlite_insert_data" and "data" in fixed_args:
            data_value = fixed_args["data"]
            # 如果data是字典，转换为JSON字符串
            if isinstance(data_value, dict):
                fixed_args["data"] = json.dumps(data_value, ensure_ascii=False)
                print(f"🔧 修复sqlite_insert_data参数: {fixed_args}")
            elif not isinstance(data_value, str):
                # 如果不是字符串也不是字典，尝试转换为JSON字符串
                fixed_args["data"] = json.dumps(data_value, ensure_ascii=False)
                print(f"🔧 修复sqlite_insert_data参数: {fixed_args}")
        
        return fixed_args
    
    def _extract_tool_call(self, text: str) -> Optional[Dict[str, Any]]:
        """从LLM响应中提取工具调用，防范幻觉"""
        try:
            print(f"🔍 尝试从以下文本中提取工具调用:\n{text}")
            
            # 检测幻觉模式：承诺未来调用工具的表述
            hallucination_patterns = [
                r'我将.*?调用',
                r'稍后.*?工具',
                r'接下来.*?使用',
                r'后续.*?执行',
                r'下一步.*?调用'
            ]
            
            for pattern in hallucination_patterns:
                if re.search(pattern, text):
                    print(f"🚨 检测到可能的工具调用幻觉模式: {pattern}")
                    # 如果检测到幻觉模式但没有实际工具调用，返回None
                    if '```json' not in text.lower():
                        print("❌ 发现幻觉：承诺调用工具但未实际执行")
                        return None
            
            # 方法1: 查找 ```json 代码块，并修复双大括号问题
            json_pattern = r'```json\s*\n?(.*?)\n?```'
            matches = re.findall(json_pattern, text, re.DOTALL | re.IGNORECASE)
            
            for match in matches:
                try:
                    # 修复双大括号问题
                    cleaned_match = match.strip()
                    # 将双大括号替换为单大括号
                    cleaned_match = cleaned_match.replace('{{', '{').replace('}}', '}')
                    print(f"🔧 清理后的JSON: {cleaned_match}")
                    
                    parsed = json.loads(cleaned_match)
                    if "tool_call" in parsed:
                        tool_call = parsed["tool_call"]
                        if "name" in tool_call and "args" in tool_call:
                            print(f"✅ 方法1成功提取工具调用: {tool_call}")
                            return tool_call
                except json.JSONDecodeError as e:
                    print(f"❌ 方法1 JSON解析失败: {e}")
                    continue
            
            # 方法2: 直接查找JSON对象，并修复双大括号
            json_pattern2 = r'\{[^{}]*"tool_call"[^{}]*\}'
            matches2 = re.findall(json_pattern2, text, re.DOTALL)
            
            for match in matches2:
                try:
                    # 修复双大括号问题
                    cleaned_match = match.replace('{{', '{').replace('}}', '}')
                    print(f"🔧 方法2清理后的JSON: {cleaned_match}")
                    
                    parsed = json.loads(cleaned_match)
                    if "tool_call" in parsed:
                        tool_call = parsed["tool_call"]
                        if "name" in tool_call and "args" in tool_call:
                            print(f"✅ 方法2成功提取工具调用: {tool_call}")
                            return tool_call
                except json.JSONDecodeError as e:
                    print(f"❌ 方法2 JSON解析失败: {e}")
                    continue
            
            # 方法3: 查找更复杂的JSON结构，支持双大括号
            json_pattern3 = r'\{\{.*?"tool_call".*?\}\}|\{.*?"tool_call".*?\}'
            matches3 = re.findall(json_pattern3, text, re.DOTALL)
            
            for match in matches3:
                try:
                    # 修复双大括号问题
                    cleaned_match = match.strip().replace('{{', '{').replace('}}', '}')
                    print(f"🔧 方法3清理后的JSON: {cleaned_match}")
                    
                    parsed = json.loads(cleaned_match)
                    if "tool_call" in parsed:
                        tool_call = parsed["tool_call"]
                        if "name" in tool_call and "args" in tool_call:
                            print(f"✅ 方法3成功提取工具调用: {tool_call}")
                            return tool_call
                except json.JSONDecodeError as e:
                    print(f"❌ 方法3 JSON解析失败: {e}")
                    continue
            
            # 方法4: 查找文本中提到的工具名称和参数
            tool_name_pattern = r'调用工具\s+(\w+).*?参数.*?\{([^}]+)\}'
            tool_matches = re.findall(tool_name_pattern, text, re.DOTALL)
            
            for tool_name, args_str in tool_matches:
                try:
                    # 尝试解析参数
                    args_json = "{" + args_str + "}"
                    args = json.loads(args_json)
                    tool_call = {"name": tool_name, "args": args}
                    print(f"✅ 方法4成功提取工具调用: {tool_call}")
                    return tool_call
                except json.JSONDecodeError as e:
                    print(f"❌ 方法4 JSON解析失败: {e}")
                    continue
            
            # 方法5: 查找特定的工具调用模式
            specific_patterns = [
                r'sqlite_describe_table.*?"table_name":\s*"([^"]+)"',
                r'sqlite_list_tables',
                r'sqlite_query.*?"query":\s*"([^"]+)"',
                r'sqlite_insert_data.*?"table_name":\s*"([^"]+)"',
                r'sqlite_get_schema'
            ]
            
            for pattern in specific_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    if 'describe_table' in pattern:
                        tool_call = {"name": "sqlite_describe_table", "args": {"table_name": matches[0]}}
                        print(f"✅ 方法5成功提取工具调用: {tool_call}")
                        return tool_call
                    elif 'list_tables' in pattern:
                        tool_call = {"name": "sqlite_list_tables", "args": {}}
                        print(f"✅ 方法5成功提取工具调用: {tool_call}")
                        return tool_call
                    elif 'query' in pattern:
                        tool_call = {"name": "sqlite_query", "args": {"query": matches[0]}}
                        print(f"✅ 方法5成功提取工具调用: {tool_call}")
                        return tool_call
                    elif 'get_schema' in pattern:
                        tool_call = {"name": "sqlite_get_schema", "args": {}}
                        print(f"✅ 方法5成功提取工具调用: {tool_call}")
                        return tool_call
            
            print("❌ 所有方法都未能提取到工具调用")
            return None
                
        except Exception as e:
            print(f"❌ 提取工具调用时出错: {e}")
            return None
    
    def _format_tool_result(self, tool_result: Any) -> str:
        """格式化工具执行结果"""
        try:
            # 如果是MCPToolResult对象，提取其内容
            if hasattr(tool_result, 'content'):
                if isinstance(tool_result.content, list) and len(tool_result.content) > 0:
                    if hasattr(tool_result.content[0], 'text'):
                        return tool_result.content[0].text
                    else:
                        return str(tool_result.content[0])
                elif isinstance(tool_result.content, str):
                    return tool_result.content
                else:
                    return str(tool_result.content)
            
            # 尝试JSON序列化
            if isinstance(tool_result, (dict, list)):
                return json.dumps(tool_result, ensure_ascii=False, indent=2)
            
            # 直接转换为字符串
            return str(tool_result)
                
        except Exception as e:
            return f"结果格式化失败: {e}"
    
    async def _call_llm(self, messages: List[Dict[str, str]], model: str = None) -> str:
        """
        调用LLM API
        
        Args:
            messages: 消息列表
            model: 使用的模型（如果为None则使用默认模型）
            
        Returns:
            LLM响应内容
        """
        try:
            # 记录LLM请求
            # self.tool_service.mcp_client.add_logs(
            #     {"messages": messages, "model": self.model, "llm_type": self.llm_type},
            #     LogType.LLM_REQUEST
            # )
            
            # 使用指定的模型或默认模型
            current_model = model if model else self.model
            print(f"🤖 调用LLM: {self.llm_type}/{current_model}")
            
            # 使用myLLM.py中的chat_with_llm函数
            response = chat_with_llm(messages, llmType=self.llm_type, model=current_model)
            
            # chat_with_llm返回的是JSON字符串，需要解析
            try:
                response_data = json.loads(response)
                content = response_data.get("reply", response)
            except json.JSONDecodeError:
                # 如果不是JSON，直接使用响应内容
                content = response
            
            print(f"✅ LLM响应长度: {len(content)} 字符")
            
            # 记录LLM响应
            # self.tool_service.mcp_client.add_logs(
            #     {"response": content[:500] + "..." if len(content) > 500 else content},
            #     LogType.LLM_RESPONSE
            # )
            
            return content
            
        except Exception as error:
            error_msg = f"LLM调用失败: {error}"
            print(f"❌ {error_msg}")
            # self.tool_service.mcp_client.add_logs(
            #     {"error": str(error)},
            #     LogType.LLM_ERROR
            # )
            raise error
    
    async def simple_chat(self, user_input: str, conversation_history: Optional[List[Dict[str, Any]]] = None, model: str = None) -> str:
        """
        简单聊天接口（非流式）
        
        Args:
            user_input: 用户输入
            conversation_history: 对话历史
            model: 使用的模型（如果为None则使用默认模型）
            
        Returns:
            LLM回答
        """
        try:
            # 构建对话历史
            messages = [{"role": "system", "content": self.base_system_prompt}]
            
            # 添加历史对话
            if conversation_history:
                for msg in conversation_history[-5:]:  # 只保留最近5轮对话
                    if msg.get("role") in ["user", "assistant"]:
                        messages.append({
                            "role": msg["role"],
                            "content": msg["content"]
                        })
            
            # 添加当前用户输入
            messages.append({"role": "user", "content": user_input})
            
            # 调用LLM
            response = await self._call_llm(messages, model)
            return response
            
        except Exception as error:
            self.logger.error(f"简单聊天失败: {error}")
            return f"抱歉，处理您的请求时发生了错误: {error}"
    
    async def simple_chat_with_persona(self, user_input: str, 
                                     conversation_history: Optional[List[Dict[str, Any]]] = None, 
                                     model: str = None,
                                     persona_prompt: str = "") -> str:
        """
        带人设的简单聊天接口（非流式）
        
        Args:
            user_input: 用户输入
            conversation_history: 对话历史
            model: 使用的模型
            persona_prompt: 人设系统提示词
            
        Returns:
            LLM回答
        """
        try:
            # 构建对话历史，使用人设提示词作为系统消息
            messages = []
            
            # 使用人设提示词或默认系统提示词
            system_prompt = persona_prompt if persona_prompt else self.base_system_prompt
            messages.append({"role": "system", "content": system_prompt})
            
            # 添加历史对话
            if conversation_history:
                for msg in conversation_history[-5:]:  # 只保留最近5轮对话
                    if msg.get("role") in ["user", "assistant"]:
                        messages.append({
                            "role": msg["role"],
                            "content": msg["content"]
                        })
            
            # 添加当前用户输入
            messages.append({"role": "user", "content": user_input})
            
            print(f"🎭 使用人设聊天，消息数量: {len(messages)}")
            
            # 调用LLM
            response = await self._call_llm(messages, model)
            print(f"🎭 人设聊天响应: {response}， messages: {messages}")

            return response
            
        except Exception as error:
            self.logger.error(f"人设聊天失败: {error}")
            return f"抱歉，处理您的请求时发生了错误: {error}" 