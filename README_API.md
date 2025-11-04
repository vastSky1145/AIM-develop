# AI论文辅助系统 - FastAPI后端接口文档

## 项目简介

这是一个基于FastAPI的AI论文写作辅助系统后端，提供论文管理、AI辅助写作、知识库检索等功能。

## 技术栈

- **FastAPI**: 现代、高性能的Python Web框架
- **MongoDB**: 文档数据库，存储论文数据
- **ChromaDB**: 向量数据库，用于知识库检索
- **LangChain**: AI应用开发框架
- **JWT**: 用户认证

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements_fastapi.txt
```

### 2. 配置环境变量

复制`.env.example`为`.env`并填入配置：

```bash
cp .env.example .env
```

### 3. 启动MongoDB

确保MongoDB服务已启动：

```bash
# Windows
net start MongoDB

# Linux/Mac
sudo systemctl start mongod
```

### 4. 运行服务器

```bash
# 开发模式（自动重载）
python app.py

# 或使用uvicorn
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### 5. 访问API文档

启动后访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API接口概览

### 认证模块 (`/api/auth`)

- `POST /api/auth/login` - 用户登录
- `POST /api/auth/register` - 用户注册（待实现）
- `GET /api/auth/me` - 获取当前用户信息

### 论文管理 (`/api/papers`)

- `GET /api/papers/list` - 获取论文列表
- `POST /api/papers/upload-ppt` - 上传PPT并解析
- `POST /api/papers/create` - 创建新论文
- `PUT /api/papers/update` - 更新论文
- `DELETE /api/papers/delete` - 删除论文
- `GET /api/papers/get/{paper_title}` - 获取论文详情

### AI辅助写作 (`/api/ai`)

- `POST /api/ai/generate` - AI生成内容
- `POST /api/ai/modify` - AI修改内容

### 知识库管理 (`/api/knowledge`)

- `POST /api/knowledge/search` - 检索知识库
- `POST /api/knowledge/upload-pdf` - 上传PDF到知识库
- `GET /api/knowledge/sources` - 获取知识来源列表
- `DELETE /api/knowledge/delete` - 删除知识
- `DELETE /api/knowledge/clear` - 清空知识库

### Prompt模板 (`/api/prompts`)

- `GET /api/prompts/get/{ppt_id}` - 获取Prompt模板
- `POST /api/prompts/save` - 保存Prompt模板

## 认证说明

### 获取Token

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "sxs", "password": "123456"}'
```

响应：
```json
{
  "success": true,
  "message": "登录成功",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user_info": {
      "user_id": "sxs",
      "username": "sxs",
      "email": null
    },
    "expires_in": 604800
  }
}
```

### 使用Token

在请求头中添加Authorization：

```bash
curl -X GET http://localhost:8000/api/papers/list \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## 使用示例

### 1. 登录获取Token

```python
import requests

response = requests.post(
    "http://localhost:8000/api/auth/login",
    json={"username": "sxs", "password": "123456"}
)
token = response.json()["data"]["token"]
```

### 2. 获取论文列表

```python
headers = {"Authorization": f"Bearer {token}"}
response = requests.get(
    "http://localhost:8000/api/papers/list",
    headers=headers
)
papers = response.json()["data"]
```

### 3. 上传PPT

```python
with open("paper.pptx", "rb") as f:
    files = {"file": ("paper.pptx", f, "application/vnd.openxmlformats-officedocument.presentationml.presentation")}
    response = requests.post(
        "http://localhost:8000/api/papers/upload-ppt",
        files=files,
        headers=headers
    )
```

### 4. AI生成内容

```python
response = requests.post(
    "http://localhost:8000/api/ai/generate",
    headers=headers,
    json={
        "existing_text": "Introduction\n\nThis paper discusses...",
        "kb_content": "Related work from knowledge base...",
        "section_text": "Background section content...",
        "prompt_template": "请将已有内容$$补全，参考知识库$$和章节内容$$"
    }
)
generated = response.json()["data"]["generated_content"]
```

### 5. 知识库检索

```python
response = requests.post(
    "http://localhost:8000/api/knowledge/search",
    headers=headers,
    json={"query": "video streaming", "k": 6}
)
documents = response.json()["data"]["documents"]
```

## 响应格式

所有API响应遵循统一格式：

```json
{
  "success": true,
  "message": "操作成功",
  "data": { }
}
```

- `success`: 布尔值，表示请求是否成功
- `message`: 字符串，响应消息
- `data`: 任意类型，响应数据

## 错误处理

错误响应示例：

```json
{
  "detail": "错误描述信息"
}
```

常见HTTP状态码：
- `200`: 成功
- `400`: 请求参数错误
- `401`: 未认证或Token无效
- `403`: 无权限
- `404`: 资源不存在
- `500`: 服务器内部错误

## 开发说明

### 项目结构

```
.
├── app.py                 # FastAPI主应用
├── routers/              # 路由模块
│   ├── auth.py           # 认证路由
│   ├── papers.py         # 论文管理路由
│   ├── ai_assistant.py   # AI辅助路由
│   ├── knowledge.py      # 知识库路由
│   └── prompts.py        # Prompt模板路由
├── schemas/              # 数据模型
│   ├── common.py         # 通用模型
│   ├── user.py           # 用户模型
│   ├── paper.py          # 论文模型
│   ├── ai.py             # AI模型
│   ├── knowledge.py      # 知识库模型
│   └── prompt.py         # Prompt模型
├── utils/                # 工具函数
│   └── auth.py           # 认证工具
├── AI.py                 # LLM配置
├── mongodb.py            # 数据库操作
├── models.py             # 数据模型定义
├── ppt_to_json.py        # PPT解析
├── filter.py             # 内容过滤
└── test.py               # 知识库管理
```

### 添加新接口

1. 在`schemas/`中定义数据模型
2. 在`routers/`中创建路由处理函数
3. 在`app.py`中注册路由

### 测试API

使用Swagger UI或Postman进行测试。

## 部署

### 使用Gunicorn（生产环境）

```bash
pip install gunicorn
gunicorn app:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### 使用Docker

创建`Dockerfile`：

```dockerfile
FROM python:3.10
WORKDIR /app
COPY requirements_fastapi.txt .
RUN pip install -r requirements_fastapi.txt
COPY . .
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

构建并运行：

```bash
docker build -t paper-assistant-api .
docker run -p 8000:8000 paper-assistant-api
```

## 常见问题

### Q: MongoDB连接失败？
A: 确保MongoDB服务已启动，检查连接字符串是否正确。

### Q: 上传PPT失败？
A: 确保安装了comtypes（Windows）且PowerPoint已安装。

### Q: 向量数据库初始化慢？
A: 首次运行需要下载HuggingFace模型，可能需要几分钟。

### Q: Token过期怎么办？
A: Token默认7天有效期，过期后需要重新登录获取新Token。

## 许可证

MIT License

## 联系方式

如有问题请提交Issue。

