"""
数据库迁移脚本：创建新的测试管理表
用于支持检索器测试用例和生成测试用例的新数据模型
"""

from sqlalchemy import text
from app.database import engine, Base
from app.database.models import (
    RetrieverTestCaseORM,
    GenerationTestCaseORM,
    RetrieverEvaluationResultORM,
    GenerationEvaluationResultORM
)
import logging

logger = logging.getLogger(__name__)


def create_new_tables():
    """创建新的测试管理表"""
    try:
        # 创建新表
        RetrieverTestCaseORM.__table__.create(bind=engine, checkfirst=True)
        logger.info("retriever_test_cases 表创建成功")
        
        GenerationTestCaseORM.__table__.create(bind=engine, checkfirst=True)
        logger.info("generation_test_cases 表创建成功")
        
        RetrieverEvaluationResultORM.__table__.create(bind=engine, checkfirst=True)
        logger.info("retriever_evaluation_results 表创建成功")
        
        GenerationEvaluationResultORM.__table__.create(bind=engine, checkfirst=True)
        logger.info("generation_evaluation_results 表创建成功")
        
        logger.info("所有新表创建完成")
    except Exception as e:
        logger.error(f"创建表失败: {e}", exc_info=True)
        raise


def drop_new_tables():
    """删除新的测试管理表（谨慎使用）"""
    try:
        GenerationEvaluationResultORM.__table__.drop(bind=engine, checkfirst=True)
        RetrieverEvaluationResultORM.__table__.drop(bind=engine, checkfirst=True)
        GenerationTestCaseORM.__table__.drop(bind=engine, checkfirst=True)
        RetrieverTestCaseORM.__table__.drop(bind=engine, checkfirst=True)
        logger.info("新表删除成功")
    except Exception as e:
        logger.error(f"删除表失败: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "drop":
        drop_new_tables()
    else:
        create_new_tables()
