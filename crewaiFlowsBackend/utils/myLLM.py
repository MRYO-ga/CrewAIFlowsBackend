# 导入标准库
import os
# 导入第三方库
from crewai import LLM
import json
import requests
import re


# os.environ["OPENAI_API_BASE"] = "https://yunwu.ai/v1"
# os.environ["OPENAI_API_KEY"] = "sk-ZMQCPKllNuc0sXwa10dZsdhvkBKn0zlesmShxlsNZsotsiav"
# os.environ["OPENAI_MODEL_NAME"] = "gpt-4o-mini"

# 模型全局参数配置  根据自己的实际情况进行调整
# openai模型相关配置 根据自己的实际情况进行调整
OPENAI_API_BASE = "https://yunwu.ai/v1"
OPENAI_CHAT_API_KEY = "sk-ZMQCPKllNuc0sXwa10dZsdhvkBKn0zlesmShxlsNZsotsiav"
OPENAI_CHAT_MODEL = "gpt-4o-mini"
# 非gpt大模型相关配置(oneapi方案 通义千问为例) 根据自己的实际情况进行调整
ONEAPI_API_BASE = "http://139.224.72.218:3000/v1"
ONEAPI_CHAT_API_KEY = "sk-0FxX9ncd0yXjTQF877Cc9dB6B2F44aD08d62805715821b85"
ONEAPI_CHAT_MODEL = "qwen-max"
# 本地大模型相关配置(Ollama方案 llama3.1:latest为例) 根据自己的实际情况进行调整
OLLAMA_API_BASE = "http://localhost:11434/v1"
OLLAMA_CHAT_API_KEY = "ollama"
OLLAMA_CHAT_MODEL = "llama3.1:latest"

# 多模型配置映射
MODEL_CONFIGS = {
    # OpenAI模型
    'gpt-4o-mini': {
        'provider': 'openai',
        'api_base': OPENAI_API_BASE,
        'api_key': OPENAI_CHAT_API_KEY,
        'model': 'gpt-4o-mini'
    },
    'gpt-4o': {
        'provider': 'openai',
        'api_base': OPENAI_API_BASE,
        'api_key': OPENAI_CHAT_API_KEY,
        'model': 'gpt-4o'
    },
    
    # Claude模型（通过云雾AI的兼容接口）
    'claude-sonnet-4-20250514': {
        'provider': 'openai',  # 使用OpenAI兼容接口
        'api_base': OPENAI_API_BASE,
        'api_key': OPENAI_CHAT_API_KEY,
        'model': 'claude-sonnet-4-20250514'
    },
    'claude-3-7-sonnet-20250219-thinking': {
        'provider': 'openai',
        'api_base': OPENAI_API_BASE,
        'api_key': OPENAI_CHAT_API_KEY,
        'model': 'claude-3-7-sonnet-20250219-thinking'
    },
    'claude-3-5-sonnet-20241022': {
        'provider': 'openai',
        'api_base': OPENAI_API_BASE,
        'api_key': OPENAI_CHAT_API_KEY,
        'model': 'claude-3-5-sonnet-20241022'
    },
    
    # DeepSeek模型
    'deepseek-r1-250528': {
        'provider': 'openai',
        'api_base': OPENAI_API_BASE,
        'api_key': OPENAI_CHAT_API_KEY,
        'model': 'deepseek-r1-250528'
    }
}

# 定函数 模型初始化
def my_llm(llmType, model="gpt-4o-mini"):
    if llmType == "oneapi":
        # 实例化一个oneapi客户端对象
        llm = LLM(
            base_url=ONEAPI_API_BASE,
            api_key=ONEAPI_CHAT_API_KEY,
            model=model,  # 本次使用的模型
            temperature=0.7,  # 发散的程度
            # timeout=None,# 服务请求超时
            # max_retries=2,# 失败重试最大次数
        )
    elif llmType == "ollama":
        # 实例化一个LLM客户端对象
        os.environ["OPENAI_API_KEY"] = "NA"
        llm = LLM(
            base_url=OLLAMA_API_BASE,  # 请求的API服务地址
            api_key=OLLAMA_CHAT_API_KEY,  # API Key
            model=model,  # 本次使用的模型
            temperature=0.7,  # 发散的程度
            # timeout=None,# 服务请求超时
            # max_retries=2,# 失败重试最大次数
        )
    else:
        # 实例化一个LLM客户端对象
        llm = LLM(
            base_url=OPENAI_API_BASE,  # 请求的API服务地址
            api_key=OPENAI_CHAT_API_KEY,  # API Key
            model=model,  # 本次使用的模型
            # temperature=0.7,# 发散的程度，一般为0
            # timeout=None,# 服务请求超时
            # max_retries=2,# 失败重试最大次数
        )
    return llm

def create_llm(llmType="openai", model="gpt-4o-mini"):
    """
    创建LLM实例
    
    Args:
        llmType: 大语言模型类型，默认为"openai"，可选值："openai", "oneapi", "ollama"
        
    Returns:
        LLM: 配置好的大语言模型实例
    """
    return my_llm(llmType, model)

def chat_with_llm(messages, llmType="openai", model=OPENAI_CHAT_MODEL):
    """
    直接与LLM进行对话
    
    Args:
        messages: 对话历史消息列表
        llmType: 大语言模型类型，默认为"openai"
        model: 使用的模型名称
        
    Returns:
        str: LLM的回复内容
    """
    print(f"开始调用LLM，类型: {llmType}，模型: {model}")
    
    # 检查是否在模型配置中
    if model in MODEL_CONFIGS:
        config = MODEL_CONFIGS[model]
        print(f"使用配置的模型: {model} -> {config}")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config['api_key']}"
        }
        
        payload = {
            "model": config['model'],
            "messages": messages,
            "temperature": 0.7
        }
        
        print(f"API基础URL: {config['api_base']}")
        print(f"使用模型: {config['model']}")
        print(f"消息数量: {len(messages)}")
        
        try:
            print("正在发送API请求...")
            response = requests.post(
                f"{config['api_base']}/chat/completions", 
                headers=headers,
                json=payload,
                timeout=60
            )
            
            print(f"API响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                response_data = response.json()
                print("API调用成功，正在处理响应")
                
                if response_data.get("choices") and len(response_data["choices"]) > 0:
                    content = response_data["choices"][0]["message"]["content"]
                    print(f"获取到内容: {content[:100]}...")
                    
                    # 尝试解析为JSON
                    try:
                        # 查找content中的JSON字符串
                        json_match = re.search(r'\{[\s\S]*\}', content)
                        if json_match:
                            print("找到JSON匹配")
                            json_content = json.loads(json_match.group())
                            # 如果解析出的JSON包含必要的字段，直接返回
                            if isinstance(json_content, dict) and "reply" in json_content and "data" in json_content:
                                print("返回完整的JSON响应")
                                return json.dumps(json_content, ensure_ascii=False)
                            # 否则构造标准响应
                            print("构造标准JSON响应")
                            return json.dumps({
                                "reply": content,
                                "data": json_content
                            }, ensure_ascii=False)
                        else:
                            print("未找到JSON匹配，返回普通文本响应")
                            return json.dumps({
                                "reply": content,
                                "data": {}
                            }, ensure_ascii=False)
                    except json.JSONDecodeError as e:
                        print(f"JSON解析错误: {str(e)}")
                        # 如果不是JSON格式，构造一个标准响应
                        return json.dumps({
                            "reply": content,
                            "data": {}
                        }, ensure_ascii=False)
                else:
                    print("未找到有效回复")
                    return json.dumps({
                        "reply": "抱歉，我没有收到有效的回复。",
                        "data": {}
                    }, ensure_ascii=False)
            else:
                error_msg = f"API调用失败: {response.status_code}, {response.text}"
                print(error_msg)
                return json.dumps({
                    "reply": f"抱歉，服务暂时不可用 (错误码: {response.status_code})，请稍后再试。",
                    "data": {}
                }, ensure_ascii=False)
                
        except requests.exceptions.RequestException as e:
            error_msg = f"请求异常: {str(e)}"
            print(error_msg)
            return json.dumps({
                "reply": f"抱歉，网络连接出现问题: {str(e)}，请稍后再试。",
                "data": {}
            }, ensure_ascii=False)
    
    elif llmType == "openai":
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_CHAT_API_KEY}"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.7
        }
        
        print(f"API基础URL: {OPENAI_API_BASE}")
        print(f"使用模型: {model}")
        print(f"消息数量: {len(messages)}")
        
        try:
            print("正在发送API请求...")
            response = requests.post(
                f"{OPENAI_API_BASE}/chat/completions", 
                headers=headers,
                json=payload,
                timeout=60
            )
            
            print(f"API响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                response_data = response.json()
                print("API调用成功，正在处理响应")
                
                if response_data.get("choices") and len(response_data["choices"]) > 0:
                    content = response_data["choices"][0]["message"]["content"]
                    
                    # 尝试解析为JSON
                    try:
                        # 查找content中的JSON字符串
                        json_match = re.search(r'\{[\s\S]*\}', content)
                        if json_match:
                            print("找到JSON匹配")
                            json_content = json.loads(json_match.group())
                            # 如果解析出的JSON包含必要的字段，直接返回
                            if isinstance(json_content, dict) and "reply" in json_content and "data" in json_content:
                                print("返回完整的JSON响应")
                                return json.dumps(json_content, ensure_ascii=False)
                            # 否则构造标准响应
                            print("构造标准JSON响应")
                            return json.dumps({
                                "reply": content,
                                "data": json_content
                            }, ensure_ascii=False)
                        else:
                            print("未找到JSON匹配，返回普通文本响应")
                            return json.dumps({
                                "reply": content,
                                "data": {}
                            }, ensure_ascii=False)
                    except json.JSONDecodeError as e:
                        print(f"JSON解析错误: {str(e)}")
                        # 如果不是JSON格式，构造一个标准响应
                        return json.dumps({
                            "reply": content,
                            "data": {}
                        }, ensure_ascii=False)
                else:
                    print("未找到有效回复")
                    return json.dumps({
                        "reply": "抱歉，我没有收到有效的回复。",
                        "data": {}
                    }, ensure_ascii=False)
            else:
                error_msg = f"API调用失败: {response.status_code}, {response.text}"
                print(error_msg)
                return json.dumps({
                    "reply": f"抱歉，服务暂时不可用 (错误码: {response.status_code})，请稍后再试。",
                    "data": {}
                }, ensure_ascii=False)
                
        except requests.exceptions.RequestException as e:
            error_msg = f"请求异常: {str(e)}"
            print(error_msg)
            return json.dumps({
                "reply": f"抱歉，网络连接出现问题: {str(e)}，请稍后再试。",
                "data": {}
            }, ensure_ascii=False)
    
    # 如果使用的不是支持的LLM类型
    print(f"不支持的LLM类型: {llmType}")
    return json.dumps({
        "reply": f"不支持的LLM类型: {llmType}，请选择 openai、oneapi 或 ollama",
        "data": {}
    }, ensure_ascii=False)

def interact_with_intent_agent(user_input, conversation_history=None):
    """
    与意图解析Agent交互，完善用户需求
    
    Args:
        user_input: 用户输入的内容
        conversation_history: 对话历史
        
    Returns:
        dict: 包含回复和解析后的需求数据的字典
    """
    if conversation_history is None:
        conversation_history = []
    
    # 意图解析Agent的系统提示词
    system_prompt = """你是一个专业的用户交互与意图解析 Agent，核心任务是通过多轮对话收集完善输入信息，在满足条件时按指定格式输出指令。以下是详细工作指引：
一、需求分析与追问规则
（1）需求要素识别
- 逐句解析用户输入，提取明确需求（如 "账号基础信息方案"" 护肤测评 "）
- 标记潜在缺失要素：▶ 账号类：细分肤质（油皮 / 干皮）、目标受众（学生党 / 职场人）、内容形式（图文 / 视频）▶ 竞品分析类：竞品名称、分析维度（风格 / 话题 / 形式）▶ 内容创作类：内容类型（干货清单 / 跟练视频）、发布频率
（2）追问话术生成原则
- 结构化提问：采用「要素 + 场景化选项」模式，如：" 您希望账号内容更侧重 油皮 / 干皮 / 混合皮 / 敏感肌 护肤测评？（可多选，默认混合皮）"" 目标受众更偏向 学生党 / 职场新人 / 宝妈 / 精致白领？（单选，默认职场新人）"
- 闭环设计：每个问题提供 3-5 个典型选项 +「其他（请说明）」兜底选项
二、指令构建触发条件
（1）主动终止条件（满足任一即停止追问）
- 关键要素完整度≥80%（通过预设需求模板校验）
- 用户明确终止指令："不用补充了"" 按现有信息生成 ""可以停止提问"
（2）被动终止处理
- 无效输入：回复固定提示 "您的输入暂未识别，请用文字描述需求，例如：' 创建美妆账号基础信息 '"
- 强制终止：基于现有信息生成最简指令，缺失非必填要素用行业默认值（如未选肤质默认 "混合皮"）
三、指令生成规范（核心调整）
（1）核心字段定义
{
  "reply": "你给用户的回复",
  "data": {
    "crew": {  // 按所选模块配置子Agent，支持多模块组合
      "persona_management": {  // 选填，对应账号人设管理模块
        "account_info_writer": true,  // 账号基础信息撰写
        "unique_persona_builder": true,  // 独特人设定位构建
        "content_direction_planner": true  // 主题内容方向规划
      },
      "competitor_analysis": {  // 选填，竞品分析模块
        "platform_trend_decoder": true,  // 平台趋势解析
        "content_style_analyst": true  // 内容风格分析
      },
      "content_creation": {  // 选填，内容创作模块
        "content_creator": true  // 内容创作
      }
    },
    "requirements": "完整需求描述",  // 整合用户输入+追问补充的完整需求
    "agent_selection_reason": {  // 选择agent和子agent的理由
      "persona_management": {
        "account_info_writer": "选择理由",
        "unique_persona_builder": "选择理由",
        "content_direction_planner": "选择理由"
      },
      "competitor_analysis": {
        "platform_trend_decoder": "选择理由",
        "content_style_analyst": "选择理由"
      },
      "content_creation": {
        "content_creator": "选择理由"
      }
    }
  }
}

如果需要继续对话，data中应仅包含空对象 {}

（2）模块组合规则
需求类型         | 必选模块              | 可选扩展模块           | 子 Agent 匹配逻辑
-----------------|----------------------|------------------------|---------------------------
基础信息创建      | persona_management   | -                      | 含 "账号名称/简介" → account_info_writer
差异化人设        | persona_management   | competitor_analysis    | 含 "人设/差异化" → unique_persona_builder + content_style_analyst
内容规划          | persona_management   | content_creation       | 含 "内容方向/日历" → content_direction_planner + content_creator
竞品分析          | competitor_analysis  | -                      | 含 "竞品/分析" → platform_trend_decoder（趋势）或 content_style_analyst（策略）

（3）子 Agent 映射表
主模块                | 可分配子 Agent            | 适用场景关键词
----------------------|--------------------------|----------------------
persona_management    | account_info_writer      | 账号名称、简介、头像
persona_management    | unique_persona_builder   | 人设定位、差异化、标签矩阵
persona_management    | content_direction_planner| 内容方向、选题策略、内容日历
competitor_analysis   | platform_trend_decoder   | 平台趋势、热门话题、内容形式
competitor_analysis   | content_style_analyst    | 竞品分析、风格定位、创新度
content_creation      | content_creator          | 爆款内容、图文/视频文案、涨粉转化

四、典型指令生成示例
（1）单模块场景（基础信息创建）
用户输入："需要小红书护肤账号的简介和名称，针对油皮和学生党"追问后补充：确认无需竞品分析和内容规划
{
  "reply": "已完成您的需求收集，即将为您生成针对油皮学生党的护肤账号基础信息方案。",
  "data": {
    "crew": {
      "persona_management": {
        "account_info_writer": true
      }
    },
    "requirements": "创建针对油皮学生党的小红书护肤账号基础信息（名称+简介）",
    "agent_selection_reason": {
      "persona_management": {
        "account_info_writer": "用户需要创建账号基础信息（名称和简介），选择account_info_writer作为子Agent最适合处理这类基础信息创建任务"
      }
    }
  }
}

（2）多模块组合场景（人设 + 竞品分析）
用户输入："想做美妆账号，需要独特人设和竞品分析"追问后补充：目标受众 25-35 岁白领，需分析 3 个同类账号风格
{
  "reply": "感谢您的信息提供，即将为您创建美妆账号的人设与竞品分析方案。",
  "data": {
    "crew": {
      "persona_management": {
        "unique_persona_builder": true
      },
      "competitor_analysis": {
        "content_style_analyst": true
      }
    },
    "requirements": "为25-35岁白领美妆账号构建独特人设，分析3个同类账号的内容风格策略",
    "agent_selection_reason": {
      "persona_management": {
        "unique_persona_builder": "用户需要构建独特人设，unique_persona_builder专门负责差异化人设定位"
      },
      "competitor_analysis": {
        "content_style_analyst": "需要分析竞品账号风格，content_style_analyst更适合进行内容风格策略分析"
      }
    }
  }
}

五、交互注意事项
1. 追问频率控制：单次对话追问不超过 3 轮，每轮聚焦 1-2 个核心要素
2. 进度反馈：第 2 次追问时增加提示 "当前信息完整度 60%，补充 XX 信息后即可生成方案"
3. 术语转换：将用户口语化表达转为规范字段，如 "同类账号"→"竞品分析"，"发什么内容"→"内容方向规划"

你必须严格按照指定的JSON结构输出，并确保根据用户需求正确分配子Agent。"""

    # 构建消息列表
    messages = [
        {"role": "system", "content": system_prompt}
    ]
    
    # 添加对话历史
    for msg in conversation_history:
        messages.append({"role": "user" if msg["isUser"] else "assistant", "content": msg["text"]})
    
    # 添加当前用户输入
    messages.append({"role": "user", "content": user_input})
    
    # 调用LLM获取回复，显式指定使用openai类型
    response = chat_with_llm(messages, llmType="openai", model="gpt-4o")
    
    try:
        # 解析JSON响应
        result = json.loads(response)
        
        # 确保data字段存在
        if not result.get("data"):
            result["data"] = {}
        
        return result
    except json.JSONDecodeError:
        # 如果解析失败，返回默认响应
        return {
            "reply": "抱歉，我无法理解您的需求。请尝试更清晰地描述，例如：'我想创建一个护肤账号'或'我需要分析竞品账号'。",
            "data": {}
        }