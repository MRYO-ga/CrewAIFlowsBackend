# 内容生成Agent (ContentCreationAgent)
# 该模块为小红书多Agent自动化运营系统的"内容创作引擎"
# 负责高质量小红书内容生成

import os
import yaml
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from typing import List, Dict, Any
from utils.models import ContentCreation
from utils.jobManager import append_event
from utils.event_logger import create_event_logger
from tools.xiaohongshu_tool_adapters import XiaoHongShuToolAdapters

@CrewBase
class ContentCreationAgent:
    """
    内容生成Agent - 负责小红书高质量内容创作
    """
    def __init__(self, job_id: str, llm, input_data: Dict, manager_agent=None):
        """
        初始化内容生成Agent
        
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

        # 根据crew配置初始化所需的Agent和任务
        self.required_agents = []
        self.required_tasks = []
        
        # 检查是否存在crew配置
        if 'crew' in input_data and 'content_creation' in input_data['crew']:
            agent_config = input_data['crew']['content_creation']
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
        # 内容创建者Agent
        if agent_type == "content_creator" or agent_type.find("content_creator") != -1:
            append_event(self.job_id, f"加载内容创建者Agent")
            self.required_agents.append(self.content_creator())
            self.required_tasks.append(self.content_creation_task())
        
        # 如果未来添加更多类型的内容创建者，可以在这里扩展
        if agent_type == "viral_content_creator" or agent_type.find("viral_content_creator") != -1:
            append_event(self.job_id, f"加载爆款内容创建者Agent")
            self.required_agents.append(self.content_creator())
            self.required_tasks.append(self.content_creation_task())

    def append_event_callback(self, task_output):
        append_event(self.job_id, task_output.raw)

    @agent
    def content_creator(self) -> Agent:
        """内容创建者Agent，负责生成高质量内容"""
        if not self.agents_config or 'content_creator' not in self.agents_config:
            append_event(self.job_id, "警告：找不到content_creator配置，使用默认配置")
            config = {
                'role': '小红书内容创作专家',
                'goal': '创作引人入胜的小红书内容',
                'backstory': '你是一位资深的小红书内容创作者'
            }
        else:
            config = self.agents_config['content_creator']
            
        return Agent(
            role=config['role'],
            goal=config['goal'],
            backstory=config['backstory'],
            tools=self.tool_adapters.get_content_creator_tools(),
            verbose=True,
            memory=False,
            llm=self.llm
        )

    @task
    def content_creation_task(self) -> Task:
        """内容创建任务"""
        if not self.tasks_config or 'content_creation_task' not in self.tasks_config:
            append_event(self.job_id, "警告：找不到content_creation_task配置，使用默认配置")
            config = {
                'description': '创建高质量小红书内容',
                'expected_output': '完整的内容创作方案'
            }
        else:
            config = self.tasks_config['content_creation_task']
            
        return Task(
            description=config['description'],
            expected_output=config['expected_output'],
            callback=self.append_event_callback,
            output_json=ContentCreation
        )

    @crew
    def crew(self) -> Crew:
        """创建并配置内容生成Crew"""
        # 根据是否有特定的Agent要求，确定使用哪些Agent
        if self.required_agents:
            agents_list = self.required_agents
        else:
            agents_list = self.agents
            
        # 根据是否有特定的任务要求，确定使用哪些任务
        tasks_to_use = self.required_tasks if self.required_tasks else self.tasks
        
        append_event(self.job_id, f"配置内容创建Crew - 使用{len(agents_list)}个Agent和{len(tasks_to_use)}个任务")
        
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
                self.content_creation_task()
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
                    self.content_creator()
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
        使用指定的agents启动内容生成流程
        
        Args:
            *agents: 要使用的Agent实例
            
        Returns:
            运行结果
        """
        crew = self.create_personalized_crew(*agents)
        
        append_event(self.job_id, "启动自定义Agents的ContentCreationAgent任务")
        try:
            results = crew.kickoff(inputs=self.input_data)
            append_event(self.job_id, "自定义Agents的ContentCreationAgent任务完成")
            return results
        except Exception as e:
            append_event(self.job_id, f"执行过程中发生错误: {e}")
            return str(e)

    def kickoff(self):
        """启动内容生成流程"""
        if not self.crew():
            append_event(self.job_id, "ContentCreationAgent not set up")
            return "ContentCreationAgent not set up"
            
        append_event(self.job_id, "ContentCreationAgent's Task Started")
        try:
            results = self.crew().kickoff(inputs=self.input_data)
            append_event(self.job_id, "ContentCreationAgent's Task Complete")
            return results
        except Exception as e:
            append_event(self.job_id, f"An error occurred: {e}")
            return str(e)

    # 辅助方法，用于获取生成的内容
    def get_generated_content(self, content_id: str = None) -> Dict[str, Any]:
        """
        获取生成的内容
        
        Args:
            content_id: 内容ID，为None时返回最新生成的内容
            
        Returns:
            Dict[str, Any]: 包含生成内容的字典
        """
        # 实际实现中会从数据库或前一步结果中获取
        # 示例返回数据
        return {
            "content_id": content_id or "content_001",
            "title": "这款面霜我已经用了3年了，效果太好了",
            "content_sections": [
                {
                    "type": "opening",
                    "text": "大家好，今天要给大家分享一款我用了3年都在回购的面霜，它就是...[正文开头]"
                },
                {
                    "type": "product_intro",
                    "text": "这款面霜的成分非常简单，主打xx功效，特别适合xx肤质...[产品介绍]"
                },
                {
                    "type": "experience",
                    "text": "我是油性肌肤，用了它之后感觉...[使用体验]"
                },
                {
                    "type": "comparison",
                    "text": "相比市面上同类产品，它的优势在于...[对比分析]"
                },
                {
                    "type": "closing",
                    "text": "如果你也是xx肤质，建议可以尝试一下，不知道你们用过后感觉如何？欢迎评论区留言...[结尾互动]"
                }
            ],
            "tags": ["面霜", "护肤", "口碑好物", "测评"],
            "image_recommendations": [
                {
                    "position": "cover",
                    "description": "产品正面特写，背景简洁，暖色调",
                    "style": "高级感"
                },
                {
                    "position": "section_2",
                    "description": "产品成分表截图，标注重点成分",
                    "style": "专业清晰"
                },
                {
                    "position": "section_3",
                    "description": "使用前后对比图，分屏展示",
                    "style": "真实记录"
                }
            ],
            "compliance_check": {
                "is_compliant": True,
                "detected_sensitive_words": [],
                "recommendation": "内容符合平台规范"
            }
        }
        
    # 批量生成多个内容
    def batch_generate_content(self, topics: List[Dict], account_id: str) -> Dict[str, Any]:
        """
        批量生成多个内容
        
        Args:
            topics: 话题列表，每个话题包含关键词、类型等信息
            account_id: 账号ID，用于获取账号人设
            
        Returns:
            Dict[str, Any]: 批量生成结果
        """
        results = []
        for topic in topics:
            # 构建输入数据
            topic_input = {
                "account_id": account_id,
                "topic": topic["topic"],
                "keywords": topic["keywords"],
                "content_type": topic.get("content_type", "测评"),
                "target_emotion": topic.get("target_emotion", "惊喜"),
            }
            
            # 模拟生成过程
            content = {
                "topic": topic["topic"],
                "title": f"关于{topic['topic']}的一些真实体验分享",
                "sections_count": 5,
                "tags": topic["keywords"],
                "status": "generated"
            }
            
            results.append(content)
            
        return {
            "batch_operation": "content_generation",
            "account_id": account_id,
            "total_topics": len(topics),
            "success_count": len(results),
            "generated_contents": results
        } 