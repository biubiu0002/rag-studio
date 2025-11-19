"""
测试 MySQL 数据库连接和表创建
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.config import settings
from app.database import engine
from sqlalchemy import inspect, text
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def test_database_connection():
    """测试数据库连接"""
    try:
        logger.info("=" * 60)
        logger.info("测试数据库连接...")
        logger.info(f"数据库URL: {settings.database_url.replace(settings.DB_PASSWORD, '***')}")
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        
        logger.info("✓ 数据库连接成功")
        return True
    except Exception as e:
        logger.error(f"✗ 数据库连接失败: {e}")
        return False


def check_tables():
    """检查表是否存在"""
    try:
        logger.info("\n检查数据库表...")
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        required_tables = [
            "knowledge_bases",
            "documents",
            "document_chunks",
            "test_sets",
            "test_cases",
            "retriever_test_cases",
            "generation_test_cases",
            "test_set_knowledge_bases",
            "import_tasks",
            "evaluation_tasks",
            "evaluation_case_results",
            "evaluation_summaries",
            "retriever_evaluation_results",
            "generation_evaluation_results",
            "task_queue",
        ]
        
        logger.info(f"已存在的表: {len(existing_tables)} 个")
        for table in sorted(existing_tables):
            logger.info(f"  - {table}")
        
        missing_tables = [t for t in required_tables if t not in existing_tables]
        
        if missing_tables:
            logger.warning(f"\n缺少以下表 ({len(missing_tables)} 个):")
            for table in missing_tables:
                logger.warning(f"  ✗ {table}")
            return False
        else:
            logger.info(f"\n✓ 所有必需的表都存在 ({len(required_tables)} 个)")
            return True
            
    except Exception as e:
        logger.error(f"检查表失败: {e}", exc_info=True)
        return False


def check_storage_type():
    """检查存储类型配置"""
    logger.info("\n检查存储类型配置...")
    storage_type = settings.STORAGE_TYPE.lower()
    logger.info(f"当前存储类型: {storage_type}")
    
    if storage_type != "mysql":
        logger.warning(f"⚠ 存储类型为 {storage_type}，不是 mysql")
        logger.info("请在 .env 文件中设置: STORAGE_TYPE=mysql")
        return False
    else:
        logger.info("✓ 存储类型配置正确")
        return True


def main():
    """主测试函数"""
    logger.info("MySQL 数据库设置测试")
    logger.info("=" * 60)
    
    # 检查存储类型
    if not check_storage_type():
        logger.error("\n请先配置 STORAGE_TYPE=mysql")
        return False
    
    # 测试数据库连接
    if not test_database_connection():
        logger.error("\n数据库连接失败，请检查数据库配置")
        return False
    
    # 检查表
    tables_ok = check_tables()
    
    logger.info("\n" + "=" * 60)
    if tables_ok:
        logger.info("✓ 所有检查通过！")
        logger.info("\n下一步：运行数据迁移脚本")
        logger.info("  python scripts/migrate_json_to_mysql.py")
    else:
        logger.warning("⚠ 部分检查未通过")
        logger.info("\n请先运行表创建脚本：")
        logger.info("  python migrations/005_create_all_tables.py")
    
    logger.info("=" * 60)
    
    return tables_ok


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        logger.error(f"测试过程出错: {e}", exc_info=True)
        sys.exit(1)

