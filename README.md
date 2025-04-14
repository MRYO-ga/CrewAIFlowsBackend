# 0、项目相关视频                
**(1)FastAPI+CrewAI+MySQL+Celery实现AI Agent复杂工作流，支持工作流的并发异步调度和全生命周期状态监测，支持gpt、国产、本地大模型**                                            
https://www.bilibili.com/video/BV1P91tY6ELE/?vd_source=30acb5331e4f5739ebbad50f7cc6b949                            
https://youtu.be/G-Sa5OcuQRE           
**(2)详细剖析源码帮助你快速构建自己的工作流，FastAPI+CrewAI+MySQL+Celery实现AI Agent复杂工作流，支持gpt、国产、本地大模型**                    
https://www.bilibili.com/video/BV1nk17YMEec/?vd_source=30acb5331e4f5739ebbad50f7cc6b949                   
https://youtu.be/U_Af8HGw1Hk             

# 1、项目介绍
## 1.1、本次分享介绍
本期视频主要实现使用FastAPI后端框架+CrewAI实现AI Agent复杂工作流项目案例                                
**(1)本次分享内容主要为:**               
(a)分享的项目案例是在“营销战略协作智能体”项目的基础之上进行迭代，那本期视频也会从零进行操作演示(无需看以往相关视频)                                                         
(b)代码实现CrewAI的Flows功能，并支持Flow运行中间结果进行持久化存储和查询(MySQL)，支持多Flow并行(Celery是一个强大的异步任务队列/作业队列库)                                               
(c)代码实现将AI Agent工作流对外封装API接口提供服务，完成调度Flow接口和查看Flow中间结果接口，并使用Apifox进行前后端联调测试                                  
**(2)项目案例业务流程图如下所示:**                 
<img src="./img.png" alt="业务流程图" width="900" />                  
## 1.2、应用案例简介               
Flow中定义了2个Crew、3个Agent、5个Task                  
**(a)Crew1:市场分析**                
**Agent1:首席市场分析师**                                                    
分配的任务Task1:入分析其产品和主要竞争对手，挖掘关键趋势与相关洞察，确保收集到任何有价值的信息（限定2024年内）                               
**(b)Crew2:营销战略制定**                  
**Agent2:首席营销战略师**                                                
分配的任务1:详细了解项目背景和目标受众。审阅提供的材料并收集所需的其他信息                                
分配的任务2:制定全面的营销战略，综合研究任务与项目理解任务中的关键洞察，以构建高质量的战略方案                                
**Agent3:首席创意内容创作师**                                               
分配的任务1:构思创新的营销活动方案，确保创意独特且具吸引力，与整体营销战略保持一致                                
分配的任务2:编写营销文案，确保内容吸引人、清晰易懂，并适配目标受众

## 1.3 CrewAI介绍
### (1)简介    
CrewAI是一个用于构建多Agent协作应用的框架，它能够让多个具有不同角色和目标的Agent共同协作，完成复杂的任务                          
该工具可以将任务分解，分配给不同的Agent，借助它们的特定技能和工具，完成各自负责的子任务，最终实现整体任务目标              
官网:https://www.crewai.com/                                          
GitHub:https://github.com/crewAIInc/crewAI                                           
### (2)核心概念
**(1)Agents**          
是一个自主可控单元，通过编程可以实现执行任务、作出决定、与其他Agent协作交流，可类比为团队中的一员，拥有特定的技能和任务                                        
role(角色):定义Agent在团队中的角色                                          
goal(目标):定义Agent需要实现的目标                             
backstory(背景信息):定义Agent的背景描述信息                                              
**(2)Tasks**               
分配给Agent的具体任务，并定义任务所需的所有细节                                               
description(任务描述):简明扼要说明任务要求                                                 
agent(分配的Agent):分配负责该任务的Agent                                                
expected_output(期望输出):期望任务完成后输出的详细描述                                                         
Tools(工具列表):为Agent提供可用于执行该任务的工具列表                   
output_json(输出json):设置任务的输出为自定义的json数据格式                                
output_file(输出到文件):将任务结果输出到一个文件中，指定输出的文件格式                                                     
callback(回调函数):指定任务执行完成后的回调处理函数                                                 
**(3)Processes**                      
CrewAI中负责协调Agent执行任务,类似于团队中的项目经理,确保任务分配和执行效率与预定计划保持一致                       
目前拥有两种运行机制:                             
sequential(按顺序运行):以深思熟虑、系统化的方式推进各项任务，按照任务列表中预定义的顺序执行，一个任务的输出作为下一个任务的上下文                               
hierarchical(按顶层规划运行):允许指定一个自定义的管理角色的Agent，负责监督任务执行，包括计划、授权和验证。任务不是预先分配的，而是根据Agent的能力进行任务分配，审查产出并评估任务完成情况                          
**(4)Crews**          
1个crew代表一个协作团队，即一组协作完成一系列任务的Agent                            
Agents(Agent列表):分配给crew的Agents                                   
Tasks(任务列表):分配给crew的Tasks                                                
Process(运行机制):sequential(按顺序运行)、hierarchical(按顶层规划运行)                                                 
manager_llm(大模型):在Process为hierarchical下指定的大模型                                    
**(5)Flows**          
为构建复杂的AI Agent WorkFlow(工作流)设计的一个强大的技术框架                 
**核心特点:**           
(a)简化工作流程创建                      
轻松串联多个crew和任务(自定义的方法)，创建复杂的工作流              
(b)状态管理                  
Flows可以在工作流中的不同任务之间轻松管理和共享状态              
(c)事件驱动架构                                         
基于事件驱动模型构建可实现动态响应的工作流           
(d)灵活的控制流                 
在工作流中实现条件逻辑、循环、分支等逻辑控制                   
**关键参数:**            
(a)@start()装饰器                               
用于将一个方法标记为Flow的起点。在一个Flow中支持对多个方法进行@start()标记，当Flow启动时，所有用@start()装饰的方法都会并行执行           
(b)@listen装饰器                                    
用于将一个方法标记为Flow中的监听器。在一个Flow中支持对多个方法进行@listen()装饰，当Flow启动后被监听的方法执行完成后，所有用@listen()监听该方法的方法都会被执行             
(c)@router装饰器                                                         
在Flow中允许根据方法的输出内容来定义路由的执行逻辑，根据方法的输出指定不同的路由，从而动态控制执行流程                     
**条件控制:**              
(a)条件逻辑 or_()                             
Flows中@listen()中可以使用or_()函数允许监听多个方法，在这些被监听方法中任何一个执行完成后，监听该方法的方法就会被执行               
(b)条件逻辑 and_()                                           
Flows中@listen()中可以使用and_()函数允许监听多个方法，在这些被监听方法中全部执行完成后，监听该方法的方法就会被执                 
**结果输出:**                 
(a)检索结果的最后输出                              
运行Flow时，最终的输出是由最后完成的方法决定的                                 
(b)访问和更新状态                                  
状态可用于在Flow中的不同方法之间存储和共享数据                       
(c)状态管理                  
有效管理状态对于构建可靠、可维护的AI工作流至关重要。 Flows为非结构化、结构化状态管理提供了强大的机制，允许根据需求自行选择            
非结构化状态管理:所有状态都存储在Flow类的状态属性中。这种方法具有很大的灵活性，开发人员可随时添加或修改状态属性，而无需定义严格的模式            
结构化状态管理:利用预定义的模式来确保整个工作流程的一致性和类型安全性                      


# 2、前期准备工作
## 2.1 集成开发环境搭建  
anaconda提供python虚拟环境,pycharm提供集成开发环境                                              
**具体参考如下视频:**                        
【大模型应用开发-入门系列】03 集成开发环境搭建-开发前准备工作                         
https://youtu.be/KyfGduq5d7w                     
https://www.bilibili.com/video/BV1nvdpYCE33/                      

## 2.2 大模型LLM服务接口调用方案
(1)gpt大模型等国外大模型使用方案                  
国内无法直接访问，可以使用代理的方式，具体代理方案自己选择                        
这里推荐大家使用:https://nangeai.top/register?aff=Vxlp                        
(2)非gpt大模型方案 OneAPI方式或大模型厂商原生接口                                              
(3)本地开源大模型方案(Ollama方式)                                              
**具体参考如下视频:**                                           
【大模型应用开发-入门系列】04 大模型LLM服务接口调用方案                    
https://youtu.be/mTrgVllUl7Y               
https://www.bilibili.com/video/BV1BvduYKE75/                                                                                         

## 2.3 Apifox          
官网下载软件安装即可，进行接口调试                          
https://apifox.com/                

## 2.4 MySQL数据库安装          
官网下载软件安装即可。本项目使用的版本是8.4.3LTS                            
https://dev.mysql.com/downloads/mysql/8.0.html                
安装完成之后，新建一个数据库:crewai               

## 2.5 Redis安装、启动、测试       
### (1)Redis安装、启动            
**MacOS (使用 Homebrew)**            
brew install redis             
brew services start redis              
**Ubuntu**             
sudo apt update                 
sudo apt install redis-server              
sudo systemctl start redis              
**Windows**               
Redis 需手动下载并安装，下载地址：https://github.com/microsoftarchive/redis/releases                  
安装完成后，启动 Redis 服务器             
redis-server             
### (2)Redis测试              
确认 Redis 已成功启动，可以使用以下命令检查 Redis 服务状态                          
redis-cli ping                 

## 2.6 Google搜索引擎APIKEY申请          
进入官网进行申请即可，用于Google搜索引擎的API                                                              
https://serper.dev/                                          
https://serper.dev/dashboard                     


# 3、项目初始化
## 3.1 下载源码
GitHub或Gitee中下载工程文件到本地，下载地址如下：                
https://github.com/NanGePlus/CrewAIFlowsFullStack                                               
https://gitee.com/NanGePlus/CrewAIFlowsFullStack                                   

## 3.2 构建项目
使用pycharm构建一个项目，为项目配置虚拟python环境               
项目名称：CrewAIFlowsFullStack                   

## 3.3 将相关代码拷贝到项目工程中           
直接将下载的文件夹中的文件拷贝到新建的项目目录中               

## 3.4 安装项目依赖          
命令行终端中执行cd crewaiFlowsBackend 命令进入到该文件夹内，然后执行如下命令安装依赖包                                           
pip install -r requirements.txt            
每个软件包后面都指定了本次视频测试中固定的版本号           
**注意:** 截止2024.10.25，本项目crewai最新版本0.76.2，crewai-tools最新版本0.13.2，建议先使用要求的对应版本进行本项目测试，避免因版本升级造成的代码不兼容。测试通过后，可进行升级测试。          


# 4、项目测试          
### （1）运行main脚本启动API服务
cd crewaiFlowsBackend 命令进入到该文件夹内，分别执行如下命令启动服务:                                        
celery -A tasks worker --loglevel=info                   
uvicorn main:app --host 0.0.0.0 --port 8012                    
启动前，需根据自己的实际情况做如下配置:           
**(a)调整utils/myLLM.py代码中关于大模型配置相关的参数:**                                       
**openai模型相关配置 根据自己的实际情况进行调整**              
OPENAI_API_BASE = "https://api.wlai.vip/v1"            
OPENAI_CHAT_API_KEY = "sk-XmrIEFplNArLlYa0E8C5A7C5F82041FdBd923e9d115746D0"          
OPENAI_CHAT_MODEL = "gpt-4o-mini"           
**非gpt大模型相关配置(oneapi方案 通义千问为例) 根据自己的实际情况进行调整**              
ONEAPI_API_BASE = "http://139.224.72.218:3000/v1"            
ONEAPI_CHAT_API_KEY = "sk-0FxX9ncd0yXjTQF877Cc9dB6B2F44aD08d62805715821b85"               
ONEAPI_CHAT_MODEL = "qwen-max"               
**本地大模型相关配置(Ollama方案 qwen2.5:7b为例) 根据自己的实际情况进行调整**             
OLLAMA_API_BASE = "http://localhost:11434/v1"                
OLLAMA_CHAT_API_KEY = "ollama"          
OLLAMA_CHAT_MODEL = "qwen2.5:7b"                      
**服务访问的端口**                                  
PORT = 8012                            
**(b)调整tasks.py中CrewAI默认的大模型环境变量配置，主要目的是解决Task中output_json属性依赖大模型问题**                                     
**设置OpenAI的大模型的参数  Task中设置输出为:output_json时，需要用到默认的大模型**                 
os.environ["OPENAI_API_BASE"] = "https://api.wlai.vip/v1"                    
os.environ["OPENAI_API_KEY"] = "sk-FQZgr4fvjIv8iKaTR8QgtvEEhdS6CfFcNI1EHUTiVqD0R4hr"                      
os.environ["OPENAI_MODEL_NAME"] = "gpt-4o-mini"                           
**设置google搜索引擎**                         
os.environ["SERPER_API_KEY"] = "ddfea55d4d309045283e518773f11b872c318f0d"                           
                               
                       
### （2）打开Apifox进行测试            
在Apifox中新建项目，将提供的crewaiFlowsBackend文件夹下的./others/apifox.json接口文件导入            
然后，测试运行crew POST请求                
http://127.0.0.1:8012/api/crew                  
获取某次运行crew作业详情 GET请求                    
http://127.0.0.1:8012/api/crew/{jobId}        
请求体内容:              
{                 
    "customer_domain": "https://www.emqx.com/zh",                          
    "project_description": "EMQX是一种开源的分布式消息中间件，专注于处理物联网 (IoT) 场景下的大规模消息通信。它基于MQTT协议，能够实现高并发、低延迟的实时消息推送，支持设备之间、设备与服务器之间的双向通信。客户领域:分布式消息中间件解决方案,项目概述:创建一个全面的营销活动，以提高企业客户对 EMQX 服务的认识和采用。"                 
}                  





