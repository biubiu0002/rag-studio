"""
数据库配置和连接管理
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# 创建同步引擎
# 注意：pymysql不支持异步，需要使用aiomysql或mysqlclient
# 这里先使用同步方式，后续可以改为异步
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 同步引擎（暂时使用，后续可改为异步）
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=settings.DEBUG
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 声明基类
Base = declarative_base()


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

