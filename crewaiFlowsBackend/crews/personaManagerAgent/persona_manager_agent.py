# 账号人设管理Agent (PersonaManagerAgent)
# 该模块为小红书多Agent自动化运营系统的"账号孪生管家"
# 负责账号基础信息管理、粉丝画像分析和策略配置

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool, ScrapeWebsiteTool
from typing import List, Dict, Any
from utils.models import AccountProfile, FansProfile
from utils.jobManager import append_event
# from utils.manager_agent import create_manager_agent
from utils.event_logger import create_event_logger
from tools.xiaohongshu_tools import XiaoHongShuAccountTool

@CrewBase
class PersonaManagerAgent:
    """
    账号人设管理Agent - 负责小红书账号档案管理、粉丝画像分析和策略制定
    """
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'
    
    def __init__(self, job_id: str, llm, input_data: Dict, manager_agent=None):
        """
        初始化账号人设管理Agent
        
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
        self.account_tool = XiaoHongShuAccountTool()

    def append_event_callback(self, task_output):
        append_event(self.job_id, task_output.raw)

    @agent
    def account_profiler(self) -> Agent:
        """账号档案专家Agent，负责账号基础信息与定位管理"""
        return Agent(
            config=self.agents_config['account_profiler'],
            tools=[XiaoHongShuAccountTool()],
            verbose=True,
            memory=False,
            llm=self.llm
        )
        
    @agent
    def audience_analyst(self) -> Agent:
        """受众分析师Agent，负责粉丝画像和互动分析"""
        return Agent(
            config=self.agents_config['audience_analyst'],
            tools=[XiaoHongShuAccountTool()],
            verbose=True,
            memory=False,
            llm=self.llm
        )

    @task
    def account_profile_creation_task(self) -> Task:
        return Task(
            config=self.tasks_config['account_profile_creation_task'],
            callback=self.append_event_callback,
            output_json=AccountProfile
        )
        
    @task
    def audience_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config['audience_analysis_task'],
            callback=self.append_event_callback,
            output_json=FansProfile
        )
        
    @task
    def strategy_recommendation_task(self) -> Task:
        return Task(
            config=self.tasks_config['strategy_recommendation_task'],
            callback=self.append_event_callback,
            output_json=None
        )

    @crew
    def crew(self) -> Crew:
        """创建并配置账号人设管理Crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            manager_agent=self.manager_agent,
            process=Process.hierarchical,
            verbose=True,
            respect_context_window=True
        )

    def kickoff(self):
        """启动账号人设管理流程"""
        if not self.crew():
            append_event(self.job_id, "PersonaManagerAgent not set up")
            return "PersonaManagerAgent not set up"
            
        append_event(self.job_id, "PersonaManagerAgent's Task Started")
        try:
            results = self.crew().kickoff(inputs=self.input_data)
            append_event(self.job_id, "PersonaManagerAgent's Task Complete")
            return results
        except Exception as e:
            append_event(self.job_id, f"An error occurred: {e}")
            return str(e)
            
    # 辅助方法，用于获取账号档案
    def get_account_profile(self, account_id: str) -> Dict[str, Any]:
        """
        获取账号档案信息
        
        Args:
            account_id: 小红书账号ID
            
        Returns:
            Dict[str, Any]: 包含账号档案的字典
        """
        # 实际实现中会从数据库或调用API获取
        basic_info = self.account_tool.fetch_account_info(account_id)
        fans_info = self.account_tool.analyze_fans_profile(account_id)
        
        return {
            "basic_info": basic_info,
            "fans_profile": fans_info,
            "persona": {
                "tone": "专业真诚，亲和力强",
                "style": "干货分享为主，穿插个人使用体验",
                "values": ["真实", "专业", "实用"],
                "topics": ["护肤品评测", "成分分析", "护肤技巧", "新品推荐"]
            },
            "operation_strategy": {
                "posting_schedule": "每周3-4次，21:00前后发布",
                "content_ratio": {"测评": 40, "教程": 30, "分享": 20, "互动": 10},
                "interaction_strategy": "重点回复专业问题，引导粉丝讨论产品体验"
            }
        }
        
    # 批量管理多个账号
    def manage_multiple_accounts(self, account_ids: List[str], strategy: Dict) -> Dict[str, Any]:
        """
        批量管理多个账号
        
        Args:
            account_ids: 小红书账号ID列表
            strategy: 统一策略配置
            
        Returns:
            Dict[str, Any]: 操作结果
        """
        results = {}
        for account_id in account_ids:
            # 获取账号信息
            account_info = self.get_account_profile(account_id)
            
            # 应用统一策略但保持个性化调整
            account_strategy = {
                **strategy,
                "account_id": account_id,
                "customization": f"根据账号'{account_info['basic_info']['name']}'特点定制"
            }
            
            # 更新账号策略
            update_success = self.account_tool.update_account_persona(
                account_id, 
                {"operation_strategy": account_strategy}
            )
            
            results[account_id] = {
                "success": update_success,
                "strategy_applied": account_strategy
            }
            
        return {
            "batch_operation": "account_strategy_update",
            "total_accounts": len(account_ids),
            "success_count": sum(1 for r in results.values() if r["success"]),
            "account_results": results
        } 