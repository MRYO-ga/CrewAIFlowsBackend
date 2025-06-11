# API 模块说明

本目录包含了所有的API路由模块，按功能模块化组织，提供清晰的API结构。

## 目录结构

```
api/
├── __init__.py          # API模块初始化文件，统一导出所有路由器
├── accounts.py          # 账号管理API - 社交媒体账号CRUD操作
├── contents.py          # 内容管理API - 内容创建、编辑、发布管理
├── competitors.py       # 竞品分析API - 竞争对手分析和监控
├── schedules.py         # 发布计划API - 内容发布时间规划
├── chat.py             # 智能对话API - AI聊天和智能优化
├── analytics.py         # 数据分析API - 性能指标和分析报告
├── crew.py             # 工作流API - Agent协作和任务执行
└── README.md           # 本说明文件
```

## 各模块功能

### 1. accounts.py - 账号管理
**路由前缀：** `/api/accounts`

- **GET** `/` - 获取账号列表（支持平台、状态筛选）
- **GET** `/{account_id}` - 获取单个账号详情
- **POST** `/` - 创建新账号
- **PUT** `/{account_id}` - 更新账号信息
- **DELETE** `/{account_id}` - 删除账号
- **GET** `/{account_id}/analytics` - 获取账号数据分析

### 2. contents.py - 内容管理
**路由前缀：** `/api/contents`

- **GET** `/` - 获取内容列表（支持状态、分类筛选）
- **GET** `/{content_id}` - 获取单个内容详情
- **POST** `/` - 创建新内容
- **PUT** `/{content_id}` - 更新内容信息
- **DELETE** `/{content_id}` - 删除内容
- **PUT** `/{content_id}/status` - 更新内容状态
- **GET** `/account/{account_id}` - 获取指定账号的内容
- **GET** `/account/{account_id}/stats` - 获取账号内容统计

### 3. competitors.py - 竞品分析
**路由前缀：** `/api/competitors`

- **GET** `/` - 获取竞品列表（支持分类筛选）
- **GET** `/{competitor_id}` - 获取单个竞品详情
- **POST** `/` - 添加新竞品
- **PUT** `/{competitor_id}` - 更新竞品信息
- **DELETE** `/{competitor_id}` - 删除竞品
- **GET** `/search` - 搜索竞品（按名称模糊搜索）
- **GET** `/trending` - 获取热门竞品

### 4. schedules.py - 发布计划
**路由前缀：** `/api/schedules`

- 基础的发布计划管理功能（开发中）

### 5. chat.py - 智能对话
**路由前缀：** `/api`

- **POST** `/chat` - 智能聊天接口（支持MCP数据获取和分析）
- **POST** `/optimize` - 专门的数据优化接口
- **GET** `/user-context/{user_id}` - 获取用户数据上下文
- **GET** `/chat/history` - 获取聊天历史
- **POST** `/chat/save` - 保存聊天消息

### 6. analytics.py - 数据分析
**路由前缀：** `/api/analytics`

- 数据分析和报告功能（开发中）

### 7. tasks.py - 任务管理
**路由前缀：** `/api/tasks`

- **GET** `/` - 获取任务列表（支持状态、类型、负责人筛选）
- **GET** `/stats` - 获取任务统计信息
- **GET** `/{task_id}` - 获取单个任务详情
- **POST** `/` - 创建新任务
- **PUT** `/{task_id}` - 更新任务信息
- **DELETE** `/{task_id}` - 删除任务
- **POST** `/{task_id}/complete` - 完成任务
- **POST** `/{task_id}/start` - 开始任务
- **PUT** `/{task_id}/progress` - 更新任务进度
- **GET** `/overdue/list` - 获取超时任务列表

### 8. analytics.py - 数据分析
**路由前缀：** `/api/analytics`

- **GET** `/overview` - 获取数据分析总览
- **GET** `/content` - 获取内容数据分析
- **GET** `/accounts` - 获取账号数据分析
- **GET** `/competitors` - 获取竞品数据分析
- **GET** `/trends` - 获取趋势分析
- **GET** `/performance/report` - 获取性能报告
- **GET** `/dashboard/data` - 获取仪表板数据
- **GET** `/export/csv` - 导出分析数据为CSV
- **GET** `/insights/recommendations` - 获取智能洞察和建议
- **GET** `/metrics/comparison` - 获取指标对比分析

### 9. crew.py - 工作流管理
**路由前缀：** `/api`

- **POST** `/crew` - 启动Agent工作流
- **GET** `/crew/{job_id}` - 查询工作流状态
- **POST** `/chat` - 智能对话接口
- **POST** `/optimize` - 智能优化功能

## API使用示例

### 创建发布计划
```python
import requests

# 创建发布计划
data = {
    "title": "春季护肤专题发布",
    "description": "针对春季护肤需求制定的发布计划",
    "type": "single",
    "account_id": "1",
    "content_id": "3",
    "platform": "xiaohongshu",
    "publish_datetime": "2024-03-25T14:00:00",
    "note": "需要配合春季话题"
}

response = requests.post("http://localhost:8012/api/schedules/", json=data)
print(response.json())
```

### 创建任务
```python
# 创建内容创作任务
task_data = {
    "title": "制作春季护肤教程",
    "description": "针对春季护肤需求制作详细教程",
    "type": "content",
    "priority": "high",
    "assignee": "张编辑",
    "deadline": "2024-03-25T18:00:00",
    "account_id": "1",
    "tags": ["护肤", "教程", "春季"]
}

response = requests.post("http://localhost:8012/api/tasks/", json=task_data)
print(response.json())
```

### 获取数据分析
```python
# 获取数据分析总览
response = requests.get("http://localhost:8012/api/analytics/overview?days=30")
analytics = response.json()

print(f"总账号数: {analytics['total_accounts']}")
print(f"总内容数: {analytics['total_contents']}")
print(f"平均互动率: {analytics['avg_engagement_rate']}%")
```

### 启动AI工作流
```python
# 启动内容创作工作流
workflow_data = {
    "inputs": {
        "topic": "春季护肤",
        "target_audience": "18-25岁女性",
        "platform": "xiaohongshu",
        "content_type": "图文"
    },
    "agent_config": {
        "content_creator": True
    }
}

response = requests.post("http://localhost:8012/api/crew", json=workflow_data)
job_id = response.json()["job_id"]

# 查询工作流状态
status_response = requests.get(f"http://localhost:8012/api/crew/{job_id}")
print(status_response.json())
```

## 错误处理

所有API接口都使用标准的HTTP状态码：

- **200 OK** - 请求成功
- **201 Created** - 资源创建成功
- **400 Bad Request** - 请求参数错误
- **401 Unauthorized** - 未授权访问
- **404 Not Found** - 资源不存在
- **422 Unprocessable Entity** - 数据验证失败
- **500 Internal Server Error** - 服务器内部错误

错误响应格式：
```json
{
    "detail": "错误信息描述"
}
```

## 数据库模型关系

```
Account (账号)
├── Contents (内容) - 一对多
├── Schedules (发布计划) - 一对多
└── Tasks (任务) - 一对多

Content (内容)
├── Schedules (发布计划) - 一对多
└── Tasks (任务) - 一对多

Schedule (发布计划)
└── Tasks (任务) - 一对多

Competitor (竞品) - 独立表

ChatMessage (聊天记录) - 关联Account

Analytics (分析数据) - 独立表
```

## 开发和测试

1. **启动开发服务器**
```bash
cd crewaiFlowsBackend
python main.py
```

2. **访问API文档**
```
http://localhost:8012/docs
```

3. **运行API测试**
```bash
python test_api.py
```

4. **数据迁移**
```bash
python run_migration.py
```

## 部署说明

### 环境变量配置
```bash
# 数据库配置
DATABASE_URL=sqlite:///./social_media.db
# 或者使用MySQL
# DATABASE_URL=mysql+pymysql://user:password@localhost/dbname

# API密钥
OPENAI_API_KEY=your_openai_api_key
```

### Docker部署
```dockerfile
FROM python:3.10

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8012

CMD ["python", "main.py"]
```

## 注意事项

1. **数据库连接**：默认使用SQLite，生产环境建议使用MySQL
2. **API限流**：建议在生产环境中添加API限流机制
3. **认证授权**：当前为开发版本，生产环境需要添加认证机制
4. **日志记录**：建议添加详细的日志记录
5. **错误监控**：集成错误监控系统
6. **缓存机制**：对于频繁查询的数据可以添加缓存
7. **API版本控制**：后续版本更新时考虑API版本控制

## 使用说明

### 1. 路由器注册
所有路由器在 `__init__.py` 中统一导出，在 `main.py` 中注册：

```python
from api import (
    accounts_router, 
    contents_router, 
    competitors_router,
    schedules_router,
    chat_router,
    analytics_router,
    crew_router
)

app.include_router(accounts_router)
app.include_router(contents_router)
# ... 其他路由器
```

### 2. 数据模型
每个API模块使用对应的数据模型：
- `schemas/account_schemas.py` - 账号相关模型
- `schemas/content_schemas.py` - 内容相关模型
- `schemas/competitor_schemas.py` - 竞品相关模型
- 等

### 3. 服务层
每个API模块通过服务层处理业务逻辑：
- `services/account_service.py` - 账号业务逻辑
- `services/content_service.py` - 内容业务逻辑
- `services/competitor_service.py` - 竞品业务逻辑
- 等

## API文档

启动服务后，可通过以下地址访问自动生成的API文档：
- Swagger UI: `http://localhost:8012/docs`
- ReDoc: `http://localhost:8012/redoc`

## 开发指南

### 添加新的API模块

1. 在 `api/` 目录下创建新的模块文件，如 `new_module.py`
2. 创建对应的数据模型文件 `schemas/new_module_schemas.py`
3. 创建服务层文件 `services/new_module_service.py`
4. 在 `api/__init__.py` 中添加导入和导出
5. 在 `main.py` 中注册新路由器

### API开发规范

1. **路由命名**：使用RESTful规范
2. **错误处理**：统一使用HTTPException
3. **数据验证**：使用Pydantic模型
4. **文档注释**：为每个接口添加详细的docstring
5. **依赖注入**：使用FastAPI的依赖注入系统
6. **分页支持**：对于列表接口，支持limit和offset参数

## 安全性

- 所有接口支持CORS跨域请求
- 可根据需要添加认证和授权中间件
- 输入数据通过Pydantic模型进行验证和清理 