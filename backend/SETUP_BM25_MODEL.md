# BM25 模型自动下载和初始化指南

## 概述

本项目已集成自动化的 BM25 模型管理系统，在项目启动时会自动检查并下载必要的模型文件。

## 系统架构

### 组件说明

1. **模型下载脚本** (`scripts/download_models.py`)
   - 负责从 OSS 下载 BM25 模型
   - 支持断点续传和重试机制
   - 自动检查文件是否已存在，避免重复下载
   - 支持文件完整性验证

2. **配置管理** (`app/config.py`)
   - `MODELS_PATH`: 模型存储目录（默认：`resources/models/`）
   - `BM25_MODEL_NAME`: 模型文件名（默认：`bm25_zh_default.json`）
   - `BM25_MODEL_URL`: 模型下载地址

3. **模型服务** (`app/services/sparse_vector_service.py`)
   - `BM25SparseVectorService`: BM25 稀疏向量生成服务
   - `SparseVectorServiceFactory`: 工厂类，支持创建 BM25 服务实例
   - 采用单例模式，避免重复加载模型

4. **应用启动** (`run.py`)
   - 在 FastAPI 应用启动前自动执行模型下载
   - 模型下载失败不会中断应用启动

5. **模型初始化** (`app/main.py`)
   - 在应用启动时加载 BM25 模型
   - 提供详细的启动日志

## 使用流程

### 1. 安装依赖

```bash
# 安装或升级 pip 依赖（包含 dashtext）
pip install -r requirements.txt
```

### 2. 启动应用（完全自动）

```bash
# 方式 1：使用启动脚本
cd /root/study-project/rag-studio/backend
python run.py

# 方式 2：使用 uvicorn 直接启动（需要手动执行模型下载）
# 建议先执行下面的脚本下载模型
python scripts/download_models.py
# 然后启动应用
uvicorn app.main:app --reload
```

### 3. 应用启动流程

启动应用时，会按顺序执行以下步骤：

```
🚀 启动应用
📁 工作目录: /root/study-project/rag-studio/backend

============================================================
🤖 检查且下载模型文件
============================================================
📦 处理 BM25 模型...
✅ BM25 模型文件已存在: /root/study-project/rag-studio/backend/resources/models/bm25_zh_default.json
✅ BM25 模型文件有效
✅ 所有模型下载完成
============================================================

🚀 启动 RAG Studio Backend v1.0.0
📍 地址: http://0.0.0.0:8000
📚 API文档: http://0.0.0.0:8000/api/v1/docs
🔄 调试模式: 开启

🤖 初始化 AI 模型...
✅ BM25 模型初始化成功

[...FastAPI启动日志...]
```

## 手动操作

### 单独下载模型

```bash
cd /root/study-project/rag-studio/backend
python scripts/download_models.py
```

输出示例：
```
============================================================
🤖 模型下载管理器
============================================================
模型存储路径: /root/study-project/rag-studio/backend/resources/models
============================================================

📦 处理 BM25 模型...
✅ BM25 模型文件已存在: .../bm25_zh_default.json
文件大小: 45.23 MB
✅ 文件哈希校验成功
✅ BM25 模型已就绪

============================================================
✅ 所有模型下载完成
============================================================
```

### 在代码中使用 BM25 模型

```python
from app.config import settings
from app.services.sparse_vector_service import SparseVectorServiceFactory

# 创建 BM25 服务实例（第一次创建时加载模型，之后返回单例）
bm25_service = SparseVectorServiceFactory.create(
    'bm25',
    model_path=os.path.join(settings.MODELS_PATH, settings.BM25_MODEL_NAME)
)

# 生成单个文本的稀疏向量
text = "这是一个测试文本"
sparse_vector = bm25_service.generate_sparse_vector(text)
# 输出：{"indices": [...], "values": [...]}

# 批量生成稀疏向量
texts = ["文本1", "文本2", "文本3"]
sparse_vectors = bm25_service.generate_sparse_vector(texts)
# 输出：[{"indices": [...], "values": [...]}, ...]
```

## 配置自定义

### 修改模型存储路径

编辑 `app/config.py`：

```python
# 模型配置
MODELS_PATH: str = Field(default=os.path.join(PROJECT_ROOT, "your_custom_path", "models"), description="模型文件存储路径")
```

### 修改下载地址

编辑 `.env` 文件或 `app/config.py`：

```python
BM25_MODEL_URL: str = Field(default="your_custom_url", description="BM25模型下载URL")
```

## 故障排除

### 1. 模型下载失败

**问题**：网络连接问题导致下载失败

**解决方案**：
```bash
# 删除失败的文件
rm -f resources/models/bm25_zh_default.json

# 手动重新下载
python scripts/download_models.py
```

### 2. 模型加载错误

**问题**：`FileNotFoundError: BM25 模型文件不存在`

**解决方案**：
```bash
# 检查模型文件是否存在
ls -lh resources/models/

# 如果不存在，运行下载脚本
python scripts/download_models.py
```

### 3. dashtext 导入失败

**问题**：`ImportError: No module named 'dashtext'`

**解决方案**：
```bash
# 安装 dashtext
pip install dashtext>=0.2.0
```

### 4. 内存不足

**问题**：加载模型时内存不足导致应用崩溃

**解决方案**：
- 增加系统可用内存
- 模型文件约 45MB，确保有足够的可用内存

## 性能优化

### 单例模式

BM25 服务使用单例模式，确保：
- 模型只加载一次，避免重复加载
- 多次调用返回同一实例
- 内存使用效率高

```python
# 多次调用都返回同一实例
service1 = SparseVectorServiceFactory.create('bm25', model_path=...)
service2 = SparseVectorServiceFactory.create('bm25', model_path=...)
assert service1 is service2  # True
```

### 断点续传

下载脚本支持断点续传：
- 网络中断后可继续下载
- 自动重试（最多 3 次）
- 指数退避策略

## 进阶配置

### 添加新的模型

1. 在 `download_models.py` 的 `model_config` 中添加新模型配置
2. 在 `config.py` 中添加对应的配置字段
3. 在 `run.py` 中更新 `ensure_models()` 函数

示例：

```python
# app/config.py
OTHER_MODEL_URL: str = Field(default="...", description="其他模型下载URL")

# run.py
model_config = {
    'bm25': {...},
    'other_model': {
        'name': settings.OTHER_MODEL_NAME,
        'url': settings.OTHER_MODEL_URL
    }
}
```

## 相关文件

- `scripts/download_models.py` - 模型下载管理脚本
- `app/config.py` - 应用配置
- `app/services/sparse_vector_service.py` - 稀疏向量服务
- `app/main.py` - FastAPI 应用入口
- `run.py` - 应用启动脚本
- `requirements.txt` - 项目依赖

## 最佳实践

1. **项目初始化**：第一次启动应用时会自动下载模型，无需手动操作
2. **生产环境**：可以提前运行 `python scripts/download_models.py` 预热模型，加快应用启动
3. **CI/CD 集成**：在部署流程中添加 `python scripts/download_models.py` 确保模型就绪
4. **多实例部署**：所有实例可共享 `resources/models/` 目录，避免重复下载

## 相关链接

- [DashVector 稀疏向量](https://dashvector.readthedocs.io/)
- [dashtext 库](https://github.com/alibaba/dashtext)
- [BM25 算法](https://en.wikipedia.org/wiki/Okapi_BM25)
