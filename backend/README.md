# RAG Studio Backend

RAG管理平台后端服务 - 支持云边架构的知识库管理、链路排查和测试评估

## 技术栈

- **Web框架**: FastAPI
- **AI框架**: LangChain
- **数据库**: MySQL
- **AI服务**: Ollama (支持自研服务扩展)
- **向量数据库**: Elasticsearch / Qdrant / Milvus
- **存储方式**: JSON文件 / MySQL (可切换)

## 项目结构

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI应用入口
│   ├── config.py            # 配置管理
│   ├── core/                # 核心功能
│   │   ├── exceptions.py    # 异常处理
│   │   ├── middleware.py    # 中间件
│   │   └── response.py      # 统一响应格式
│   ├── models/              # 数据模型
│   ├── schemas/             # Pydantic schemas
│   ├── controllers/         # 控制器（路由处理）
│   ├── services/            # 业务逻辑服务
│   ├── repositories/        # 数据访问层
│   └── utils/               # 工具函数
├── storage/                 # JSON本地存储目录
├── pyproject.toml          # 项目配置和依赖（uv）
├── env.example             # 环境变量示例
└── README.md               # 项目说明
```

## 快速开始

### 前置要求

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) - 快速Python包管理器

安装uv：
```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# 或使用pip
pip install uv
```

### 1. 安装依赖

使用uv同步依赖并创建虚拟环境：

```bash
cd backend
uv sync
```

如果需要安装开发依赖：
```bash
uv sync --extra dev
```

### 2. 配置环境变量

复制 `env.example` 为 `.env` 并修改配置：

```bash
cp env.example .env
```

主要配置项：
- `STORAGE_TYPE`: 存储类型 (json/mysql)
- `OLLAMA_BASE_URL`: Ollama服务地址
- `VECTOR_DB_TYPE`: 向量数据库类型 (elasticsearch/qdrant/milvus)

### 3. 启动服务

使用uv运行（推荐，会自动使用虚拟环境）：

```bash
# 方式1：使用启动脚本（推荐）
uv run python run.py

# 方式2：使用 uvicorn 命令
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 方式3：生产环境（无热重载）
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

或者激活虚拟环境后运行：

```bash
# 激活虚拟环境（uv会在.venv目录创建虚拟环境）
source .venv/bin/activate  # macOS/Linux
# 或
.venv\Scripts\activate  # Windows

# 然后运行
python run.py
```

**注意**：请确保在 `backend` 目录下运行启动命令。

### 依赖管理

使用uv管理依赖：

```bash
# 添加新依赖
uv add <package-name>

# 添加开发依赖
uv add --dev <package-name>

# 移除依赖
uv remove <package-name>

# 同步依赖（根据pyproject.toml更新虚拟环境）
uv sync

# 更新所有依赖到最新版本
uv sync --upgrade
```

### 4. 访问文档

- Swagger UI: http://localhost:8000/api/v1/docs
- ReDoc: http://localhost:8000/api/v1/redoc

## 核心功能模块

### 1. 知识库管理
- 知识库创建、查询、更新、删除
- 文档上传和管理
- 知识库配置管理

### 2. 链路排查
- 知识库配置查看
- 文档处理流程追踪
- 文档嵌入过程
- 文档分词结果
- 索引写入状态
- 检索结果分析
- 生成结果分析

### 3. 测试管理
- 测试集管理
- 检索测试
- 生成测试
- 测试结果评估

## 架构特点

### 存储抽象
支持多种存储方式切换：
- **JSON文件存储**: 适合本地开发和链路排查
- **MySQL存储**: 适合生产环境（预留接口）

### AI服务抽象
- **Ollama集成**: 本地部署，支持多种模型
- **自研服务**: 预留HTTP接口，方便接入自研AI服务

### 向量数据库抽象
支持多种向量数据库：
- **Elasticsearch**: 强大的全文检索+向量检索
- **Qdrant**: 轻量级向量数据库，适合边缘部署
- **Milvus**: 高性能向量数据库，适合云端部署

## 开发规范

- 遵循 **MVC架构模式**
- 使用 **Pydantic** 进行请求验证
- 统一的 **异常处理机制**
- 统一的 **响应格式**
- 完善的 **日志记录**

## API响应格式

### 成功响应
```json
{
  "success": true,
  "data": {...},
  "message": "操作成功"
}
```

### 错误响应
```json
{
  "success": false,
  "error_code": "NOT_FOUND",
  "message": "资源不存在",
  "details": null
}
```

### 分页响应
```json
{
  "success": true,
  "data": [...],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "total_pages": 5
}
```

## License

MIT

