# 账号人设管理Agent (PersonaManagerAgent)
# 该模块为小红书多Agent自动化运营系统的"账号孪生管家"
# 负责账号基础信息管理、人设定位和内容规划

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from typing import List, Dict, Any
from utils.models import AccountProfile, ContentPlan
from utils.jobManager import append_event
from utils.event_logger import create_event_logger
from tools.xiaohongshu_tool_adapters import XiaoHongShuToolAdapters

@CrewBase
class PersonaManagerAgent:
    """
    账号人设管理Agent - 负责小红书账号基础信息、人设定位和内容规划
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
        self.tool_adapters = XiaoHongShuToolAdapters()

    def append_event_callback(self, task_output):
        append_event(self.job_id, task_output.raw)

    @agent
    def account_info_writer(self) -> Agent:
        """账号基础信息撰写Agent，负责账号基础信息优化"""
        return Agent(
            config=self.agents_config['account_info_writer'],
            tools=self.tool_adapters.get_account_profile_tools(),
            verbose=True,
            memory=False,
            llm=self.llm
        )
        
    @agent
    def unique_persona_builder(self) -> Agent:
        """独特人设定位构建Agent，负责账号人设塑造"""
        return Agent(
            config=self.agents_config['unique_persona_builder'],
            tools=self.tool_adapters.get_persona_builder_tools(),
            verbose=True,
            memory=False,
            llm=self.llm
        )
        
    @agent
    def content_direction_planner(self) -> Agent:
        """主题内容方向规划Agent，负责内容策略规划"""
        return Agent(
            config=self.agents_config['content_direction_planner'],
            tools=self.tool_adapters.get_content_planner_tools(),
            verbose=True,
            memory=False,
            llm=self.llm
        )

    @task
    def account_info_creation_task(self) -> Task:
        return Task(
            config=self.tasks_config['account_info_creation_task'],
            callback=self.append_event_callback,
            output_json=AccountProfile
        )
        
    @task
    def persona_development_task(self) -> Task:
        return Task(
            config=self.tasks_config['persona_development_task'],
            callback=self.append_event_callback,
            output_json=AccountProfile
        )
        
    @task
    def content_planning_task(self) -> Task:
        return Task(
            config=self.tasks_config['content_planning_task'],
            callback=self.append_event_callback,
            output_json=ContentPlan
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
            
    def get_account_profile(self, account_id: str) -> Dict[str, Any]:
        """
        获取账号档案信息
        
        Args:
            account_id: 小红书账号ID
            
        Returns:
            Dict[str, Any]: 包含账号档案的字典
        """
        basic_info = self.tool_adapters.fetch_account_info(account_id)
        
        return {
            "basic_info": basic_info,
            "persona": {
                "account_name": "专业护肤测评师",
                "bio": "8年护肤经验 | 成分党 | 专业测评\n只分享真实使用体验，拒绝虚假种草",
                "avatar_style": "专业且亲和的形象展示",
                "key_tags": ["护肤测评", "成分分析", "真实体验"],
                "tone_style": "专业、真诚、亲和"
            },
            "content_strategy": {
                "main_topics": ["护肤品测评", "成分科普", "护肤方法", "产品推荐"],
                "content_ratio": {
                    "测评报告": 40,
                    "成分解析": 30,
                    "护肤教程": 20,
                    "热点话题": 10
                },
                "posting_schedule": "每周3-4次，优先在20:00-22:00发布",
                "interaction_strategy": "重点回复专业问题，组织线上互动活动"
            }
        }
        
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
            account_info = self.get_account_profile(account_id)
            
            account_strategy = {
                **strategy,
                "account_id": account_id,
                "customization": f"根据账号'{account_info['basic_info']['name']}'特点定制"
            }
            
            update_success = self.tool_adapters.update_account_persona(
                account_id, 
                {"persona": account_strategy}
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