"""
数据库迁移脚本：创建评估相关表
"""

from sqlalchemy import text
from app.database import engine, Base
from app.database.models import (
    TestSetORM, TestCaseORM, EvaluationTaskORM,
    EvaluationCaseResultORM, EvaluationSummaryORM
)
import logging

logger = logging.getLogger(__name__)


def create_tables():
    """创建所有表"""
    try:
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        logger.info("评估相关表创建成功")
    except Exception as e:
        logger.error(f"创建表失败: {e}", exc_info=True)
        raise


def drop_tables():
    """删除所有表（谨慎使用）"""
    try:
        Base.metadata.drop_all(bind=engine)
        logger.info("评估相关表删除成功")
    except Exception as e:
        logger.error(f"删除表失败: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "drop":
        drop_tables()
    else:
        create_tables()

