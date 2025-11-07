# T2Ranking导入链路快速测试指南

## 🎯 目标

验证T2Ranking数据集导入到知识库的完整链路是否正常工作。

---

## ✅ 当前已实现的链路节点

```
1. ✅ 加载T2Ranking数据集（collection, queries, qrels）
2. ✅ 批量创建文档到知识库
3. ✅ 创建测试集
4. ✅ 批量创建测试用例
```

---

## 🚀 快速开始

### 方式1: 使用测试脚本（推荐）

```bash
# 1. 进入backend目录并激活虚拟环境
cd backend
source .venv/bin/activate

# 2. 运行链路测试脚本
python test_t2ranking_pipeline.py
```

**预期输出:**
```
============================================================
T2Ranking数据集导入链路测试
============================================================

【步骤1】加载T2Ranking数据集...
✅ 数据集加载成功:
   - 文档数: 100
   - 查询数: 10
   ...

【步骤2】创建测试知识库...
✅ 知识库创建成功:
   - ID: kb_abc123
   ...

【步骤3】批量导入文档到知识库...
✅ 文档导入完成:
   - 成功创建: 100 个
   - 失败: 0 个

【步骤4】创建测试集...
✅ 测试集创建成功

【步骤5】批量创建测试用例...
✅ 测试用例创建完成:
   - 成功创建: 10 个

============================================================
✅ 链路测试完成！
============================================================
```

---

### 方式2: 使用前端界面

#### 步骤1: 启动后端服务
```bash
cd backend
source .venv/bin/activate
python run.py
```

#### 步骤2: 启动前端服务
```bash
cd web
npm run dev
```

#### 步骤3: 访问检索器评估页面
1. 打开浏览器访问 http://localhost:3000
2. 点击侧边栏"检索器评估"
3. 点击"获取数据集统计"查看T2Ranking数据集信息
4. 点击"导入数据集到知识库"开始导入
5. 查看导入结果（文档数、测试用例数等）

---

### 方式3: 使用API直接测试

#### 1. 获取数据集统计
```bash
curl "http://localhost:8000/api/v1/retriever-evaluation/dataset-statistics?collection_path=/Users/yeruijian/Documents/知识库平台/dataset/T2Ranking/data/collection.tsv&queries_path=/Users/yeruijian/Documents/知识库平台/dataset/T2Ranking/data/queries.dev.tsv&qrels_path=/Users/yeruijian/Documents/知识库平台/dataset/T2Ranking/data/qrels.dev.tsv&max_queries=10"
```

#### 2. 先创建知识库
```bash
curl -X POST "http://localhost:8000/api/v1/knowledge-bases" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "测试知识库",
    "description": "用于T2Ranking测试",
    "embedding_model": "bge-m3:latest",
    "vector_db_type": "chromadb"
  }'
```

**记录返回的知识库ID，如: kb_abc123**

#### 3. 导入数据集
```bash
curl -X POST "http://localhost:8000/api/v1/retriever-evaluation/import-t2ranking" \
  -H "Content-Type: application/json" \
  -d '{
    "kb_id": "kb_abc123",
    "test_set_name": "T2Ranking测试集",
    "collection_path": "/Users/yeruijian/Documents/知识库平台/dataset/T2Ranking/data/collection.tsv",
    "queries_path": "/Users/yeruijian/Documents/知识库平台/dataset/T2Ranking/data/queries.dev.tsv",
    "qrels_path": "/Users/yeruijian/Documents/知识库平台/dataset/T2Ranking/data/qrels.dev.tsv",
    "max_queries": 10,
    "description": "测试导入"
  }'
```

---

## 📊 验证导入结果

### 检查文档是否创建成功

```bash
# 查询知识库的文档列表
curl "http://localhost:8000/api/v1/documents?kb_id=kb_abc123&page=1&page_size=10"
```

**预期看到:**
- 文档列表中包含导入的文档
- 每个文档有 `external_id` 字段（T2Ranking的原始doc_id）
- 每个文档的 `content` 字段包含文本内容

### 检查测试用例是否创建成功

```bash
# 先获取测试集ID
curl "http://localhost:8000/api/v1/tests/test-sets?kb_id=kb_abc123"

# 使用测试集ID查询测试用例
curl "http://localhost:8000/api/v1/tests/test-cases?test_set_id=ts_xxx&page=1&page_size=10"
```

**预期看到:**
- 测试用例列表
- 每个用例包含 `query` 和 `expected_chunks`
- `expected_chunks` 是新生成的document_id列表（不是原始doc_id）

---

## 🔍 验证数据映射

### 验证doc_id映射关系

**原始数据:** T2Ranking的doc_id (如 "1234567")  
**映射到:** Document.external_id = "1234567"  
**新ID:** Document.id = "doc_abc123"

**验证方法:**
```bash
# 查看某个文档的详情
curl "http://localhost:8000/api/v1/documents/doc_abc123"
```

应该看到:
```json
{
  "id": "doc_abc123",
  "external_id": "1234567",
  "name": "1234567",
  "content": "实际文档内容...",
  "metadata": {
    "source": "t2ranking",
    "import_method": "batch_create_from_dict"
  }
}
```

### 验证测试用例映射

**原始数据:** qrels中的 query_id → [doc_id列表]  
**映射到:** TestCase.expected_chunks = [新的document_id列表]

**验证方法:**
查看测试用例的metadata字段，应该包含:
```json
{
  "metadata": {
    "query_id": "原始query_id",
    "original_doc_ids": ["原始doc_id列表"]
  },
  "expected_chunks": ["新的document_id列表"]
}
```

---

## ⚠️ 常见问题

### 1. 数据集文件未找到

**错误:** `FileNotFoundError: [Errno 2] No such file or directory`

**解决:**
- 检查 `test_t2ranking_pipeline.py` 中的 `DATASET_PATHS` 配置
- 或前端 `retriever-evaluation.tsx` 中的 `defaultPaths`
- 确保路径指向实际的TSV文件

### 2. 知识库不存在

**错误:** `知识库不存在: kb_demo`

**解决:**
- 先创建知识库（方式3步骤2）
- 或使用前端创建知识库
- 将返回的kb_id替换到导入请求中

### 3. 导入成功但文档数为0

**原因:** 可能是max_docs或max_queries设置过小

**解决:**
- 调整 `max_docs` 和 `max_queries` 参数
- 或者不传这两个参数（导入全部数据）

### 4. 测试用例的expected_chunks为空

**原因:** doc_id映射失败，qrels中的doc_id在collection中不存在

**解决:**
- 检查collection.tsv和qrels.tsv的doc_id是否匹配
- 查看导入日志中的警告信息：`找不到文档映射: xxx`

---

## 📈 链路完整性检查清单

- [ ] 步骤1: 数据集统计接口正常返回
- [ ] 步骤2: 知识库创建成功
- [ ] 步骤3: 文档批量导入成功（created > 0, failed = 0）
- [ ] 步骤4: 测试集创建成功
- [ ] 步骤5: 测试用例批量创建成功（created > 0, failed = 0）
- [ ] 验证1: 文档包含external_id和content
- [ ] 验证2: 测试用例的expected_chunks不为空
- [ ] 验证3: doc_id映射关系正确

---

## 🎯 下一步（待实现）

当前链路只完成了数据导入，要执行检索评估还需要：

1. **文档向量化** ❌
   - 文档分块
   - 向量化（embedding）
   - 写入向量数据库

2. **检索功能** ❌
   - 查询向量化
   - 向量检索
   - 返回相关文档

3. **评估执行** ❌
   - 批量检索
   - 计算评估指标
   - 保存评估结果

---

## 📚 相关文档

- **完整链路分析:** `backend/链路排查_T2Ranking导入.md`
- **实施总结:** `backend/链路实施总结.md`
- **详细README:** `backend/README_RETRIEVER_EVAL.md`

---

## 💡 提示

如果你只是想验证数据导入功能，推荐使用**方式1（测试脚本）**，它会：
- 自动创建测试知识库
- 完整执行所有步骤
- 显示详细的日志和统计信息
- 出错时提供清晰的错误提示

测试脚本默认只导入100个文档和10个查询，速度很快（几秒钟），非常适合快速验证。

---

**最后更新:** 2025-11-07  
**状态:** 核心数据流已实现并测试通过 ✅

