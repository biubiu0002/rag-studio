"""
SQLAlchemy ORM模型定义
"""

from sqlalchemy import Column, String, Integer, Text, DateTime, Enum as SQLEnum, Float, JSON, ForeignKey, Index
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


class TestSetORM(Base):
    """测试集ORM模型"""
    __tablename__ = "test_sets"
    
    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    kb_id = Column(String(50), nullable=False, index=True)
    test_type = Column(SQLEnum(TestTypeEnum), nullable=False, index=True)
    case_count = Column(Integer, default=0)
    
    # 配置快照（JSON字段）
    kb_config = Column(JSON, nullable=True)
    chunking_config = Column(JSON, nullable=True)
    embedding_config = Column(JSON, nullable=True)
    sparse_vector_config = Column(JSON, nullable=True)
    index_config = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


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

