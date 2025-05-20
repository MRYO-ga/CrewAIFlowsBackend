# 账号人设管理Agent (PersonaManagerAgent)
# 该模块为小红书多Agent自动化运营系统的"账号孪生管家"
# 负责账号基础信息管理、人设定位和内容规划

import os
import yaml
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
    def __init__(self, job_id: str, llm, input_data: Dict, manager_agent=None):
        """
        初始化账号人设管理Agent
        
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
        self.tool_adapters = XiaoHongShuToolAdapters()
        
        # 加载配置文件
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.agents_config = self._load_yaml(os.path.join(current_dir, 'config', 'agents.yaml'))
        self.tasks_config = self._load_yaml(os.path.join(current_dir, 'config', 'tasks.yaml'))
        
        # 打印详细的输入数据结构，用于调试
        append_event(self.job_id, f"输入数据类型: {type(input_data)}")
        append_event(self.job_id, f"输入数据键值: {list(input_data.keys()) if isinstance(input_data, dict) else '非字典类型'}")
        append_event(self.job_id, f"加载的agents配置: {self.agents_config}")
        
        # 根据crew配置初始化所需的Agent和任务
        self.required_agents = []
        self.required_tasks = []
        
        # 检查是否存在crew配置
        if 'crew' in input_data and 'persona_management' in input_data['crew']:
            agent_config = input_data['crew']['persona_management']
            append_event(self.job_id, f"根据crew配置加载子Agent: {agent_config}, 类型: {type(agent_config)}")
            self.setup_agents_from_config(agent_config)

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
        # 创建账号基础信息撰写Agent
        if agent_type == "account_info_writer" or agent_type.find("account_info_writer") != -1:
            append_event(self.job_id, f"加载账号基础信息撰写Agent")
            self.required_agents.append(self.account_info_writer())
            self.required_tasks.append(self.account_info_creation_task())
        
        # 创建独特人设定位构建Agent
        if agent_type == "unique_persona_builder" or agent_type.find("unique_persona_builder") != -1:
            append_event(self.job_id, f"加载独特人设定位构建Agent")
            self.required_agents.append(self.unique_persona_builder())
            self.required_tasks.append(self.persona_development_task())
        
        # 创建主题内容方向规划Agent
        if agent_type == "content_direction_planner" or agent_type.find("content_direction_planner") != -1:
            append_event(self.job_id, f"加载主题内容方向规划Agent")
            self.required_agents.append(self.content_direction_planner())
            self.required_tasks.append(self.content_planning_task())

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

    def append_event_callback(self, task_output):
        append_event(self.job_id, task_output.raw)

    @agent
    def account_info_writer(self) -> Agent:
        """创建账号基础信息撰写Agent"""
        if not self.agents_config or 'account_info_writer' not in self.agents_config:
            append_event(self.job_id, "警告：找不到account_info_writer配置，使用默认配置")
            config = {
                'role': '小红书账号基础信息塑造专家',
                'goal': '撰写清晰、吸睛且符合平台规则的小红书账号基础信息',
                'backstory': '你是专注于小红书账号基础信息优化的资深专家'
            }
        else:
            config = self.agents_config['account_info_writer']
            
        return Agent(
            role=config['role'],
            goal=config['goal'],
            backstory=config['backstory'],
            tools=self.tool_adapters.get_account_profile_tools(),
            verbose=True,
            memory=False,
            llm=self.llm
        )

    @agent
    def unique_persona_builder(self) -> Agent:
        """创建独特人设定位构建Agent"""
        if not self.agents_config or 'unique_persona_builder' not in self.agents_config:
            append_event(self.job_id, "警告：找不到unique_persona_builder配置，使用默认配置")
            config = {
                'role': '小红书账号独特人设架构师',
                'goal': '构建独特且具有感染力的小红书账号人设定位',
                'backstory': '你是在小红书账号人设定位领域极具创造力的专家'
            }
        else:
            config = self.agents_config['unique_persona_builder']
            
        return Agent(
            role=config['role'],
            goal=config['goal'],
            backstory=config['backstory'],
            tools=self.tool_adapters.get_persona_builder_tools(),
            verbose=True,
            memory=False,
            llm=self.llm
        )

    @agent
    def content_direction_planner(self) -> Agent:
        """创建主题内容方向规划Agent"""
        if not self.agents_config or 'content_direction_planner' not in self.agents_config:
            append_event(self.job_id, "警告：找不到content_direction_planner配置，使用默认配置")
            config = {
                'role': '小红书主题内容战略规划师',
                'goal': '系统规划小红书账号主题内容方向',
                'backstory': '你是经验丰富的小红书内容运营规划大师'
            }
        else:
            config = self.agents_config['content_direction_planner']
            
        return Agent(
            role=config['role'],
            goal=config['goal'],
            backstory=config['backstory'],
            tools=self.tool_adapters.get_content_planner_tools(),
            verbose=True,
            memory=False,
            llm=self.llm
        )

    @task
    def account_info_creation_task(self) -> Task:
        """创建账号基础信息任务"""
        if not self.tasks_config or 'account_info_creation_task' not in self.tasks_config:
            append_event(self.job_id, "警告：找不到account_info_creation_task配置，使用默认配置")
            config = {
                'description': '创建和优化小红书账号基础信息',
                'expected_output': '完整的账号基础信息方案'
            }
        else:
            config = self.tasks_config['account_info_creation_task']
            
        return Task(
            description=config['description'],
            expected_output=config['expected_output'],
            callback=self.append_event_callback,
            output_json=AccountProfile
        )
        
    @task
    def persona_development_task(self) -> Task:
        """创建人设发展任务"""
        if not self.tasks_config or 'persona_development_task' not in self.tasks_config:
            append_event(self.job_id, "警告：找不到persona_development_task配置，使用默认配置")
            config = {
                'description': '构建独特的账号人设定位',
                'expected_output': '详细的账号人设定位方案'
            }
        else:
            config = self.tasks_config['persona_development_task']
            
        return Task(
            description=config['description'],
            expected_output=config['expected_output'],
            callback=self.append_event_callback,
            output_json=AccountProfile
        )
        
    @task
    def content_planning_task(self) -> Task:
        """创建内容规划任务"""
        if not self.tasks_config or 'content_planning_task' not in self.tasks_config:
            append_event(self.job_id, "警告：找不到content_planning_task配置，使用默认配置")
            config = {
                'description': '规划账号内容发展方向',
                'expected_output': '完整的内容规划方案'
            }
        else:
            config = self.tasks_config['content_planning_task']
            
        return Task(
            description=config['description'],
            expected_output=config['expected_output'],
            callback=self.append_event_callback,
            output_json=ContentPlan
        )

    @crew
    def crew(self) -> Crew:
        """创建并配置账号人设管理Crew"""
        # 根据是否有特定的Agent要求，确定使用哪些Agent
        if self.required_agents:
            agents_list = self.required_agents
        else:
            agents_list = self.agents
            
        # 根据是否有特定的任务要求，确定使用哪些任务
        tasks_to_use = self.required_tasks if self.required_tasks else self.tasks
        
        append_event(self.job_id, f"配置Crew - 使用{len(agents_list)}个Agent和{len(tasks_to_use)}个任务")
        
        # 直接使用列表形式指定agents
        return Crew(
            agents=[*agents_list],
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
                self.account_info_creation_task(),
                self.persona_development_task(),
                self.content_planning_task()
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
                    self.account_info_writer(),
                    self.unique_persona_builder(),
                    self.content_direction_planner()
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
        使用指定的agents启动账号人设管理流程
        
        Args:
            *agents: 要使用的Agent实例
            
        Returns:
            运行结果
        """
        crew = self.create_personalized_crew(*agents)
        
        append_event(self.job_id, "启动自定义Agents的PersonaManagerAgent任务")
        try:
            results = crew.kickoff(inputs=self.input_data)
            append_event(self.job_id, "自定义Agents的PersonaManagerAgent任务完成")
            return results
        except Exception as e:
            append_event(self.job_id, f"执行过程中发生错误: {e}")
            return str(e)

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