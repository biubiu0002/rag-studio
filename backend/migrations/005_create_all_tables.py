"""
数据库迁移脚本：创建所有表
统一创建所有 ORM 模型对应的数据库表
"""

from sqlalchemy import text, inspect
from app.database import engine, Base
from app.database.models import (
    # 测试相关
    TestSetORM,
    TestCaseORM,
    RetrieverTestCaseORM,
    GenerationTestCaseORM,
    TestSetKnowledgeBaseORM,
    ImportTaskORM,
    # 评估相关
    EvaluationTaskORM,
    EvaluationCaseResultORM,
    EvaluationSummaryORM,
    RetrieverEvaluationResultORM,
    GenerationEvaluationResultORM,
    # 任务队列
    TaskQueueORM,
    # 知识库和文档
    KnowledgeBaseORM,
    DocumentORM,
    DocumentChunkORM,
)
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def check_table_exists(table_name: str) -> bool:
    """检查表是否存在"""
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()


def create_all_tables():
    """创建所有表"""
    try:
        logger.info("开始创建数据库表...")
        
        # 检查并创建每个表
        tables_to_create = [
            ("knowledge_bases", KnowledgeBaseORM),
            ("documents", DocumentORM),
            ("document_chunks", DocumentChunkORM),
            ("test_sets", TestSetORM),
            ("test_cases", TestCaseORM),
            ("retriever_test_cases", RetrieverTestCaseORM),
            ("generation_test_cases", GenerationTestCaseORM),
            ("test_set_knowledge_bases", TestSetKnowledgeBaseORM),
            ("import_tasks", ImportTaskORM),
            ("evaluation_tasks", EvaluationTaskORM),
            ("evaluation_case_results", EvaluationCaseResultORM),
            ("evaluation_summaries", EvaluationSummaryORM),
            ("retriever_evaluation_results", RetrieverEvaluationResultORM),
            ("generation_evaluation_results", GenerationEvaluationResultORM),
            ("task_queue", TaskQueueORM),
        ]
        
        created_count = 0
        skipped_count = 0
        
        for table_name, orm_model in tables_to_create:
            if check_table_exists(table_name):
                logger.info(f"表 {table_name} 已存在，跳过")
                skipped_count += 1
            else:
                try:
                    orm_model.__table__.create(bind=engine, checkfirst=True)
                    logger.info(f"✓ 表 {table_name} 创建成功")
                    created_count += 1
                except Exception as e:
                    logger.error(f"✗ 创建表 {table_name} 失败: {e}")
        
        logger.info(f"\n创建完成: 新建 {created_count} 个表，跳过 {skipped_count} 个已存在的表")
        
        # 使用 Base.metadata.create_all 确保所有表都创建（包括外键约束）
        Base.metadata.create_all(bind=engine, checkfirst=True)
        logger.info("所有表结构已同步")
        
    except Exception as e:
        logger.error(f"创建表失败: {e}", exc_info=True)
        raise


def drop_all_tables():
    """删除所有表（谨慎使用）"""
    try:
        logger.warning("警告：即将删除所有表！")
        Base.metadata.drop_all(bind=engine)
        logger.info("所有表已删除")
    except Exception as e:
        logger.error(f"删除表失败: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "drop":
        confirm = input("确认删除所有表？(yes/no): ")
        if confirm.lower() == "yes":
            drop_all_tables()
        else:
            logger.info("操作已取消")
    else:
        create_all_tables()

