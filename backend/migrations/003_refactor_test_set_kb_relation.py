"""
数据库迁移脚本：重构测试集与知识库的关系
- 将test_sets.kb_id改为可空
- 创建test_set_knowledge_bases关联表
- 创建import_tasks导入任务表
- 清空现有测试集数据（根据用户要求）
"""

from sqlalchemy import text
from app.database import engine, Base
from app.database.models import (
    TestSetORM,
    TestSetKnowledgeBaseORM,
    ImportTaskORM
)
import logging

logger = logging.getLogger(__name__)


def upgrade():
    """执行迁移"""
    try:
        with engine.connect() as conn:
            # 1. 清空现有测试集数据（根据用户要求）
            logger.info("清空现有测试集数据...")
            conn.execute(text("DELETE FROM test_sets"))
            conn.commit()
            logger.info("测试集数据清空完成")
            
            # 2. 修改test_sets表的kb_id字段为可空
            logger.info("修改test_sets.kb_id字段为可空...")
            try:
                # MySQL语法
                conn.execute(text("ALTER TABLE test_sets MODIFY COLUMN kb_id VARCHAR(50) NULL"))
            except Exception as e:
                # 如果MySQL语法失败，尝试SQLite语法
                logger.warning(f"MySQL语法失败，尝试SQLite语法: {e}")
                try:
                    # SQLite需要重建表
                    conn.execute(text("""
                        CREATE TABLE test_sets_new (
                            id VARCHAR(50) PRIMARY KEY,
                            name VARCHAR(100) NOT NULL,
                            description TEXT,
                            kb_id VARCHAR(50),
                            test_type VARCHAR(20) NOT NULL,
                            case_count INTEGER DEFAULT 0,
                            kb_config JSON,
                            chunking_config JSON,
                            embedding_config JSON,
                            sparse_vector_config JSON,
                            index_config JSON,
                            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                        )
                    """))
                    conn.execute(text("""
                        INSERT INTO test_sets_new 
                        SELECT id, name, description, kb_id, test_type, case_count,
                               kb_config, chunking_config, embedding_config,
                               sparse_vector_config, index_config, created_at, updated_at
                        FROM test_sets
                    """))
                    conn.execute(text("DROP TABLE test_sets"))
                    conn.execute(text("ALTER TABLE test_sets_new RENAME TO test_sets"))
                except Exception as e2:
                    logger.error(f"SQLite语法也失败: {e2}")
                    raise
            conn.commit()
            logger.info("test_sets.kb_id字段修改完成")
            
            # 3. 创建test_set_knowledge_bases表
            logger.info("创建test_set_knowledge_bases表...")
            TestSetKnowledgeBaseORM.__table__.create(bind=engine, checkfirst=True)
            logger.info("test_set_knowledge_bases表创建成功")
            
            # 4. 创建import_tasks表
            logger.info("创建import_tasks表...")
            ImportTaskORM.__table__.create(bind=engine, checkfirst=True)
            logger.info("import_tasks表创建成功")
            
            logger.info("迁移完成")
    except Exception as e:
        logger.error(f"迁移失败: {e}", exc_info=True)
        raise


def downgrade():
    """回滚迁移（谨慎使用）"""
    try:
        with engine.connect() as conn:
            # 删除新创建的表
            logger.info("删除import_tasks表...")
            ImportTaskORM.__table__.drop(bind=engine, checkfirst=True)
            
            logger.info("删除test_set_knowledge_bases表...")
            TestSetKnowledgeBaseORM.__table__.drop(bind=engine, checkfirst=True)
            
            # 恢复kb_id为非空（需要先确保没有NULL值）
            logger.info("恢复test_sets.kb_id字段为非空...")
            conn.execute(text("UPDATE test_sets SET kb_id = '' WHERE kb_id IS NULL"))
            try:
                conn.execute(text("ALTER TABLE test_sets MODIFY COLUMN kb_id VARCHAR(50) NOT NULL"))
            except Exception as e:
                logger.warning(f"恢复kb_id字段失败: {e}")
            
            conn.commit()
            logger.info("回滚完成")
    except Exception as e:
        logger.error(f"回滚失败: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "downgrade":
        downgrade()
    else:
        upgrade()

