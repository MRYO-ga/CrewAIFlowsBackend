"""
LLM服务模块
负责处理大语言模型的调用、任务拆解和工具集成
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Union, AsyncGenerator
from datetime import datetime
from enum import Enum

import sys
import os
from pathlib import Path

# 添加utils路径到sys.path
utils_path = Path(__file__).parent.parent / "utils"
if str(utils_path) not in sys.path:
    sys.path.append(str(utils_path))

from myLLM import chat_with_llm
from pydantic import BaseModel

from .tool_service import ToolService
from .mcp_client_service import MCPClientService, LogType

class TaskType(Enum):
    """任务类型枚举"""
    SIMPLE_QUERY = "simple_query"  # 简单查询，无需工具
    DATA_READ = "data_read"  # 数据读取
    DATA_WRITE = "data_write"  # 数据写入
    DATA_ANALYSIS = "data_analysis"  # 数据分析
    COMPLEX_TASK = "complex_task"  # 复杂任务，需要多步骤

class TaskStep(BaseModel):
    """任务步骤模型"""
    step_id: int
    step_name: str
    step_description: str
    tool_name: Optional[str] = None
    tool_args: Optional[Dict[str, Any]] = None
    result: Optional[Any] = None
    status: str = "pending"  # pending, running, completed, failed
    error: Optional[str] = None

class TaskDecomposition(BaseModel):
    """任务拆解结果模型"""
    task_type: TaskType
    task_description: str
    steps: List[TaskStep]
    estimated_time: Optional[int] = None  # 预估时间（秒）
    requires_tools: bool = False
    tool_names: List[str] = []

class LLMResponse(BaseModel):
    """LLM响应模型"""
    content: str
    task_decomposition: Optional[TaskDecomposition] = None
    tool_calls: List[Dict[str, Any]] = []
    steps_executed: List[TaskStep] = []
    final_answer: str
    metadata: Dict[str, Any] = {}

class LLMService:
    """LLM服务类"""
    
    def __init__(self, tool_service: ToolService, api_key: str = None, model: str = "gpt-4o-mini", llm_type: str = "openai"):
        """
        初始化LLM服务
        
        Args:
            tool_service: 工具服务实例
            api_key: API密钥（已配置在myLLM.py中）
            model: 使用的模型名称
            llm_type: LLM类型（openai, oneapi, ollama）
        """
        self.tool_service = tool_service
        self.model = model
        self.llm_type = llm_type
        self.logger = logging.getLogger(__name__)
        
        print(f"🤖 初始化LLM服务: 类型={llm_type}, 模型={model}")
        
        # 不再使用AsyncOpenAI客户端，而是使用myLLM中的配置
        
        # 系统提示词
        self.system_prompt = """你是一个智能助手，能够帮助用户完成各种任务。
你可以使用以下能力：
1. 分析用户问题并拆解为具体步骤
2. 调用工具获取和处理数据
3. 提供清晰的步骤执行过程
4. 给出最终答案和建议

当用户提出问题时，请按照以下流程：
1. 分析问题类型和复杂度
2. 如果需要工具，拆解为具体步骤
3. 按步骤执行并展示过程
4. 提供最终答案

请用中文回答用户问题。"""
        
    async def analyze_user_input(self, user_input: str, conversation_history: Optional[List[Dict[str, Any]]] = None) -> TaskDecomposition:
        """
        分析用户输入并拆解任务
        
        Args:
            user_input: 用户输入
            conversation_history: 对话历史
            
        Returns:
            任务拆解结果
        """
        try:
            print(f"🔍 [分析阶段] 开始分析用户输入: '{user_input}'")
            
            # 获取可用工具
            print("📦 [分析阶段] 正在获取可用工具列表...")
            available_tools = await self.tool_service.get_tools_for_llm()
            print(f"✅ [分析阶段] 获取到 {len(available_tools)} 个可用工具:")
            for i, tool in enumerate(available_tools, 1):
                print(f"   {i}. {tool['name']}: {tool['description']}")
            
            # 构建分析提示
            analysis_prompt = f"""
请分析以下用户问题，并判断是否需要使用工具来完成任务。

用户问题：{user_input}

可用工具：
{json.dumps(available_tools, ensure_ascii=False, indent=2)}

请按照以下JSON格式返回分析结果：
{{
    "task_type": "simple_query|data_read|data_write|data_analysis|complex_task",
    "task_description": "任务描述",
    "requires_tools": true/false,
    "tool_names": ["工具名称列表"],
    "steps": [
        {{
            "step_id": 1,
            "step_name": "步骤名称",
            "step_description": "步骤描述",
            "tool_name": "工具名称或null",
            "tool_args": {{"参数": "值"}}
        }}
    ],
    "estimated_time": 预估时间秒数
}}

请只返回JSON，不要其他内容。
"""
            
            # 调用LLM分析
            print("🧠 [分析阶段] 准备调用LLM进行任务分析...")
            print(f"📝 [分析阶段] 分析提示词长度: {len(analysis_prompt)} 字符")
            
            messages = [
                {"role": "system", "content": "你是一个任务分析专家，能够将用户问题拆解为具体的执行步骤。"},
                {"role": "user", "content": analysis_prompt}
            ]
            
            print("⏳ [分析阶段] 正在调用LLM...")
            response = await self._call_llm(messages)
            print(f"📄 [分析阶段] LLM分析响应: {response[:200]}..." if len(response) > 200 else f"📄 [分析阶段] LLM分析响应: {response}")
            
            # 解析返回结果
            print("🔧 [分析阶段] 开始解析LLM响应...")
            try:
                analysis_result = json.loads(response)
                print("✅ [分析阶段] JSON解析成功")
                print(f"📋 [分析阶段] 任务类型: {analysis_result.get('task_type', 'unknown')}")
                print(f"🎯 [分析阶段] 任务描述: {analysis_result.get('task_description', 'unknown')}")
                print(f"🛠️ [分析阶段] 需要工具: {analysis_result.get('requires_tools', False)}")
                print(f"📝 [分析阶段] 工具列表: {analysis_result.get('tool_names', [])}")
                print(f"⏱️ [分析阶段] 预计时间: {analysis_result.get('estimated_time', 'unknown')} 秒")
                
                # 构建TaskStep对象
                steps = []
                steps_data = analysis_result.get("steps", [])
                print(f"📊 [分析阶段] 拆解为 {len(steps_data)} 个步骤:")
                
                for step_data in steps_data:
                    step = TaskStep(
                        step_id=step_data.get("step_id", 0),
                        step_name=step_data.get("step_name", ""),
                        step_description=step_data.get("step_description", ""),
                        tool_name=step_data.get("tool_name"),
                        tool_args=step_data.get("tool_args")
                    )
                    steps.append(step)
                    print(f"   步骤{step.step_id}: {step.step_name} (工具: {step.tool_name or '无'})")
                
                # 构建TaskDecomposition对象
                task_decomposition = TaskDecomposition(
                    task_type=TaskType(analysis_result.get("task_type", "simple_query")),
                    task_description=analysis_result.get("task_description", user_input),
                    steps=steps,
                    estimated_time=analysis_result.get("estimated_time"),
                    requires_tools=analysis_result.get("requires_tools", False),
                    tool_names=analysis_result.get("tool_names", [])
                )
                
                print("🎉 [分析阶段] 任务分析完成！")
                return task_decomposition
                
            except json.JSONDecodeError as e:
                # 如果JSON解析失败，创建简单任务
                print(f"❌ [分析阶段] JSON解析失败: {e}")
                print(f"📄 [分析阶段] 原始响应: {response}")
                print("🔄 [分析阶段] 创建默认简单任务...")
                self.logger.warning("LLM返回的JSON格式不正确，创建简单任务")
                return TaskDecomposition(
                    task_type=TaskType.SIMPLE_QUERY,
                    task_description=user_input,
                    steps=[TaskStep(
                        step_id=1,
                        step_name="回答问题",
                        step_description="直接回答用户问题",
                        tool_name=None,
                        tool_args=None
                    )],
                    requires_tools=False,
                    tool_names=[]
                )
                
        except Exception as error:
            self.logger.error(f"分析用户输入失败: {error}")
            # 返回默认的简单任务
            return TaskDecomposition(
                task_type=TaskType.SIMPLE_QUERY,
                task_description=user_input,
                steps=[TaskStep(
                    step_id=1,
                    step_name="回答问题",
                    step_description="直接回答用户问题",
                    tool_name=None,
                    tool_args=None
                )],
                requires_tools=False,
                tool_names=[]
            )
    
    async def execute_task(self, task_decomposition: TaskDecomposition, user_input: str) -> LLMResponse:
        """
        执行任务
        
        Args:
            task_decomposition: 任务拆解结果
            user_input: 原始用户输入
            
        Returns:
            LLM响应结果
        """
        try:
            print(f"🚀 [执行阶段] 开始执行任务: {task_decomposition.task_description}")
            print(f"📋 [执行阶段] 任务类型: {task_decomposition.task_type.value}")
            print(f"🛠️ [执行阶段] 需要工具: {task_decomposition.requires_tools}")
            print(f"📊 [执行阶段] 共有 {len(task_decomposition.steps)} 个步骤需要执行")
            
            executed_steps = []
            tool_results = []
            
            # 执行每个步骤
            for step in task_decomposition.steps:
                print(f"\n⚡ [执行阶段] 执行步骤 {step.step_id}: {step.step_name}")
                print(f"📄 [执行阶段] 步骤描述: {step.step_description}")
                print(f"🔧 [执行阶段] 需要工具: {step.tool_name or '无'}")
                if step.tool_args:
                    print(f"📝 [执行阶段] 工具参数: {step.tool_args}")
                
                step.status = "running"
                self.logger.info(f"执行步骤 {step.step_id}: {step.step_name}")
                
                try:
                    if step.tool_name:
                        # 需要调用工具
                        print(f"🛠️ [执行阶段] 正在调用工具: {step.tool_name}")
                        result = await self.tool_service.call_tool(step.tool_name, step.tool_args or {})
                        print(f"📦 [执行阶段] 工具调用返回原始结果: {type(result)}")
                        
                        step.result = self.tool_service.format_tool_result(result)
                        print(f"✅ [执行阶段] 工具结果格式化完成: {step.result}")
                        
                        tool_results.append({
                            "step_id": step.step_id,
                            "tool_name": step.tool_name,
                            "result": step.result
                        })
                    else:
                        # 不需要工具，直接标记完成
                        print("⏭️ [执行阶段] 此步骤不需要工具，直接完成")
                        step.result = {"message": "步骤完成"}
                    
                    step.status = "completed"
                    print(f"✅ [执行阶段] 步骤 {step.step_id} 执行成功")
                    
                except Exception as error:
                    step.status = "failed"
                    step.error = str(error)
                    print(f"❌ [执行阶段] 步骤 {step.step_id} 执行失败: {error}")
                    self.logger.error(f"步骤 {step.step_id} 执行失败: {error}")
                
                executed_steps.append(step)
            
            # 生成最终回答
            final_answer = await self._generate_final_answer(user_input, executed_steps, tool_results)
            
            # 构建响应
            response = LLMResponse(
                content=final_answer,
                task_decomposition=task_decomposition,
                steps_executed=executed_steps,
                final_answer=final_answer,
                metadata={
                    "execution_time": datetime.now().isoformat(),
                    "steps_count": len(executed_steps),
                    "tools_used": [step.tool_name for step in executed_steps if step.tool_name],
                    "success_rate": len([s for s in executed_steps if s.status == "completed"]) / len(executed_steps) if executed_steps else 0
                }
            )
            
            return response
            
        except Exception as error:
            self.logger.error(f"执行任务失败: {error}")
            # 返回错误响应
            return LLMResponse(
                content=f"执行任务时发生错误: {error}",
                final_answer=f"抱歉，处理您的请求时发生了错误: {error}",
                metadata={"error": str(error)}
            )
    
    async def _generate_final_answer(self, user_input: str, executed_steps: List[TaskStep], tool_results: List[Dict[str, Any]]) -> str:
        """
        生成最终答案
        
        Args:
            user_input: 用户输入
            executed_steps: 执行的步骤
            tool_results: 工具调用结果
            
        Returns:
            最终答案
        """
        try:
            print(f"\n📝 [答案生成] 开始生成最终答案")
            print(f"❓ [答案生成] 用户问题: {user_input}")
            print(f"📊 [答案生成] 已执行步骤数: {len(executed_steps)}")
            print(f"🛠️ [答案生成] 工具调用结果数: {len(tool_results)}")
            
            # 统计步骤状态
            completed_steps = [s for s in executed_steps if s.status == "completed"]
            failed_steps = [s for s in executed_steps if s.status == "failed"]
            print(f"✅ [答案生成] 成功步骤: {len(completed_steps)}")
            print(f"❌ [答案生成] 失败步骤: {len(failed_steps)}")
            
            # 构建上下文
            print("🔧 [答案生成] 正在构建上下文...")
            context = f"""
用户问题：{user_input}

执行的步骤：
"""
            for step in executed_steps:
                context += f"\n{step.step_id}. {step.step_name} - {step.step_description}"
                if step.status == "completed" and step.result:
                    context += f"\n   结果：{json.dumps(step.result, ensure_ascii=False, indent=2)}"
                elif step.status == "failed":
                    context += f"\n   错误：{step.error}"
                    
            print(f"📄 [答案生成] 上下文长度: {len(context)} 字符")
            
            # 生成回答提示
            answer_prompt = f"""
基于以上执行的步骤和结果，请为用户提供一个清晰、详细的最终答案。

要求：
1. 用中文回答
2. 总结执行的步骤
3. 提供具体的结果或建议
4. 如果有数据，请用易懂的方式呈现
5. 如果有错误，请说明并提供解决建议

请直接提供答案，不要重复问题。
"""
            
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": context + "\n\n" + answer_prompt}
            ]
            
            print("🧠 [答案生成] 正在调用LLM生成最终答案...")
            print(f"📝 [答案生成] 消息数量: {len(messages)}")
            print(f"📄 [答案生成] 总输入长度: {len(messages[0]['content']) + len(messages[1]['content'])} 字符")
            
            final_answer = await self._call_llm(messages)
            print(f"✅ [答案生成] 最终答案生成完成，长度: {len(final_answer)} 字符")
            print(f"📋 [答案生成] 答案预览: {final_answer[:100]}..." if len(final_answer) > 100 else f"📋 [答案生成] 完整答案: {final_answer}")
            return final_answer
            
        except Exception as error:
            self.logger.error(f"生成最终答案失败: {error}")
            return f"抱歉，生成答案时发生错误: {error}"
    
    async def _call_llm(self, messages: List[Dict[str, str]]) -> str:
        """
        调用LLM API
        
        Args:
            messages: 消息列表
            
        Returns:
            LLM响应内容
        """
        try:
            # 记录LLM请求
            self.tool_service.mcp_client.add_logs(
                {"messages": messages, "model": self.model, "llm_type": self.llm_type},
                LogType.LLM_REQUEST
            )
            
            print(f"🤖 调用LLM: {self.llm_type}/{self.model}")
            
            # 使用myLLM.py中的chat_with_llm函数
            response = chat_with_llm(messages, llmType=self.llm_type, model=self.model)
            
            # chat_with_llm返回的是JSON字符串，需要解析
            import json
            try:
                response_data = json.loads(response)
                content = response_data.get("reply", response)
            except json.JSONDecodeError:
                # 如果不是JSON，直接使用响应内容
                content = response
            
            print(f"✅ LLM响应长度: {len(content)} 字符")
            
            # 记录LLM响应
            self.tool_service.mcp_client.add_logs(
                {"response": content[:500] + "..." if len(content) > 500 else content, "full_response": response},
                LogType.LLM_RESPONSE
            )
            
            return content
            
        except Exception as error:
            error_msg = f"LLM调用失败: {error}"
            print(f"❌ {error_msg}")
            self.tool_service.mcp_client.add_logs(
                {"error": str(error)},
                LogType.LLM_ERROR
            )
            raise error
    
    async def process_user_input(self, user_input: str, conversation_history: Optional[List[Dict[str, Any]]] = None) -> LLMResponse:
        """
        处理用户输入的完整流程
        
        Args:
            user_input: 用户输入
            conversation_history: 对话历史
            
        Returns:
            完整的LLM响应
        """
        try:
            # 1. 分析用户输入
            task_decomposition = await self.analyze_user_input(user_input, conversation_history)
            
            # 2. 执行任务
            response = await self.execute_task(task_decomposition, user_input)
            
            return response
            
        except Exception as error:
            self.logger.error(f"处理用户输入失败: {error}")
            return LLMResponse(
                content=f"处理请求时发生错误: {error}",
                final_answer=f"抱歉，处理您的请求时发生了错误: {error}",
                metadata={"error": str(error)}
            )
    
    async def stream_response(self, user_input: str, conversation_history: Optional[List[Dict[str, Any]]] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式响应用户输入
        
        Args:
            user_input: 用户输入
            conversation_history: 对话历史
            
        Yields:
            流式响应数据
        """
        try:
            # 发送开始信号
            yield {"type": "start", "message": "开始处理您的请求..."}
            
            # 1. 分析用户输入
            yield {"type": "analysis", "message": "正在分析您的问题..."}
            task_decomposition = await self.analyze_user_input(user_input, conversation_history)
            
            yield {
                "type": "decomposition",
                "message": f"已拆解为 {len(task_decomposition.steps)} 个步骤",
                "data": task_decomposition.dict()
            }
            
            # 2. 执行步骤
            executed_steps = []
            tool_results = []
            
            for step in task_decomposition.steps:
                yield {
                    "type": "step_start",
                    "message": f"执行步骤 {step.step_id}: {step.step_name}",
                    "step": step.dict()
                }
                
                step.status = "running"
                
                try:
                    if step.tool_name:
                        result = await self.tool_service.call_tool(step.tool_name, step.tool_args or {})
                        step.result = self.tool_service.format_tool_result(result)
                        tool_results.append({
                            "step_id": step.step_id,
                            "tool_name": step.tool_name,
                            "result": step.result
                        })
                    else:
                        step.result = {"message": "步骤完成"}
                    
                    step.status = "completed"
                    
                    yield {
                        "type": "step_completed",
                        "message": f"步骤 {step.step_id} 完成",
                        "step": step.dict()
                    }
                    
                except Exception as error:
                    step.status = "failed"
                    step.error = str(error)
                    
                    yield {
                        "type": "step_failed",
                        "message": f"步骤 {step.step_id} 失败: {error}",
                        "step": step.dict()
                    }
                
                executed_steps.append(step)
            
            # 3. 生成最终答案
            yield {"type": "generating", "message": "正在生成最终答案..."}
            final_answer = await self._generate_final_answer(user_input, executed_steps, tool_results)
            
            # 4. 发送完成信号
            yield {
                "type": "completed",
                "message": "处理完成",
                "final_answer": final_answer,
                "metadata": {
                    "steps_count": len(executed_steps),
                    "tools_used": [step.tool_name for step in executed_steps if step.tool_name],
                    "success_rate": len([s for s in executed_steps if s.status == "completed"]) / len(executed_steps) if executed_steps else 0
                }
            }
            
        except Exception as error:
            yield {
                "type": "error",
                "message": f"处理过程中发生错误: {error}",
                "error": str(error)
            } 