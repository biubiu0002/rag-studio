# 项目模型架构说明

## 概述

本项目采用**三层模型架构**，实现了清晰的关注点分离：

1. **`database/models.py`** - SQLAlchemy ORM模型（数据库层）
2. **`models/`** - Pydantic业务模型（业务逻辑层）
3. **`schemas/`** - Pydantic API Schema（API层）

## 三层架构详解

### 1. Database层 (`database/models.py`)

**职责**：定义数据库表结构，负责数据持久化

**特点**：
- 使用 **SQLAlchemy ORM**
- 继承自 `Base`（SQLAlchemy的declarative_base）
- 模型名以 `ORM` 结尾（如 `TestSetORM`, `KnowledgeBaseORM`）
- 包含数据库相关配置：
  - 表名（`__tablename__`）
  - 列类型和约束（`Column`, `ForeignKey`, `Index`）
  - 索引和唯一约束（`__table_args__`）
  - 数据库默认值（`server_default`）

**示例**：
```python
class TestSetORM(Base):
    """测试集ORM模型"""
    __tablename__ = "test_sets"
    
    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    test_type = Column(SQLEnum(TestTypeEnum), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
```

**使用场景**：
- 数据库迁移脚本
- Repository层的数据库操作
- 直接映射到数据库表

---

### 2. Models层 (`models/`)

**职责**：定义业务逻辑层的数据模型，用于服务层处理

**特点**：
- 使用 **Pydantic**
- 继承自 `BaseModelMixin`（Pydantic的`BaseModel`）
- 模型名无后缀（如 `TestSet`, `KnowledgeBase`）
- 包含业务验证规则：
  - 字段验证（`min_length`, `max_length`, `ge`, `le`等）
  - 枚举类型（`TestType`, `TestStatus`等）
  - 字段描述和示例（`json_schema_extra`）
- 支持从ORM模型自动转换（`from_attributes = True`）

**文件组织**：
```
models/
├── base.py              # 基础模型混入类
├── test.py              # 测试相关模型
├── evaluation.py        # 评估相关模型
├── knowledge_base.py    # 知识库模型
├── document.py          # 文档模型
└── task_queue.py        # 任务队列模型
```

**示例**：
```python
class TestSet(BaseModelMixin):
    """测试集模型"""
    
    name: str = Field(..., description="测试集名称", min_length=1, max_length=100)
    test_type: TestType = Field(..., description="测试类型")
    case_count: int = Field(default=0, description="测试用例数量")
    
    class Config:
        from_attributes = True  # 允许从ORM模型创建
```

**使用场景**：
- Service层的业务逻辑处理
- 数据验证和转换
- 业务规则实现

---

### 3. Schemas层 (`schemas/`)

**职责**：定义API请求和响应的数据格式，用于接口层验证

**特点**：
- 使用 **Pydantic**
- 按操作类型分类：
  - `Create` - 创建请求（如 `TestSetCreate`）
  - `Update` - 更新请求（如 `TestSetUpdate`）
  - `Response` - 响应格式（如 `TestSetResponse`）
- 只包含API需要的字段
- 包含请求示例（`json_schema_extra`）
- 支持从ORM模型自动转换（`from_attributes = True`）

**文件组织**：
```
schemas/
├── common.py            # 通用Schema（分页、ID响应等）
├── test.py              # 测试相关Schema
├── knowledge_base.py    # 知识库Schema
└── document.py          # 文档Schema
```

**示例**：
```python
class TestSetCreate(BaseModel):
    """创建测试集请求"""
    name: str = Field(..., description="测试集名称", min_length=1, max_length=100)
    test_type: TestType = Field(..., description="测试类型")

class TestSetResponse(BaseModel):
    """测试集响应"""
    id: str
    name: str
    test_type: TestType
    case_count: int
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True  # 允许从ORM模型创建
```

**使用场景**：
- Controller层的请求验证
- API响应格式化
- OpenAPI文档生成

---

## 数据流转过程

### 完整的数据流转图

```
┌─────────────────────────────────────────────────────────────┐
│                    API层 (Controller)                        │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Schema: TestSetCreate (请求验证)                    │   │
│  │  Schema: TestSetResponse (响应格式化)                │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  业务层 (Service)                            │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Model: TestSet (业务逻辑处理)                       │   │
│  │  - 业务规则验证                                       │   │
│  │  - 数据转换和处理                                     │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                 仓储层 (Repository)                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Model ↔ ORM 转换                                    │   │
│  │  - _pydantic_to_orm()                                │   │
│  │  - _orm_to_pydantic()                                │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                 数据库层 (Database)                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  ORM: TestSetORM (表结构定义)                        │   │
│  │  - 数据库约束                                         │   │
│  │  - 索引和关系                                         │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 创建流程示例

**完整代码示例**：

```python
# ========== 1. Controller层 (schemas/test.py) ==========
@router.post("/test-sets")
async def create_test_set(data: TestSetCreate):  # ← 接收Schema
    """
    TestSetCreate Schema:
    - name: str (验证: min_length=1, max_length=100)
    - test_type: TestType (枚举验证)
    - description: Optional[str]
    """
    test_service = TestService()
    test_set = await test_service.create_test_set(data)  # ← 返回Model
    
    # 转换为Response Schema
    response = TestSetResponse.model_validate(test_set.model_dump())
    return success_response(data=response.model_dump())


# ========== 2. Service层 (services/test_service.py) ==========
async def create_test_set(self, data: TestSetCreate) -> TestSet:  # ← 接收Schema，返回Model
    """
    TestSet Model:
    - id: str
    - name: str
    - test_type: TestType
    - case_count: int
    - created_at: datetime
    - updated_at: datetime
    """
    test_set_id = f"ts_{uuid.uuid4().hex[:12]}"
    
    # Schema → Model: 使用model_dump()转换为字典，然后创建Model
    create_data = data.model_dump(exclude_none=True)
    create_data['id'] = test_set_id
    
    test_set = TestSet(**create_data)  # ← 创建Model对象
    
    # 传递给Repository
    await self.test_set_repo.create(test_set)  # ← 返回Model
    return test_set


# ========== 3. Repository层 (repositories/mysql_repository.py) ==========
async def create(self, entity: TestSet) -> TestSet:  # ← 接收Model，返回Model
    """
    TestSetORM:
    - id = Column(String(50), primary_key=True)
    - name = Column(String(100), nullable=False)
    - test_type = Column(SQLEnum(TestTypeEnum), nullable=False)
    """
    def _create_sync():
        db = SessionLocal()
        try:
            # Model → ORM: 转换为ORM对象
            orm_obj = self._pydantic_to_orm(entity)  # ← TestSet → TestSetORM
            
            db.add(orm_obj)
            db.commit()
            db.refresh(orm_obj)
            
            # ORM → Model: 转换回Model对象
            return self._orm_to_pydantic(orm_obj)  # ← TestSetORM → TestSet
        finally:
            db.close()
    
    return await asyncio.to_thread(_create_sync)
```

### 查询流程示例

```python
# ========== 1. Controller层 ==========
@router.get("/test-sets/{test_set_id}")
async def get_test_set(test_set_id: str):
    test_service = TestService()
    test_set = await test_service.get_test_set(test_set_id)  # ← 返回Model
    
    if not test_set:
        raise NotFoundException("测试集不存在")
    
    # Model → Response Schema
    response = TestSetResponse.model_validate(test_set.model_dump())
    return success_response(data=response.model_dump())


# ========== 2. Service层 ==========
async def get_test_set(self, test_set_id: str) -> Optional[TestSet]:
    # 直接返回Repository的Model结果
    return await self.test_set_repo.get_by_id(test_set_id)


# ========== 3. Repository层 ==========
async def get_by_id(self, entity_id: str) -> Optional[TestSet]:
    def _get_sync():
        db = SessionLocal()
        try:
            # 查询ORM对象
            orm_obj = db.query(self.orm_model).filter(
                self.orm_model.id == entity_id
            ).first()
            
            if not orm_obj:
                return None
            
            # ORM → Model: 转换回Model对象
            return self._orm_to_pydantic(orm_obj)  # ← TestSetORM → TestSet
        finally:
            db.close()
    
    return await asyncio.to_thread(_get_sync)
```

---

## 三层对比表

| 特性 | Database层 (ORM) | Models层 (Pydantic) | Schemas层 (Pydantic) |
|------|------------------|---------------------|---------------------|
| **框架** | SQLAlchemy | Pydantic | Pydantic |
| **职责** | 数据库表结构 | 业务逻辑模型 | API请求/响应 |
| **命名** | `TestSetORM` | `TestSet` | `TestSetCreate/Response` |
| **字段** | 数据库列定义 | 业务字段+验证 | API字段 |
| **验证** | 数据库约束 | 业务规则验证 | API参数验证 |
| **使用层** | Repository | Service | Controller |
| **转换** | 直接映射数据库 | 从ORM转换 | 从Model转换 |

---

## 为什么需要三层？

### 1. **关注点分离**
- **ORM层**：专注于数据库结构，不关心业务逻辑
- **Model层**：专注于业务逻辑，不关心API格式
- **Schema层**：专注于API接口，不关心数据库细节

### 2. **灵活性**
- 数据库结构变化不影响API
- API格式变化不影响业务逻辑
- 业务逻辑变化不影响数据库

### 3. **可维护性**
- 每层职责清晰，易于理解和修改
- 减少层间耦合
- 便于测试和调试

### 4. **类型安全**
- Pydantic提供运行时类型验证
- 清晰的类型提示
- IDE更好的代码补全

---

## 最佳实践

### 1. **命名规范**
- ORM模型：`{Entity}ORM`（如 `TestSetORM`）
- Model模型：`{Entity}`（如 `TestSet`）
- Schema：`{Entity}{Operation}`（如 `TestSetCreate`, `TestSetResponse`）

### 2. **字段映射**
- ORM → Model：使用 `from_attributes = True`
- Model → Schema：使用 `model_dump()` + `model_validate()`
- Schema → Model：使用 `model_dump()` + 构造函数

### 3. **验证规则**
- **ORM层**：数据库约束（`nullable`, `unique`, `index`）
- **Model层**：业务规则（`min_length`, `max_length`, `ge`, `le`）
- **Schema层**：API规则（请求参数验证）

### 4. **枚举类型**
- 在 `models/` 中定义枚举（如 `TestType`, `TestStatus`）
- 在 `database/models.py` 中定义对应的SQLAlchemy枚举（如 `TestTypeEnum`）
- Schema层引用Model层的枚举

---

## 常见问题

### Q1: 为什么Model和Schema都用Pydantic？
**A**: 虽然都用Pydantic，但职责不同：
- **Model**：业务逻辑层的完整数据模型
- **Schema**：API层的请求/响应格式（可能只包含部分字段）

### Q2: 可以直接用ORM模型作为API响应吗？
**A**: 不推荐。原因：
1. ORM模型包含数据库细节（如外键关系）
2. API响应应该只包含客户端需要的字段
3. 分离后可以独立演化

### Q3: 三层之间的转换性能如何？
**A**: Pydantic的转换性能很好，开销很小。如果性能成为瓶颈，可以考虑：
1. 使用 `model_validate()` 而不是手动转换
2. 缓存转换结果
3. 批量转换

---

## 总结

本项目通过三层模型架构实现了：
- ✅ **清晰的职责分离**：每层专注于自己的职责
- ✅ **灵活的架构设计**：各层可以独立演化
- ✅ **类型安全**：完整的类型提示和验证
- ✅ **易于维护**：代码结构清晰，易于理解和修改

这种架构设计符合**SOLID原则**中的单一职责原则，是一个成熟的企业级应用架构模式。

