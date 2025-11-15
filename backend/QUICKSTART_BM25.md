# BM25 模型快速开始指南

## 🚀 最快 3 步启动

### 1️⃣ 安装依赖

```bash
cd /root/study-project/rag-studio/backend
pip install -r requirements.txt
```

### 2️⃣ 启动应用

```bash
python run.py
```

**该命令会自动：**
- ✅ 检查 BM25 模型是否存在
- ✅ 如果不存在，自动从 OSS 下载 (~45MB)
- ✅ 初始化模型
- ✅ 启动 FastAPI 服务

### 3️⃣ 验证完成

看到以下日志说明成功：

```
============================================================
🤖 检查且下载模型文件
============================================================
📦 处理 BM25 模型...
✅ BM25 模型文件已存在: .../bm25_zh_default.json
✅ BM25 模型文件有效
✅ 所有模型下载完成
============================================================

🚀 启动 RAG Studio Backend v1.0.0
...

🤖 初始化 AI 模型...
✅ BM25 模型初始化成功

Uvicorn running on http://0.0.0.0:8000
```

## 💻 在代码中使用

### 生成稀疏向量

```python
from app.config import settings
from app.services.sparse_vector_service import SparseVectorServiceFactory
import os

# 创建 BM25 服务（第一次创建时加载模型，之后返回单例）
service = SparseVectorServiceFactory.create(
    'bm25',
    model_path=os.path.join(settings.MODELS_PATH, settings.BM25_MODEL_NAME)
)

# 单个文本
text = "这是一个示例文本"
sparse_vector = service.generate_sparse_vector(text)
print(sparse_vector)
# 输出: {"indices": [...], "values": [...]}

# 批量文本
texts = ["文本1", "文本2", "文本3"]
sparse_vectors = service.generate_sparse_vector(texts)
# 输出: [{"indices": [...], "values": [...]}, ...]
```

### 使用其他稀疏向量算法

```python
# TF-IDF
tfidf_service = SparseVectorServiceFactory.create('tf-idf')

# Simple（词频）
simple_service = SparseVectorServiceFactory.create('simple')
```

## 🔍 手动操作

### 仅下载模型（不启动应用）

```bash
python scripts/download_models.py
```

### 验证设置

```bash
# 检查所有文件和代码
bash check_implementation.sh

# 检查语法（需要 Python 环境）
python3 -m py_compile app/services/sparse_vector_service.py app/config.py app/main.py run.py scripts/download_models.py
```

## 📋 常见问题

### Q：模型在哪里？

```
A：在 resources/models/bm25_zh_default.json
  尺寸：约 45 MB
  首次启动会自动下载
```

### Q：可以离线使用吗？

```
A：可以，但需要提前下载模型。
  运行: python scripts/download_models.py
  然后就可以离线启动应用了。
```

### Q：如何修改模型路径？

```python
# 编辑 app/config.py
MODELS_PATH: str = Field(
    default=os.path.join(PROJECT_ROOT, "your_path", "models")
)
```

### Q：模型下载很慢怎么办？

```
A：模型 ~45MB，取决于网络速度。
  支持断点续传，失败会自动重试。
  可以手动运行: python scripts/download_models.py
```

### Q：生产环境怎么部署？

```
A：建议提前下载模型：
  1. 在部署前运行: python scripts/download_models.py
  2. 或在 CI/CD 流程中添加该步骤
  3. 所有实例可共享 resources/models/ 目录
```

## 📚 详细文档

- 📖 **SETUP_BM25_MODEL.md** - 完整使用指南
- 📋 **BM25_MODEL_IMPLEMENTATION_SUMMARY.md** - 技术实施总结

## ✨ 核心特性

| 特性 | 说明 |
|------|------|
| 🤖 自动下载 | 项目启动前自动检查和下载模型 |
| 💾 智能缓存 | 已有模型不会重复下载 |
| 🔄 断点续传 | 网络中断后可继续下载 |
| ⚙️ 单例模式 | 模型只加载一次，提高性能 |
| 📊 详细日志 | 清晰的启动和错误日志 |
| 🛡️ 容错机制 | 模型下载失败不影响应用启动 |

## 🎯 下一步

1. **启动应用** → `python run.py`
2. **查看 API 文档** → `http://localhost:8000/api/v1/docs`
3. **集成到业务** → 在检索服务中使用 BM25
4. **深入了解** → 查看详细文档

---

**有问题？** 查看 SETUP_BM25_MODEL.md 的故障排除部分。
