# T2Ranking数据集导入知识库 - 完整链路排查

## 概述

本文档详细分析T2Ranking数据集导入知识库的完整链路，标识每个节点的实现状态和缺失功能。

## 完整链路图

```
T2Ranking数据集文件
    ↓
【步骤1】加载数据集 ✅
    ↓ 输出：dataset对象
    ↓
【步骤2】导出数据集JSON ❌ (需实现)
    ↓ 输出：t2ranking_export.json
    ↓
【步骤3】批量创建文档 ❌ (需实现)
    ↓ 输出：documents.json
    ↓
【步骤4】批量向量化文档 ❌ (需实现)
    ↓ 输出：vectorized_docs.json
    ↓
【步骤5】创建测试集 ✅
    ↓ 输出：test_set.json
    ↓
【步骤6】批量创建测试用例 ❌ (需实现)
    ↓ 输出：test_cases.json
    ↓
【步骤7】执行检索评估 ❌ (需实现)
    ↓ 输出：evaluation_result.json
```

## 节点详细分析

### 步骤1：加载数据集 ✅ 已实现

**文件：** `backend/app/services/dataset_loader.py`

**功能：**
- ✅ 加载collection.tsv（文档集合）
- ✅ 加载queries.tsv（查询集合）
- ✅ 加载qrels.tsv（相关性标注）
- ✅ 获取统计信息
- ✅ 采样功能（max_docs, max_queries）

**输入：**
```json
{
  "collection_path": "/path/to/collection.tsv",
  "queries_path": "/path/to/queries.dev.tsv",
  "qrels_path": "/path/to/qrels.dev.tsv",
  "max_docs": 1000,
  "max_queries": 100
}
```

**输出：**
- dataset对象（内存）
- 包含：collection（字典）、queries（字典）、qrels（字典）

**测试方法：**
```bash
# 使用API测试
curl "http://localhost:8000/api/v1/retriever-evaluation/dataset-statistics?collection_path=/path/to/collection.tsv&queries_path=/path/to/queries.dev.tsv&qrels_path=/path/to/qrels.dev.tsv&max_queries=100"
```

---

### 步骤2：导出数据集JSON ❌ 需实现

**需要实现的接口：**
- `POST /retriever-evaluation/export-dataset`

**功能：**
- 将加载的数据集导出为JSON文件
- 支持后续手动检查和调试

**预期输入：**（同步骤1）

**预期输出：**
```json
{
  "metadata": {
    "dataset_name": "T2Ranking",
    "total_documents": 1000,
    "total_queries": 100,
    "export_time": "2025-11-07T10:00:00Z"
  },
  "collection": {
    "doc_001": "文档内容1...",
    "doc_002": "文档内容2..."
  },
  "queries": {
    "query_001": "查询文本1",
    "query_002": "查询文本2"
  },
  "qrels": {
    "query_001": ["doc_003", "doc_015"],
    "query_002": ["doc_008"]
  }
}
```

**保存位置：** `storage/exports/t2ranking_export_{timestamp}.json`

---

### 步骤3：批量创建文档 ❌ 需实现

**文件：** `backend/app/services/document.py`

**需要实现的方法：**
```python
async def batch_create_documents_from_dict(
    kb_id: str,
    documents: Dict[str, str],  # {doc_id: content}
    source: str = "t2ranking"
) -> List[Document]
```

**需要实现的接口：**
- `POST /documents/batch-create`
- `POST /documents/batch-import-json`（从JSON文件导入）

**预期输入：**
```json
{
  "kb_id": "kb_123",
  "source": "t2ranking",
  "documents": {
    "doc_001": "文档内容1...",
    "doc_002": "文档内容2..."
  }
}
```

或从JSON文件：
```json
{
  "kb_id": "kb_123",
  "json_file_path": "storage/exports/t2ranking_export_xxx.json"
}
```

**预期输出：**
```json
{
  "success": true,
  "data": {
    "created_count": 1000,
    "failed_count": 0,
    "documents": [
      {
        "id": "doc_abc123",
        "external_id": "doc_001",
        "kb_id": "kb_123",
        "name": "doc_001",
        "content": "文档内容1...",
        "status": "uploaded",
        "created_at": "2025-11-07T10:00:00Z"
      }
    ]
  }
}
```

**保存JSON：** `storage/exports/documents_{kb_id}_{timestamp}.json`

**状态：**
- ❌ document.py中没有批量创建方法
- ❌ 文档模型中没有external_id字段（用于保存原始doc_id）

---

### 步骤4：批量向量化文档 ❌ 需实现

**文件：** `backend/app/services/document.py`

**需要实现的方法：**
```python
async def batch_process_documents(
    kb_id: str,
    document_ids: List[str] = None  # None表示处理所有未处理的
) -> dict
```

**需要实现的接口：**
- `POST /documents/batch-process`

**功能流程：**
1. 获取知识库配置（embedding模型、向量DB配置等）
2. 批量文档分块（根据chunk_size、chunk_overlap）
3. 批量向量化（调用embedding服务）
4. 批量写入向量数据库
5. 更新文档状态

**预期输入：**
```json
{
  "kb_id": "kb_123",
  "document_ids": ["doc_abc123", "doc_abc124"],  // 为空则处理所有
  "batch_size": 50  // 批次大小
}
```

**预期输出：**
```json
{
  "success": true,
  "data": {
    "total_documents": 1000,
    "processed_documents": 1000,
    "total_chunks": 3500,
    "failed_documents": 0,
    "processing_time_seconds": 120.5,
    "chunks_per_document": 3.5
  }
}
```

**保存JSON：** `storage/exports/vectorized_docs_{kb_id}_{timestamp}.json`

**状态：**
- ❌ document.py的process_document只是标记状态，没有实际处理逻辑
- ❌ 没有批量处理方法
- ❌ _parse_document, _chunk_document, _embed_chunks, _index_chunks都未实现

---

### 步骤5：创建测试集 ✅ 已实现

**文件：** `backend/app/services/test_service.py`

**功能：**
- ✅ 创建测试集（create_test_set）

**输入：**
```json
{
  "name": "T2Ranking测试集",
  "description": "用于检索器评估",
  "kb_id": "kb_123",
  "test_type": "retrieval"
}
```

**输出：**
```json
{
  "success": true,
  "data": {
    "id": "ts_abc123",
    "name": "T2Ranking测试集",
    "kb_id": "kb_123",
    "test_type": "retrieval",
    "case_count": 0,
    "created_at": "2025-11-07T10:00:00Z"
  }
}
```

---

### 步骤6：批量创建测试用例 ❌ 需实现

**文件：** `backend/app/services/test_service.py`

**需要实现的方法：**
```python
async def batch_create_test_cases(
    test_set_id: str,
    test_cases: List[Dict[str, Any]]
) -> List[TestCase]
```

**需要实现的接口：**
- `POST /tests/test-cases/batch-create`
- `POST /tests/test-cases/batch-import-json`

**预期输入：**
```json
{
  "test_set_id": "ts_abc123",
  "test_cases": [
    {
      "query": "查询文本1",
      "expected_chunks": ["doc_003", "doc_015"],
      "metadata": {"query_id": "query_001"}
    },
    {
      "query": "查询文本2",
      "expected_chunks": ["doc_008"],
      "metadata": {"query_id": "query_002"}
    }
  ]
}
```

或从JSON导入：
```json
{
  "test_set_id": "ts_abc123",
  "json_file_path": "storage/exports/t2ranking_export_xxx.json"
}
```

**预期输出：**
```json
{
  "success": true,
  "data": {
    "created_count": 100,
    "failed_count": 0,
    "test_cases": [
      {
        "id": "tc_xyz789",
        "test_set_id": "ts_abc123",
        "kb_id": "kb_123",
        "query": "查询文本1",
        "expected_chunks": ["doc_003", "doc_015"],
        "created_at": "2025-11-07T10:00:00Z"
      }
    ]
  }
}
```

**保存JSON：** `storage/exports/test_cases_{test_set_id}_{timestamp}.json`

**状态：**
- ❌ test_service.py只有单个创建方法create_test_case
- ❌ 没有批量创建方法

---

### 步骤7：执行检索评估 ❌ 需实现

**文件：** 
- `backend/app/controllers/retriever_evaluation.py`
- `backend/app/services/retriever_evaluation.py`
- `backend/app/services/rag_service.py`

**需要完善的功能：**

1. **RAGService.retrieve** (rag_service.py:29-81)
   - ❌ 向量化查询
   - ❌ 向量检索
   - ❌ 返回chunk_id列表

2. **evaluate_retriever接口** (retriever_evaluation.py:136-233)
   - ❌ 调用RAGService.retrieve
   - ❌ 执行评估
   - ❌ 保存评估结果

**预期输入：**
```json
{
  "kb_id": "kb_123",
  "test_set_id": "ts_abc123",
  "top_k": 10,
  "vector_db_type": "chromadb",
  "embedding_provider": "ollama",
  "embedding_model": "bge-m3:latest"
}
```

**预期输出：**
```json
{
  "success": true,
  "data": {
    "evaluation_id": "eval_xyz789",
    "kb_id": "kb_123",
    "test_set_id": "ts_abc123",
    "total_queries": 100,
    "successful_queries": 100,
    "failed_queries": 0,
    "overall_metrics": {
      "precision": 0.85,
      "recall": 0.72,
      "f1_score": 0.78,
      "mrr": 0.90,
      "map": 0.88,
      "ndcg": 0.91,
      "hit_rate": 0.95
    },
    "config": {
      "top_k": 10,
      "vector_db_type": "chromadb",
      "embedding_provider": "ollama",
      "embedding_model": "bge-m3:latest"
    },
    "created_at": "2025-11-07T10:00:00Z"
  }
}
```

**保存JSON：** `storage/exports/evaluation_result_{evaluation_id}.json`

**状态：**
- ❌ RAGService.retrieve返回空列表
- ❌ evaluate_retriever的核心逻辑都注释掉了
- ❌ 没有保存评估结果到数据库

---

## 缺失功能汇总

### 后端需要实现

1. **数据导出功能**
   - [ ] POST /retriever-evaluation/export-dataset
   - [ ] 数据集JSON导出

2. **批量文档管理**
   - [ ] Document模型添加external_id字段
   - [ ] DocumentService.batch_create_documents_from_dict()
   - [ ] POST /documents/batch-create
   - [ ] POST /documents/batch-import-json

3. **批量文档处理**
   - [ ] DocumentService._parse_document()
   - [ ] DocumentService._chunk_document()
   - [ ] DocumentService._embed_chunks()
   - [ ] DocumentService._index_chunks()
   - [ ] DocumentService.batch_process_documents()
   - [ ] POST /documents/batch-process

4. **批量测试用例**
   - [ ] TestService.batch_create_test_cases()
   - [ ] POST /tests/test-cases/batch-create
   - [ ] POST /tests/test-cases/batch-import-json

5. **检索评估**
   - [ ] RAGService.retrieve()实现
   - [ ] evaluate_retriever完整实现
   - [ ] 评估结果保存到数据库

### 前端需要实现

1. **分步导入UI**
   - [ ] 步骤1：加载并预览数据集
   - [ ] 步骤2：导出数据集JSON
   - [ ] 步骤3：批量创建文档
   - [ ] 步骤4：批量向量化
   - [ ] 步骤5：创建测试集
   - [ ] 步骤6：批量创建测试用例
   - [ ] 步骤7：执行评估

2. **JSON管理**
   - [ ] 下载导出的JSON文件
   - [ ] 上传JSON文件作为输入
   - [ ] JSON文件预览

3. **进度监控**
   - [ ] 显示每步执行进度
   - [ ] 显示成功/失败统计
   - [ ] 错误信息展示

---

## 实施计划

### 阶段1：核心数据流（最小可行路径）

1. ✅ 加载数据集
2. 实现批量创建文档（不向量化，纯文本）
3. 实现批量创建测试用例
4. 前端基础UI

**目标：** 数据能完整导入，不做向量化

### 阶段2：向量化链路

1. 实现文档分块
2. 实现向量化
3. 实现向量索引

**目标：** 文档能被向量化并索引

### 阶段3：检索评估

1. 实现RAG检索
2. 实现评估逻辑
3. 保存评估结果

**目标：** 完整评估流程跑通

### 阶段4：JSON导入导出

1. 每步添加JSON导出
2. 每步支持JSON导入
3. 前端文件管理

**目标：** 每个节点都可独立测试

---

## 测试验证

每个步骤需要：
1. 单元测试
2. API集成测试
3. JSON导入导出测试
4. 前端E2E测试

---

## 文件清单

### 需要修改的文件

- `backend/app/models/document.py` - 添加external_id
- `backend/app/services/document.py` - 批量创建和处理
- `backend/app/services/test_service.py` - 批量创建测试用例
- `backend/app/services/rag_service.py` - 实现检索
- `backend/app/controllers/retriever_evaluation.py` - 完善接口
- `backend/app/controllers/document.py` - 添加批量接口
- `backend/app/controllers/test_management.py` - 添加批量接口

### 需要创建的文件

- `backend/app/services/document_processor.py` - 文档处理流水线
- `backend/test_t2ranking_pipeline.py` - 链路测试脚本
- `web/components/views/t2ranking-import-wizard.tsx` - 分步导入UI

---

## 总结

**已实现：** 2/7 步骤 (29%)
**需实现：** 5/7 步骤 (71%)

**核心问题：**
1. 批量操作缺失
2. 文档处理流水线未实现
3. 检索功能未实现
4. JSON导入导出机制缺失

**预计工作量：**
- 后端开发：5-7天
- 前端开发：2-3天
- 测试验证：2-3天
- 总计：9-13天

