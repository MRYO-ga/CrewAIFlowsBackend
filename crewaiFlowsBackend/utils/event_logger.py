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
    crewai_event_bus
)
from crewai.utilities.events.base_event_listener import BaseEventListener
from utils.jobManager import append_event
import json

class CrewAIEventLogger(BaseEventListener):
    """
    精简版CrewAI事件监听器，只记录主要事件到MySQL数据库，不记录err和lmm相关事件
    """
    def __init__(self, job_id):
        super().__init__()
        self.job_id = job_id
        
    def _format_event(self, event_type, data):
        """格式化事件数据为JSON字符串"""
        try:
            # 将事件数据转换为字典
            event_data = {
                "event_type": event_type,
                "data": data
            }
            return json.dumps(event_data, ensure_ascii=False)
        except Exception as e:
            return f"{{\"event_type\": \"{event_type}\", \"error\": \"{str(e)}\"}}"
    
    def setup_listeners(self, crewai_event_bus):
        """设置所有事件的监听器"""
        
        # ==================== Crew事件 ====================
        @crewai_event_bus.on(CrewKickoffStartedEvent)
        def on_crew_kickoff_started(source, event):
            data = {"crew_name": getattr(event, "crew_name", "unknown")}
            append_event(self.job_id, self._format_event("crew_kickoff_started", data))
        
        @crewai_event_bus.on(CrewKickoffCompletedEvent)
        def on_crew_kickoff_completed(source, event):
            data = {
                "crew_name": getattr(event, "crew_name", "unknown"),
                "output": str(getattr(event, "output", ""))
            }
            append_event(self.job_id, self._format_event("crew_kickoff_completed", data))
        
        @crewai_event_bus.on(CrewTestStartedEvent)
        def on_crew_test_started(source, event):
            data = {"crew_name": getattr(event, "crew_name", "unknown")}
            append_event(self.job_id, self._format_event("crew_test_started", data))
        
        @crewai_event_bus.on(CrewTestCompletedEvent)
        def on_crew_test_completed(source, event):
            data = {"crew_name": getattr(event, "crew_name", "unknown")}
            append_event(self.job_id, self._format_event("crew_test_completed", data))
        
        @crewai_event_bus.on(CrewTrainStartedEvent)
        def on_crew_train_started(source, event):
            data = {"crew_name": getattr(event, "crew_name", "unknown")}
            append_event(self.job_id, self._format_event("crew_train_started", data))
        
        @crewai_event_bus.on(CrewTrainCompletedEvent)
        def on_crew_train_completed(source, event):
            data = {"crew_name": getattr(event, "crew_name", "unknown")}
            append_event(self.job_id, self._format_event("crew_train_completed", data))
        
        # ==================== Agent事件 ====================
        @crewai_event_bus.on(AgentExecutionStartedEvent)
        def on_agent_execution_started(source, event):
            data = {
                "agent_role": getattr(event.agent, "role", "unknown") if hasattr(event, "agent") else "unknown",
                "task_description": getattr(event, "task_description", "")
            }
            append_event(self.job_id, self._format_event("agent_execution_started", data))
        
        @crewai_event_bus.on(AgentExecutionCompletedEvent)
        def on_agent_execution_completed(source, event):
            data = {
                "agent_role": getattr(event.agent, "role", "unknown") if hasattr(event, "agent") else "unknown",
                "output": str(getattr(event, "output", ""))
            }
            append_event(self.job_id, self._format_event("agent_execution_completed", data))
        
        # ==================== Task事件 ====================
        @crewai_event_bus.on(TaskStartedEvent)
        def on_task_started(source, event):
            data = {
                "task_description": getattr(event, "task_description", "")
            }
            append_event(self.job_id, self._format_event("task_started", data))
        
        @crewai_event_bus.on(TaskCompletedEvent)
        def on_task_completed(source, event):
            data = {
                "task_description": getattr(event, "task_description", ""),
                "output": str(getattr(event, "output", ""))
            }
            append_event(self.job_id, self._format_event("task_completed", data))
        
        @crewai_event_bus.on(TaskEvaluationEvent)
        def on_task_evaluation(source, event):
            data = {
                "task_description": getattr(event, "task_description", ""),
                "evaluation": str(getattr(event, "evaluation", ""))
            }
            append_event(self.job_id, self._format_event("task_evaluation", data))
        
        # ==================== Tool使用事件 ====================
        @crewai_event_bus.on(ToolUsageStartedEvent)
        def on_tool_usage_started(source, event):
            agent_role = "unknown"
            if hasattr(event, "agent") and event.agent:
                agent_role = getattr(event.agent, "role", "unknown")
            data = {
                "tool_name": getattr(event, "tool_name", "unknown"),
                "agent_role": agent_role,
                "args": str(getattr(event, "tool_args", {}))
            }
            append_event(self.job_id, self._format_event("tool_usage_started", data))
        
        @crewai_event_bus.on(ToolUsageFinishedEvent)
        def on_tool_usage_finished(source, event):
            data = {
                "tool_name": getattr(event, "tool_name", "unknown"),
                "result": str(getattr(event, "result", ""))
            }
            append_event(self.job_id, self._format_event("tool_usage_finished", data))
            
        # ==================== Flow事件 ====================
        @crewai_event_bus.on(FlowCreatedEvent)
        def on_flow_created(source, event):
            data = {"flow_name": getattr(event, "flow_name", "unknown")}
            append_event(self.job_id, self._format_event("flow_created", data))
        
        @crewai_event_bus.on(FlowStartedEvent)
        def on_flow_started(source, event):
            data = {"flow_name": getattr(event, "flow_name", "unknown")}
            append_event(self.job_id, self._format_event("flow_started", data))
        
        @crewai_event_bus.on(FlowFinishedEvent)
        def on_flow_finished(source, event):
            data = {"flow_name": getattr(event, "flow_name", "unknown")}
            append_event(self.job_id, self._format_event("flow_finished", data))
        
        @crewai_event_bus.on(FlowPlotEvent)
        def on_flow_plot(source, event):
            data = {"flow_name": getattr(event, "flow_name", "unknown")}
            append_event(self.job_id, self._format_event("flow_plot", data))
        
        @crewai_event_bus.on(MethodExecutionStartedEvent)
        def on_method_execution_started(source, event):
            data = {"method_name": getattr(event, "method_name", "unknown")}
            append_event(self.job_id, self._format_event("method_execution_started", data))
        
        @crewai_event_bus.on(MethodExecutionFinishedEvent)
        def on_method_execution_finished(source, event):
            data = {"method_name": getattr(event, "method_name", "unknown")}
            append_event(self.job_id, self._format_event("method_execution_finished", data))

# 实例化监听器的示例
def create_event_logger(job_id):
    """创建并返回事件记录器实例"""
    return CrewAIEventLogger(job_id)