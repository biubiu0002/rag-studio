"""
测试数据库连接诊断脚本
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.config import settings
import pymysql
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_direct_connection():
    """直接使用 pymysql 测试连接"""
    try:
        logger.info("=" * 60)
        logger.info("测试直接 pymysql 连接...")
        logger.info(f"主机: {settings.DB_HOST}")
        logger.info(f"端口: {settings.DB_PORT}")
        logger.info(f"用户: {settings.DB_USER}")
        logger.info(f"密码: {'*' * len(settings.DB_PASSWORD) if settings.DB_PASSWORD else '(empty)'}")
        logger.info(f"数据库: {settings.DB_NAME}")
        
        connection = pymysql.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            database=settings.DB_NAME,
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            logger.info(f"✓ 直接连接成功: {result}")
        
        connection.close()
        return True
        
    except Exception as e:
        logger.error(f"✗ 直接连接失败: {e}")
        logger.error(f"错误类型: {type(e).__name__}")
        return False


def test_sqlalchemy_connection():
    """使用 SQLAlchemy 测试连接"""
    try:
        logger.info("\n" + "=" * 60)
        logger.info("测试 SQLAlchemy 连接...")
        logger.info(f"数据库 URL: {settings.database_url.replace(settings.DB_PASSWORD, '***') if settings.DB_PASSWORD else settings.database_url}")
        
        from sqlalchemy import create_engine, text
        
        engine = create_engine(
            settings.database_url,
            pool_pre_ping=True,
            echo=True
        )
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            row = result.fetchone()
            logger.info(f"✓ SQLAlchemy 连接成功: {row}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ SQLAlchemy 连接失败: {e}")
        logger.error(f"错误类型: {type(e).__name__}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def check_mysql_service():
    """检查 MySQL 服务是否运行"""
    import socket
    logger.info("\n" + "=" * 60)
    logger.info("检查 MySQL 服务...")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((settings.DB_HOST, settings.DB_PORT))
        sock.close()
        
        if result == 0:
            logger.info(f"✓ MySQL 服务在 {settings.DB_HOST}:{settings.DB_PORT} 上运行")
            return True
        else:
            logger.error(f"✗ 无法连接到 {settings.DB_HOST}:{settings.DB_PORT}")
            logger.info("请检查:")
            logger.info("  1. MySQL 服务是否运行")
            logger.info("  2. 端口是否正确")
            logger.info("  3. 防火墙设置")
            return False
    except Exception as e:
        logger.error(f"✗ 检查服务失败: {e}")
        return False


def main():
    """主测试函数"""
    logger.info("数据库连接诊断")
    logger.info("=" * 60)
    
    # 检查服务
    service_ok = check_mysql_service()
    if not service_ok:
        logger.error("\nMySQL 服务不可用，请先启动 MySQL 服务")
        return False
    
    # 测试直接连接
    direct_ok = test_direct_connection()
    
    # 测试 SQLAlchemy 连接
    sqlalchemy_ok = test_sqlalchemy_connection()
    
    logger.info("\n" + "=" * 60)
    if direct_ok and sqlalchemy_ok:
        logger.info("✓ 所有连接测试通过！")
        return True
    else:
        logger.error("✗ 部分连接测试失败")
        return False


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

