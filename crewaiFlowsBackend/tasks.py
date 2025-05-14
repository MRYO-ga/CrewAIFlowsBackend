# 导入标准库
import os
import json
# 导入第三方库
from celery import Celery
from utils.jobManager import append_event, get_job_by_id, update_job_by_id
from utils.myLLM import create_llm

# 导入各专业Agent模块
from crews.personaManagerAgent.persona_manager_agent import PersonaManagerAgent
from crews.competitorAnalysisAgent.competitor_analysis_agent import CompetitorAnalysisAgent
from crews.contentCreationAgent.content_creation_agent import ContentCreationAgent
from crews.complianceCheckAgent.compliance_check_agent import ComplianceCheckAgent
from crews.publicationAgent.publication_agent import PublicationAgent
from crewai import Agent
from crewai.process import Process

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
        
        # 处理新增的关键词字段
        if 'keywords' in input_data and input_data['keywords']:
            append_event(job_id, f"处理关键词: {', '.join(input_data['keywords'])}")
        
        # 根据operation_type选择对应的Agent
        operation_type = input_data.get("operation_type", "")
        task_type = input_data.get("task_type", "")
        append_event(job_id, f"操作类型: {operation_type}, 任务类型: {task_type}")
        
        # 创建LLM实例
        llm = create_llm()
        
        # 创建manager agent
        manager = Agent(
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
            当前任务类型: {operation_type} - {task_type}
            涉及品类/主题: {input_data.get('category', '未指定')}
            具体需求: {input_data.get('requirements', '未指定')}
            {f"目标受众信息: {input_data['target_audience']}" if input_data.get('target_audience') else ""}
            {f"关键词: {', '.join(input_data['keywords'])}" if input_data.get('keywords') else ""}""",
            llm=llm,
            verbose=True,
            allow_delegation=True
        )
        
        if operation_type == "account_setup" or operation_type == "persona_management":
            # 账号人设管理流程
            append_event(job_id, f"启动账号人设管理流程: {task_type}")
            agent = PersonaManagerAgent(job_id, llm, input_data, manager_agent=manager)
            result = agent.kickoff()
            
        elif operation_type == "competitor_analysis":
            # 竞品分析流程
            append_event(job_id, f"启动竞品分析流程: {task_type}")
            agent = CompetitorAnalysisAgent(job_id, llm, input_data, manager_agent=manager)
            result = agent.kickoff()
            
        elif operation_type == "content_creation":
            # 内容生成流程
            append_event(job_id, f"启动内容生成流程: {task_type}")
            agent = ContentCreationAgent(job_id, llm, input_data, manager_agent=manager)
            result = agent.kickoff()
            
        elif operation_type == "compliance_check":
            # 合规检测流程
            append_event(job_id, f"启动合规检测流程: {task_type}")
            agent = ComplianceCheckAgent(job_id, llm, input_data, manager_agent=manager)
            result = agent.kickoff()
            
        elif operation_type == "publication":
            # 发布互动流程
            append_event(job_id, f"启动发布互动流程: {task_type}")
            agent = PublicationAgent(job_id, llm, input_data, manager_agent=manager)
            result = agent.kickoff()
            
        elif operation_type == "full_process":
            # 全流程自动化处理
            append_event(job_id, "启动全流程自动化处理")
            
            # 1. 先进行竞品分析
            append_event(job_id, "1. 启动竞品分析")
            competitor_agent = CompetitorAnalysisAgent(job_id, llm, input_data, manager_agent=manager)
            competitor_result = competitor_agent.kickoff()
            
            # 2. 然后进行内容生成
            append_event(job_id, "2. 启动内容生成")
            # 将竞品分析结果添加到输入数据
            content_input = {**input_data, "competitor_analysis": competitor_result}
            content_agent = ContentCreationAgent(job_id, llm, content_input, manager_agent=manager)
            content_result = content_agent.kickoff()
            
            # 3. 接着进行合规检测
            append_event(job_id, "3. 启动合规检测")
            # 将内容生成结果添加到输入数据
            compliance_input = {**input_data, "generated_content": content_result}
            compliance_agent = ComplianceCheckAgent(job_id, llm, compliance_input, manager_agent=manager)
            compliance_result = compliance_agent.kickoff()
            
            # 4. 最后进行内容发布
            append_event(job_id, "4. 启动内容发布")
            # 整合所有结果
            publication_input = {
                **input_data,
                "competitor_analysis": competitor_result,
                "generated_content": content_result,
                "compliance_check": compliance_result
            }
            publication_agent = PublicationAgent(job_id, llm, publication_input, manager_agent=manager)
            publication_result = publication_agent.kickoff()
            
            # 返回完整结果集
            result = {
                "competitor_analysis": competitor_result,
                "content_creation": content_result,
                "compliance_check": compliance_result,
                "publication": publication_result
            }
            
        else:
            error_msg = f"不支持的操作类型: {operation_type}"
            append_event(job_id, error_msg)
            return error_msg
            
        append_event(job_id, f"任务执行完成，结果: {result}")
        # 更新任务状态为完成
        update_job_by_id(job_id, "COMPLETED", str(result), ["任务执行完成"])
        return result
        
    except Exception as e:
        error_msg = f"执行任务时出错: {str(e)}"
        append_event(job_id, error_msg)
        # 更新任务状态为错误
        update_job_by_id(job_id, "ERROR", error_msg, ["任务执行失败"])
        return error_msg
