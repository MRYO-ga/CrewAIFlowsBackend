# 合规检测Agent (ComplianceCheckAgent)
# 该模块为小红书多Agent自动化运营系统的"守门员"
# 负责内容合规性检测与敏感词过滤，保障所有内容合规

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
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'
    
    def __init__(self, job_id: str, llm, input_data: Dict, manager_agent=None):
        """
        初始化合规检测Agent
        
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
        self.compliance_tool = XiaoHongShuComplianceTool()

    def append_event_callback(self, task_output):
        append_event(self.job_id, task_output.raw)

    @agent
    def compliance_officer(self) -> Agent:
        """合规官Agent，负责规则解读和合规判断"""
        return Agent(
            config=self.agents_config['compliance_officer'],
            tools=[self.compliance_tool],
            verbose=True,
            memory=False,
            llm=self.llm
        )
        
    @agent
    def content_editor(self) -> Agent:
        """内容编辑Agent，负责提供修改建议"""
        return Agent(
            config=self.agents_config['content_editor'],
            tools=[self.compliance_tool],
            verbose=True,
            memory=False,
            llm=self.llm
        )

    @task
    def compliance_check_task(self) -> Task:
        return Task(
            config=self.tasks_config['compliance_check_task'],
            callback=self.append_event_callback,
            output_json=ComplianceReport
        )
        
    @task
    def revision_suggestion_task(self) -> Task:
        return Task(
            config=self.tasks_config['revision_suggestion_task'],
            callback=self.append_event_callback,
            output_json=None
        )

    @crew
    def crew(self) -> Crew:
        """创建并配置合规检测Crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            manager_agent=self.manager_agent,
            process=Process.hierarchical,
            verbose=True,
            respect_context_window=True
        )

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