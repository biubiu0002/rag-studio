# API接口联调指南

## 快速开始

### 1. 启动后端服务

```bash
cd backend
python run.py
```

服务将在 http://localhost:8000 启动

### 2. 访问API文档

- **Swagger UI**: http://localhost:8000/api/v1/docs
- **ReDoc**: http://localhost:8000/api/v1/redoc

### 3. 运行API测试

```bash
# 安装httpx（如果还没安装）
pip install httpx

# 运行测试脚本
python test_api.py
```

### 4. 启动前端

```bash
cd ../web
npm run dev
```

前端将在 http://localhost:3000 启动

## API测试示例

### 使用curl测试

#### 1. 健康检查
```bash
curl http://localhost:8000/api/v1/health
```

#### 2. 创建知识库
```bash
curl -X POST http://localhost:8000/api/v1/knowledge-bases \
  -H "Content-Type: application/json" \
  -d '{
    "name": "测试知识库",
    "description": "这是一个测试",
    "embedding_model": "nomic-embed-text",
    "vector_db_type": "qdrant"
  }'
```

#### 3. 获取知识库列表
```bash
curl http://localhost:8000/api/v1/knowledge-bases
```

#### 4. 获取知识库详情
```bash
curl http://localhost:8000/api/v1/knowledge-bases/{kb_id}
```

#### 5. 更新知识库
```bash
curl -X PUT http://localhost:8000/api/v1/knowledge-bases/{kb_id} \
  -H "Content-Type: application/json" \
  -d '{
    "name": "更新后的名称"
  }'
```

#### 6. 删除知识库
```bash
curl -X DELETE http://localhost:8000/api/v1/knowledge-bases/{kb_id}
```

### 使用Python测试

```python
import httpx

# 创建知识库
response = httpx.post(
    "http://localhost:8000/api/v1/knowledge-bases",
    json={
        "name": "我的知识库",
        "embedding_model": "nomic-embed-text",
        "vector_db_type": "qdrant"
    }
)
print(response.json())

# 获取列表
response = httpx.get("http://localhost:8000/api/v1/knowledge-bases")
print(response.json())
```

## 前后端联调

### 前端配置

前端已配置API地址（`web/.env.local`）：
```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

### 前端使用API

```typescript
import { knowledgeBaseAPI } from "@/lib/api"

// 创建知识库
const result = await knowledgeBaseAPI.create({
  name: "测试知识库",
  embedding_model: "nomic-embed-text",
  vector_db_type: "qdrant"
})

// 获取列表
const response = await knowledgeBaseAPI.list()
console.log(response.data)
```

## 当前已实现的功能

### ✅ 知识库管理
- [x] 创建知识库
- [x] 获取知识库列表（支持分页）
- [x] 获取知识库详情
- [x] 更新知识库
- [x] 删除知识库
- [x] 获取知识库配置
- [x] 获取知识库统计信息

### 📋 待实现功能
- [ ] 文档上传和管理
- [ ] 文档处理流程
- [ ] 检索测试
- [ ] 生成测试
- [ ] 链路排查工具

## 数据存储

当前使用JSON文件存储（用于开发调试）：
- 存储路径: `backend/storage/`
- 知识库数据: `storage/knowledge_bases.json`

可以直接查看和编辑JSON文件来验证数据。

## 故障排查

### 问题1: 前端无法连接后端

**检查**:
- 后端服务是否启动 (http://localhost:8000)
- CORS配置是否正确
- 浏览器控制台是否有跨域错误

**解决**:
```bash
# 检查后端CORS配置
# backend/.env
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001
```

### 问题2: API返回500错误

**检查**:
- 后端控制台错误日志
- storage目录是否存在且有写入权限

**解决**:
```bash
# 创建存储目录
mkdir -p backend/storage
```

### 问题3: 前端显示"加载失败"

**检查**:
- 浏览器开发者工具 Network 标签
- 查看具体的错误信息

**解决**:
- 确认API地址配置正确
- 确认后端服务正常运行

## 下一步

1. **测试基本CRUD**: 使用Swagger UI或test_api.py测试所有知识库API
2. **前端集成**: 在前端页面测试创建、查看、编辑、删除知识库
3. **实现文档上传**: 完成文档管理功能
4. **实现检索功能**: 集成向量数据库和检索

## 联系与支持

如遇到问题，请查看：
- 后端日志输出
- `storage/` 目录下的JSON文件
- API文档: http://localhost:8000/api/v1/docs

