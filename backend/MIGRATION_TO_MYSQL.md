# 从 JSON 切换到 MySQL 存储指南

## 概述

本指南将帮助您将 RAG Studio 的存储模式从 JSON 文件存储切换到 MySQL 数据库存储。

## 前置条件

1. **MySQL 数据库已安装并运行**
2. **已创建数据库**：
   ```sql
   CREATE DATABASE rag_studio CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```
3. **Python 依赖已安装**（包括 `pymysql` 或 `mysqlclient`）

## 操作步骤

### 步骤 1: 配置环境变量

编辑 `.env` 文件（或创建它），设置以下配置：

```bash
# 存储类型：从 json 改为 mysql
STORAGE_TYPE=mysql

# MySQL 数据库配置
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=rag_studio
```

### 步骤 2: 测试数据库连接

运行测试脚本检查数据库连接：

```bash
cd backend
python scripts/test_mysql_setup.py
```

如果连接失败，请检查：
- MySQL 服务是否运行
- 数据库配置是否正确
- 数据库用户是否有足够权限

### 步骤 3: 创建数据库表

运行迁移脚本创建所有必需的表：

```bash
cd backend
python migrations/005_create_all_tables.py
```

这将创建以下表：
- `knowledge_bases` - 知识库
- `documents` - 文档
- `document_chunks` - 文档分块
- `test_sets` - 测试集
- `test_cases` - 测试用例（已废弃，保留兼容性）
- `retriever_test_cases` - 检索器测试用例
- `generation_test_cases` - 生成测试用例
- `test_set_knowledge_bases` - 测试集-知识库关联
- `import_tasks` - 导入任务
- `evaluation_tasks` - 评估任务
- `evaluation_case_results` - 评估用例结果（已废弃）
- `evaluation_summaries` - 评估汇总
- `retriever_evaluation_results` - 检索器评估结果
- `generation_evaluation_results` - 生成评估结果
- `task_queue` - 任务队列

### 步骤 4: 迁移数据（可选）

如果您有现有的 JSON 数据需要迁移到 MySQL：

```bash
cd backend
python scripts/migrate_json_to_mysql.py
```

**注意**：
- 迁移脚本会跳过已存在的记录（基于 ID）
- 建议先备份 `storage/` 目录
- 迁移过程会显示进度和错误信息

### 步骤 5: 验证迁移

1. **检查表是否创建成功**：
   ```bash
   python scripts/test_mysql_setup.py
   ```

2. **重启应用**：
   ```bash
   python run.py
   ```

3. **测试功能**：
   - 访问知识库列表
   - 创建新的知识库
   - 上传文档
   - 运行测试和评估

## 故障排除

### 问题 1: 表重复定义错误

**错误信息**：
```
Table 'test_sets' is already defined for this MetaData instance
```

**解决方案**：
1. 重启 Python 应用（完全退出并重新启动）
2. 如果问题持续，检查是否有多个地方导入 `models.py`
3. 确保 `app/database/__init__.py` 中的 `Base` 只定义一次

### 问题 2: 表不存在错误

**错误信息**：
```
Table 'knowledge_bases' doesn't exist
```

**解决方案**：
1. 运行表创建脚本：
   ```bash
   python migrations/005_create_all_tables.py
   ```
2. 检查数据库连接配置
3. 确认数据库用户有 CREATE TABLE 权限

### 问题 3: 数据迁移失败

**可能原因**：
- JSON 文件格式不正确
- 数据字段不匹配
- 外键约束冲突

**解决方案**：
1. 检查 JSON 文件格式
2. 查看迁移脚本的错误日志
3. 手动修复数据后重新迁移

### 问题 4: 连接数据库失败

**错误信息**：
```
Can't connect to MySQL server
```

**解决方案**：
1. 检查 MySQL 服务是否运行：
   ```bash
   # macOS/Linux
   sudo service mysql status
   # 或
   brew services list | grep mysql
   ```
2. 检查防火墙设置
3. 验证数据库配置（主机、端口、用户名、密码）

## 回滚到 JSON 存储

如果需要回滚到 JSON 存储：

1. 修改 `.env` 文件：
   ```bash
   STORAGE_TYPE=json
   ```

2. 重启应用

3. **注意**：MySQL 中的数据不会自动删除，如果需要可以手动清理

## 数据备份建议

在切换存储模式之前，建议：

1. **备份 JSON 文件**：
   ```bash
   cp -r backend/storage backend/storage_backup_$(date +%Y%m%d)
   ```

2. **备份 MySQL 数据库**（切换后）：
   ```bash
   mysqldump -u root -p rag_studio > rag_studio_backup_$(date +%Y%m%d).sql
   ```

## 性能优化建议

切换到 MySQL 后，可以考虑以下优化：

1. **添加索引**：根据查询模式添加适当的索引
2. **连接池配置**：调整 `pool_size` 和 `max_overflow`
3. **查询优化**：使用 `select_related` 和 `prefetch_related` 减少查询次数

## 相关文件

- `backend/app/database/models.py` - ORM 模型定义
- `backend/app/repositories/mysql_repository.py` - MySQL 存储实现
- `backend/migrations/005_create_all_tables.py` - 表创建脚本
- `backend/scripts/migrate_json_to_mysql.py` - 数据迁移脚本
- `backend/scripts/test_mysql_setup.py` - 测试脚本

## 支持

如果遇到问题，请：
1. 查看日志文件：`backend/server.log`
2. 检查数据库日志
3. 运行测试脚本诊断问题

