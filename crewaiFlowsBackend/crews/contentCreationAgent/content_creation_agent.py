# 内容生成Agent (ContentCreationAgent)
# 该模块为小红书多Agent自动化运营系统的"内容创作引擎"
# 负责高质量小红书内容生成

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
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'
    
    def __init__(self, job_id: str, llm, input_data: Dict, manager_agent=None):
        """
        初始化内容生成Agent
        
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
    def content_creator(self) -> Agent:
        """内容创建者Agent，负责生成高质量内容"""
        return Agent(
            config=self.agents_config['content_creator'],
            tools=self.tool_adapters.get_content_creator_tools(),
            verbose=True,
            memory=False,
            llm=self.llm
        )

    @task
    def content_creation_task(self) -> Task:
        return Task(
            config=self.tasks_config['content_creation_task'],
            callback=self.append_event_callback,
            output_json=ContentCreation
        )

    @crew
    def crew(self) -> Crew:
        """创建并配置内容生成Crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            manager_agent=self.manager_agent,
            process=Process.hierarchical,
            verbose=True,
            respect_context_window=True
        )

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