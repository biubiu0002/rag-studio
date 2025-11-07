# 检索器评估系统 - 快速启动指南

## 🚀 5分钟快速开始

### 1. 准备环境

```bash
cd /Users/yeruijian/Documents/project/rag-studio/rag-studio/backend

# 激活虚拟环境
source .venv/bin/activate

# 安装依赖（如果还没安装）
pip install -r requirements.txt
```

### 2. 运行测试

```bash
# 运行功能测试
python test_retriever_eval.py
```

**预期输出:**
```
🚀 检索器评估系统测试
✅ T2Ranking数据集加载测试 - 通过
✅ 检索器评估功能测试 - 通过
🎉 所有测试通过！检索器评估系统已就绪。
```

### 3. 运行示例

```bash
# 运行使用示例
python example_t2ranking_usage.py
```

**你将看到:**
- 数据集加载演示
- 单查询评估演示
- 批量评估演示
- 配置对比演示

### 4. 启动API服务

```bash
# 启动后端服务
python run.py
```

访问 API 文档: http://localhost:8000/api/v1/docs

## 📊 快速评估示例

### Python代码示例

```python
from app.services.dataset_loader import DatasetService
from app.services.retriever_evaluation import RetrieverEvaluator

# 1. 加载数据集（采样100个查询）
dataset = DatasetService.load_t2ranking(
    collection_path="/Users/yeruijian/Documents/知识库平台/dataset/T2Ranking/data/collection.tsv",
    queries_path="/Users/yeruijian/Documents/知识库平台/dataset/T2Ranking/data/queries.dev.tsv",
    qrels_path="/Users/yeruijian/Documents/知识库平台/dataset/T2Ranking/data/qrels.dev.tsv",
    max_queries=100
)

# 2. 创建评估器
evaluator = RetrieverEvaluator(top_k=10)

# 3. 评估检索结果
metrics = evaluator.evaluate_single_query(
    retrieved_doc_ids=["doc_1", "doc_2", "doc_5"],
    relevant_doc_ids=["doc_2", "doc_5", "doc_7"]
)

print(f"Precision: {metrics['precision']:.4f}")
print(f"Recall: {metrics['recall']:.4f}")
print(f"F1-Score: {metrics['f1_score']:.4f}")
print(f"NDCG: {metrics['ndcg']:.4f}")
```

### cURL API示例

```bash
# 1. 查看数据集统计
curl -X GET "http://localhost:8000/api/v1/retriever-evaluation/dataset-statistics" \
  -G \
  --data-urlencode "collection_path=/Users/yeruijian/Documents/知识库平台/dataset/T2Ranking/data/collection.tsv" \
  --data-urlencode "queries_path=/Users/yeruijian/Documents/知识库平台/dataset/T2Ranking/data/queries.dev.tsv" \
  --data-urlencode "qrels_path=/Users/yeruijian/Documents/知识库平台/dataset/T2Ranking/data/qrels.dev.tsv" \
  --data-urlencode "max_queries=100"

# 2. 导入数据集到知识库
curl -X POST "http://localhost:8000/api/v1/retriever-evaluation/import-t2ranking" \
  -H "Content-Type: application/json" \
  -d '{
    "kb_id": "kb_t2ranking",
    "test_set_name": "T2Ranking测试集",
    "collection_path": "/Users/yeruijian/Documents/知识库平台/dataset/T2Ranking/data/collection.tsv",
    "queries_path": "/Users/yeruijian/Documents/知识库平台/dataset/T2Ranking/data/queries.dev.tsv",
    "qrels_path": "/Users/yeruijian/Documents/知识库平台/dataset/T2Ranking/data/qrels.dev.tsv",
    "max_queries": 100,
    "description": "用于检索器评估的T2Ranking数据集"
  }'
```

## 📈 评估指标说明

| 指标 | 说明 | 范围 | 优秀标准 |
|-----|------|------|---------|
| **Precision@K** | 检索结果中相关文档的比例 | 0-1 | > 0.7 |
| **Recall@K** | 相关文档被检索到的比例 | 0-1 | > 0.7 |
| **F1-Score** | 精确率和召回率的调和平均 | 0-1 | > 0.7 |
| **MRR** | 第一个相关文档的排名倒数 | 0-1 | > 0.8 |
| **MAP** | 所有相关文档位置的平均精度 | 0-1 | > 0.7 |
| **NDCG** | 考虑排序位置的综合指标 | 0-1 | > 0.8 |
| **Hit Rate** | 至少检索到一个相关文档的比例 | 0-1 | > 0.9 |

## 🎯 典型使用场景

### 场景1: 对比不同向量数据库

```python
# 测试 Elasticsearch
evaluator_es = RetrieverEvaluator(top_k=10)
metrics_es = evaluator_es.evaluate_single_query(retrieved_es, relevant)

# 测试 Qdrant  
evaluator_qdrant = RetrieverEvaluator(top_k=10)
metrics_qdrant = evaluator_qdrant.evaluate_single_query(retrieved_qdrant, relevant)

# 对比结果
print(f"Elasticsearch F1: {metrics_es['f1_score']:.4f}")
print(f"Qdrant F1: {metrics_qdrant['f1_score']:.4f}")
```

### 场景2: 评估embedding模型

```python
# 测试不同的embedding模型
models = ["nomic-embed-text", "bge-large-zh", "text-embedding-ada-002"]

for model in models:
    # 使用该模型进行检索
    retrieved = retrieve_with_model(query, model)
    
    # 评估结果
    metrics = evaluator.evaluate_single_query(retrieved, relevant)
    print(f"{model}: F1={metrics['f1_score']:.4f}, NDCG={metrics['ndcg']:.4f}")
```

### 场景3: 优化检索参数

```python
# 测试不同的top_k值
for k in [5, 10, 20, 50]:
    evaluator = RetrieverEvaluator(top_k=k)
    metrics = evaluator.evaluate_batch(test_results)
    
    print(f"top_k={k}: Recall={metrics['recall']:.4f}")
```

## 💡 最佳实践

### 1. 数据集规模选择

```python
# 初次测试 - 快速验证
max_queries = 50

# 中等规模测试 - 可靠评估
max_queries = 100-200

# 完整测试 - 生产环境
max_queries = 500+
```

### 2. 评估流程

1. **Baseline建立** - 使用简单配置建立基准
2. **单因素测试** - 每次只改变一个参数
3. **记录结果** - 保存每次评估的配置和指标
4. **对比分析** - 使用图表对比不同配置

### 3. 性能优化

```python
# ✅ 推荐：使用采样
dataset = DatasetService.load_t2ranking(
    ...,
    max_queries=100,  # 限制查询数量
    max_docs=None     # 自动确定相关文档
)

# ❌ 不推荐：加载完整数据集（除非必要）
dataset = DatasetService.load_t2ranking(...)
```

## 🐛 常见问题

### Q1: 数据集文件找不到
**A:** 检查文件路径是否正确，确保有读取权限

### Q2: 内存不足
**A:** 使用 `max_queries` 和 `max_docs` 参数进行采样

### Q3: 评估结果不理想
**A:** 检查以下方面：
- 文档是否正确向量化
- embedding模型是否合适
- 检索参数是否合理
- 数据质量是否达标

### Q4: API响应慢
**A:** 考虑：
- 异步执行评估任务
- 减少测试用例数量
- 使用缓存机制

## 📚 更多资源

- **完整文档**: [README_RETRIEVER_EVAL.md](README_RETRIEVER_EVAL.md)
- **系统总结**: [SUMMARY_检索器评估系统.md](SUMMARY_检索器评估系统.md)
- **API文档**: http://localhost:8000/api/v1/docs
- **测试脚本**: [test_retriever_eval.py](test_retriever_eval.py)
- **使用示例**: [example_t2ranking_usage.py](example_t2ranking_usage.py)

## 🎉 开始使用

现在你已经准备好开始使用检索器评估系统了！

```bash
# 1. 运行测试验证
python test_retriever_eval.py

# 2. 查看示例
python example_t2ranking_usage.py

# 3. 启动API服务
python run.py

# 4. 开始评估你的检索系统！
```

**祝评估顺利！** 🚀

