"""
添加schema_config字段到knowledge_bases表
"""

from sqlalchemy import text, inspect
from app.database import engine
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def upgrade():
    """添加schema_config字段到knowledge_bases表"""
    with engine.connect() as connection:
        inspector = inspect(engine)
        
        # 检查表是否存在
        if 'knowledge_bases' not in inspector.get_table_names():
            logger.warning("表 knowledge_bases 不存在，跳过迁移")
            return
        
        # 检查字段是否已存在
        columns = [col['name'] for col in inspector.get_columns('knowledge_bases')]
        if 'schema_config' in columns:
            logger.info("字段 schema_config 已存在，跳过迁移")
            return
        
        # 添加schema_config字段
        try:
            connection.execute(text("""
                ALTER TABLE knowledge_bases 
                ADD COLUMN schema_config JSON NULL 
                COMMENT 'Schema配置（字段定义等）' 
                AFTER vector_db_config;
            """))
            connection.commit()
            logger.info("✓ 成功添加 schema_config 字段到 knowledge_bases 表")
        except Exception as e:
            connection.rollback()
            logger.error(f"✗ 添加 schema_config 字段失败: {e}")
            raise


def downgrade():
    """移除schema_config字段"""
    with engine.connect() as connection:
        inspector = inspect(engine)
        
        # 检查表是否存在
        if 'knowledge_bases' not in inspector.get_table_names():
            logger.warning("表 knowledge_bases 不存在，跳过回滚")
            return
        
        # 检查字段是否存在
        columns = [col['name'] for col in inspector.get_columns('knowledge_bases')]
        if 'schema_config' not in columns:
            logger.info("字段 schema_config 不存在，跳过回滚")
            return
        
        # 删除schema_config字段
        try:
            connection.execute(text("""
                ALTER TABLE knowledge_bases 
                DROP COLUMN schema_config;
            """))
            connection.commit()
            logger.info("✓ 成功移除 schema_config 字段")
        except Exception as e:
            connection.rollback()
            logger.error(f"✗ 移除 schema_config 字段失败: {e}")
            raise


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "downgrade":
        logger.info("执行回滚操作...")
        downgrade()
    else:
        logger.info("执行迁移操作...")
        upgrade()

