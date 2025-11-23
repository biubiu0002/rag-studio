"""
SQLAlchemy ORM模型定义
"""

from sqlalchemy import Column, String, Integer, Text, DateTime, Enum as SQLEnum, Float, JSON, ForeignKey, Index, UniqueConstraint, Boolean
from sqlalchemy.sql import func
from app.database import Base
import enum


class TestTypeEnum(str, enum.Enum):
    RETRIEVAL = "retrieval"
    GENERATION = "generation"


class EvaluationStatusEnum(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ARCHIVED = "archived"


class TaskTypeEnum(str, enum.Enum):
    DOCUMENT_WRITE = "document_write"
    EVALUATION = "evaluation"
    TEST_SET_IMPORT = "test_set_import"


class TaskStatusEnum(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class TestSetORM(Base):
    """测试集ORM模型"""
    __tablename__ = "test_sets"
    
    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    kb_id = Column(String(50), nullable=True, index=True)  # 改为可空，用于兼容
    test_type = Column(SQLEnum(TestTypeEnum), nullable=False, index=True)
    case_count = Column(Integer, default=0)
    
    # 配置快照（JSON字段）- 这些配置现在保存在TestSetKnowledgeBase中
    kb_config = Column(JSON, nullable=True)
    chunking_config = Column(JSON, nullable=True)
    embedding_config = Column(JSON, nullable=True)
    sparse_vector_config = Column(JSON, nullable=True)
    index_config = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class TestSetKnowledgeBaseORM(Base):
    """测试集-知识库关联表ORM模型"""
    __tablename__ = "test_set_knowledge_bases"
    
    id = Column(String(50), primary_key=True)
    test_set_id = Column(String(50), nullable=False, index=True)  # 不使用外键，允许软删除
    kb_id = Column(String(50), nullable=False, index=True)  # 不使用外键，允许软删除
    imported_at = Column(DateTime, nullable=False, server_default=func.now())
    import_config = Column(JSON, nullable=True)  # 存储导入时的配置快照
    
    # 软删除标记
    kb_deleted = Column(Boolean, default=False, nullable=False)
    test_set_deleted = Column(Boolean, default=False, nullable=False)
    
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    
    # 唯一约束：同一测试集不能重复导入到同一知识库
    __table_args__ = (
        UniqueConstraint('test_set_id', 'kb_id', name='uq_test_set_kb'),
        Index('idx_test_set_kb', 'test_set_id', 'kb_id'),
    )


class ImportTaskORM(Base):
    """导入任务ORM模型"""
    __tablename__ = "import_tasks"
    
    id = Column(String(50), primary_key=True)
    test_set_id = Column(String(50), nullable=False, index=True)
    kb_id = Column(String(50), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="pending")  # pending/running/completed/failed
    progress = Column(Float, default=0.0)  # 0.0-1.0
    total_docs = Column(Integer, default=0)
    imported_docs = Column(Integer, default=0)
    failed_docs = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    import_config = Column(JSON, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    
    __table_args__ = (
        Index('idx_import_task_status', 'status'),
    )


class TestCaseORM(Base):
    """测试用例ORM模型（已废弃，保留用于兼容性）"""
    __tablename__ = "test_cases"
    
    id = Column(String(50), primary_key=True)
    test_set_id = Column(String(50), ForeignKey("test_sets.id", ondelete="CASCADE"), nullable=False, index=True)
    kb_id = Column(String(50), nullable=False, index=True)
    query = Column(Text, nullable=False)
    expected_chunks = Column(JSON, nullable=True)
    expected_answer = Column(Text, nullable=True)
    meta_data = Column('metadata', JSON, nullable=True)  # 使用 name 参数避免与 SQLAlchemy 保留属性冲突
    
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class RetrieverTestCaseORM(Base):
    """检索器测试用例ORM模型"""
    __tablename__ = "retriever_test_cases"
    
    id = Column(String(50), primary_key=True)
    test_set_id = Column(String(50), ForeignKey("test_sets.id", ondelete="CASCADE"), nullable=False, index=True)
    question = Column(Text, nullable=False)
    expected_answers = Column(JSON, nullable=False)  # Array of {answer_text, chunk_id, relevance_score}
    meta_data = Column('metadata', JSON, nullable=True)  # 使用 name 参数避免与 SQLAlchemy 保留属性冲突
    
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_retriever_test_case_test_set', 'test_set_id'),
    )


class GenerationTestCaseORM(Base):
    """生成测试用例ORM模型"""
    __tablename__ = "generation_test_cases"
    
    id = Column(String(50), primary_key=True)
    test_set_id = Column(String(50), ForeignKey("test_sets.id", ondelete="CASCADE"), nullable=False, index=True)
    question = Column(Text, nullable=False)
    reference_answer = Column(Text, nullable=False)
    reference_contexts = Column(JSON, nullable=True)  # Array of strings
    meta_data = Column('metadata', JSON, nullable=True)  # 使用 name 参数避免与 SQLAlchemy 保留属性冲突
    
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_generation_test_case_test_set', 'test_set_id'),
    )


class EvaluationTaskORM(Base):
    """评估任务ORM模型"""
    __tablename__ = "evaluation_tasks"
    
    id = Column(String(50), primary_key=True)
    test_set_id = Column(String(50), ForeignKey("test_sets.id"), nullable=False, index=True)
    kb_id = Column(String(50), nullable=False, index=True)
    evaluation_type = Column(SQLEnum(TestTypeEnum), nullable=False)
    task_name = Column(String(100), nullable=True)
    status = Column(SQLEnum(EvaluationStatusEnum), nullable=False, default=EvaluationStatusEnum.PENDING, index=True)
    
    retrieval_config = Column(JSON, nullable=True)
    generation_config = Column(JSON, nullable=True)
    
    total_cases = Column(Integer, default=0)
    completed_cases = Column(Integer, default=0)
    failed_cases = Column(Integer, default=0)
    
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class EvaluationCaseResultORM(Base):
    """评估用例结果ORM模型（已废弃，保留用于兼容性）"""
    __tablename__ = "evaluation_case_results"
    
    id = Column(String(50), primary_key=True)
    evaluation_task_id = Column(String(50), ForeignKey("evaluation_tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    test_case_id = Column(String(50), ForeignKey("test_cases.id"), nullable=False, index=True)
    query = Column(Text, nullable=False)
    
    retrieved_chunks = Column(JSON, nullable=True)
    retrieval_time = Column(Float, nullable=True)
    
    generated_answer = Column(Text, nullable=True)
    generation_time = Column(Float, nullable=True)
    
    retrieval_metrics = Column(JSON, nullable=True)
    ragas_retrieval_metrics = Column(JSON, nullable=True)
    ragas_generation_metrics = Column(JSON, nullable=True)
    ragas_score = Column(Float, nullable=True)
    
    status = Column(SQLEnum(EvaluationStatusEnum), nullable=False, default=EvaluationStatusEnum.PENDING)
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime, nullable=False, server_default=func.now())


class RetrieverEvaluationResultORM(Base):
    """检索器评估结果ORM模型"""
    __tablename__ = "retriever_evaluation_results"
    
    id = Column(String(50), primary_key=True)
    evaluation_task_id = Column(String(50), ForeignKey("evaluation_tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    test_case_id = Column(String(50), ForeignKey("retriever_test_cases.id"), nullable=False, index=True)
    question = Column(Text, nullable=False)
    expected_answers = Column(JSON, nullable=False)  # Array of {answer_text, chunk_id, relevance_score}
    retrieved_results = Column(JSON, nullable=False)  # Array of {chunk_id, chunk_text, score, rank, matched}
    retrieval_time = Column(Float, nullable=False)
    
    # 评估指标
    precision = Column(Float, nullable=True)
    recall = Column(Float, nullable=True)
    f1_score = Column(Float, nullable=True)
    mrr = Column(Float, nullable=True)
    map_score = Column(Float, nullable=True)
    ndcg = Column(Float, nullable=True)
    hit_rate = Column(Float, nullable=True)
    
    status = Column(SQLEnum(EvaluationStatusEnum), nullable=False, default=EvaluationStatusEnum.COMPLETED)
    
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    
    __table_args__ = (
        Index('idx_retriever_eval_task', 'evaluation_task_id'),
        Index('idx_retriever_eval_test_case', 'test_case_id'),
    )


class GenerationEvaluationResultORM(Base):
    """生成评估结果ORM模型"""
    __tablename__ = "generation_evaluation_results"
    
    id = Column(String(50), primary_key=True)
    evaluation_task_id = Column(String(50), ForeignKey("evaluation_tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    test_case_id = Column(String(50), ForeignKey("generation_test_cases.id"), nullable=False, index=True)
    question = Column(Text, nullable=False)
    
    retrieved_contexts = Column(JSON, nullable=False)  # Array of strings
    generated_answer = Column(Text, nullable=False)
    
    retrieval_time = Column(Float, nullable=False)
    generation_time = Column(Float, nullable=False)
    
    ragas_metrics = Column(JSON, nullable=False)  # {faithfulness, answer_relevancy, ...}
    llm_model = Column(String(100), nullable=True)
    
    status = Column(SQLEnum(EvaluationStatusEnum), nullable=False, default=EvaluationStatusEnum.COMPLETED)
    
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    
    __table_args__ = (
        Index('idx_generation_eval_task', 'evaluation_task_id'),
        Index('idx_generation_eval_test_case', 'test_case_id'),
    )


class EvaluationSummaryORM(Base):
    """评估汇总ORM模型"""
    __tablename__ = "evaluation_summaries"
    
    id = Column(String(50), primary_key=True)
    evaluation_task_id = Column(String(50), ForeignKey("evaluation_tasks.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    overall_retrieval_metrics = Column(JSON, nullable=True)
    overall_ragas_retrieval_metrics = Column(JSON, nullable=True)
    overall_ragas_generation_metrics = Column(JSON, nullable=True)
    overall_ragas_score = Column(Float, nullable=True)
    metrics_distribution = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class TaskQueueORM(Base):
    """任务队列ORM模型"""
    __tablename__ = "task_queue"
    
    id = Column(String(50), primary_key=True)
    task_type = Column(SQLEnum(TaskTypeEnum), nullable=False, index=True)
    status = Column(SQLEnum(TaskStatusEnum), nullable=False, default="pending", index=True)
    payload = Column(JSON, nullable=False)
    progress = Column(Float, default=0.0, nullable=False)
    result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)
    
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_task_queue_status', 'status'),
        Index('idx_task_queue_type', 'task_type'),
    )

# 在文件末尾添加

class KnowledgeBaseORM(Base):
    """知识库ORM模型"""
    __tablename__ = "knowledge_bases"
    
    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # 嵌入配置
    embedding_provider = Column(String(20), nullable=False, default="ollama")
    embedding_model = Column(String(100), nullable=False)
    embedding_dimension = Column(Integer, default=768)
    embedding_endpoint = Column(String(500), nullable=True)
    
    # Chat模型配置
    chat_provider = Column(String(20), nullable=False, default="ollama")
    chat_model = Column(String(100), nullable=True)
    chat_endpoint = Column(String(500), nullable=True)
    
    # 向量数据库配置
    vector_db_type = Column(String(20), nullable=False)
    vector_db_config = Column(JSON, nullable=True)
    schema_config = Column(JSON, nullable=True)  # Schema配置（字段定义等）
    
    # 分块配置
    chunk_size = Column(Integer, default=512)
    chunk_overlap = Column(Integer, default=50)
    
    # 检索配置
    retrieval_top_k = Column(Integer, default=5)
    retrieval_score_threshold = Column(Float, default=0.7)
    
    # 统计信息
    document_count = Column(Integer, default=0)
    chunk_count = Column(Integer, default=0)
    
    # 状态
    is_active = Column(Boolean, default=True, nullable=False)
    
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_kb_name', 'name'),
        Index('idx_kb_active', 'is_active'),
    )


class DocumentORM(Base):
    """文档ORM模型"""
    __tablename__ = "documents"
    
    id = Column(String(50), primary_key=True)
    kb_id = Column(String(50), nullable=False, index=True)
    
    # 文档基本信息
    name = Column(String(200), nullable=False)
    external_id = Column(String(100), nullable=True)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, default=0)
    file_type = Column(String(20), nullable=False)
    
    # 文档内容
    content = Column(Text, nullable=True)
    
    # 处理状态
    status = Column(String(20), nullable=False, default="uploaded", index=True)
    error_message = Column(Text, nullable=True)
    
    # 处理结果
    chunk_count = Column(Integer, default=0)
    
    # 元数据
    meta_data = Column('metadata', JSON, nullable=True)  # 使用 name 参数避免与 SQLAlchemy 保留属性冲突
    
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_doc_kb', 'kb_id'),
        Index('idx_doc_status', 'status'),
    )


class DocumentChunkORM(Base):
    """文档分块ORM模型"""
    __tablename__ = "document_chunks"
    
    id = Column(String(50), primary_key=True)
    document_id = Column(String(50), nullable=False, index=True)
    kb_id = Column(String(50), nullable=False, index=True)
    
    # 分块内容
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    
    # 分块元数据
    start_pos = Column(Integer, nullable=True)
    end_pos = Column(Integer, nullable=True)
    token_count = Column(Integer, nullable=True)
    
    # 向量信息
    embedding = Column(JSON, nullable=True)  # 存储为JSON数组
    embedding_model = Column(String(100), nullable=True)
    
    # 索引信息
    vector_id = Column(String(100), nullable=True)
    is_indexed = Column(Boolean, default=False, nullable=False)
    
    # 元数据
    meta_data = Column('metadata', JSON, nullable=True)  # 使用 name 参数避免与 SQLAlchemy 保留属性冲突
    
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_chunk_doc', 'document_id'),
        Index('idx_chunk_kb', 'kb_id'),
        Index('idx_chunk_indexed', 'is_indexed'),
    )