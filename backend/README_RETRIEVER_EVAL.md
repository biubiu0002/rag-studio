# 检索器评估系统使用指南

## 概述

本系统提供了一套完整的检索器测试评估框架，用于测试和评估向量库选择、检索算法配置以及检索质量。基于RAGAS评估框架和T2Ranking标准数据集。

## 核心功能

### 1. 数据集管理
- 支持T2Ranking数据集导入
- 自动采样优化大规模数据集
- 数据集统计分析

### 2. 检索评估指标
- **Precision@K**: 精确率 - 检索结果中相关文档的比例
- **Recall@K**: 召回率 - 相关文档被检索到的比例  
- **F1-Score**: F1分数 - 精确率和召回率的调和平均
- **MRR**: 平均倒数排名 - 第一个相关文档的排名倒数
- **MAP**: 平均精度均值 - 所有相关文档位置的平均精度
- **NDCG**: 归一化折损累积增益 - 考虑排序位置的综合指标
- **Hit Rate**: 命中率 - 至少检索到一个相关文档的查询比例

### 3. 评估场景
- 对比不同向量数据库（Elasticsearch, Qdrant, Milvus）
- 评估不同embedding模型效果
- 测试不同检索算法配置
- 追踪检索质量变化趋势

## 架构设计

### 核心模块

```
backend/app/
├── services/
│   ├── dataset_loader.py         # T2Ranking数据集加载器
│   └── retriever_evaluation.py   # 检索器评估服务（含RAGAS集成）
├── controllers/
│   └── retriever_evaluation.py   # 评估API控制器
├── models/
│   ├── test.py                   # 测试相关模型（扩展评估指标）
│   └── retriever_evaluation.py   # 评估结果模型
├── schemas/
│   └── test.py                   # 扩展Schema支持评估配置
└── repositories/
    └── retriever_evaluation_repository.py  # 评估结果存储
```

## 快速开始

### 1. 安装依赖

```bash
# 激活虚拟环境
source .venv/bin/activate

# 安装依赖（包含ragas, datasets, pandas）
pip install -r requirements.txt
```

### 2. 准备T2Ranking数据集

数据集文件路径：
```
/Users/yeruijian/Documents/知识库平台/dataset/T2Ranking/data/
├── collection.tsv    # 文档集合
├── queries.dev.tsv   # 查询集
└── qrels.dev.tsv     # 相关性标注
```

### 3. 查看数据集统计信息

```bash
curl -X GET "http://localhost:8000/api/v1/retriever-evaluation/dataset-statistics" \
  -G \
  --data-urlencode "collection_path=/Users/yeruijian/Documents/知识库平台/dataset/T2Ranking/data/collection.tsv" \
  --data-urlencode "queries_path=/Users/yeruijian/Documents/知识库平台/dataset/T2Ranking/data/queries.dev.tsv" \
  --data-urlencode "qrels_path=/Users/yeruijian/Documents/知识库平台/dataset/T2Ranking/data/qrels.dev.tsv" \
  --data-urlencode "max_queries=100"
```

响应示例：
```json
{
  "code": 200,
  "message": "数据集统计信息获取成功",
  "data": {
    "total_documents": 8841,
    "total_queries": 100,
    "total_query_doc_pairs": 6423,
    "queries_with_relevant_docs": 100,
    "avg_relevant_docs_per_query": 64.23,
    "max_relevant_docs": 500,
    "min_relevant_docs": 1
  }
}
```

### 4. 导入T2Ranking数据集

```bash
curl -X POST "http://localhost:8000/api/v1/retriever-evaluation/import-t2ranking" \
  -H "Content-Type: application/json" \
  -d '{
    "kb_id": "kb_t2ranking",
    "test_set_name": "T2Ranking检索测试集",
    "collection_path": "/Users/yeruijian/Documents/知识库平台/dataset/T2Ranking/data/collection.tsv",
    "queries_path": "/Users/yeruijian/Documents/知识库平台/dataset/T2Ranking/data/queries.dev.tsv",
    "qrels_path": "/Users/yeruijian/Documents/知识库平台/dataset/T2Ranking/data/qrels.dev.tsv",
    "max_docs": 10000,
    "max_queries": 100,
    "description": "T2Ranking开发集，用于检索器评估"
  }'
```

**参数说明：**
- `kb_id`: 目标知识库ID（需要提前创建）
- `max_docs`: 最大文档数量，用于优化大数据集（可选）
- `max_queries`: 最大查询数量，用于采样测试（可选）

### 5. 执行检索器评估

```bash
curl -X POST "http://localhost:8000/api/v1/retriever-evaluation/evaluate" \
  -H "Content-Type: application/json" \
  -d '{
    "kb_id": "kb_001",
    "test_set_id": "ts_001",
    "top_k": 10,
    "vector_db_type": "elasticsearch",
    "embedding_provider": "ollama",
    "embedding_model": "nomic-embed-text"
  }'
```

响应示例：
```json
{
  "code": 200,
  "message": "评估完成",
  "data": {
    "evaluation_id": "eval_001",
    "overall_metrics": {
      "precision": 0.85,
      "recall": 0.78,
      "f1_score": 0.81,
      "mrr": 0.89,
      "map": 0.82,
      "ndcg": 0.87,
      "hit_rate": 0.95
    },
    "total_queries": 100,
    "successful_queries": 98,
    "failed_queries": 2
  }
}
```

### 6. 查看评估历史

```bash
curl -X GET "http://localhost:8000/api/v1/retriever-evaluation/evaluation-history?kb_id=kb_001&page=1&page_size=20"
```

### 7. 对比多个评估结果

```bash
curl -X GET "http://localhost:8000/api/v1/retriever-evaluation/compare-evaluations?evaluation_ids=eval_001,eval_002,eval_003"
```

## API文档

完整API文档访问：`http://localhost:8000/api/v1/docs`

### 主要接口

| 接口 | 方法 | 说明 |
|-----|------|-----|
| `/retriever-evaluation/dataset-statistics` | GET | 获取数据集统计 |
| `/retriever-evaluation/import-t2ranking` | POST | 导入T2Ranking数据集 |
| `/retriever-evaluation/evaluate` | POST | 执行检索器评估 |
| `/retriever-evaluation/evaluation-history` | GET | 查看评估历史 |
| `/retriever-evaluation/compare-evaluations` | GET | 对比评估结果 |

## 数据集优化建议

### T2Ranking数据集规模
- 完整数据集：约8841个文档，367个查询
- 建议采样：100-200个查询，可以显著加快评估速度

### 采样策略
```python
# 推荐配置
max_queries = 100  # 采样100个查询
max_docs = None    # 自动根据采样查询确定相关文档
```

系统会自动：
1. 采样指定数量的查询
2. 只加载与这些查询相关的文档
3. 显著减少内存占用和处理时间

## 评估流程

### 完整评估流程

```mermaid
graph LR
    A[准备数据集] --> B[导入数据集]
    B --> C[创建知识库]
    C --> D[文档向量化]
    D --> E[执行评估]
    E --> F[分析结果]
    F --> G[调整配置]
    G --> E
```

### 最佳实践

1. **初始评估**
   - 使用小规模采样（50-100个查询）
   - 快速验证系统配置
   - 确定baseline性能

2. **对比测试**
   - 固定测试集
   - 变化单一参数（如embedding模型）
   - 记录每次评估结果

3. **性能优化**
   - 根据评估指标调整配置
   - 重点关注F1-Score和NDCG
   - 平衡精确率和召回率

4. **长期监控**
   - 定期执行评估
   - 追踪性能趋势
   - 及时发现性能退化

## 评估指标解读

### Precision@10 vs Recall@10
- **高Precision，低Recall**: 检索保守，结果准但遗漏多
- **低Precision，高Recall**: 检索激进，覆盖广但噪声多
- **平衡F1-Score**: 综合考虑两者

### MRR vs MAP
- **MRR**: 关注第一个相关结果的位置，适合单答案场景
- **MAP**: 考虑所有相关结果，适合多答案场景

### NDCG
- 综合考虑相关性和排序位置
- 值越接近1.0越好
- 适合对比不同检索算法

## 下一步扩展

### 待实现功能
1. 完整的数据导入流程（文档向量化）
2. RAGAS框架的深度集成
3. 更多评估指标（BM25 baseline等）
4. 评估结果可视化
5. 自动化A/B测试
6. 检索链路详细分析

### 扩展方向
1. 支持更多标准数据集（BEIR, MS MARCO等）
2. 增加生成质量评估（基于RAGAS）
3. 支持自定义评估指标
4. 分布式评估支持

## 技术栈

- **评估框架**: RAGAS 0.1.9
- **数据处理**: Pandas 2.1.4
- **数据集**: Datasets 2.16.1
- **后端**: FastAPI + Python
- **存储**: JSON / MySQL

## 常见问题

### Q: 数据集太大怎么办？
A: 使用`max_queries`和`max_docs`参数进行采样。建议从100个查询开始。

### Q: 如何选择合适的top_k？
A: 通常使用10或20。可以测试不同值，观察Recall@K的变化。

### Q: 评估结果如何解释？
A: 
- F1 > 0.7: 优秀
- F1 0.5-0.7: 良好
- F1 < 0.5: 需要优化

### Q: 如何对比不同配置？
A: 保持测试集不变，只改变单一变量（如embedding模型），使用compare-evaluations接口对比。

## 参考资料

- [RAGAS文档](https://docs.ragas.io/)
- [T2Ranking数据集](https://github.com/thuir/T2Ranking)
- [信息检索评估指标](https://en.wikipedia.org/wiki/Evaluation_measures_(information_retrieval))

