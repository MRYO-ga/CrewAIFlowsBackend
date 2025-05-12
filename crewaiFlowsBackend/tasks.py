# 导入标准库
import os
# 导入第三方库
from crewai.flow.flow import Flow, listen, start
from crews.marketAnalystCrew.marketAnalystCrew import marketAnalystCrew
from crews.contentCreatorCrew.contentCreatorCrew import contentCreatorCrew
from celery import Celery
from utils.jobManager import append_event, get_job_by_id, update_job_by_id
from utils.myLLM import my_llm


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
app = Celery('my_app', broker='redis://127.0.0.1:6379/0')


# 定义flow
class workFlow(Flow):
    # 构造初始化函数，接受job_id作为参数，用于标识作业
    def __init__(self, job_id, llm, inputData):
        super().__init__()
        self.job_id = job_id
        self.llm = llm
        self.inputData = inputData

    @start()
    def marketAnalystCrew(self):
        result = marketAnalystCrew(self.job_id, self.llm, self.inputData).kickoff()
        return result

    @listen(marketAnalystCrew)
    def contentCreatorCrew(self):
        result = contentCreatorCrew(self.job_id, self.llm, self.inputData).kickoff()
        return result


# 定义任务
@app.task
def kickoff_flow(job_id, inputData):
    print(f"Flow for job {job_id} is starting")
    results = None
    try:
        append_event(job_id, "Flow Started")
        results = workFlow(job_id, my_llm(LLM_TYPE), inputData).kickoff()
        print(f"Crew for job {job_id} is complete", results)
    except Exception as e:
        print(f"Error in kickoff_flow for job {job_id}: {e}")
        append_event(job_id, f"An error occurred: {e}")
        update_job_by_id(job_id, "ERROR", "Error", ["Flow Start Error"])
    update_job_by_id(job_id, "COMPLETE", str(results), ["Flow complete"])
