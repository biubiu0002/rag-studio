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
    """测试用例ORM模型"""
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
    """评估用例结果ORM模型"""
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

