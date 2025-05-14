# 小红书多Agent自动化运营系统

基于CrewAI框架的小红书多Agent自动化运营系统，实现账号管理、竞品分析、内容生成、合规检测、发布与互动的全流程自动化。

## 系统架构

系统由以下五大核心Agent构成，各司其职，协同工作：

1. **账号人设管理Agent (`PersonaManagerAgent`)**
   - 账号档案管理
   - 粉丝画像分析
   - 运营策略规划

2. **竞品分析Agent (`CompetitorAnalysisAgent`)**
   - 竞品筛选与监控
   - 爆款内容分析
   - 市场趋势洞察

3. **内容生成Agent (`ContentCreationAgent`)**
   - 内容结构设计
   - 文案与标题创作
   - 视觉元素建议

4. **合规检测Agent (`ComplianceCheckAgent`)**
   - 敏感词检测
   - 平台政策合规
   - 修改建议生成

5. **发布互动Agent (`PublicationAgent`)**
   - 内容定时发布
   - 互动数据收集
   - 评论自动回复

这些Agent在Manager Agent的协调下，可单独工作，也可组合成完整的工作流程。

## 技术栈

- **后端框架**: FastAPI + Celery
- **大语言模型**: OpenAI GPT/Claude (可配置)
- **任务队列**: Redis
- **数据存储**: Redis (也可扩展为MongoDB、PostgreSQL等)

## 快速开始

### 环境配置

1. 安装依赖:

```bash
pip install -r requirements.txt
```

2. 环境变量配置:

创建一个`.env`文件，配置以下环境变量:

```
OPENAI_API_KEY=你的OpenAI API密钥
OPENAI_BASE_URL=可选的API基础URL
ANTHROPIC_API_KEY=你的Anthropic API密钥(可选)
```

### 启动服务

1. 启动Redis服务:

```bash
redis-server
```

2. 启动Celery Worker:

```bash
cd crewaiFlowsBackend
celery -A tasks worker --loglevel=info
```

3. 启动FastAPI服务:

```bash
cd crewaiFlowsBackend
python main.py
```

服务将在`http://localhost:8012`启动。

## API接口

### 提交任务

```
POST /api/crew
```

请求体示例:

```json
{
  "operation_type": "content_creation",
  "category": "护肤",
  "requirements": "创建一篇关于新出的保湿面霜的测评内容",
  "account_id": "account_123",
  "keywords": ["保湿面霜", "干皮", "敏感肌"],
  "target_audience": {
    "age": "25-34",
    "gender": "female",
    "interests": ["护肤", "美妆"]
  }
}
```

响应示例:

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "任务已提交，正在处理中"
}
```

### 查询任务状态

```
GET /api/crew/{job_id}
```

响应示例:

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "完成",
  "result": {
    "title": "敏感肌必入！这款面霜保湿效果惊人，我已经用了3瓶了",
    "content_sections": [
      {"type": "opening", "text": "..."},
      {"type": "product_intro", "text": "..."},
      {"type": "experience", "text": "..."},
      {"type": "comparison", "text": "..."},
      {"type": "closing", "text": "..."}
    ],
    "tags": ["面霜", "保湿", "敏感肌", "干皮"],
    "image_recommendations": [
      {"position": "cover", "description": "...", "style": "..."},
      {"position": "section_2", "description": "...", "style": "..."}
    ]
  },
  "events": [
    {"timestamp": "2023-10-15T10:00:00", "data": "任务开始执行"},
    {"timestamp": "2023-10-15T10:01:23", "data": "启动内容生成流程"},
    {"timestamp": "2023-10-15T10:05:45", "data": "任务执行完成"}
  ]
}
```

### 获取支持的Agent类型

```
GET /api/agent-types
```

### 获取系统能力

```
GET /api/capabilities
```

## 目录结构

```
crewaiFlowsBackend/
├── crews/                          # Agent模块目录
│   ├── personaManagerAgent/        # 账号人设管理Agent
│   ├── marketAnalystCrew/          # 竞品分析Agent
│   ├── contentCreationAgent/       # 内容生成Agent
│   ├── complianceCheckAgent/       # 合规检测Agent
│   └── publicationAgent/           # 发布互动Agent
├── utils/                          # 工具函数
│   ├── manager_agent.py            # 管理Agent工厂
│   ├── models.py                   # 数据模型定义
│   ├── myLLM.py                    # LLM管理工具
│   ├── jobManager.py               # 作业管理器
│   └── event_logger.py             # 事件日志工具
├── main.py                         # FastAPI主程序
├── tasks.py                        # Celery任务定义
└── requirements.txt                # 依赖列表
```

## 扩展功能

1. **支持多平台**: 当前专注于小红书，但架构设计支持扩展到其他平台
2. **自定义工作流**: 可以通过API组合不同的Agent创建自定义工作流
3. **素材库集成**: 可以集成图片生成和素材库管理功能
4. **数据分析**: 可以添加数据分析Agent进行运营效果评估

## 许可证

MIT License 