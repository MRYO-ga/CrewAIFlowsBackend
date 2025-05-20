# 导入标准库
import os
import json
# 导入第三方库
from celery import Celery
from crewai.flow.flow import Flow, listen, start
from utils.jobManager import append_event, get_job_by_id, update_job_by_id
from utils.myLLM import create_llm
from crewai import Agent

# 导入各专业Agent模块（这些就是Crew的实现）
from crews.personaManagerAgent.persona_manager_agent import PersonaManagerAgent
from crews.competitorAnalysisAgent.competitor_analysis_agent import CompetitorAnalysisAgent
from crews.contentCreationAgent.content_creation_agent import ContentCreationAgent
from crews.complianceCheckAgent.compliance_check_agent import ComplianceCheckAgent
from crews.publicationAgent.publication_agent import PublicationAgent

# OPENAI_BASE_URL=https://yunwu.ai/v1
# OPENAI_API_KEY=sk-ZMQCPKllNuc0sXwa10dZsdhvkBKn0zlesmShxlsNZsotsiav
# OPENAI_CHAT_MODEL=gpt-4o-mini

# 设置OpenAI的大模型的参数  Task中设置输出为:output_json时，需要用到默认的大模型
os.environ["OPENAI_API_BASE"] = "https://yunwu.ai/v1"
os.environ["OPENAI_API_KEY"] = "sk-ZMQCPKllNuc0sXwa10dZsdhvkBKn0zlesmShxlsNZsotsiav"
os.environ["OPENAI_MODEL_NAME"] = "gpt-4o-mini"
# 设置google搜索引擎
os.environ["SERPER_API_KEY"] = "dab5c8339d04bf0f267f702b1dd1a1df4d22e054"

LLM_TYPE = "openai"

# 创建 Celery 实例
app = Celery('tasks', broker='redis://127.0.0.1:6379/0')

# 定义流程类
class XHSWorkflow(Flow):
    """小红书多Agent自动化运营系统工作流"""
    
    def __init__(self, job_id, llm, input_data, manager_agent):
        super().__init__()
        self.job_id = job_id
        self.llm = llm
        self.input_data = input_data
        self.manager_agent = manager_agent
        self.results = {}
    
    @start()
    def persona_management(self):
        """人设管理流程"""
        append_event(self.job_id, "启动人设管理流程")
        if 'persona_management' in self.input_data.get('crew', {}):
            result = PersonaManagerAgent(self.job_id, self.llm, self.input_data, self.manager_agent).kickoff()
            self.results["persona_management"] = result
            append_event(self.job_id, "人设管理流程完成")
            return result
        else:
            append_event(self.job_id, "人设管理流程未启用，已跳过")
            return None
    
    @listen(persona_management)
    def competitor_analysis(self, persona_result=None):
        """竞品分析流程"""
        append_event(self.job_id, "启动竞品分析流程")
        if 'competitor_analysis' in self.input_data.get('crew', {}):
            # 更新input_data，包含前一步的结果
            if persona_result:
                if hasattr(persona_result, 'raw'):
                    self.input_data["persona_management_result"] = persona_result.raw
                elif hasattr(persona_result, 'to_dict'):
                    self.input_data["persona_management_result"] = persona_result.to_dict()
                else:
                    self.input_data["persona_management_result"] = str(persona_result)
                
            result = CompetitorAnalysisAgent(self.job_id, self.llm, self.input_data, self.manager_agent).kickoff()
            self.results["competitor_analysis"] = result
            append_event(self.job_id, "竞品分析流程完成")
            return result
        else:
            append_event(self.job_id, "竞品分析流程未启用，已跳过")
            return None
    
    @listen(competitor_analysis)
    def content_creation(self, competitor_result=None):
        """内容创建流程"""
        append_event(self.job_id, "启动内容创建流程")
        if 'content_creation' in self.input_data.get('crew', {}):
            # 更新input_data，包含前一步的结果
            if competitor_result:
                if hasattr(competitor_result, 'raw'):
                    self.input_data["competitor_analysis_result"] = competitor_result.raw
                elif hasattr(competitor_result, 'to_dict'):
                    self.input_data["competitor_analysis_result"] = competitor_result.to_dict()
                else:
                    self.input_data["competitor_analysis_result"] = str(competitor_result)
                
            result = ContentCreationAgent(self.job_id, self.llm, self.input_data, self.manager_agent).kickoff()
            self.results["content_creation"] = result
            append_event(self.job_id, "内容创建流程完成")
            return result
        else:
            append_event(self.job_id, "内容创建流程未启用，已跳过")
            return None
    
    @listen(content_creation)
    def compliance_check(self, content_result=None):
        """合规检查流程"""
        append_event(self.job_id, "启动合规检查流程")
        if 'compliance_check' in self.input_data.get('crew', {}):
            # 更新input_data，包含前一步的结果
            if content_result:
                if hasattr(content_result, 'raw'):
                    self.input_data["content_creation_result"] = content_result.raw
                elif hasattr(content_result, 'to_dict'):
                    self.input_data["content_creation_result"] = content_result.to_dict()
                else:
                    self.input_data["content_creation_result"] = str(content_result)
                
            result = ComplianceCheckAgent(self.job_id, self.llm, self.input_data, self.manager_agent).kickoff()
            self.results["compliance_check"] = result
            append_event(self.job_id, "合规检查流程完成")
            return result
        else:
            append_event(self.job_id, "合规检查流程未启用，已跳过")
            return None
    
    @listen(compliance_check)
    def publication(self, compliance_result=None):
        """发布互动流程"""
        append_event(self.job_id, "启动发布互动流程")
        if 'publication' in self.input_data.get('crew', {}):
            # 更新input_data，包含前一步的结果
            if compliance_result:
                if hasattr(compliance_result, 'raw'):
                    self.input_data["compliance_check_result"] = compliance_result.raw
                elif hasattr(compliance_result, 'to_dict'):
                    self.input_data["compliance_check_result"] = compliance_result.to_dict()
                else:
                    self.input_data["compliance_check_result"] = str(compliance_result)
                
            result = PublicationAgent(self.job_id, self.llm, self.input_data, self.manager_agent).kickoff()
            self.results["publication"] = result
            append_event(self.job_id, "发布互动流程完成")
            return result
        else:
            append_event(self.job_id, "发布互动流程未启用，已跳过")
            return None
    
    def get_results(self):
        """获取所有流程的结果"""
        return self.results

@app.task
def kickoff_flow(job_id, input_data):
    """
    启动特定业务流程的Celery任务
    
    Args:
        job_id (str): 作业ID
        input_data (dict): 输入数据，包含请求参数
    """
    append_event(job_id, "任务开始执行")
    
    try:
        # 确保input_data是字典类型
        if isinstance(input_data, str):
            input_data = json.loads(input_data)
        
        # 记录输入数据
        append_event(job_id, f"收到输入数据: {json.dumps(input_data, ensure_ascii=False)}")
        
        # 创建LLM实例
        llm = create_llm()
        
        # 创建manager agent
        manager_agent = Agent(
            role='运营管理专家',
            goal="""作为小红书运营管理专家，你的目标是:
            1. 理解并分析运营需求
            2. 制定合理的任务执行计划
            3. 分配和协调各个专业Agent的工作
            4. 监控任务执行进度
            5. 确保最终输出符合要求
            
            注意: 输出格式必须为 {'coworker': str, 'task': str, 'context': str}
            例如: {'coworker': '首席市场分析师', 'task': '分析市场趋势', 'context': '分析背景说明'}""",
            backstory=f"""你是一个专业的小红书运营管理专家，负责协调和管理各个专业Agent完成小红书运营任务。
            具体需求: {input_data.get('requirements', '未指定')}""",
            llm=llm,
            verbose=True,
            allow_delegation=True
        )
        
        # 检查是否有crew配置并执行任务
        if 'crew' in input_data and input_data['crew']:
            append_event(job_id, f"使用Flow方式执行多Agent流程")
            append_event(job_id, f"配置的模块: {list(input_data['crew'].keys())}")
            
            # 使用Flow方式执行多Agent流程
            workflow = XHSWorkflow(job_id, llm, input_data, manager_agent)
            workflow.kickoff()
            
            # 获取最终结果
            all_results = workflow.get_results()
            
            append_event(job_id, f"任务执行完成，结果: {all_results}")
            # 更新任务状态为完成
            update_job_by_id(job_id, "COMPLETED", str(all_results), ["任务执行完成"])
            return all_results
        else:
            error_msg = "缺少crew配置，无法执行任务"
            append_event(job_id, error_msg)
            raise ValueError(error_msg)
        
    except Exception as e:
        error_msg = f"执行任务时出错: {str(e)}"
        append_event(job_id, error_msg)
        # 更新任务状态为错误
        update_job_by_id(job_id, "ERROR", error_msg, ["任务执行失败"])
        import traceback
        trace_info = traceback.format_exc()
        append_event(job_id, f"错误堆栈跟踪: {trace_info}")
        return error_msg
