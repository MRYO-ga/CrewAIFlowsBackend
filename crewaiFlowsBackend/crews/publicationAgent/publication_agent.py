# 发布互动Agent (PublicationAgent)
# 该模块为小红书多Agent自动化运营系统的"执行者"
# 负责自动发布内容并收集互动数据

import os
import yaml
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
    def __init__(self, job_id: str, llm, input_data: Dict, manager_agent=None):
        """
        初始化发布互动Agent
        
        Args:
            job_id: 作业ID
            llm: 大语言模型实例
            input_data: 输入数据
            manager_agent: 管理Agent实例
        """
        # 先调用父类的初始化
        super().__init__()

        self.job_id = job_id
        self.llm = llm
        self.input_data = input_data
        self.manager_agent = manager_agent
        self.event_logger = create_event_logger(job_id)
        self.publication_tool = XiaoHongShuPublicationTool()
        
        # 加载配置文件
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.agents_config = self._load_yaml(os.path.join(current_dir, 'config', 'agents.yaml'))
        self.tasks_config = self._load_yaml(os.path.join(current_dir, 'config', 'tasks.yaml'))
        
        # 根据crew配置初始化所需的Agent和任务
        self.required_agents = []
        self.required_tasks = []
        
        # 检查是否存在crew配置
        if 'crew' in input_data and 'publication' in input_data['crew']:
            agent_config = input_data['crew']['publication']
            append_event(self.job_id, f"根据crew配置加载子Agent: {agent_config}, 类型: {type(agent_config)}")
            self.setup_agents_from_config(agent_config)

    def _load_yaml(self, file_path: str) -> Dict:
        """
        加载YAML配置文件
        
        Args:
            file_path: YAML文件路径
            
        Returns:
            Dict: 配置数据
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                append_event(self.job_id, f"成功加载配置文件 {file_path}")
                return config
        except Exception as e:
            append_event(self.job_id, f"加载配置文件失败 {file_path}: {str(e)}")
            return {}

    def setup_agents_from_config(self, agent_config):
        """
        根据不同格式的配置设置所需的Agent和任务
        
        支持三种格式:
        1. 字符串格式 - "agent_type1,agent_type2"
        2. 列表格式 - ["agent_type1", "agent_type2"]
        3. 字典格式 - {"agent_type1": True, "agent_type2": False}
        
        Args:
            agent_config: Agent配置，可以是字符串、列表或字典
        """
        # 处理字典格式
        if isinstance(agent_config, dict):
            append_event(self.job_id, f"处理字典格式配置: {agent_config}")
            for agent_name, is_enabled in agent_config.items():
                if is_enabled and isinstance(agent_name, str):
                    self._add_agent_by_type(agent_name)
            return
            
        # 统一处理字符串或列表格式
        agent_types = []
        
        # 处理字符串格式
        if isinstance(agent_config, str):
            # 如果字符串包含逗号，则按逗号分隔
            if "," in agent_config:
                agent_types = [t.strip() for t in agent_config.split(",")]
                append_event(self.job_id, f"检测到多个子Agent类型(字符串): {agent_types}")
            else:
                agent_types = [agent_config]
        # 处理列表格式
        elif isinstance(agent_config, list):
            agent_types = agent_config
            append_event(self.job_id, f"检测到子Agent类型列表: {agent_types}")
        else:
            append_event(self.job_id, f"不支持的配置格式: {type(agent_config)}")
            return
            
        # 遍历所有需要的Agent类型并添加
        for agent_type in agent_types:
            if not isinstance(agent_type, str):
                append_event(self.job_id, f"跳过非字符串类型的Agent配置: {agent_type}")
                continue
            
            self._add_agent_by_type(agent_type)
    
    def _add_agent_by_type(self, agent_type: str):
        """
        根据Agent类型添加相应的Agent和任务
        
        Args:
            agent_type: Agent类型名称
        """
        # 发布专家Agent
        if agent_type == "publication_specialist" or agent_type.find("publication_specialist") != -1:
            append_event(self.job_id, f"加载发布专家Agent")
            self.required_agents.append(self.publication_specialist())
            self.required_tasks.append(self.publication_strategy_task())
            self.required_tasks.append(self.content_publication_task())
        
        # 互动分析师Agent
        if agent_type == "engagement_analyst" or agent_type.find("engagement_analyst") != -1:
            append_event(self.job_id, f"加载互动分析师Agent")
            self.required_agents.append(self.engagement_analyst())
            self.required_tasks.append(self.engagement_analysis_task())
        
        # 社区管理Agent
        if agent_type == "community_manager" or agent_type.find("community_manager") != -1:
            append_event(self.job_id, f"加载社区管理Agent")
            self.required_agents.append(self.community_manager())
            self.required_tasks.append(self.comment_response_strategy_task())

    def append_event_callback(self, task_output):
        append_event(self.job_id, task_output.raw)

    @agent
    def publication_specialist(self) -> Agent:
        """发布专家Agent，负责优化发布时间和策略"""
        if not self.agents_config or 'publication_specialist' not in self.agents_config:
            append_event(self.job_id, "警告：找不到publication_specialist配置，使用默认配置")
            config = {
                'role': '小红书内容发布专家',
                'goal': '确保内容以最佳方式发布',
                'backstory': '你是负责小红书内容发布策略的专家'
            }
        else:
            config = self.agents_config['publication_specialist']
            
        return Agent(
            role=config['role'],
            goal=config['goal'],
            backstory=config['backstory'],
            tools=[self.publication_tool],
            verbose=True,
            llm=self.llm
        )
        
    @agent
    def engagement_analyst(self) -> Agent:
        """互动分析师Agent，负责分析互动数据和优化策略"""
        if not self.agents_config or 'engagement_analyst' not in self.agents_config:
            append_event(self.job_id, "警告：找不到engagement_analyst配置，使用默认配置")
            config = {
                'role': '互动数据分析专家',
                'goal': '分析内容互动数据，提供优化建议',
                'backstory': '你是专注于社交媒体互动数据分析的专家'
            }
        else:
            config = self.agents_config['engagement_analyst']
            
        return Agent(
            role=config['role'],
            goal=config['goal'],
            backstory=config['backstory'],
            tools=[self.publication_tool],
            verbose=True,
            memory=False,
            llm=self.llm
        )
        
    @agent
    def community_manager(self) -> Agent:
        """社区管理Agent，负责评论回复和互动管理"""
        if not self.agents_config or 'community_manager' not in self.agents_config:
            append_event(self.job_id, "警告：找不到community_manager配置，使用默认配置")
            config = {
                'role': '社群运营专家',
                'goal': '维护良好的粉丝互动关系',
                'backstory': '你是经验丰富的社群运营专家'
            }
        else:
            config = self.agents_config['community_manager']
            
        return Agent(
            role=config['role'],
            goal=config['goal'],
            backstory=config['backstory'],
            tools=[self.publication_tool],
            verbose=True,
            memory=False,
            llm=self.llm
        )

    @task
    def publication_strategy_task(self) -> Task:
        """发布策略任务"""
        if not self.tasks_config or 'publication_strategy_task' not in self.tasks_config:
            append_event(self.job_id, "警告：找不到publication_strategy_task配置，使用默认配置")
            config = {
                'description': '制定内容发布策略，确定最佳发布时间和标签',
                'expected_output': '一份详细的发布策略建议'
            }
        else:
            config = self.tasks_config['publication_strategy_task']
            
        return Task(
            description=config['description'],
            expected_output=config['expected_output'],
            callback=self.append_event_callback,
            output_json=None
        )
        
    @task
    def content_publication_task(self) -> Task:
        """内容发布任务"""
        if not self.tasks_config or 'content_publication_task' not in self.tasks_config:
            append_event(self.job_id, "警告：找不到content_publication_task配置，使用默认配置")
            config = {
                'description': '按照既定策略执行内容发布',
                'expected_output': '发布结果报告'
            }
        else:
            config = self.tasks_config['content_publication_task']
            
        return Task(
            description=config['description'],
            expected_output=config['expected_output'],
            callback=self.append_event_callback,
            output_json=PublicationResult
        )
        
    @task
    def engagement_analysis_task(self) -> Task:
        """互动分析任务"""
        if not self.tasks_config or 'engagement_analysis_task' not in self.tasks_config:
            append_event(self.job_id, "警告：找不到engagement_analysis_task配置，使用默认配置")
            config = {
                'description': '收集并分析内容的互动数据',
                'expected_output': '完整的互动数据统计报告'
            }
        else:
            config = self.tasks_config['engagement_analysis_task']
            
        return Task(
            description=config['description'],
            expected_output=config['expected_output'],
            callback=self.append_event_callback,
            output_json=InteractionStats
        )
        
    @task
    def comment_response_strategy_task(self) -> Task:
        """评论回复策略任务"""
        if not self.tasks_config or 'comment_response_strategy_task' not in self.tasks_config:
            append_event(self.job_id, "警告：找不到comment_response_strategy_task配置，使用默认配置")
            config = {
                'description': '制定评论回复策略',
                'expected_output': '详细的评论回复策略指南'
            }
        else:
            config = self.tasks_config['comment_response_strategy_task']
            
        return Task(
            description=config['description'],
            expected_output=config['expected_output'],
            callback=self.append_event_callback,
            output_json=None
        )

    @crew
    def crew(self) -> Crew:
        """创建并配置发布互动Crew"""
        # 根据是否有特定的Agent要求，确定使用哪些Agent
        if self.required_agents:
            agents_list = self.required_agents
        else:
            agents_list = self.agents
            
        # 根据是否有特定的任务要求，确定使用哪些任务
        tasks_to_use = self.required_tasks if self.required_tasks else self.tasks
        
        append_event(self.job_id, f"配置发布互动Crew - 使用{len(agents_list)}个Agent和{len(tasks_to_use)}个任务")
        
        return Crew(
            agents=agents_list,
            tasks=tasks_to_use,
            manager_agent=self.manager_agent,
            process=Process.hierarchical,
            verbose=True,
            respect_context_window=True
        )

    def create_personalized_crew(self, *agents):
        """
        创建自定义Crew，可以指定任意数量的agents
        
        Args:
            *agents: 任意数量的Agent实例
            
        Returns:
            Crew: 配置好的Crew实例
        """
        # 确定要使用的任务列表
        if hasattr(self, 'required_tasks') and self.required_tasks:
            tasks_to_use = self.required_tasks
        elif hasattr(self, 'tasks') and self.tasks:
            tasks_to_use = self.tasks
        else:
            # 如果没有任务，创建默认任务
            append_event(self.job_id, "未找到任务列表，创建默认任务")
            tasks_to_use = [
                self.publication_strategy_task(),
                self.content_publication_task(),
                self.engagement_analysis_task(),
                self.comment_response_strategy_task()
            ]
        
        # 如果没有提供agents，则使用默认的
        if not agents:
            if hasattr(self, 'required_agents') and self.required_agents:
                agents_to_use = self.required_agents
                append_event(self.job_id, f"使用required_agents配置Crew - {len(agents_to_use)}个Agent")
            elif hasattr(self, 'agents') and self.agents:
                agents_to_use = self.agents
                append_event(self.job_id, f"使用agents配置Crew - {len(agents_to_use)}个Agent")
            else:
                # 如果没有agent，创建默认agents
                append_event(self.job_id, "未找到agent列表，创建默认agents")
                agents_to_use = [
                    self.publication_specialist(),
                    self.engagement_analyst(),
                    self.community_manager()
                ]
        else:
            agents_to_use = agents
            append_event(self.job_id, f"使用自定义Agents配置Crew - {len(agents_to_use)}个Agent")
        
        append_event(self.job_id, f"最终配置: {len(agents_to_use)}个Agent, {len(tasks_to_use)}个任务")
        
        return Crew(
            agents=list(agents_to_use),
            tasks=tasks_to_use,
            manager_agent=self.manager_agent,
            process=Process.hierarchical,
            verbose=True,
            respect_context_window=True
        )
        
    def kickoff_with_agents(self, *agents):
        """
        使用指定的agents启动发布互动流程
        
        Args:
            *agents: 要使用的Agent实例
            
        Returns:
            运行结果
        """
        crew = self.create_personalized_crew(*agents)
        
        append_event(self.job_id, "启动自定义Agents的PublicationAgent任务")
        try:
            results = crew.kickoff(inputs=self.input_data)
            append_event(self.job_id, "自定义Agents的PublicationAgent任务完成")
            return results
        except Exception as e:
            append_event(self.job_id, f"执行过程中发生错误: {e}")
            return str(e)

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