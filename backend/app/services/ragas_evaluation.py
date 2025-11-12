"""
RAGAS评估服务
基于RAGAS框架实现检索器和生成器评估
"""

from typing import List, Dict, Any, Optional
import logging
import asyncio
from datetime import datetime

# 先初始化logger，确保错误处理可以使用
logger = logging.getLogger(__name__)

# 延迟导入RAGAS，避免启动时的依赖问题
RAGAS_AVAILABLE = None
_ragas_modules = {}

def _check_ragas_available():
    """检查RAGAS是否可用（延迟检查）"""
    global RAGAS_AVAILABLE, _ragas_modules
    if RAGAS_AVAILABLE is not None:
        return RAGAS_AVAILABLE
    
    try:
        # 尝试导入RAGAS相关模块
        # 注意：RAGAS在某些Python版本下可能有兼容性问题
        # 特别是与pydantic v1和Python 3.12的兼容性
        from ragas import evaluate
        from ragas.metrics import (
            faithfulness,
            answer_relevancy,
            answer_similarity,
            answer_correctness,
        )
        # 使用非 LLM 版本的指标，避免需要 OpenAI API Key
        # 这些指标需要实例化，且需要 rapidfuzz 库
        context_precision = None
        context_recall = None
        try:
            from ragas.metrics import (
                NonLLMContextPrecisionWithReference,
                NonLLMContextRecall,
            )
            # 尝试实例化非 LLM 版本的指标
            # 注意：实例化时需要 rapidfuzz 库
            try:
                context_precision = NonLLMContextPrecisionWithReference()
                context_recall = NonLLMContextRecall()
                logger.info("成功使用非 LLM 版本的 RAGAS 指标（不需要 OpenAI API Key）")
            except (ImportError, ModuleNotFoundError) as e:
                # 如果缺少 rapidfuzz，提示安装
                if 'rapidfuzz' in str(e).lower():
                    logger.warning(f"非 LLM 版本指标需要 rapidfuzz 库: {e}")
                    logger.warning("请运行: pip install rapidfuzz")
                    logger.warning("将回退到 LLM 版本指标（需要配置 LLM）")
                    raise  # 重新抛出异常，让外层处理
                else:
                    raise
        except (ImportError, ModuleNotFoundError) as e:
            # 如果非 LLM 版本不可用或实例化失败，回退到 LLM 版本并配置 Ollama
            logger.warning(f"非 LLM 版本指标不可用: {e}，将使用 LLM 版本并配置 Ollama")
            from ragas.metrics import (
                ContextPrecision,
                ContextRecall,
            )
            # 配置 LLM 版本的指标使用 Ollama
            try:
                from ragas.llms import LangchainLLMWrapper
                from langchain_community.llms import Ollama
                from app.config import settings
                
                # 创建 Ollama LLM 实例
                ollama_llm = Ollama(
                    model=settings.OLLAMA_CHAT_MODEL,
                    base_url=settings.OLLAMA_BASE_URL
                )
                wrapped_llm = LangchainLLMWrapper(ollama_llm)
                
                # 创建使用 Ollama 的指标实例
                context_precision = ContextPrecision(llm=wrapped_llm)
                context_recall = ContextRecall(llm=wrapped_llm)
                logger.info("已配置 LLM 版本的 RAGAS 指标使用 Ollama")
            except Exception as llm_error:
                logger.error(f"配置 Ollama LLM 失败: {llm_error}，将使用默认配置（可能需要 OpenAI API Key）")
                # 如果配置 Ollama 失败，使用默认的 LLM 版本（可能需要 OpenAI API Key）
                from ragas.metrics import (
                    context_precision,
                    context_recall,
                )
        except Exception as e:
            # 捕获其他异常
            logger.warning(f"非 LLM 版本指标初始化失败: {e}，将使用 LLM 版本并配置 Ollama")
            from ragas.metrics import (
                ContextPrecision,
                ContextRecall,
            )
            # 尝试配置 Ollama
            try:
                from ragas.llms import LangchainLLMWrapper
                from langchain_community.llms import Ollama
                from app.config import settings
                
                ollama_llm = Ollama(
                    model=settings.OLLAMA_CHAT_MODEL,
                    base_url=settings.OLLAMA_BASE_URL
                )
                wrapped_llm = LangchainLLMWrapper(ollama_llm)
                context_precision = ContextPrecision(llm=wrapped_llm)
                context_recall = ContextRecall(llm=wrapped_llm)
                logger.info("已配置 LLM 版本的 RAGAS 指标使用 Ollama")
            except Exception as llm_error:
                logger.error(f"配置 Ollama LLM 失败: {llm_error}")
                from ragas.metrics import (
                    context_precision,
                    context_recall,
                )
        # RAGAS 0.3.x 版本中，context_relevancy 改为 ContextRelevance 类
        # ContextRelevance 需要 LLM，但我们不在模块加载时创建实例
        # 而是在每次评估时根据传入的 llm_model 动态创建
        # 这里只保存导入信息和字段名
        context_relevancy_class = None
        context_relevancy_field_name = "context_relevancy"
        try:
            # 尝试使用 _nv_metrics 版本的 ContextRelevance（支持 LangchainLLMWrapper）
            from ragas.metrics._nv_metrics import ContextRelevance
            context_relevancy_class = ContextRelevance
            logger.info("成功导入 ContextRelevance 类（将在评估时动态创建实例）")
        except ImportError as e:
            # 如果导入失败，尝试使用默认的 context_relevancy（可能需要 OpenAI）
            logger.warning(f"无法导入 ContextRelevance: {e}")
            try:
                from ragas.metrics import context_relevancy
                context_relevancy_class = context_relevancy
                # 获取指标的实际字段名
                if hasattr(context_relevancy, 'name'):
                    context_relevancy_field_name = context_relevancy.name
                logger.warning("使用默认的 context_relevancy（可能需要 OpenAI API Key）")
            except ImportError:
                logger.warning("无法导入 context_relevancy，将跳过此指标")
                context_relevancy_class = None
        
        from datasets import Dataset
        
        # 验证导入的模块是否可用
        _ragas_modules = {
            'evaluate': evaluate,
            'context_precision': context_precision,
            'context_recall': context_recall,
            'context_relevancy_class': context_relevancy_class,  # 保存类而不是实例
            'context_relevancy_field_name': context_relevancy_field_name,  # 保存字段名
            'faithfulness': faithfulness,
            'answer_relevancy': answer_relevancy,
            'answer_similarity': answer_similarity,
            'answer_correctness': answer_correctness,
            'Dataset': Dataset,
        }
        RAGAS_AVAILABLE = True
        logger.info("RAGAS模块加载成功")
        return True
    except ImportError as e:
        logger.warning(f"RAGAS未安装，评估功能将受限: {e}")
        RAGAS_AVAILABLE = False
        _ragas_modules = {}
        return False
    except (TypeError, AttributeError, RuntimeError) as e:
        # 捕获兼容性相关的异常
        error_msg = str(e)
        error_type = type(e).__name__
        logger.warning(f"RAGAS加载失败（{error_type}），评估功能将受限: {error_msg}")
        if "recursive_guard" in error_msg or "ForwardRef" in error_msg or "_evaluate" in error_msg:
            logger.warning(
                "这是RAGAS与Python 3.12/pydantic v1的兼容性问题。"
                "解决方案：1) 升级pydantic到v2: pip install 'pydantic>=2.0' "
                "2) 或降级Python版本到3.11"
            )
        RAGAS_AVAILABLE = False
        _ragas_modules = {}
        return False
    except Exception as e:
        # 捕获所有其他异常
        error_msg = str(e)
        error_type = type(e).__name__
        logger.warning(f"RAGAS加载失败（{error_type}），评估功能将受限: {error_msg}")
        RAGAS_AVAILABLE = False
        _ragas_modules = {}
        return False

from app.services.retriever_evaluation import RetrieverEvaluator


class RAGASEvaluationService:
    """RAGAS评估服务"""
    
    def __init__(self):
        """初始化RAGAS评估服务"""
        # 延迟检查RAGAS可用性
        available = _check_ragas_available()
        if not available:
            logger.warning("RAGAS未安装，部分评估功能不可用")
        self.retriever_evaluator = RetrieverEvaluator()
    
    async def evaluate_retrieval(
        self,
        queries: List[str],
        retrieved_contexts: List[List[str]],
        ground_truth_contexts: List[List[str]],
        llm_model: Optional[str] = None,
        llm_base_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        评估检索质量（使用RAGAS）
        
        Args:
            queries: 查询列表
            retrieved_contexts: 检索到的上下文列表（每个查询对应一个上下文列表）
            ground_truth_contexts: 真实相关的上下文列表（每个查询对应一个上下文列表）
        
        Returns:
            评估结果字典，包含RAGAS指标和基础指标
        """
        # 延迟检查RAGAS可用性
        if not _check_ragas_available():
            # 如果RAGAS不可用，使用基础评估
            return await self._evaluate_retrieval_basic(
                queries, retrieved_contexts, ground_truth_contexts
            )
        
        try:
            # 获取RAGAS模块
            evaluate = _ragas_modules['evaluate']
            Dataset = _ragas_modules['Dataset']
            context_precision = _ragas_modules['context_precision']
            context_recall = _ragas_modules['context_recall']
            context_relevancy_class = _ragas_modules.get('context_relevancy_class')
            
            # 动态创建 ContextRelevance 实例（如果需要）
            # 注意：ContextRelevance 需要 LLM，所以只有在明确提供了 llm_model 时才创建
            # 如果没有提供 LLM 配置，就跳过这个指标（检索评估主要使用非 LLM 版本的指标）
            context_relevancy = None
            if context_relevancy_class is not None and llm_model is not None:
                try:
                    from ragas.llms import LangchainLLMWrapper
                    from langchain_community.llms import Ollama
                    from app.config import settings
                    
                    # 使用传入的 llm_model 和 llm_base_url
                    model_name = llm_model
                    base_url = (llm_base_url or settings.OLLAMA_BASE_URL).rstrip('/')
                    
                    logger.info(f"创建 ContextRelevance 实例: model={model_name}, base_url={base_url}")
                    
                    ollama_llm = Ollama(
                        model=model_name,
                        base_url=base_url
                    )
                    wrapped_llm = LangchainLLMWrapper(ollama_llm)
                    
                    # 创建 ContextRelevance 实例
                    if callable(context_relevancy_class):
                        context_relevancy = context_relevancy_class(llm=wrapped_llm)
                        logger.info(f"✓ ContextRelevance 实例创建成功（使用模型: {model_name}）")
                    else:
                        # 如果已经是实例，直接使用
                        context_relevancy = context_relevancy_class
                except Exception as e:
                    logger.error(f"❌ 创建 ContextRelevance 实例失败: {e}", exc_info=True)
                    logger.warning("将跳过 context_relevancy 指标")
                    context_relevancy = None
            elif context_relevancy_class is not None and llm_model is None:
                logger.info("未提供 LLM 配置，跳过 ContextRelevance 指标（检索评估主要使用非 LLM 版本的指标）")
                context_relevancy = None
            
            # 准备RAGAS数据集格式
            # RAGAS 0.3.x 版本字段要求：
            # - NonLLMContextPrecisionWithReference 和 NonLLMContextRecall 需要: retrieved_contexts, reference_contexts
            # - ContextRelevance 需要: user_input, retrieved_contexts (不需要 reference_contexts)
            # 注意：reference_contexts 需要是 List[List[str]] 格式（每个元素是一个字符串列表）
            # ground_truth_contexts 已经是 List[List[str]] 格式，可以直接使用
            # 确保每个元素都是列表格式
            reference_contexts_list = []
            for ref_list in ground_truth_contexts:
                if isinstance(ref_list, list):
                    # 确保每个元素都是字符串
                    ref_list_clean = [str(item) for item in ref_list if item]
                    reference_contexts_list.append(ref_list_clean if ref_list_clean else [""])
                else:
                    # 如果已经是字符串，转换为列表
                    reference_contexts_list.append([str(ref_list)] if ref_list else [""])
            
            dataset_dict = {
                "user_input": queries,  # ContextRelevance 需要此字段
                "retrieved_contexts": retrieved_contexts,  # 使用 retrieved_contexts 而不是 contexts
                "reference_contexts": reference_contexts_list,  # NonLLM 版本的指标需要此字段（List[List[str]]）
            }
            
            # 创建Dataset
            dataset = Dataset.from_dict(dataset_dict)
            
            # 执行评估（在线程中运行，避免嵌套事件循环问题）
            # RAGAS 的 evaluate 函数内部使用异步代码，在 FastAPI 的异步环境中会导致嵌套事件循环错误
            # 构建指标列表（只包含可用的指标）
            metrics_list = [
                context_precision,
                context_recall,
            ]
            # 如果 context_relevancy 可用，添加到列表中
            if context_relevancy is not None:
                metrics_list.append(context_relevancy)
            
            def _run_ragas_evaluate():
                """在线程中运行 RAGAS 评估"""
                return evaluate(
                    dataset,
                    metrics=metrics_list
                )
            
            # 使用 asyncio.to_thread 在线程池中运行同步的 RAGAS 评估
            result = await asyncio.to_thread(_run_ragas_evaluate)
            
            # 提取指标（RAGAS返回的是Dataset，可以通过列名访问）
            # Dataset对象支持字典式访问，返回的是每个用例的分数列表
            # 我们计算平均值作为总体指标
            def get_average_from_result(result, key):
                """从RAGAS结果中提取指标并计算平均值"""
                try:
                    # 尝试字典式访问
                    if hasattr(result, 'get'):
                        values = result.get(key, [0.0])
                    else:
                        # 尝试属性访问
                        values = getattr(result, key, [0.0])
                    
                    # 如果是列表，计算平均值；如果是标量，直接使用
                    if isinstance(values, list):
                        return sum(values) / len(values) if values else 0.0
                    elif isinstance(values, (int, float)):
                        return float(values)
                    else:
                        # 尝试转换为列表
                        try:
                            values_list = list(values)
                            return sum(values_list) / len(values_list) if values_list else 0.0
                        except:
                            return 0.0
                except Exception as e:
                    logger.warning(f"提取指标 {key} 失败: {e}")
                    return 0.0
            
            context_precision_avg = get_average_from_result(result, "context_precision")
            context_recall_avg = get_average_from_result(result, "context_recall")
            
            metrics = {
                "context_precision": context_precision_avg,
                "context_recall": context_recall_avg,
            }
            
            # 如果 context_relevancy 可用，提取其指标
            if context_relevancy is not None:
                context_relevancy_field_name = _ragas_modules.get('context_relevancy_field_name', 'context_relevancy')
                context_relevancy_avg = get_average_from_result(result, context_relevancy_field_name)
                metrics["context_relevancy"] = context_relevancy_avg
            else:
                metrics["context_relevancy"] = 0.0
            
            # 计算综合评分（所有指标的平均值）
            metrics["ragas_score"] = sum(metrics.values()) / len(metrics) if metrics else 0.0
            
            context_relevancy_value = metrics.get("context_relevancy", 0.0)
            logger.info(f"RAGAS检索评估完成: precision={context_precision_avg:.4f}, recall={context_recall_avg:.4f}, relevancy={context_relevancy_value:.4f}, score={metrics['ragas_score']:.4f}")
            
            # 同时计算基础指标
            basic_metrics = await self._calculate_basic_retrieval_metrics(
                queries, retrieved_contexts, ground_truth_contexts
            )
            
            return {
                **basic_metrics,
                **metrics
            }
            
        except Exception as e:
            logger.error(f"RAGAS检索评估失败: {e}", exc_info=True)
            # 降级到基础评估
            return await self._evaluate_retrieval_basic(
                queries, retrieved_contexts, ground_truth_contexts
            )
    
    async def evaluate_generation(
        self,
        queries: List[str],
        answers: List[str],
        contexts: List[List[str]],
        ground_truth_answers: Optional[List[str]] = None,
        llm_model: Optional[str] = None,
        llm_base_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        评估生成质量（使用RAGAS）
        
        Args:
            queries: 查询列表
            answers: 生成的答案列表
            contexts: 使用的上下文列表（每个查询对应一个上下文列表）
            ground_truth_answers: 真实答案列表（可选）
        
        Returns:
            评估结果字典，包含RAGAS指标
        """
        # 延迟检查RAGAS可用性
        if not _check_ragas_available():
            # 如果RAGAS不可用，返回空指标
            return {
                "faithfulness": 0.0,
                "answer_relevancy": 0.0,
                "answer_similarity": 0.0 if ground_truth_answers else None,
                "answer_correctness": 0.0 if ground_truth_answers else None,
                "ragas_score": 0.0
            }
        
        try:
            # 获取RAGAS模块
            evaluate = _ragas_modules['evaluate']
            Dataset = _ragas_modules['Dataset']
            faithfulness = _ragas_modules['faithfulness']
            answer_relevancy = _ragas_modules['answer_relevancy']
            answer_similarity = _ragas_modules['answer_similarity']
            answer_correctness = _ragas_modules['answer_correctness']
            
            # 如果提供了 LLM 配置，创建 Ollama LLM 实例供 evaluate 使用
            # 这样所有需要 LLM 的指标都会使用 Ollama 而不是默认的 OpenAI
            configured_llm = None
            if llm_model:
                try:
                    from ragas.llms import LangchainLLMWrapper
                    from langchain_community.llms import Ollama
                    from app.config import settings
                    
                    base_url = (llm_base_url or settings.OLLAMA_BASE_URL).rstrip('/')
                    logger.info(f"生成评估使用 LLM 配置: model={llm_model}, base_url={base_url}")
                    
                    ollama_llm = Ollama(
                        model=llm_model,
                        base_url=base_url
                    )
                    configured_llm = LangchainLLMWrapper(ollama_llm)
                    logger.info(f"✓ 已配置 Ollama LLM 供 RAGAS 指标使用（模型: {llm_model}）")
                except Exception as e:
                    logger.warning(f"配置 Ollama LLM 失败: {e}，RAGAS 可能会尝试使用默认的 OpenAI")
                    configured_llm = None
            
            # 准备RAGAS数据集格式
            dataset_dict = {
                "question": queries,
                "answer": answers,
                "contexts": contexts,
            }
            
            # 如果有真实答案，添加ground_truths
            if ground_truth_answers:
                dataset_dict["ground_truths"] = ground_truth_answers
            
            # 创建Dataset
            dataset = Dataset.from_dict(dataset_dict)
            
            # 构建评估指标列表
            metrics_list = [
                faithfulness,
                answer_relevancy,
            ]
            
            # 如果有真实答案，添加相似度和正确性指标
            if ground_truth_answers:
                metrics_list.extend([
                    answer_similarity,
                    answer_correctness,
                ])
            
            # 执行评估（在线程中运行，避免嵌套事件循环问题）
            def _run_ragas_evaluate():
                """在线程中运行 RAGAS 评估"""
                # 如果配置了 LLM，传入 evaluate 函数
                # 这样所有需要 LLM 的指标都会使用我们配置的 Ollama LLM
                if configured_llm is not None:
                    return evaluate(dataset, metrics=metrics_list, llm=configured_llm)
                else:
                    return evaluate(dataset, metrics=metrics_list)
            
            # 使用 asyncio.to_thread 在线程池中运行同步的 RAGAS 评估
            result = await asyncio.to_thread(_run_ragas_evaluate)
            
            # 提取指标（RAGAS返回的是Dataset，需要正确处理）
            def get_average_from_result(result, key):
                """从RAGAS结果中提取指标并计算平均值"""
                try:
                    if hasattr(result, 'get'):
                        values = result.get(key, [0.0])
                    else:
                        values = getattr(result, key, [0.0])
                    
                    if isinstance(values, list):
                        return sum(values) / len(values) if values else 0.0
                    elif isinstance(values, (int, float)):
                        return float(values)
                    else:
                        try:
                            values_list = list(values)
                            return sum(values_list) / len(values_list) if values_list else 0.0
                        except:
                            return 0.0
                except Exception as e:
                    logger.warning(f"提取指标 {key} 失败: {e}")
                    return 0.0
            
            metrics = {
                "faithfulness": get_average_from_result(result, "faithfulness"),
                "answer_relevancy": get_average_from_result(result, "answer_relevancy"),
            }
            
            if ground_truth_answers:
                metrics["answer_similarity"] = get_average_from_result(result, "answer_similarity")
                metrics["answer_correctness"] = get_average_from_result(result, "answer_correctness")
            
            # 计算综合评分
            metrics["ragas_score"] = sum(metrics.values()) / len(metrics) if metrics else 0.0
            
            logger.info(f"RAGAS生成评估完成: metrics={metrics}")
            
            return metrics
            
        except Exception as e:
            logger.error(f"RAGAS生成评估失败: {e}", exc_info=True)
            return {
                "faithfulness": 0.0,
                "answer_relevancy": 0.0,
                "ragas_score": 0.0
            }
    
    async def _evaluate_retrieval_basic(
        self,
        queries: List[str],
        retrieved_contexts: List[List[str]],
        ground_truth_contexts: List[List[str]]
    ) -> Dict[str, Any]:
        """基础检索评估（RAGAS不可用时使用）"""
        # 使用现有的RetrieverEvaluator
        results = []
        for i, query in enumerate(queries):
            # 这里需要将contexts转换为doc_ids
            # 简化处理：假设contexts是文档内容，需要根据实际情况调整
            retrieved_doc_ids = [f"doc_{j}" for j in range(len(retrieved_contexts[i]))]
            relevant_doc_ids = [f"doc_{j}" for j in range(len(ground_truth_contexts[i]))]
            
            metrics = self.retriever_evaluator.evaluate_single_query(
                retrieved_doc_ids, relevant_doc_ids
            )
            results.append(metrics)
        
        # 计算平均值
        avg_metrics = {}
        if results:
            for key in results[0].keys():
                avg_metrics[key] = sum(r[key] for r in results) / len(results)
        
        return {
            **avg_metrics,
            "context_precision": avg_metrics.get("precision", 0.0),
            "context_recall": avg_metrics.get("recall", 0.0),
            "context_relevancy": 0.0,  # 基础评估无法计算
            "ragas_score": 0.0
        }
    
    async def _calculate_basic_retrieval_metrics(
        self,
        queries: List[str],
        retrieved_contexts: List[List[str]],
        ground_truth_contexts: List[List[str]]
    ) -> Dict[str, float]:
        """计算基础检索指标"""
        results = []
        for i in range(len(queries)):
            # 简化处理：假设contexts是文档内容
            retrieved_doc_ids = [f"doc_{j}" for j in range(len(retrieved_contexts[i]))]
            relevant_doc_ids = [f"doc_{j}" for j in range(len(ground_truth_contexts[i]))]
            
            metrics = self.retriever_evaluator.evaluate_single_query(
                retrieved_doc_ids, relevant_doc_ids
            )
            results.append(metrics)
        
        # 计算平均值
        avg_metrics = {}
        if results:
            for key in results[0].keys():
                avg_metrics[key] = sum(r[key] for r in results) / len(results)
        
        return avg_metrics

