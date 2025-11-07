"""
检索器评估控制器
提供基于T2Ranking等标准数据集的检索器评估能力
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import logging

from app.schemas.test import (
    ImportT2RankingDatasetRequest,
    RetrieverEvaluationRequest,
    RetrieverEvaluationResultResponse,
    DatasetStatisticsResponse,
)
from app.core.response import success_response
from app.services.dataset_loader import DatasetService
from app.services.retriever_evaluation import RetrieverEvaluator, RetrievalTestRunner
from app.repositories.factory import RepositoryFactory

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/retriever-evaluation", tags=["检索器评估"])


@router.post("/import-t2ranking", response_model=None, summary="导入T2Ranking数据集")
async def import_t2ranking_dataset(data: ImportT2RankingDatasetRequest):
    """
    导入T2Ranking数据集并创建测试集
    
    此接口会：
    1. 加载T2Ranking数据集文件（collection.tsv, queries.tsv, qrels.tsv）
    2. 如果设置了max_docs和max_queries，会自动采样优化数据规模
    3. 将文档导入到指定知识库
    4. 创建对应的测试集和测试用例
    
    **参数说明：**
    - kb_id: 目标知识库ID（需要提前创建）
    - test_set_name: 测试集名称
    - collection_path: 文档集合TSV文件路径
    - queries_path: 查询TSV文件路径
    - qrels_path: 相关性标注TSV文件路径
    - max_docs: 最大文档数量（用于大数据集优化）
    - max_queries: 最大查询数量（用于大数据集优化）
    """
    try:
        # 加载数据集
        dataset = DatasetService.load_t2ranking(
            collection_path=data.collection_path,
            queries_path=data.queries_path,
            qrels_path=data.qrels_path,
            max_docs=data.max_docs,
            max_queries=data.max_queries
        )
        
        # 获取数据集统计信息
        stats = dataset.get_statistics()
        logger.info(f"T2Ranking数据集统计: {stats}")
        
        # 1. 检查知识库是否存在
        kb_repo = RepositoryFactory.create_knowledge_base_repository()
        kb = await kb_repo.get_by_id(data.kb_id)
        if not kb:
            raise HTTPException(status_code=404, detail=f"知识库不存在: {data.kb_id}")
        
        # 2. 批量导入文档到知识库
        from app.services.document import DocumentService
        document_service = DocumentService()
        
        collection = dataset.load_collection()
        logger.info(f"开始导入 {len(collection)} 个文档到知识库 {data.kb_id}")
        
        created_docs, failed_docs = await document_service.batch_create_documents_from_dict(
            kb_id=data.kb_id,
            documents=collection,
            source="t2ranking"
        )
        
        logger.info(f"文档导入完成: 成功 {len(created_docs)}, 失败 {len(failed_docs)}")
        
        # 3. 创建测试集
        from app.schemas.test import TestSetCreate
        test_service = TestService()
        
        test_set_create_data = TestSetCreate(
            name=data.test_set_name,
            description=data.description or f"T2Ranking数据集导入 - {len(created_docs)}个文档",
            kb_id=data.kb_id,
            test_type="retrieval"
        )
        test_set = await test_service.create_test_set(test_set_create_data)
        logger.info(f"测试集创建成功: {test_set.id}")
        
        # 4. 批量创建测试用例
        # 需要将doc_id映射到新创建的document_id
        external_id_to_doc_id = {doc.external_id: doc.id for doc in created_docs}
        
        test_cases_data = []
        raw_test_cases = dataset.get_test_cases()
        
        for raw_case in raw_test_cases:
            # 将external_id（原始doc_id）映射到新的document_id
            expected_chunks = []
            for external_id in raw_case['relevant_doc_ids']:
                if external_id in external_id_to_doc_id:
                    expected_chunks.append(external_id_to_doc_id[external_id])
                else:
                    logger.warning(f"找不到文档映射: {external_id}")
            
            if expected_chunks:  # 只添加有有效文档的测试用例
                test_cases_data.append({
                    "query": raw_case['query'],
                    "expected_chunks": expected_chunks,
                    "metadata": {
                        "query_id": raw_case['query_id'],
                        "original_doc_ids": raw_case['relevant_doc_ids']
                    }
                })
        
        created_cases, failed_cases = await test_service.batch_create_test_cases(
            test_set_id=test_set.id,
            test_cases_data=test_cases_data
        )
        
        logger.info(f"测试用例创建完成: 成功 {len(created_cases)}, 失败 {len(failed_cases)}")
        
        return JSONResponse(
            content=success_response(
                data={
                    "statistics": stats,
                    "kb_id": data.kb_id,
                    "documents": {
                        "total": len(collection),
                        "created": len(created_docs),
                        "failed": len(failed_docs),
                        "failed_records": failed_docs[:10] if failed_docs else []  # 只返回前10条错误
                    },
                    "test_set": {
                        "id": test_set.id,
                        "name": test_set.name,
                        "case_count": len(created_cases)
                    },
                    "test_cases": {
                        "total": len(test_cases_data),
                        "created": len(created_cases),
                        "failed": len(failed_cases),
                        "failed_records": failed_cases[:10] if failed_cases else []
                    }
                },
                message=f"T2Ranking数据集导入成功: {len(created_docs)}个文档, {len(created_cases)}个测试用例"
            )
        )
        
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=f"数据集文件未找到: {str(e)}")
    except Exception as e:
        logger.error(f"导入T2Ranking数据集失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}")


@router.get("/dataset-statistics", response_model=None, summary="获取数据集统计信息")
async def get_dataset_statistics(
    collection_path: str,
    queries_path: str,
    qrels_path: str,
    max_docs: int = None,
    max_queries: int = None
):
    """
    获取T2Ranking数据集的统计信息
    
    用于在导入前预览数据集规模，帮助决定是否需要采样
    """
    try:
        dataset = DatasetService.load_t2ranking(
            collection_path=collection_path,
            queries_path=queries_path,
            qrels_path=qrels_path,
            max_docs=max_docs,
            max_queries=max_queries
        )
        
        stats = dataset.get_statistics()
        
        return JSONResponse(
            content=success_response(
                data=stats,
                message="数据集统计信息获取成功"
            )
        )
        
    except Exception as e:
        logger.error(f"获取数据集统计失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")


@router.post("/evaluate", response_model=None, summary="执行检索器评估")
async def evaluate_retriever(data: RetrieverEvaluationRequest):
    """
    执行检索器评估
    
    基于测试集对检索器进行全面评估，返回多个评估指标：
    - Precision@K: 精确率
    - Recall@K: 召回率
    - F1-Score: F1分数
    - MRR: 平均倒数排名
    - MAP: 平均精度均值
    - NDCG: 归一化折损累积增益
    - Hit Rate: 命中率
    
    **使用场景：**
    1. 对比不同向量数据库的检索性能
    2. 评估不同embedding模型的效果
    3. 测试不同检索算法配置
    4. 追踪检索质量的变化趋势
    """
    try:
        # 获取测试集和测试用例
        test_service = TestService()
        test_set = await test_service.get_test_set(data.test_set_id)
        if not test_set:
            raise HTTPException(status_code=404, detail=f"测试集不存在: {data.test_set_id}")
        
        if test_set.kb_id != data.kb_id:
            raise HTTPException(
                status_code=400,
                detail=f"测试集不属于指定知识库"
            )
        
        # 获取测试用例
        test_cases, _ = await test_service.list_test_cases(
            test_set_id=data.test_set_id,
            page=1,
            page_size=10000  # 获取所有测试用例
        )
        
        if not test_cases:
            raise HTTPException(status_code=400, detail="测试集中没有测试用例")
        
        # 创建评估器
        evaluator = RetrieverEvaluator(top_k=data.top_k)
        test_runner = RetrievalTestRunner(evaluator, top_k=data.top_k)
        
        # 定义检索函数
        async def retriever_func(query: str, top_k: int):
            # TODO: 调用实际的检索服务
            # from app.services.rag_service import RAGService
            # rag_service = RAGService(kb_id=data.kb_id)
            # results = await rag_service.retrieve(query, top_k=top_k)
            # return [r['chunk_id'] for r in results]
            
            # 临时返回空结果
            return []
        
        # 执行测试
        # result = await test_runner.run_test(
        #     retriever_func=retriever_func,
        #     test_cases=[
        #         {
        #             'query_id': tc.id,
        #             'query': tc.query,
        #             'relevant_doc_ids': tc.expected_chunks or []
        #         }
        #         for tc in test_cases
        #     ]
        # )
        
        # TODO: 保存评估结果到数据库
        # eval_result_repo = RepositoryFactory.create_retriever_evaluation_repository()
        # await eval_result_repo.create(...)
        
        return JSONResponse(
            content=success_response(
                data={
                    "message": "检索器评估功能待完整实现",
                    "kb_id": data.kb_id,
                    "test_set_id": data.test_set_id,
                    "total_test_cases": len(test_cases),
                    "config": {
                        "top_k": data.top_k,
                        "vector_db_type": data.vector_db_type,
                        "embedding_provider": data.embedding_provider,
                        "embedding_model": data.embedding_model,
                    }
                },
                message="评估任务已创建（待实现）"
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"执行检索器评估失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"评估失败: {str(e)}")


@router.get("/evaluation-history", response_model=None, summary="获取评估历史")
async def get_evaluation_history(
    kb_id: str,
    test_set_id: str = None,
    page: int = 1,
    page_size: int = 20
):
    """
    获取检索器评估历史记录
    
    可用于：
    - 查看历史评估结果
    - 对比不同配置的性能
    - 分析性能变化趋势
    """
    try:
        # TODO: 从数据库获取评估历史
        # eval_result_repo = RepositoryFactory.create_retriever_evaluation_repository()
        # results = await eval_result_repo.get_all(filters=...)
        
        return JSONResponse(
            content=success_response(
                data={
                    "items": [],
                    "total": 0,
                    "page": page,
                    "page_size": page_size
                },
                message="评估历史查询（待实现）"
            )
        )
        
    except Exception as e:
        logger.error(f"获取评估历史失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/compare-evaluations", response_model=None, summary="对比多个评估结果")
async def compare_evaluations(evaluation_ids: str):
    """
    对比多个评估结果
    
    用于：
    - A/B测试不同配置
    - 可视化性能差异
    - 选择最优配置
    
    **参数：**
    - evaluation_ids: 逗号分隔的评估ID列表，如 "eval_001,eval_002,eval_003"
    """
    try:
        eval_id_list = evaluation_ids.split(',')
        
        # TODO: 获取多个评估结果并对比
        # eval_result_repo = RepositoryFactory.create_retriever_evaluation_repository()
        # results = []
        # for eval_id in eval_id_list:
        #     result = await eval_result_repo.get_by_id(eval_id)
        #     results.append(result)
        
        return JSONResponse(
            content=success_response(
                data={
                    "comparison": [],
                    "evaluation_ids": eval_id_list
                },
                message="评估对比（待实现）"
            )
        )
        
    except Exception as e:
        logger.error(f"对比评估结果失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"对比失败: {str(e)}")


# 需要导入TestService
from app.services.test_service import TestService

