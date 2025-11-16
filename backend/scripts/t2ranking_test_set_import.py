"""
T2Ranking测试集导入脚本
读取T2Ranking数据集的三个TSV文件，将前100个问题及其相关文档导入为检索测试集
"""

import os
import sys
import logging
import asyncio
from typing import Dict, List, Tuple
from collections import defaultdict

# 添加项目根目录到 sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 硬编码的文件路径
QUERIES_PATH = "/Users/yeruijian/Documents/知识库平台/dataset/T2Ranking/data/queries.dev.tsv"
COLLECTION_PATH = "/Users/yeruijian/Documents/知识库平台/dataset/T2Ranking/data/collection.tsv"
QRELS_PATH = "/Users/yeruijian/Documents/知识库平台/dataset/T2Ranking/data/qrels.dev.tsv"

# 测试集配置
TEST_SET_NAME = "t2ranking_first_100"
MAX_QUERIES = 100


def load_queries(file_path: str, max_queries: int = 100) -> Dict[str, str]:
    """
    读取queries.dev.tsv文件，返回前N个问题的字典
    
    Args:
        file_path: queries文件路径
        max_queries: 最大问题数量
    
    Returns:
        {query_id: query_text} 字典
    """
    queries = {}
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"查询文件不存在: {file_path}")
    
    logger.info(f"正在加载查询文件: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for idx, line in enumerate(f):
            if idx >= max_queries:
                break
            
            line = line.strip()
            if not line:
                continue
            
            parts = line.split('\t')
            if len(parts) < 2:
                logger.warning(f"跳过格式错误的行 {idx + 1}: {line[:50]}...")
                continue
            
            query_id = parts[0].strip()
            query_text = parts[1].strip()
            
            if query_id and query_text:
                queries[query_id] = query_text
    
    logger.info(f"成功加载 {len(queries)} 个查询")
    return queries


def load_collection(file_path: str) -> Dict[str, str]:
    """
    读取collection.tsv文件，返回文档字典
    
    Args:
        file_path: collection文件路径
    
    Returns:
        {doc_id: document_content} 字典
    """
    collection = {}
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文档集合文件不存在: {file_path}")
    
    logger.info(f"正在加载文档集合文件: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for idx, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            
            parts = line.split('\t', 1)  # 只分割第一个制表符
            if len(parts) < 2:
                logger.warning(f"跳过格式错误的行 {idx + 1}: {line[:50]}...")
                continue
            
            doc_id = parts[0].strip()
            doc_content = parts[1].strip()
            
            if doc_id and doc_content:
                collection[doc_id] = doc_content
            
            # 每10000行显示一次进度
            if (idx + 1) % 10000 == 0:
                logger.info(f"已加载 {idx + 1} 个文档...")
    
    logger.info(f"成功加载 {len(collection)} 个文档")
    return collection


def load_qrels(file_path: str) -> Dict[str, List[Tuple[str, float]]]:
    """
    读取qrels.dev.tsv文件，返回问题-文档关联关系
    
    Args:
        file_path: qrels文件路径
    
    Returns:
        {query_id: [(doc_id, relevance), ...]} 字典
    """
    qrels = defaultdict(list)
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"关联文件不存在: {file_path}")
    
    logger.info(f"正在加载关联文件: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for idx, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            
            parts = line.split('\t')
            if len(parts) < 4:
                logger.warning(f"跳过格式错误的行 {idx + 1}: {line[:50]}...")
                continue
            
            query_id = parts[0].strip()
            doc_id = parts[2].strip()  # 跳过中间的0
            relevance_str = parts[3].strip()
            
            try:
                relevance = float(relevance_str)
            except ValueError:
                logger.warning(f"跳过无效的relevance值: {relevance_str}")
                continue
            
            if query_id and doc_id:
                qrels[query_id].append((doc_id, relevance))
            
            # 每10000行显示一次进度
            if (idx + 1) % 10000 == 0:
                logger.info(f"已加载 {idx + 1} 条关联记录...")
    
    logger.info(f"成功加载 {len(qrels)} 个问题的关联关系")
    return dict(qrels)


async def create_test_set() -> str:
    """
    创建测试集
    
    Returns:
        测试集ID
    """
    from app.services.test_service import TestService
    from app.schemas.test import TestSetCreate
    from app.models.test import TestType
    
    test_service = TestService()
    
    # 检查测试集是否已存在
    test_sets, _ = await test_service.list_test_sets(test_type=TestType.RETRIEVAL, page=1, page_size=1000)
    for ts in test_sets:
        if ts.name == TEST_SET_NAME:
            logger.warning(f"测试集 '{TEST_SET_NAME}' 已存在，ID: {ts.id}")
            return ts.id
    
    # 创建测试集
    create_data = TestSetCreate(
        name=TEST_SET_NAME,
        description="T2Ranking数据集前100个问题",
        test_type=TestType.RETRIEVAL
    )
    
    test_set = await test_service.create_test_set(create_data)
    logger.info(f"成功创建测试集: {test_set.id} - {test_set.name}")
    
    return test_set.id


async def import_test_cases(
    test_set_id: str,
    queries: Dict[str, str],
    collection: Dict[str, str],
    qrels: Dict[str, List[Tuple[str, float]]]
):
    """
    导入测试用例
    
    Args:
        test_set_id: 测试集ID
        queries: 查询字典 {query_id: query_text}
        collection: 文档集合 {doc_id: document_content}
        qrels: 关联关系 {query_id: [(doc_id, relevance), ...]}
    """
    from app.services.test_service import RetrieverTestCaseService
    
    test_case_service = RetrieverTestCaseService()
    
    # 准备测试用例数据
    cases_data = []
    skipped_queries = []
    order_index = 0  # 用于排序的序号
    
    # 按照queries的顺序遍历，保持顺序
    for query_id, query_text in queries.items():
        order_index += 1
        
        # 获取该问题的所有相关文档（包括relevance=0的非关联文档）
        related_docs = qrels.get(query_id, [])
        
        if not related_docs:
            logger.warning(f"问题 {query_id} (序号 {order_index}) 在qrels中没有关联文档，跳过")
            skipped_queries.append({
                "query_id": query_id,
                "order": order_index,
                "reason": "qrels中无记录"
            })
            continue
        
        # 构建expected_answers列表
        expected_answers = []
        missing_docs = []
        for doc_id, relevance in related_docs:
            # 从collection中获取文档内容
            doc_content = collection.get(doc_id)
            if not doc_content:
                missing_docs.append(doc_id)
                continue
            
            expected_answers.append({
                "answer_text": doc_content,
                "chunk_id": None,  # 文档导入后才有chunk_id
                "relevance_score": float(relevance)  # qrels中的relevance值（0-4范围）
            })
        
        if missing_docs:
            logger.warning(f"问题 {query_id} 有 {len(missing_docs)} 个文档在collection中不存在")
        
        if not expected_answers:
            logger.warning(f"问题 {query_id} (序号 {order_index}) 没有有效的期望答案，跳过")
            skipped_queries.append({
                "query_id": query_id,
                "order": order_index,
                "reason": "collection中无对应文档"
            })
            continue
        
        # 构建测试用例数据
        case_data = {
            "question": query_text,
            "expected_answers": expected_answers,
            "metadata": {
                "query_id": query_id,
                "source": "t2ranking",
                "doc_count": len(expected_answers),
                "order": order_index  # 添加排序字段
            }
        }
        
        cases_data.append(case_data)
    
    logger.info(f"准备导入 {len(cases_data)} 个测试用例")
    if skipped_queries:
        logger.info(f"跳过了 {len(skipped_queries)} 个问题:")
        for skipped in skipped_queries[:10]:  # 只显示前10个
            logger.info(f"  - 序号 {skipped['order']}, query_id: {skipped['query_id']}, 原因: {skipped['reason']}")
        if len(skipped_queries) > 10:
            logger.info(f"  ... 还有 {len(skipped_queries) - 10} 个被跳过的问题")
    
    # 批量创建测试用例（每批100个）
    batch_size = 100
    total_success = 0
    total_failed = 0
    
    for i in range(0, len(cases_data), batch_size):
        batch = cases_data[i:i + batch_size]
        batch_num = i // batch_size + 1
        total_batches = (len(cases_data) + batch_size - 1) // batch_size
        
        logger.info(f"正在导入第 {batch_num}/{total_batches} 批测试用例 ({len(batch)} 个)...")
        
        success_count, failed_count, failed_records = await test_case_service.batch_create_test_cases(
            test_set_id=test_set_id,
            cases_data=batch
        )
        
        total_success += success_count
        total_failed += failed_count
        
        if failed_records:
            logger.warning(f"第 {batch_num} 批有 {failed_count} 个用例创建失败:")
            for record in failed_records[:5]:  # 只显示前5个错误
                logger.warning(f"  - 索引 {record['index']}: {record.get('error', 'Unknown error')}")
        
        logger.info(f"第 {batch_num} 批完成: 成功 {success_count}, 失败 {failed_count}")
    
    logger.info(f"测试用例导入完成: 总计成功 {total_success}, 失败 {total_failed}")


async def main():
    """主函数"""
    try:
        logger.info("=" * 60)
        logger.info("T2Ranking测试集导入脚本")
        logger.info("=" * 60)
        
        # 1. 加载数据文件
        logger.info("\n【步骤1】加载数据文件...")
        queries = load_queries(QUERIES_PATH, max_queries=MAX_QUERIES)
        collection = load_collection(COLLECTION_PATH)
        qrels = load_qrels(QRELS_PATH)
        
        logger.info(f"\n数据统计:")
        logger.info(f"  - 查询数量: {len(queries)}")
        logger.info(f"  - 文档数量: {len(collection)}")
        logger.info(f"  - 关联关系数量: {sum(len(docs) for docs in qrels.values())}")
        logger.info(f"  - 在qrels中有记录的问题数: {len(set(queries.keys()) & set(qrels.keys()))}")
        logger.info(f"  - 在qrels中无记录的问题数: {len(set(queries.keys()) - set(qrels.keys()))}")
        
        # 2. 创建测试集
        logger.info("\n【步骤2】创建测试集...")
        test_set_id = await create_test_set()
        
        # 3. 导入测试用例
        logger.info("\n【步骤3】导入测试用例...")
        await import_test_cases(test_set_id, queries, collection, qrels)
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ 导入完成！")
        logger.info("=" * 60)
        
    except FileNotFoundError as e:
        logger.error(f"❌ 文件不存在: {e}")
        return 1
    except Exception as e:
        logger.error(f"❌ 导入失败: {e}", exc_info=True)
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

