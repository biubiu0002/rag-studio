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
    metadata = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class RetrieverTestCaseORM(Base):
    """检索器测试用例ORM模型"""
    __tablename__ = "retriever_test_cases"
    
    id = Column(String(50), primary_key=True)
    test_set_id = Column(String(50), ForeignKey("test_sets.id", ondelete="CASCADE"), nullable=False, index=True)
    question = Column(Text, nullable=False)
    expected_answers = Column(JSON, nullable=False)  # Array of {answer_text, chunk_id, relevance_score}
    metadata = Column(JSON, nullable=True)
    
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
    metadata = Column(JSON, nullable=True)
    
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

