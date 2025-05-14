# 在utils目录下创建一个新文件 event_logger.py

from crewai.utilities.events import (
    CrewKickoffStartedEvent,
    CrewKickoffCompletedEvent,
    CrewTestStartedEvent,
    CrewTestCompletedEvent,
    CrewTrainStartedEvent,
    CrewTrainCompletedEvent,
    AgentExecutionStartedEvent,
    AgentExecutionCompletedEvent,
    TaskStartedEvent,
    TaskCompletedEvent,
    TaskEvaluationEvent,
    ToolUsageStartedEvent,
    ToolUsageFinishedEvent,
    FlowCreatedEvent,
    FlowStartedEvent,
    FlowFinishedEvent,
    FlowPlotEvent,
    MethodExecutionStartedEvent,
    MethodExecutionFinishedEvent,
    # LLMCallStartedEvent,
    # LLMCallCompletedEvent,
    # LLMCallFailedEvent,
    # LLMStreamChunkEvent,
    crewai_event_bus
)
from crewai.utilities.events.base_event_listener import BaseEventListener
from utils.jobManager import append_event
import json
from datetime import datetime
import os
import traceback
import pickle

class CrewAIEventLogger(BaseEventListener):
    """
    精简版CrewAI事件监听器，记录事件到MySQL数据库和文件系统
    """
    def __init__(self, job_id):
        super().__init__()
        self.job_id = job_id
        self.log_base_dir = os.path.join(os.path.dirname(__file__), "event_logs")
        self._ensure_log_dirs()
        
    def _ensure_log_dirs(self):
        """确保日志目录存在"""
        # 创建基础目录
        if not os.path.exists(self.log_base_dir):
            os.makedirs(self.log_base_dir)
            
        # 创建当天的日志目录
        self.today_log_dir = os.path.join(
            self.log_base_dir,
            datetime.now().strftime("%Y-%m-%d")
        )
        if not os.path.exists(self.today_log_dir):
            os.makedirs(self.today_log_dir)
            
        # 创建job专属目录
        self.job_log_dir = os.path.join(self.today_log_dir, self.job_id)
        if not os.path.exists(self.job_log_dir):
            os.makedirs(self.job_log_dir)
    
    def _save_event_to_file(self, event_type: str, event_data: dict, source=None, event=None):
        """将事件追加到日志文件"""
        try:
            # 生成事件日志内容
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
            log_content = f"\n{'='*50} Event Log {'='*50}\n"
            log_content += f"Timestamp: {timestamp}\n"
            log_content += f"Event Type: {event_type}\n\n"
            
            # 添加源对象信息
            if source:
                log_content += "Source Object:\n"
                log_content += f"Type: {type(source).__name__}\n"
                for attr in dir(source):
                    if not attr.startswith('_'):
                        try:
                            value = getattr(source, attr)
                            if not callable(value):
                                log_content += f"{attr}: {str(value)}\n"
                        except Exception as e:
                            log_content += f"{attr}: <Error: {str(e)}>\n"
                log_content += "\n"
            
            # 添加事件对象信息
            if event:
                log_content += "Event Object:\n"
                log_content += f"Class: {event.__class__.__name__}\n"
                for attr in dir(event):
                    if not attr.startswith('_'):
                        try:
                            value = getattr(event, attr)
                            if not callable(value):
                                log_content += f"{attr}: {str(value)}\n"
                        except Exception as e:
                            log_content += f"{attr}: <Error: {str(e)}>\n"
                log_content += "\n"
            
            # 添加处理后的数据
            log_content += "Processed Data:\n"
            log_content += json.dumps(event_data, ensure_ascii=False, indent=2)
            log_content += "\n\n"
            
            # 追加到日志文件
            log_file = os.path.join(self.job_log_dir, "events.log")
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(log_content)
            
            # 同时保存一个JSON格式的事件记录（用于程序处理）
            json_file = os.path.join(self.job_log_dir, "events.json")
            json_entry = {
                "timestamp": timestamp,
                "event_type": event_type,
                "processed_data": event_data
            }
            
            try:
                # 读取现有的JSON数据
                if os.path.exists(json_file):
                    with open(json_file, 'r', encoding='utf-8') as f:
                        events = json.load(f)
                else:
                    events = []
                
                # 添加新事件
                events.append(json_entry)
                
                # 写回文件
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(events, ensure_ascii=False, indent=2, fp=f)
                    
            except Exception as e:
                print(f"Warning: Failed to update JSON events file: {str(e)}")
                
        except Exception as e:
            print(f"Error saving event to file: {str(e)}")
            traceback.print_exc()
            
            # 记录错误信息
            try:
                error_log = os.path.join(self.job_log_dir, "errors.log")
                with open(error_log, 'a', encoding='utf-8') as f:
                    f.write(f"\n{'='*50} Error Log {'='*50}\n")
                    f.write(f"Timestamp: {timestamp}\n")
                    f.write(f"Event Type: {event_type}\n")
                    f.write(f"Error: {str(e)}\n")
                    f.write(f"Traceback:\n{traceback.format_exc()}\n")
            except:
                print("Failed to save error information to file")
    
    def _format_event(self, event_type, data):
        """格式化事件数据为JSON字符串"""
        try:
            event_data = {
                "event_type": event_type,
                "data": data
            }
            return json.dumps(event_data, ensure_ascii=False)
        except Exception as e:
            return f"{{\"event_type\": \"{event_type}\", \"error\": \"{str(e)}\"}}"
    
    def setup_listeners(self, crewai_event_bus):
        """设置所有事件的监听器"""
        
        # ==================== LLM事件 ====================
        # @crewai_event_bus.on(LLMCallStartedEvent)
        # def on_llm_call_started(source, event):
        #     data = {
        #         "prompt": getattr(event, "prompt", ""),
        #         "model": getattr(event, "model", "unknown"),
        #         "temperature": getattr(event, "temperature", None)
        #     }
        #     self._save_event_to_file("llm_call_started", data, source, event)
        #     append_event(self.job_id, self._format_event("llm_call_started", data))
        
        # @crewai_event_bus.on(LLMCallCompletedEvent)
        # def on_llm_call_completed(source, event):
        #     data = {
        #         "response": str(getattr(event, "response", "")),
        #         "model": getattr(event, "model", "unknown"),
        #         "tokens_used": getattr(event, "tokens_used", None),
        #         "completion_time": getattr(event, "completion_time", None)
        #     }
        #     self._save_event_to_file("llm_call_completed", data, source, event)
        #     append_event(self.job_id, self._format_event("llm_call_completed", data))
        
        # @crewai_event_bus.on(LLMCallFailedEvent)
        # def on_llm_call_failed(source, event):
        #     data = {
        #         "error": str(getattr(event, "error", "")),
        #         "model": getattr(event, "model", "unknown"),
        #         "prompt": getattr(event, "prompt", "")
        #     }
        #     self._save_event_to_file("llm_call_failed", data, source, event)
        #     append_event(self.job_id, self._format_event("llm_call_failed", data))
        
        # @crewai_event_bus.on(LLMStreamChunkEvent)
        # def on_llm_stream_chunk(source, event):
        #     data = {
        #         "chunk": str(getattr(event, "chunk", "")),
        #         "model": getattr(event, "model", "unknown"),
        #         "chunk_type": getattr(event, "chunk_type", "unknown")
        #     }
        #     self._save_event_to_file("llm_stream_chunk", data, source, event)
        #     append_event(self.job_id, self._format_event("llm_stream_chunk", data))
            
            
        # ==================== Crew事件 ====================
        @crewai_event_bus.on(CrewKickoffStartedEvent)
        def on_crew_kickoff_started(source, event):
            data = {"crew_name": getattr(event, "crew_name", "unknown")}
            self._save_event_to_file("crew_kickoff_started", data, source, event)
            append_event(self.job_id, self._format_event("crew_kickoff_started", data))
        
        @crewai_event_bus.on(CrewKickoffCompletedEvent)
        def on_crew_kickoff_completed(source, event):
            data = {
                "crew_name": getattr(event, "crew_name", "unknown"),
                "output": str(getattr(event, "output", ""))
            }
            self._save_event_to_file("crew_kickoff_completed", data, source, event)
            append_event(self.job_id, self._format_event("crew_kickoff_completed", data))
        
        @crewai_event_bus.on(CrewTestStartedEvent)
        def on_crew_test_started(source, event):
            data = {"crew_name": getattr(event, "crew_name", "unknown")}
            self._save_event_to_file("crew_test_started", data, source, event)
            append_event(self.job_id, self._format_event("crew_test_started", data))
        
        @crewai_event_bus.on(CrewTestCompletedEvent)
        def on_crew_test_completed(source, event):
            data = {"crew_name": getattr(event, "crew_name", "unknown")}
            self._save_event_to_file("crew_test_completed", data, source, event)
            append_event(self.job_id, self._format_event("crew_test_completed", data))
        
        
        @crewai_event_bus.on(CrewTrainStartedEvent)
        def on_crew_train_started(source, event):
            data = {"crew_name": getattr(event, "crew_name", "unknown")}
            self._save_event_to_file("crew_train_started", data, source, event)
            append_event(self.job_id, self._format_event("crew_train_started", data))
        
        @crewai_event_bus.on(CrewTrainCompletedEvent)
        def on_crew_train_completed(source, event):
            data = {"crew_name": getattr(event, "crew_name", "unknown")}
            self._save_event_to_file("crew_train_completed", data, source, event)
            append_event(self.job_id, self._format_event("crew_train_completed", data))
        
        # ==================== Agent事件 ====================
        @crewai_event_bus.on(AgentExecutionStartedEvent)
        def on_agent_execution_started(source, event):
            data = {
                "agent_role": getattr(event.agent, "role", "unknown") if hasattr(event, "agent") else "unknown",
                "task_description": getattr(event, "task_description", "")
            }
            self._save_event_to_file("agent_execution_started", data, source, event)
            append_event(self.job_id, self._format_event("agent_execution_started", data))
        
        @crewai_event_bus.on(AgentExecutionCompletedEvent)
        def on_agent_execution_completed(source, event):
            data = {
                "agent_role": getattr(event.agent, "role", "unknown") if hasattr(event, "agent") else "unknown",
                "output": str(getattr(event, "output", ""))
            }
            self._save_event_to_file("agent_execution_completed", data, source, event)
            append_event(self.job_id, self._format_event("agent_execution_completed", data))
        
        # ==================== Task事件 ====================
        @crewai_event_bus.on(TaskStartedEvent)
        def on_task_started(source, event):
            data = {
                "task_description": getattr(event, "task_description", "")
            }
            self._save_event_to_file("task_started", data, source, event)
            append_event(self.job_id, self._format_event("task_started", data))
        
        @crewai_event_bus.on(TaskCompletedEvent)
        def on_task_completed(source, event):
            data = {
                "task_description": getattr(event, "task_description", ""),
                "output": str(getattr(event, "output", ""))
            }
            self._save_event_to_file("task_completed", data, source, event)
            append_event(self.job_id, self._format_event("task_completed", data))
        
        @crewai_event_bus.on(TaskEvaluationEvent)
        def on_task_evaluation(source, event):
            data = {
                "task_description": getattr(event, "task_description", ""),
                "evaluation": str(getattr(event, "evaluation", ""))
            }
            self._save_event_to_file("task_evaluation", data, source, event)
            append_event(self.job_id, self._format_event("task_evaluation", data))
        
        # ==================== Tool使用事件 ====================
        @crewai_event_bus.on(ToolUsageStartedEvent)
        def on_tool_usage_started(source, event):
            agent_role = "unknown"
            if hasattr(event, "agent") and event.agent:
                agent_role = getattr(event.agent, "role", "unknown")
            
            tool_args = getattr(event, "tool_args", {})
            if isinstance(tool_args, str):
                try:
                    tool_args = json.loads(tool_args)
                except:
                    tool_args = {"raw_args": tool_args}
            
            data = {
                "tool_name": getattr(event, "tool_name", "unknown"),
                "agent_role": agent_role,
                "args": tool_args,
                "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
            }
            self._save_event_to_file("tool_usage_started", data, source, event)
            append_event(self.job_id, self._format_event("tool_usage_started", data))
        
        @crewai_event_bus.on(ToolUsageFinishedEvent)
        def on_tool_usage_finished(source, event):
            # 获取工具执行结果
            result = getattr(event, "result", None)
            
            # 处理结果数据
            if isinstance(result, dict):
                processed_result = result
            elif isinstance(result, (list, tuple)):
                processed_result = {"items": result}
            elif isinstance(result, str):
                try:
                    processed_result = json.loads(result)
                except:
                    processed_result = {"text": result}
            else:
                processed_result = {"value": str(result)} if result is not None else {"value": ""}
            
            # 获取工具名称和执行时间
            tool_name = getattr(event, "tool_name", "unknown")
            execution_time = None
            
            # 计算执行时间
            if hasattr(event, "start_time"):
                start_time = datetime.strptime(event.start_time, "%Y-%m-%d %H:%M:%S.%f")
                execution_time = (datetime.now() - start_time).total_seconds()
            
            # 获取代理角色
            agent_role = "unknown"
            if hasattr(event, "agent") and event.agent:
                agent_role = getattr(event.agent, "role", "unknown")
            
            data = {
                "tool_name": tool_name,
                "agent_role": agent_role,
                "result": processed_result,
                "execution_time": f"{execution_time:.2f}s" if execution_time else None,
                "status": "success" if result is not None else "no_result",
                "finish_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
            }
            self._save_event_to_file("tool_usage_finished", data, source, event)
            append_event(self.job_id, self._format_event("tool_usage_finished", data))
            
        # ==================== Flow事件 ====================
        @crewai_event_bus.on(FlowCreatedEvent)
        def on_flow_created(source, event):
            data = {"flow_name": getattr(event, "flow_name", "unknown")}
            self._save_event_to_file("flow_created", data, source, event)
            append_event(self.job_id, self._format_event("flow_created", data))
        
        @crewai_event_bus.on(FlowStartedEvent)
        def on_flow_started(source, event):
            data = {"flow_name": getattr(event, "flow_name", "unknown")}
            self._save_event_to_file("flow_started", data, source, event)
            append_event(self.job_id, self._format_event("flow_started", data))
        
        @crewai_event_bus.on(FlowFinishedEvent)
        def on_flow_finished(source, event):
            data = {"flow_name": getattr(event, "flow_name", "unknown")}
            self._save_event_to_file("flow_finished", data, source, event)
            append_event(self.job_id, self._format_event("flow_finished", data))
        
        @crewai_event_bus.on(FlowPlotEvent)
        def on_flow_plot(source, event):
            data = {"flow_name": getattr(event, "flow_name", "unknown")}
            self._save_event_to_file("flow_plot", data, source, event)
            append_event(self.job_id, self._format_event("flow_plot", data))
        
        @crewai_event_bus.on(MethodExecutionStartedEvent)
        def on_method_execution_started(source, event):
            data = {"method_name": getattr(event, "method_name", "unknown")}
            self._save_event_to_file("method_execution_started", data, source, event)
            append_event(self.job_id, self._format_event("method_execution_started", data))
        
        @crewai_event_bus.on(MethodExecutionFinishedEvent)
        def on_method_execution_finished(source, event):
            data = {"method_name": getattr(event, "method_name", "unknown")}
            self._save_event_to_file("method_execution_finished", data, source, event)
            append_event(self.job_id, self._format_event("method_execution_finished", data))


# 实例化监听器的示例
def create_event_logger(job_id):
    """创建并返回事件记录器实例"""
    return CrewAIEventLogger(job_id)