# 竞品分析Agent (CompetitorAnalysisAgent)
# 该模块为小红书多Agent自动化运营系统的"情报中心"
# 负责从竞品数据中提取可复用的运营公式和爆款策略

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from typing import List, Dict, Any
from utils.models import CompetitorAnalysis, HotContentTemplate
from utils.jobManager import append_event
# from utils.manager_agent import create_manager_agent
from utils.event_logger import create_event_logger
from tools.xiaohongshu_tools import XiaoHongShuCompetitorTool

@CrewBase
class CompetitorAnalysisAgent:
    """
    竞品分析Agent - 负责分析小红书竞品账号和内容策略
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
        self.competitor_tool = XiaoHongShuCompetitorTool()

    def append_event_callback(self, task_output):
        append_event(self.job_id, task_output.raw)

    @agent
    def market_analyst(self) -> Agent:
        """市场分析师Agent，负责市场趋势和竞品账号概况分析"""
        return Agent(
            role="market_analyst",
            goal=(
                "Analyze market trends and competitor accounts on Xiaohongshu. "
                "Identify target audience demographics and market positioning. "
                "When using any tool, ensure the Action Input is a clean Python dict."
            ),
            backstory="An expert in social media market research and trend analysis with deep knowledge of Xiaohongshu platform.",
            verbose=True,
            llm=self.llm,
            tools=[self.competitor_tool],
        )
        
    @agent
    def content_analyzer(self) -> Agent:
        """内容分析师Agent，负责分析爆款内容结构和特点"""
        return Agent(
            role="content_analyzer",
            goal=(
                "Dissect viral content on Xiaohongshu to extract reusable patterns. "
                "Analyze titles, tags, image styles, and content structure. "
                "Provide actionable insights for content creation."
            ),
            backstory="A content strategist specialized in analyzing viral social media content patterns.",
            verbose=True,
            llm=self.llm,
            tools=[self.competitor_tool],
        )

    @task
    def competitor_search_task(self) -> Task:
        return Task(
            config=self.tasks_config['competitor_search_task'],
            callback=self.append_event_callback,
            output_json=None
        )
        
    @task
    def competitor_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config['competitor_analysis_task'],
            callback=self.append_event_callback,
            output_json=CompetitorAnalysis,
        )
        
    @task
    def viral_content_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config['viral_content_analysis_task'],
            callback=self.append_event_callback,
            output_json=HotContentTemplate
        )

    @crew
    def crew(self) -> Crew:
        """创建并配置竞品分析Crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            manager_agent=self.manager_agent,
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
            
    # 辅助方法，用于获取竞品分析结果
    def get_competitor_insights(self) -> Dict[str, Any]:
        """
        获取竞品分析的核心洞察
        
        Returns:
            Dict[str, Any]: 包含竞品分析结果的字典
        """
        # 实际实现中会从数据库或之前的结果中获取
        return {
            "top_competitors": [
                {"name": "美妆达人A", "followers": 50000, "engagement_rate": 5.2, "content_focus": "护肤测评"},
                {"name": "护肤专家B", "followers": 35000, "engagement_rate": 6.8, "content_focus": "成分分析"},
            ],
            "content_templates": [
                {"title_pattern": "{产品名}+{效果}+{使用感受}", "example": "这款面霜我已经用了3年了，效果太好了"},
                {"title_pattern": "{数字}+{问题}+{解决方案}", "example": "5个护肤误区，你中了几个？"},
            ],
            "posting_strategy": {
                "best_time": ["21:00-22:00", "12:00-13:00"],
                "optimal_frequency": "3-4次/周",
                "best_formats": ["产品测评", "使用教程", "成分分析"]
            }
        } 