"""
评估任务服务
负责评估任务的创建、执行和管理
"""

from typing import List, Dict, Any, Optional
import uuid
import logging
from datetime import datetime
import asyncio

from app.models.evaluation import (
    EvaluationTask, EvaluationCaseResult, EvaluationSummary,
    EvaluationType, EvaluationStatus
)
from app.models.test import TestSet, TestCase, TestType, RetrieverTestCase, GenerationTestCase
from app.repositories.factory import RepositoryFactory
from app.services.ragas_evaluation import RAGASEvaluationService
from app.services.retrieval_service import RetrievalService
from app.services.rag_service import RAGService
from app.core.exceptions import NotFoundException

logger = logging.getLogger(__name__)


class EvaluationTaskService:
    """评估任务服务"""
    
    def __init__(self):
        self.task_repo = RepositoryFactory.create_evaluation_task_repository()
        self.case_result_repo = RepositoryFactory.create_evaluation_case_result_repository()
        self.summary_repo = RepositoryFactory.create_evaluation_summary_repository()
        self.test_set_repo = RepositoryFactory.create_test_set_repository()
        self.retriever_case_repo = RepositoryFactory.create_retriever_test_case_repository()
        self.generation_case_repo = RepositoryFactory.create_generation_test_case_repository()
        self.ragas_service = RAGASEvaluationService()
    
    async def create_evaluation_task(
        self,
        test_set_id: str,
        kb_id: str,
        evaluation_type: EvaluationType,
        retrieval_config: Optional[Dict[str, Any]] = None,
        generation_config: Optional[Dict[str, Any]] = None,
        task_name: Optional[str] = None
    ) -> EvaluationTask:
        """
        创建评估任务
        
        Args:
            test_set_id: 测试集ID
            kb_id: 知识库ID
            evaluation_type: 评估类型
            retrieval_config: 检索配置
            generation_config: 生成配置
            task_name: 任务名称
        
        Returns:
            创建的评估任务
        """
        # 获取测试集
        test_set = await self.test_set_repo.get_by_id(test_set_id)
        if not test_set:
            raise NotFoundException(message=f"测试集不存在: {test_set_id}")
        
        # 验证知识库是否存在
        from app.services.knowledge_base import KnowledgeBaseService
        kb_service = KnowledgeBaseService()
        kb = await kb_service.get_knowledge_base(kb_id)
        if not kb:
            raise NotFoundException(message=f"知识库不存在: {kb_id}")
        
        # 验证测试集是否已导入到知识库（可选，根据需求允许未导入的情况）
        from app.models.test import TestSetKnowledgeBase
        test_set_kb_repo = RepositoryFactory.create_test_set_knowledge_base_repository()
        filters = {"test_set_id": test_set_id, "kb_id": kb_id, "kb_deleted": False, "test_set_deleted": False}
        associations = await test_set_kb_repo.get_all(skip=0, limit=1, filters=filters)
        
        # 如果未导入，给出警告但不阻止创建（根据需求）
        if not associations:
            logger.warning(f"测试集 {test_set_id} 未导入到知识库 {kb_id}，但允许创建评估任务")
        
        # 获取测试用例数量（根据评估类型选择不同的仓库）
        if evaluation_type == EvaluationType.RETRIEVAL:
            retriever_case_repo = RepositoryFactory.create_retriever_test_case_repository()
            filters = {"test_set_id": test_set_id}
            total = await retriever_case_repo.count(filters=filters)
        else:
            generation_case_repo = RepositoryFactory.create_generation_test_case_repository()
            filters = {"test_set_id": test_set_id}
            total = await generation_case_repo.count(filters=filters)
        
        # 生成任务ID
        task_id = f"eval_task_{uuid.uuid4().hex[:12]}"
        
        # 创建评估任务
        task = EvaluationTask(
            id=task_id,
            test_set_id=test_set_id,
            kb_id=kb_id,
            evaluation_type=evaluation_type,
            task_name=task_name or f"{evaluation_type.value}_eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            status=EvaluationStatus.PENDING,
            retrieval_config=retrieval_config or {},
            generation_config=generation_config or {},
            total_cases=total
        )
        
        await self.task_repo.create(task)
        return task
    
    async def execute_evaluation_task(
        self,
        task_id: str,
        save_detailed_results: bool = True
    ) -> EvaluationTask:
        """
        执行评估任务
        
        Args:
            task_id: 评估任务ID
            save_detailed_results: 是否保存详细结果
        
        Returns:
            更新后的评估任务
        """
        # 获取任务
        task = await self.task_repo.get_by_id(task_id)
        if not task:
            raise NotFoundException(message=f"评估任务不存在: {task_id}")
        
        # 更新状态为运行中
        task.status = EvaluationStatus.RUNNING
        task.started_at = datetime.now()
        await self.task_repo.update(task_id, task)
        
        try:
            # 获取测试集和测试用例
            test_set = await self.test_set_repo.get_by_id(task.test_set_id)
            if not test_set:
                raise NotFoundException(message=f"测试集不存在: {task.test_set_id}")
            
            # 检查知识库是否存在
            from app.services.knowledge_base import KnowledgeBaseService
            kb_service = KnowledgeBaseService()
            kb = await kb_service.get_knowledge_base(task.kb_id)
            if not kb:
                raise NotFoundException(message=f"知识库不存在: {task.kb_id}")
            
            # 检查知识库是否已写入数据（检查集合是否存在）
            if kb.vector_db_type == "qdrant":
                from app.services.vector_db_service import VectorDBServiceFactory
                try:
                    vector_db_service = VectorDBServiceFactory.create(
                        kb.vector_db_type,
                        config=kb.vector_db_config if kb.vector_db_config else None
                    )
                    # 尝试检查集合是否存在（通过尝试搜索来验证）
                    # 注意：这里不阻止执行，如果集合不存在，检索服务会处理错误
                    logger.info(f"准备执行评估任务，知识库: {task.kb_id}, 向量数据库类型: {kb.vector_db_type}")
                except Exception as e:
                    logger.warning(f"无法检查知识库集合: {e}")
            
            # 根据评估类型获取对应的测试用例
            if task.evaluation_type == EvaluationType.RETRIEVAL:
                filters = {"test_set_id": task.test_set_id}
                test_cases = await self.retriever_case_repo.get_all(
                    skip=0,
                    limit=10000,
                    filters=filters
                )
                if not test_cases:
                    raise ValueError(f"测试集 {task.test_set_id} 中没有检索器测试用例")
                await self._execute_retrieval_evaluation(
                    task, test_set, test_cases, save_detailed_results
                )
            elif task.evaluation_type == EvaluationType.GENERATION:
                filters = {"test_set_id": task.test_set_id}
                test_cases = await self.generation_case_repo.get_all(
                    skip=0,
                    limit=10000,
                    filters=filters
                )
                if not test_cases:
                    raise ValueError(f"测试集 {task.test_set_id} 中没有生成器测试用例")
                await self._execute_generation_evaluation(
                    task, test_set, test_cases, save_detailed_results
                )
            else:
                raise ValueError(f"不支持的评估类型: {task.evaluation_type}")
            
            # 更新任务状态
            task.status = EvaluationStatus.COMPLETED
            task.completed_at = datetime.now()
            await self.task_repo.update(task_id, task)
            
            # 创建评估汇总
            await self._create_evaluation_summary(task_id)
            
        except Exception as e:
            logger.error(f"执行评估任务失败: {e}", exc_info=True)
            task.status = EvaluationStatus.FAILED
            await self.task_repo.update(task_id, task)
            raise
        
        return task
    
    async def _execute_retrieval_evaluation(
        self,
        task: EvaluationTask,
        test_set: TestSet,
        test_cases: List[RetrieverTestCase],
        save_detailed_results: bool
    ):
        """执行检索器评估"""
        retrieval_service = RetrievalService()
        
        # 准备RAGAS评估数据
        queries = []
        retrieved_contexts = []
        ground_truth_contexts = []
        
        completed_count = 0
        failed_count = 0
        
        for test_case in test_cases:
            try:
                # 执行检索
                retrieval_config = task.retrieval_config
                top_k = retrieval_config.get("top_k", 10)
                
                # 使用知识库的检索服务
                results = await retrieval_service.qdrant_hybrid_search(
                    kb_id=task.kb_id,
                    query=test_case.question,
                    query_vector=None,  # 自动生成
                    query_sparse_vector=None,  # 自动生成
                    top_k=top_k,
                    score_threshold=retrieval_config.get("score_threshold", 0.0),
                    fusion=retrieval_config.get("fusion", "rrf")
                )
                
                # 提取检索结果
                retrieved_chunks = [r.to_dict() for r in results]
                retrieved_contexts_list = [r.content for r in results]
                
                # 从expected_answers中提取期望的chunk_ids或external_ids
                expected_chunk_ids = set()
                expected_external_ids = set()
                ground_truth_contexts_list = []
                
                for idx, answer in enumerate(test_case.expected_answers):
                    if answer.get("chunk_id"):
                        expected_chunk_ids.add(answer["chunk_id"])
                    elif answer.get("answer_text"):
                        # 如果没有chunk_id，通过external_id匹配
                        # external_id格式: test_set_{test_set_id}_case_{case_id}_answer_{answer_index}
                        external_id = f"test_set_{test_set.id}_case_{test_case.id}_answer_{idx}"
                        expected_external_ids.add(external_id)
                    if answer.get("answer_text"):
                        ground_truth_contexts_list.append(answer["answer_text"])
                
                queries.append(test_case.question)
                retrieved_contexts.append(retrieved_contexts_list)
                ground_truth_contexts.append(ground_truth_contexts_list)
                
                # 计算评估指标
                # 基础指标：优先使用chunk_id匹配，如果没有则使用external_id匹配
                from app.services.retriever_evaluation import RetrieverEvaluator
                evaluator = RetrieverEvaluator(top_k=top_k)
                
                if expected_chunk_ids:
                    # 使用chunk_id匹配
                    retrieved_chunk_ids = [r.chunk_id for r in results]
                    basic_metrics = evaluator.evaluate_single_query(
                        retrieved_chunk_ids, list(expected_chunk_ids)
                    )
                elif expected_external_ids:
                    # 使用external_id匹配
                    retrieved_external_ids = []
                    for r in results:
                        # 从metadata中提取external_id
                        if r.metadata and isinstance(r.metadata, dict):
                            external_id = r.metadata.get('external_id')
                            if external_id:
                                retrieved_external_ids.append(external_id)
                    
                    basic_metrics = evaluator.evaluate_single_query(
                        retrieved_external_ids, list(expected_external_ids)
                    )
                else:
                    # 既没有chunk_id也没有answer_text，无法评估
                    basic_metrics = evaluator._empty_metrics()
                
                # 保存详细结果（先不包含RAGAS指标，后面批量评估后更新）
                if save_detailed_results:
                    case_result = EvaluationCaseResult(
                        id=f"eval_result_{uuid.uuid4().hex[:12]}",
                        evaluation_task_id=task.id,
                        test_case_id=test_case.id,
                        query=test_case.question,
                        retrieved_chunks=retrieved_chunks,
                        retrieval_time=0.0,  # TODO: 实际测量
                        retrieval_metrics=basic_metrics,
                        ragas_retrieval_metrics={},
                        ragas_score=None,  # 稍后批量评估后更新
                        status=EvaluationStatus.COMPLETED
                    )
                    await self.case_result_repo.create(case_result)
                
                completed_count += 1
                
                # 更新任务进度
                task.completed_cases = completed_count
                await self.task_repo.update(task.id, task)
                
            except Exception as e:
                logger.error(f"评估测试用例失败 {test_case.id}: {e}", exc_info=True)
                failed_count += 1
                
                if save_detailed_results:
                    case_result = EvaluationCaseResult(
                        id=f"eval_result_{uuid.uuid4().hex[:12]}",
                        evaluation_task_id=task.id,
                        test_case_id=test_case.id,
                        query=test_case.question,
                        status=EvaluationStatus.FAILED,
                        error_message=str(e)
                    )
                    await self.case_result_repo.create(case_result)
                
                task.failed_cases = failed_count
                await self.task_repo.update(task.id, task)
        
        # 批量RAGAS评估（所有用例完成后）
        if len(queries) > 0 and save_detailed_results:
            try:
                # 从任务配置中获取 LLM 配置（如果有）
                llm_model = None
                llm_base_url = None
                if task.generation_config:
                    llm_model = task.generation_config.get("llm_model")
                    # base_url 从全局配置获取
                    from app.config import settings
                    llm_base_url = settings.OLLAMA_BASE_URL
                
                ragas_result = await self.ragas_service.evaluate_retrieval(
                    queries=queries,
                    retrieved_contexts=retrieved_contexts,
                    ground_truth_contexts=ground_truth_contexts,
                    llm_model=llm_model,
                    llm_base_url=llm_base_url
                )
                
                # RAGAS返回的结果格式处理
                # 提取RAGAS指标
                ragas_metrics = {
                    "context_precision": ragas_result.get("context_precision", 0.0),
                    "context_recall": ragas_result.get("context_recall", 0.0),
                    "context_relevancy": ragas_result.get("context_relevancy", 0.0),
                }
                
                # 如果ragas_result中没有ragas_score，我们自己计算
                ragas_score = ragas_result.get("ragas_score")
                if ragas_score is None or ragas_score == 0.0:
                    # 手动计算综合评分（三个指标的平均值）
                    metric_values = [v for v in ragas_metrics.values() if v is not None]
                    if metric_values:
                        ragas_score = sum(metric_values) / len(metric_values)
                    else:
                        ragas_score = 0.0
                
                logger.info(f"RAGAS评估结果: metrics={ragas_metrics}, score={ragas_score}")
                
                # 更新所有已保存的结果中的RAGAS指标
                filters = {"evaluation_task_id": task.id, "status": EvaluationStatus.COMPLETED.value}
                case_results = await self.case_result_repo.get_all(
                    skip=0,
                    limit=10000,
                    filters=filters
                )
                
                # 为每个用例分配RAGAS指标（使用平均值）
                for case_result in case_results:
                    case_result.ragas_retrieval_metrics = ragas_metrics
                    case_result.ragas_score = ragas_score
                    await self.case_result_repo.update(case_result.id, case_result)
                    
                logger.info(f"批量RAGAS评估完成，更新了 {len(case_results)} 个用例结果")
            except Exception as e:
                logger.error(f"批量RAGAS评估失败: {e}", exc_info=True)
                # 不阻止任务完成，只是RAGAS指标会缺失
    
    async def _execute_generation_evaluation(
        self,
        task: EvaluationTask,
        test_set: TestSet,
        test_cases: List[GenerationTestCase],
        save_detailed_results: bool
    ):
        """执行生成器评估"""
        rag_service = RAGService(kb_id=task.kb_id)
        generation_config = task.generation_config
        
        queries = []
        answers = []
        contexts = []
        ground_truth_answers = []
        
        completed_count = 0
        failed_count = 0
        
        for test_case in test_cases:
            try:
                # 执行RAG生成
                # 先检索上下文
                retrieval_config = generation_config.get("retrieval_config", {})
                top_k = retrieval_config.get("top_k", 10)
                retrieved_chunks = await rag_service.retrieve(
                    query=test_case.question,
                    top_k=top_k
                )
                
                # 调用LLM生成（使用debug_pipeline中的call_llm逻辑）
                from app.controllers.debug_pipeline import call_llm
                context = [chunk.get("content", "") for chunk in retrieved_chunks]
                context_str = "\n\n".join(context) if context else ""
                
                prompt_template = generation_config.get("prompt_template") or """基于以下上下文回答问题。如果上下文中没有相关信息，请说'信息不足'。

上下文：
{context}

问题：{query}

答案："""
                prompt = prompt_template.format(context=context_str, query=test_case.question)
                
                answer = await call_llm(
                    prompt=prompt,
                    provider=generation_config.get("llm_provider", "ollama"),
                    model=generation_config.get("llm_model", "deepseek-r1:1.5b"),
                    temperature=generation_config.get("temperature", 0.7),
                    max_tokens=generation_config.get("max_tokens"),
                    stream=False
                )
                
                result = {
                    "query": test_case.question,
                    "answer": answer,
                    "contexts": retrieved_chunks,
                    "retrieval_time": 0.0,  # TODO: 实际测量
                    "generation_time": 0.0  # TODO: 实际测量
                }
                
                queries.append(test_case.question)
                answers.append(result.get("answer", ""))
                contexts.append([chunk.get("content", "") for chunk in result.get("contexts", [])])
                if test_case.reference_answer:
                    ground_truth_answers.append(test_case.reference_answer)
                
                # 保存详细结果
                if save_detailed_results:
                    case_result = EvaluationCaseResult(
                        id=f"eval_result_{uuid.uuid4().hex[:12]}",
                        evaluation_task_id=task.id,
                        test_case_id=test_case.id,
                        query=test_case.question,
                        retrieved_chunks=result.get("contexts", []),
                        generated_answer=result.get("answer", ""),
                        retrieval_time=result.get("retrieval_time", 0.0),
                        generation_time=result.get("generation_time", 0.0),
                        status=EvaluationStatus.COMPLETED
                    )
                    await self.case_result_repo.create(case_result)
                
                completed_count += 1
                task.completed_cases = completed_count
                await self.task_repo.update(task.id, task)
                
            except Exception as e:
                logger.error(f"评估测试用例失败 {test_case.id}: {e}", exc_info=True)
                failed_count += 1
                
                if save_detailed_results:
                    case_result = EvaluationCaseResult(
                        id=f"eval_result_{uuid.uuid4().hex[:12]}",
                        evaluation_task_id=task.id,
                        test_case_id=test_case.id,
                        query=test_case.question,
                        status=EvaluationStatus.FAILED,
                        error_message=str(e)
                    )
                    await self.case_result_repo.create(case_result)
                
                task.failed_cases = failed_count
                await self.task_repo.update(task.id, task)
        
        # 批量RAGAS评估
        if len(queries) > 0:
            # 从任务配置中获取 LLM 配置
            llm_model = generation_config.get("llm_model") if generation_config else None
            llm_base_url = None
            if llm_model:
                from app.config import settings
                llm_base_url = settings.OLLAMA_BASE_URL
            
            ragas_result = await self.ragas_service.evaluate_generation(
                queries=queries,
                answers=answers,
                contexts=contexts,
                ground_truth_answers=ground_truth_answers if ground_truth_answers else None,
                llm_model=llm_model,
                llm_base_url=llm_base_url
            )
            
            # 更新已保存的结果中的RAGAS指标
            if save_detailed_results:
                filters = {"evaluation_task_id": task.id}
                case_results = await self.case_result_repo.get_all(
                    skip=0,
                    limit=10000,
                    filters=filters
                )
                
                # 分配RAGAS指标到各个结果
                for i, case_result in enumerate(case_results):
                    if i < len(queries):
                        case_result.ragas_generation_metrics = {
                            "faithfulness": ragas_result.get("faithfulness", 0.0),
                            "answer_relevancy": ragas_result.get("answer_relevancy", 0.0),
                        }
                        if ground_truth_answers:
                            case_result.ragas_generation_metrics.update({
                                "answer_similarity": ragas_result.get("answer_similarity", 0.0),
                                "answer_correctness": ragas_result.get("answer_correctness", 0.0),
                            })
                        case_result.ragas_score = ragas_result.get("ragas_score", 0.0)
                        await self.case_result_repo.update(case_result.id, case_result)
    
    async def _create_evaluation_summary(self, task_id: str):
        """创建评估汇总"""
        # 获取所有用例结果
        filters = {"evaluation_task_id": task_id}
        case_results = await self.case_result_repo.get_all(
            skip=0,
            limit=10000,
            filters=filters
        )
        
        if not case_results:
            return
        
        # 计算总体指标
        completed_results = [r for r in case_results if r.status == EvaluationStatus.COMPLETED]
        
        if not completed_results:
            return
        
        # 计算平均值
        overall_retrieval_metrics = {}
        overall_ragas_retrieval_metrics = {}
        overall_ragas_generation_metrics = {}
        
        # 检索指标
        if completed_results[0].retrieval_metrics:
            for key in completed_results[0].retrieval_metrics.keys():
                values = [r.retrieval_metrics.get(key, 0.0) for r in completed_results if r.retrieval_metrics]
                if values:
                    overall_retrieval_metrics[key] = sum(values) / len(values)
        
        # RAGAS检索指标
        if completed_results[0].ragas_retrieval_metrics:
            for key in completed_results[0].ragas_retrieval_metrics.keys():
                values = [r.ragas_retrieval_metrics.get(key, 0.0) for r in completed_results if r.ragas_retrieval_metrics]
                if values:
                    overall_ragas_retrieval_metrics[key] = sum(values) / len(values)
        
        # RAGAS生成指标
        if completed_results[0].ragas_generation_metrics:
            for key in completed_results[0].ragas_generation_metrics.keys():
                values = [r.ragas_generation_metrics.get(key, 0.0) for r in completed_results if r.ragas_generation_metrics]
                if values:
                    overall_ragas_generation_metrics[key] = sum(values) / len(values)
        
        # 计算综合评分
        overall_ragas_score = None
        ragas_scores = [r.ragas_score for r in completed_results if r.ragas_score is not None]
        if ragas_scores:
            overall_ragas_score = sum(ragas_scores) / len(ragas_scores)
        
        # 计算指标分布
        metrics_distribution = {}
        # TODO: 实现指标分布计算（最大值、最小值、标准差等）
        
        # 创建汇总
        summary = EvaluationSummary(
            id=f"eval_summary_{uuid.uuid4().hex[:12]}",
            evaluation_task_id=task_id,
            overall_retrieval_metrics=overall_retrieval_metrics,
            overall_ragas_retrieval_metrics=overall_ragas_retrieval_metrics,
            overall_ragas_generation_metrics=overall_ragas_generation_metrics,
            overall_ragas_score=overall_ragas_score,
            metrics_distribution=metrics_distribution
        )
        
        await self.summary_repo.create(summary)
    
    async def get_evaluation_task(self, task_id: str) -> Optional[EvaluationTask]:
        """获取评估任务"""
        return await self.task_repo.get_by_id(task_id)
    
    async def list_evaluation_tasks(
        self,
        test_set_id: Optional[str] = None,
        kb_id: Optional[str] = None,
        status: Optional[EvaluationStatus] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[EvaluationTask], int]:
        """获取评估任务列表"""
        filters = {}
        if test_set_id:
            filters["test_set_id"] = test_set_id
        if kb_id:
            filters["kb_id"] = kb_id
        if status:
            filters["status"] = status
        
        skip = (page - 1) * page_size
        # 按创建时间倒序排序（最新的在最上方）
        tasks = await self.task_repo.get_all(skip=skip, limit=page_size, filters=filters, order_by="-created_at")
        total = await self.task_repo.count(filters=filters)
        
        return tasks, total
    
    async def get_evaluation_summary(self, task_id: str) -> Optional[EvaluationSummary]:
        """获取评估汇总"""
        filters = {"evaluation_task_id": task_id}
        summaries = await self.summary_repo.get_all(
            skip=0,
            limit=1,
            filters=filters
        )
        return summaries[0] if summaries else None
    
    async def get_evaluation_case_results(
        self,
        task_id: str,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[EvaluationCaseResult], int]:
        """获取评估用例结果列表"""
        # 注意：MySQL仓储的filters需要字段名匹配，这里直接使用evaluation_task_id
        filters = {"evaluation_task_id": task_id}
        skip = (page - 1) * page_size
        
        results = await self.case_result_repo.get_all(skip=skip, limit=page_size, filters=filters)
        total = await self.case_result_repo.count(filters=filters)
        
        return results, total

