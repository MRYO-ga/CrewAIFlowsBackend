# 合规检测Agent (ComplianceCheckAgent)
# 该模块为小红书多Agent自动化运营系统的"守门员"
# 负责内容合规性检测与敏感词过滤，保障所有内容合规

import os
import yaml
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from typing import List, Dict, Any
from utils.models import ComplianceReport
from utils.jobManager import append_event
# from utils.manager_agent import create_manager_agent
from utils.event_logger import create_event_logger
from tools.xiaohongshu_tools import XiaoHongShuComplianceTool

@CrewBase
class ComplianceCheckAgent:
    """
    合规检测Agent - 负责内容合规性检测与敏感词过滤
    """
    def __init__(self, job_id: str, llm, input_data: Dict, manager_agent=None):
        """
        初始化合规检测Agent
        
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
        self.compliance_tool = XiaoHongShuComplianceTool()
        
        # 加载配置文件
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.agents_config = self._load_yaml(os.path.join(current_dir, 'config', 'agents.yaml'))
        self.tasks_config = self._load_yaml(os.path.join(current_dir, 'config', 'tasks.yaml'))
        
        # 根据crew配置初始化所需的Agent和任务
        self.required_agents = []
        self.required_tasks = []
        
        # 检查是否存在crew配置
        if 'crew' in input_data and 'compliance_check' in input_data['crew']:
            agent_config = input_data['crew']['compliance_check']
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
        # 合规官Agent
        if agent_type == "compliance_officer" or agent_type.find("compliance_officer") != -1:
            append_event(self.job_id, f"加载合规官Agent")
            self.required_agents.append(self.compliance_officer())
            self.required_tasks.append(self.compliance_check_task())
        
        # 内容编辑Agent
        if agent_type == "content_editor" or agent_type.find("content_editor") != -1:
            append_event(self.job_id, f"加载内容编辑Agent")
            self.required_agents.append(self.content_editor())
            self.required_tasks.append(self.revision_suggestion_task())

    def append_event_callback(self, task_output):
        append_event(self.job_id, task_output.raw)

    @agent
    def compliance_officer(self) -> Agent:
        """合规官Agent，负责规则解读和合规判断"""
        if not self.agents_config or 'compliance_officer' not in self.agents_config:
            append_event(self.job_id, "警告：找不到compliance_officer配置，使用默认配置")
            config = {
                'role': '内容合规专家',
                'goal': '确保所有内容符合平台规范和法律要求',
                'backstory': '你是负责确保内容合规的专家'
            }
        else:
            config = self.agents_config['compliance_officer']
            
        return Agent(
            role=config['role'],
            goal=config['goal'],
            backstory=config['backstory'],
            tools=[self.compliance_tool],
            verbose=True,
            memory=False,
            llm=self.llm
        )
        
    @agent
    def content_editor(self) -> Agent:
        """内容编辑Agent，负责提供修改建议"""
        if not self.agents_config or 'content_editor' not in self.agents_config:
            append_event(self.job_id, "警告：找不到content_editor配置，使用默认配置")
            config = {
                'role': '内容优化专家',
                'goal': '在保持内容核心价值的前提下优化表达方式',
                'backstory': '你是专注于内容优化的专家'
            }
        else:
            config = self.agents_config['content_editor']
            
        return Agent(
            role=config['role'],
            goal=config['goal'],
            backstory=config['backstory'],
            tools=[self.compliance_tool],
            verbose=True,
            memory=False,
            llm=self.llm
        )

    @task
    def compliance_check_task(self) -> Task:
        """合规检查任务"""
        if not self.tasks_config or 'compliance_check_task' not in self.tasks_config:
            append_event(self.job_id, "警告：找不到compliance_check_task配置，使用默认配置")
            config = {
                'description': '执行内容合规性检查',
                'expected_output': '详细的合规检查报告'
            }
        else:
            config = self.tasks_config['compliance_check_task']
            
        return Task(
            description=config['description'],
            expected_output=config['expected_output'],
            callback=self.append_event_callback,
            output_json=ComplianceReport
        )
        
    @task
    def revision_suggestion_task(self) -> Task:
        """修改建议任务"""
        if not self.tasks_config or 'revision_suggestion_task' not in self.tasks_config:
            append_event(self.job_id, "警告：找不到revision_suggestion_task配置，使用默认配置")
            config = {
                'description': '提供内容修改建议',
                'expected_output': '具体的修改建议方案'
            }
        else:
            config = self.tasks_config['revision_suggestion_task']
            
        return Task(
            description=config['description'],
            expected_output=config['expected_output'],
            callback=self.append_event_callback,
            output_json=None
        )

    @crew
    def crew(self) -> Crew:
        """创建并配置合规检测Crew"""
        # 根据是否有特定的Agent要求，确定使用哪些Agent
        if self.required_agents:
            agents_list = self.required_agents
        else:
            agents_list = self.agents
            
        # 根据是否有特定的任务要求，确定使用哪些任务
        tasks_to_use = self.required_tasks if self.required_tasks else self.tasks
        
        append_event(self.job_id, f"配置合规检测Crew - 使用{len(agents_list)}个Agent和{len(tasks_to_use)}个任务")
        
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
                self.compliance_check_task(),
                self.revision_suggestion_task()
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
                    self.compliance_officer(),
                    self.content_editor()
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
        使用指定的agents启动合规检测流程
        
        Args:
            *agents: 要使用的Agent实例
            
        Returns:
            运行结果
        """
        crew = self.create_personalized_crew(*agents)
        
        append_event(self.job_id, "启动自定义Agents的ComplianceCheckAgent任务")
        try:
            results = crew.kickoff(inputs=self.input_data)
            append_event(self.job_id, "自定义Agents的ComplianceCheckAgent任务完成")
            return results
        except Exception as e:
            append_event(self.job_id, f"执行过程中发生错误: {e}")
            return str(e)

    def kickoff(self):
        """启动合规检测流程"""
        if not self.crew():
            append_event(self.job_id, "ComplianceCheckAgent not set up")
            return "ComplianceCheckAgent not set up"
            
        append_event(self.job_id, "ComplianceCheckAgent's Task Started")
        try:
            results = self.crew().kickoff(inputs=self.input_data)
            append_event(self.job_id, "ComplianceCheckAgent's Task Complete")
            return results
        except Exception as e:
            append_event(self.job_id, f"An error occurred: {e}")
            return str(e)
            
    # 辅助方法：直接检查内容合规性
    def check_content(self, title: str, content: str) -> Dict[str, Any]:
        """
        检查标题和内容的合规性
        
        Args:
            title: 内容标题
            content: 内容正文
            
        Returns:
            Dict[str, Any]: 合规检查报告
        """
        title_check = self.compliance_tool.check_title_compliance(title)
        content_check = self.compliance_tool.check_content_compliance(content)
        
        # 合并检测到的敏感词
        all_sensitive_words = []
        
        if not title_check["is_compliant"]:
            for issue in title_check["issues"]:
                if "敏感词" in issue:
                    words = issue.split(": ")[1].split(", ")
                    all_sensitive_words.extend(words)
                    
        if not content_check["is_compliant"]:
            for issue in content_check["issues"]:
                if "敏感词" in issue:
                    words = issue.split(": ")[1].split(", ")
                    all_sensitive_words.extend(words)
        
        # 去重
        all_sensitive_words = list(set(all_sensitive_words))
        
        # 获取替代词建议
        alternatives = self.compliance_tool.suggest_alternatives(all_sensitive_words) if all_sensitive_words else {}
        
        return {
            "is_compliant": title_check["is_compliant"] and content_check["is_compliant"],
            "title_check": title_check,
            "content_check": content_check,
            "sensitivity_level": "高" if len(all_sensitive_words) > 5 else "中" if len(all_sensitive_words) > 0 else "低",
            "detected_sensitive_words": all_sensitive_words,
            "alternative_suggestions": alternatives,
            "recommendation_summary": "内容需要修改后发布" if not (title_check["is_compliant"] and content_check["is_compliant"]) else "内容符合平台规范，可直接发布"
        }
    
    # 批量检查多个内容
    def batch_check_contents(self, contents: List[Dict]) -> Dict[str, Any]:
        """
        批量检查多个内容的合规性
        
        Args:
            contents: 内容列表，每个内容包含title和content字段
            
        Returns:
            Dict[str, Any]: 批量检查结果
        """
        results = []
        compliant_count = 0
        
        for content_item in contents:
            check_result = self.check_content(content_item["title"], content_item["content"])
            
            if check_result["is_compliant"]:
                compliant_count += 1
                
            results.append({
                "content_id": content_item.get("content_id", f"content_{len(results)+1}"),
                "title": content_item["title"],
                "is_compliant": check_result["is_compliant"],
                "sensitivity_level": check_result["sensitivity_level"],
                "issues_count": len(check_result["title_check"]["issues"]) + len(check_result["content_check"]["issues"]),
                "needs_revision": not check_result["is_compliant"]
            })
            
        return {
            "batch_operation": "compliance_check",
            "total_contents": len(contents),
            "compliant_count": compliant_count,
            "non_compliant_count": len(contents) - compliant_count,
            "compliance_rate": f"{(compliant_count / len(contents) * 100):.1f}%" if contents else "0%",
            "check_results": results
        } 