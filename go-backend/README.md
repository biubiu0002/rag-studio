# RAG Studio Go Backend

Go 版本的检索服务，用于压力测试和性能对比。

## 功能

- 实现统一检索接口 `/api/v1/debug/retrieve/unified`
- 支持语义向量检索（semantic 模式）
- 对接 Ollama embedding 服务
- 对接 Qdrant 向量数据库（同时支持 HTTP 6333 和 gRPC 6334 接口）
- 默认使用 HTTP 接口，可切换至 gRPC 接口

## 环境要求

- Go 1.21+
- Qdrant 服务运行中
- Ollama 服务运行中

## 配置

通过环境变量配置：

```bash
# 服务器配置
export HOST=0.0.0.0
export PORT=8001

# Ollama配置
export OLLAMA_BASE_URL=http://localhost:11434

# Qdrant配置
export QDRANT_HOST=localhost
export QDRANT_HTTP_PORT=6334  # 注意：Go客户端使用gRPC端口（6334），不是HTTP端口（6333  # HTTP接口端口
export QDRANT_GRPC_PORT=6334  # gRPC接口端口）
export QDRANT_API_KEY=  # 可选
```

### Qdrant 连接方式

系统同时支持 HTTP 和 gRPC 两种连接方式：

- **HTTP 接口（默认）**: 使用端口 6333，通过 REST API 与 Qdrant 通信
- **gRPC 接口**: 使用端口 6334，通过 gRPC 协议与 Qdrant 通信

默认使用 HTTP 接口，如需切换到 gRPC，可在代码中调用：

```go
qdrantService.SetUseHTTP(false)  // 切换到gRPC
```

## 构建和运行

```bash
# 设置代理（如果需要）
export https_proxy=http://192.168.0.50:7890

# 安装依赖
go mod tidy

# 构建
go build -o rag-studio-go-backend .

# 运行
./rag-studio-go-backend
```

## API 接口

### 统一检索接口

**POST** `/api/v1/debug/retrieve/unified`

请求体：

```json
{
  "kb_id": "kb_xxx",
  "query": "查询文本",
  "retrieval_mode": "semantic",
  "top_k": 10,
  "score_threshold": 0.0,
  "fusion_method": "rrf",
  "semantic_weight": 0.7,
  "keyword_weight": 0.3,
  "rrf_k": 60
}
```

响应：

```json
{
  "code": 0,
  "message": "semantic检索完成: 10 个结果",
  "data": {
    "query": "查询文本",
    "results": [
      {
        "doc_id": "doc_xxx",
        "chunk_id": "chunk_xxx",
        "content": "内容",
        "score": 0.95,
        "rank": 1,
        "source": "vector",
        "metadata": {}
      }
    ],
    "config": {
      "retrieval_mode": "semantic",
      "top_k": 10,
      "fusion_method": "rrf",
      "rrf_k": 60,
      "semantic_weight": 0.7,
      "keyword_weight": 0.3
    }
  }
}
```

### 健康检查

**GET** `/api/v1/debug/health`

响应：

```json
{
  "status": "ok"
}
```

## 注意事项

1. 知识库配置从 `../backend/storage/knowledge_bases.json` 读取
2. 目前只实现了语义向量检索（semantic 模式）
3. 稀疏向量和混合检索暂未实现
4. 确保 Qdrant 和 Ollama 服务正常运行

## 性能测试

可以使用压力测试工具对比 Python 版本和 Go 版本的性能：

```bash
# 使用wrk进行压力测试
wrk -t12 -c400 -d30s --script=test.lua http://localhost:8001/api/v1/debug/retrieve/unified
```
