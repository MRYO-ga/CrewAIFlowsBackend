# 发布互动Agent (PublicationAgent)
# 该模块为小红书多Agent自动化运营系统的"执行者"
# 负责自动发布内容并收集互动数据

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from typing import List, Dict, Any
from datetime import datetime, timedelta
from utils.models import PublicationResult, InteractionStats
from utils.jobManager import append_event
# from utils.manager_agent import create_manager_agent
from utils.event_logger import create_event_logger
from tools.xiaohongshu_tools import XiaoHongShuPublicationTool

@CrewBase
class PublicationAgent:
    """
    发布互动Agent - 负责小红书内容发布与互动数据收集
    """
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'
    
    def __init__(self, job_id: str, llm, input_data: Dict, manager_agent=None):
        """
        初始化发布互动Agent
        
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
        self.publication_tool = XiaoHongShuPublicationTool()

    def append_event_callback(self, task_output):
        append_event(self.job_id, task_output.raw)

    @agent
    def publication_specialist(self) -> Agent:
        """发布专家Agent，负责优化发布时间和策略"""
        return Agent(
            config=self.agents_config['publication_specialist'],
            tools=[self.publication_tool],
            verbose=True,
            llm=self.llm
        )
        
    @agent
    def engagement_analyst(self) -> Agent:
        """互动分析师Agent，负责分析互动数据和优化策略"""
        return Agent(
            config=self.agents_config['engagement_analyst'],
            tools=[self.publication_tool],
            verbose=True,
            memory=False,
            llm=self.llm
        )
        
    @agent
    def community_manager(self) -> Agent:
        """社区管理Agent，负责评论回复和互动管理"""
        return Agent(
            config=self.agents_config['community_manager'],
            tools=[self.publication_tool],
            verbose=True,
            memory=False,
            llm=self.llm
        )

    @task
    def publication_strategy_task(self) -> Task:
        return Task(
            config=self.tasks_config['publication_strategy_task'],
            callback=self.append_event_callback,
            output_json=None
        )
        
    @task
    def content_publication_task(self) -> Task:
        return Task(
            config=self.tasks_config['content_publication_task'],
            callback=self.append_event_callback,
            output_json=PublicationResult
        )
        
    @task
    def engagement_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config['engagement_analysis_task'],
            callback=self.append_event_callback,
            output_json=InteractionStats
        )
        
    @task
    def comment_response_strategy_task(self) -> Task:
        return Task(
            config=self.tasks_config['comment_response_strategy_task'],
            callback=self.append_event_callback,
            output_json=None
        )

    @crew
    def crew(self) -> Crew:
        """创建并配置发布互动Crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            manager_agent=self.manager_agent,
            process=Process.hierarchical,
            verbose=True,
            respect_context_window=True
        )

    def kickoff(self):
        """启动发布互动流程"""
        if not self.crew():
            append_event(self.job_id, "PublicationAgent not set up")
            return "PublicationAgent not set up"
            
        append_event(self.job_id, "PublicationAgent's Task Started")
        try:
            results = self.crew().kickoff(inputs=self.input_data)
            append_event(self.job_id, "PublicationAgent's Task Complete")
            return results
        except Exception as e:
            append_event(self.job_id, f"An error occurred: {e}")
            return str(e)
            
    # 辅助方法：直接发布内容
    def publish_content(self, account_id: str, content: Dict, publish_time: str = None) -> Dict[str, Any]:
        """
        发布内容到小红书
        
        Args:
            account_id: 小红书账号ID
            content: 内容数据，包含标题、正文、图片等
            publish_time: 发布时间，格式为"YYYY-MM-DD HH:MM:SS"，为None时立即发布
            
        Returns:
            Dict[str, Any]: 发布结果
        """
        # 检查内容必要字段
        if not content.get("title"):
            return {"success": False, "error": "内容缺少标题"}
            
        if not content.get("content_sections"):
            return {"success": False, "error": "内容缺少正文"}
            
        # 调用发布工具
        result = self.publication_tool.schedule_publication(
            account_id=account_id,
            content=content,
            publish_time=publish_time,
            tags=content.get("tags", [])
        )
        
        return {
            "success": True,
            "publication_id": result["publication_id"],
            "status": result["status"],
            "publish_time": result["publish_time"],
            "url": result["url"]
        }
    
    # 辅助方法：获取互动数据
    def get_interaction_data(self, publication_id: str) -> Dict[str, Any]:
        """
        获取内容互动数据
        
        Args:
            publication_id: 发布ID
            
        Returns:
            Dict[str, Any]: 互动数据
        """
        # 获取基础互动数据
        interaction_data = self.publication_tool.collect_interaction_data(publication_id)
        
        # 获取评论数据
        comments = self.publication_tool.retrieve_comments(publication_id)
        
        # 整合数据
        return {
            "publication_id": publication_id,
            "collection_time": interaction_data["collection_time"],
            "stats": interaction_data["stats"],
            "comments": {
                "total_count": len(comments),
                "replied_count": sum(1 for c in comments if c["has_replied"]),
                "popular_comments": sorted(comments, key=lambda x: x["likes"], reverse=True)[:5]
            },
            "analysis": {
                "engagement_rate": interaction_data["stats"]["engagement_rate"],
                "trending_keywords": interaction_data["trending_keywords"],
                "audience_growth": interaction_data["audience_breakdown"]["new_followers"]
            }
        }
    
    # 批量发布管理
    def manage_bulk_publications(self, account_id: str, contents: List[Dict], schedule_strategy: str = "optimal") -> Dict[str, Any]:
        """
        批量管理内容发布
        
        Args:
            account_id: 小红书账号ID
            contents: 内容列表，每个内容包含标题、正文、图片等
            schedule_strategy: 调度策略，"optimal"为优化发布时间，"evenly"为均匀分布
            
        Returns:
            Dict[str, Any]: 批量发布结果
        """
        results = []
        
        # 确定发布时间
        now = datetime.now()
        if schedule_strategy == "optimal":
            # 优化发布时间 - 实际应用中会基于账号数据分析最佳发布时间
            optimal_hours = [21, 12, 19, 8, 22]  # 示例最佳发布时段
            publish_times = []
            
            for i, _ in enumerate(contents):
                day_offset = i // len(optimal_hours)
                hour_index = i % len(optimal_hours)
                publish_time = now + timedelta(days=day_offset)
                publish_time = publish_time.replace(hour=optimal_hours[hour_index], minute=0, second=0)
                publish_times.append(publish_time.strftime("%Y-%m-%d %H:%M:%S"))
        else:
            # 均匀分布 - 每天固定时间发布
            publish_times = []
            for i, _ in enumerate(contents):
                publish_time = now + timedelta(days=i)
                publish_time = publish_time.replace(hour=20, minute=0, second=0)  # 每天晚上8点
                publish_times.append(publish_time.strftime("%Y-%m-%d %H:%M:%S"))
        
        # 执行发布
        for i, content in enumerate(contents):
            # 调用发布工具
            result = self.publish_content(
                account_id=account_id,
                content=content,
                publish_time=publish_times[i]
            )
            
            results.append({
                "content_id": content.get("content_id", f"content_{i+1}"),
                "title": content.get("title", ""),
                "publish_time": publish_times[i],
                "status": result.get("status", "failed"),
                "publication_id": result.get("publication_id", ""),
                "url": result.get("url", "")
            })
            
        return {
            "batch_operation": "bulk_publication",
            "account_id": account_id,
            "total_contents": len(contents),
            "schedule_strategy": schedule_strategy,
            "start_date": now.strftime("%Y-%m-%d"),
            "end_date": (now + timedelta(days=len(contents)//len(optimal_hours) if schedule_strategy == "optimal" else len(contents))).strftime("%Y-%m-%d"),
            "publications": results
        } 