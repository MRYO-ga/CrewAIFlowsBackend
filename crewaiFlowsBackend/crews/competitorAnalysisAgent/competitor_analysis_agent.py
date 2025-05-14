# 竞品分析Agent (CompetitorAnalysisAgent)
# 该模块为小红书多Agent自动化运营系统的"竞品分析引擎"
# 负责平台趋势解构和竞品内容分析

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from typing import List, Dict, Any
from utils.models import TrendReport, CompetitorMatrix
from utils.jobManager import append_event
from utils.event_logger import create_event_logger
from tools.xiaohongshu_tool_adapters import XiaoHongShuToolAdapters

@CrewBase
class CompetitorAnalysisAgent:
    """
    竞品分析Agent - 负责小红书平台趋势解构和竞品内容策略分析
    """
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'
    
    def __init__(self, job_id: str, llm, input_data: Dict, manager_agent=None):
        """
        初始化竞品分析Agent
        
        Args:
            job_id: 作业ID
            llm: 大语言模型实例
            input_data: 输入数据
            manager_agent: 管理Agent实例
        """
        self.job_id = job_id
        self.llm = llm
        self.input_data = input_data
        self.manager_agent = manager_agent
        self.event_logger = create_event_logger(job_id)
        self.tool_adapters = XiaoHongShuToolAdapters()

    def append_event_callback(self, task_output):
        append_event(self.job_id, task_output.raw)

    @agent
    def platform_trend_decoder(self) -> Agent:
        """平台生态趋势解构Agent，负责分析平台内容趋势"""
        return Agent(
            config=self.agents_config['platform_trend_decoder'],
            tools=self.tool_adapters.get_platform_trend_tools(),
            verbose=True,
            memory=False,
            llm=self.llm
        )
        
    @agent
    def content_style_analyst(self) -> Agent:
        """内容策略风格拆解Agent，负责分析竞品内容策略"""
        return Agent(
            config=self.agents_config['content_style_analyst'],
            tools=self.tool_adapters.get_content_style_tools(),
            verbose=True,
            memory=False,
            llm=self.llm
        )
        
    @agent
    def manager_agent_impl(self) -> Agent:
        """管理Agent，负责任务协调和监控"""
        return Agent(
            config=self.agents_config['manager'],
            tools=[],
            verbose=True,
            memory=True,
            llm=self.llm
        )

    @task
    def platform_trend_decoding_task(self) -> Task:
        return Task(
            config=self.tasks_config['platform_trend_decoding_task'],
            callback=self.append_event_callback,
            output_json=TrendReport
        )
        
    @task
    def content_style_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config['content_style_analysis_task'],
            callback=self.append_event_callback,
            output_json=CompetitorMatrix
        )

    @crew
    def crew(self) -> Crew:
        """创建并配置竞品分析Crew"""
        manager = self.manager_agent or self.manager_agent_impl()
        
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            manager_agent=manager,
            process=Process.hierarchical,
            verbose=True,
            respect_context_window=True
        )

    def kickoff(self):
        """启动竞品分析流程"""
        if not self.crew():
            append_event(self.job_id, "CompetitorAnalysisAgent not set up")
            return "CompetitorAnalysisAgent not set up"
            
        append_event(self.job_id, "CompetitorAnalysisAgent's Task Started")
        try:
            results = self.crew().kickoff(inputs=self.input_data)
            append_event(self.job_id, "CompetitorAnalysisAgent's Task Complete")
            return results
        except Exception as e:
            append_event(self.job_id, f"An error occurred: {e}")
            return str(e) 