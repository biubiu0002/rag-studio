"""
将 JSON 存储的数据迁移到 MySQL
"""

import json
import asyncio
import os
from pathlib import Path
from app.config import settings
from app.repositories.factory import RepositoryFactory
from app.models.knowledge_base import KnowledgeBase
from app.models.document import Document, DocumentChunk
from app.models.test import (
    TestSet, RetrieverTestCase, GenerationTestCase, 
    TestSetKnowledgeBase, ImportTask
)
from app.models.evaluation import (
    EvaluationTask, EvaluationCaseResult, EvaluationSummary
)
from app.models.task_queue import TaskQueue
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


async def migrate_collection(collection_name: str, model_class, file_path: Path):
    """迁移单个集合的数据"""
    if not file_path.exists():
        logger.warning(f"文件不存在: {file_path}，跳过")
        return 0
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            logger.warning(f"{collection_name} 数据格式不正确（不是列表），跳过")
            return 0
        
        if len(data) == 0:
            logger.info(f"{collection_name} 数据为空，跳过")
            return 0
        
        repository = RepositoryFactory.create(model_class, collection_name)
        migrated = 0
        skipped = 0
        errors = 0
        
        logger.info(f"开始迁移 {collection_name}，共 {len(data)} 条记录...")
        
        for idx, item in enumerate(data, 1):
            try:
                # 处理可能的 None 值
                if item is None:
                    continue
                
                entity = model_class(**item)
                
                # 检查是否已存在
                existing = await repository.get_by_id(entity.id)
                if existing:
                    logger.debug(f"{collection_name} ID {entity.id} 已存在，跳过")
                    skipped += 1
                    continue
                
                await repository.create(entity)
                migrated += 1
                
                if idx % 100 == 0:
                    logger.info(f"{collection_name}: 已处理 {idx}/{len(data)} 条记录...")
                    
            except Exception as e:
                errors += 1
                logger.error(
                    f"迁移 {collection_name} 数据失败 "
                    f"(ID: {item.get('id', 'unknown')}, 索引: {idx}): {e}"
                )
                if errors > 10:  # 如果错误太多，停止迁移
                    logger.error(f"{collection_name} 错误过多，停止迁移")
                    break
        
        logger.info(
            f"{collection_name}: 完成 - 成功: {migrated}, 跳过: {skipped}, 错误: {errors}"
        )
        return migrated
        
    except json.JSONDecodeError as e:
        logger.error(f"读取 {file_path} JSON 解析失败: {e}")
        return 0
    except Exception as e:
        logger.error(f"读取 {file_path} 失败: {e}", exc_info=True)
        return 0


async def main():
    """主迁移函数"""
    storage_path = Path(settings.STORAGE_PATH)
    
    # 确保当前使用 MySQL
    if settings.STORAGE_TYPE.lower() != "mysql":
        logger.error(f"当前存储类型为 {settings.STORAGE_TYPE}，请先将 STORAGE_TYPE 设置为 mysql")
        logger.info("请在 .env 文件中设置: STORAGE_TYPE=mysql")
        return
    
    logger.info("=" * 60)
    logger.info("开始迁移 JSON 数据到 MySQL...")
    logger.info(f"存储路径: {storage_path}")
    logger.info(f"数据库: {settings.DB_NAME}@{settings.DB_HOST}:{settings.DB_PORT}")
    logger.info("=" * 60)
    
    # 定义迁移映射（按依赖顺序）
    migrations = [
        # 基础数据（无依赖）
        ("knowledge_bases", KnowledgeBase, storage_path / "knowledge_bases.json"),
        ("documents", Document, storage_path / "documents.json"),
        ("document_chunks", DocumentChunk, storage_path / "document_chunks.json"),
        
        # 测试相关
        ("test_sets", TestSet, storage_path / "test_sets.json"),
        ("retriever_test_cases", RetrieverTestCase, storage_path / "retriever_test_cases.json"),
        ("generation_test_cases", GenerationTestCase, storage_path / "generation_test_cases.json"),
        ("test_set_knowledge_bases", TestSetKnowledgeBase, storage_path / "test_set_knowledge_bases.json"),
        ("import_tasks", ImportTask, storage_path / "import_tasks.json"),
        
        # 评估相关
        ("evaluation_tasks", EvaluationTask, storage_path / "evaluation_tasks.json"),
        ("evaluation_case_results", EvaluationCaseResult, storage_path / "evaluation_case_results.json"),
        ("evaluation_summaries", EvaluationSummary, storage_path / "evaluation_summaries.json"),
        
        # 任务队列
        ("task_queue", TaskQueue, storage_path / "task_queue.json"),
    ]
    
    total_migrated = 0
    total_skipped = 0
    
    for collection_name, model_class, file_path in migrations:
        count = await migrate_collection(collection_name, model_class, file_path)
        total_migrated += count
    
    logger.info("=" * 60)
    logger.info(f"迁移完成！总共迁移 {total_migrated} 条记录")
    logger.info("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n迁移被用户中断")
    except Exception as e:
        logger.error(f"迁移过程出错: {e}", exc_info=True)

