"""
检索器评估服务
基于RAGAS框架实现检索质量评估
"""

from typing import List, Dict, Any, Optional
import logging
import numpy as np

from app.models.retriever_evaluation import RetrievalMetrics

logger = logging.getLogger(__name__)


class RetrieverEvaluator:
    """检索器评估器"""
    
    def __init__(self, top_k: int = 10):
        """
        初始化检索器评估器
        
        Args:
            top_k: 评估时考虑的top-k结果
        """
        self.top_k = top_k
    
    def evaluate_single_query(
        self,
        retrieved_doc_ids: List[str],
        relevant_doc_ids: List[str],
        relevance_scores: Optional[Dict[str, float]] = None
    ) -> Dict[str, float]:
        """
        评估单个查询的检索结果
        
        Args:
            retrieved_doc_ids: 检索返回的文档ID列表（按相关性排序）
            relevant_doc_ids: 真实相关的文档ID列表
            relevance_scores: 可选的关联度分数字典，key为文档ID，value为关联度分数（0.0-1.0）
                            如果提供，NDCG等指标将使用这些分数；否则使用二值判断
        
        Returns:
            评估指标字典
        """
        # 取top_k结果
        retrieved_doc_ids = retrieved_doc_ids[:self.top_k]
        
        # 计算各项指标
        precision = self._calculate_precision(retrieved_doc_ids, relevant_doc_ids)
        recall = self._calculate_recall(retrieved_doc_ids, relevant_doc_ids)
        f1_score = self._calculate_f1(precision, recall)
        mrr = self._calculate_mrr(retrieved_doc_ids, relevant_doc_ids)
        map_score = self._calculate_map(retrieved_doc_ids, relevant_doc_ids)
        ndcg = self._calculate_ndcg(retrieved_doc_ids, relevant_doc_ids, relevance_scores)
        hit_rate = self._calculate_hit_rate(retrieved_doc_ids, relevant_doc_ids)
        
        return {
            'precision': precision,
            'recall': recall,
            'f1_score': f1_score,
            'mrr': mrr,
            'map': map_score,
            'ndcg': ndcg,
            'hit_rate': hit_rate
        }
    
    def evaluate_batch(
        self,
        results: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """
        批量评估多个查询的检索结果
        
        Args:
            results: 检索结果列表，每个包含:
                - query_id: 查询ID（可选）
                - retrieved_doc_ids: 检索到的文档ID列表
                - relevant_doc_ids: 真实相关文档ID列表
                - relevance_scores: 可选的关联度分数字典（可选）
        
        Returns:
            平均评估指标
        """
        if not results:
            return self._empty_metrics()
        
        metrics_list = []
        for result in results:
            relevance_scores = result.get('relevance_scores')
            metrics = self.evaluate_single_query(
                result['retrieved_doc_ids'],
                result['relevant_doc_ids'],
                relevance_scores=relevance_scores
            )
            metrics_list.append(metrics)
        
        # 计算平均值
        avg_metrics = {}
        for key in metrics_list[0].keys():
            avg_metrics[key] = np.mean([m[key] for m in metrics_list])
        
        return avg_metrics
    
    def _calculate_precision(
        self,
        retrieved: List[str],
        relevant: List[str]
    ) -> float:
        """
        计算精确率 Precision@K
        Precision = |检索到的相关文档| / |检索到的文档|
        """
        if not retrieved:
            return 0.0
        
        relevant_set = set(relevant)
        retrieved_relevant = sum(1 for doc_id in retrieved if doc_id in relevant_set)
        
        return retrieved_relevant / len(retrieved)
    
    def _calculate_recall(
        self,
        retrieved: List[str],
        relevant: List[str]
    ) -> float:
        """
        计算召回率 Recall@K
        Recall = |检索到的相关文档| / |所有相关文档|
        """
        if not relevant:
            return 0.0
        
        relevant_set = set(relevant)
        retrieved_relevant = sum(1 for doc_id in retrieved if doc_id in relevant_set)
        
        return retrieved_relevant / len(relevant)
    
    def _calculate_f1(self, precision: float, recall: float) -> float:
        """
        计算F1分数
        F1 = 2 * (Precision * Recall) / (Precision + Recall)
        """
        if precision + recall == 0:
            return 0.0
        
        return 2 * (precision * recall) / (precision + recall)
    
    def _calculate_mrr(
        self,
        retrieved: List[str],
        relevant: List[str]
    ) -> float:
        """
        计算平均倒数排名 Mean Reciprocal Rank
        MRR = 1 / rank of first relevant doc
        """
        relevant_set = set(relevant)
        
        for rank, doc_id in enumerate(retrieved, start=1):
            if doc_id in relevant_set:
                return 1.0 / rank
        
        return 0.0
    
    def _calculate_map(
        self,
        retrieved: List[str],
        relevant: List[str]
    ) -> float:
        """
        计算平均精度 Average Precision
        AP = (sum of P@k for each relevant doc) / |relevant docs|
        """
        if not relevant:
            return 0.0
        
        relevant_set = set(relevant)
        precision_sum = 0.0
        relevant_count = 0
        
        for k, doc_id in enumerate(retrieved, start=1):
            if doc_id in relevant_set:
                relevant_count += 1
                # 计算P@k
                precision_at_k = relevant_count / k
                precision_sum += precision_at_k
        
        if relevant_count == 0:
            return 0.0
        
        return precision_sum / len(relevant)
    
    def _calculate_ndcg(
        self,
        retrieved: List[str],
        relevant: List[str],
        relevance_scores: Optional[Dict[str, float]] = None,
        k: Optional[int] = None
    ) -> float:
        """
        计算归一化折损累积增益 Normalized Discounted Cumulative Gain
        
        Args:
            retrieved: 检索结果列表
            relevant: 相关文档列表
            relevance_scores: 可选的关联度分数字典，key为文档ID，value为关联度分数
                            如果提供，使用实际分数；否则使用二值判断（相关=1.0，不相关=0.0）
            k: 考虑的位置数，默认为retrieved长度
        """
        if k is None:
            k = len(retrieved)
        
        # 计算DCG（实际排序的折扣累积增益）
        dcg = 0.0
        for i, doc_id in enumerate(retrieved[:k], start=1):
            if relevance_scores is not None:
                # 使用关联度分数
                rel_score = relevance_scores.get(doc_id, 0.0)
            else:
                # 使用二值判断
                rel_score = 1.0 if doc_id in relevant else 0.0
            
            if rel_score > 0:
                dcg += rel_score / np.log2(i + 1)
        
        # 计算IDCG（理想情况下的DCG）
        # 理想情况：按关联度分数从高到低排序
        if relevance_scores is not None:
            # 使用关联度分数计算IDCG
            ideal_relevance_scores = []
            for doc_id in relevant:
                rel_score = relevance_scores.get(doc_id, 0.0)
                # 只考虑关联度大于0的文档
                if rel_score > 0:
                    ideal_relevance_scores.append(rel_score)
            # 按分数从高到低排序
            ideal_relevance_scores.sort(reverse=True)
            # 计算IDCG
            idcg = 0.0
            for i, rel_score in enumerate(ideal_relevance_scores[:k], start=1):
                idcg += rel_score / np.log2(i + 1)
        else:
            # 使用二值判断计算IDCG
            idcg = 0.0
            for i in range(1, min(len(relevant), k) + 1):
                idcg += 1.0 / np.log2(i + 1)
        
        if idcg == 0:
            return 0.0
        
        return dcg / idcg
    
    def _calculate_hit_rate(
        self,
        retrieved: List[str],
        relevant: List[str]
    ) -> float:
        """
        计算命中率
        Hit Rate = 1 if 至少有一个相关文档被检索到, 0 otherwise
        """
        relevant_set = set(relevant)
        for doc_id in retrieved:
            if doc_id in relevant_set:
                return 1.0
        return 0.0
    
    def _empty_metrics(self) -> Dict[str, float]:
        """返回空指标"""
        return {
            'precision': 0.0,
            'recall': 0.0,
            'f1_score': 0.0,
            'mrr': 0.0,
            'map': 0.0,
            'ndcg': 0.0,
            'hit_rate': 0.0
        }


class RAGASEvaluator:
    """
    基于RAGAS框架的RAG评估器
    
    RAGAS提供的评估指标：
    1. Context Precision: 检索上下文的精确度
    2. Context Recall: 检索上下文的召回率
    3. Faithfulness: 答案对上下文的忠实度
    4. Answer Relevancy: 答案与问题的相关性
    """
    
    def __init__(self):
        """初始化RAGAS评估器"""
        self.retriever_evaluator = RetrieverEvaluator()
    
    async def evaluate_retrieval(
        self,
        query: str,
        retrieved_contexts: List[str],
        ground_truth_contexts: List[str]
    ) -> Dict[str, float]:
        """
        评估检索质量
        
        Args:
            query: 查询文本
            retrieved_contexts: 检索到的上下文列表
            ground_truth_contexts: 真实相关的上下文列表
        
        Returns:
            评估指标
        """
        # TODO: 集成RAGAS的context_precision和context_recall
        # from ragas.metrics import context_precision, context_recall
        
        logger.warning("RAGAS集成待完善，当前使用基础评估指标")
        
        return {
            'context_precision': 0.0,
            'context_recall': 0.0
        }
    
    async def evaluate_generation(
        self,
        query: str,
        answer: str,
        contexts: List[str],
        ground_truth_answer: Optional[str] = None
    ) -> Dict[str, float]:
        """
        评估生成质量
        
        Args:
            query: 查询文本
            answer: 生成的答案
            contexts: 使用的上下文
            ground_truth_answer: 真实答案（可选）
        
        Returns:
            评估指标
        """
        # TODO: 集成RAGAS的faithfulness和answer_relevancy
        # from ragas.metrics import faithfulness, answer_relevancy
        
        logger.warning("RAGAS集成待完善")
        
        return {
            'faithfulness': 0.0,
            'answer_relevancy': 0.0
        }


class RetrievalTestRunner:
    """检索测试运行器"""
    
    def __init__(
        self,
        evaluator: RetrieverEvaluator,
        top_k: int = 10
    ):
        """
        初始化测试运行器
        
        Args:
            evaluator: 评估器实例
            top_k: 检索返回的top-k数量
        """
        self.evaluator = evaluator
        self.top_k = top_k
    
    async def run_test(
        self,
        retriever_func,
        test_cases: List[Dict[str, Any]],
        **retriever_kwargs
    ) -> Dict[str, Any]:
        """
        运行检索测试
        
        Args:
            retriever_func: 检索函数，接收query返回doc_ids
            test_cases: 测试用例列表
            **retriever_kwargs: 传递给检索函数的额外参数
        
        Returns:
            测试结果，包含总体指标和详细结果
        """
        results = []
        
        for test_case in test_cases:
            query = test_case['query']
            relevant_doc_ids = test_case['relevant_doc_ids']
            
            try:
                # 执行检索
                retrieved_doc_ids = await retriever_func(
                    query=query,
                    top_k=self.top_k,
                    **retriever_kwargs
                )
                
                # 评估结果
                metrics = self.evaluator.evaluate_single_query(
                    retrieved_doc_ids,
                    relevant_doc_ids
                )
                
                results.append({
                    'query_id': test_case.get('query_id'),
                    'query': query,
                    'retrieved_doc_ids': retrieved_doc_ids,
                    'relevant_doc_ids': relevant_doc_ids,
                    'metrics': metrics
                })
                
            except Exception as e:
                logger.error(f"查询 {test_case.get('query_id')} 执行失败: {str(e)}")
                results.append({
                    'query_id': test_case.get('query_id'),
                    'query': query,
                    'error': str(e)
                })
        
        # 计算总体指标
        valid_results = [r for r in results if 'metrics' in r]
        overall_metrics = self.evaluator.evaluate_batch([
            {
                'retrieved_doc_ids': r['retrieved_doc_ids'],
                'relevant_doc_ids': r['relevant_doc_ids']
            }
            for r in valid_results
        ])
        
        return {
            'overall_metrics': overall_metrics,
            'total_queries': len(test_cases),
            'successful_queries': len(valid_results),
            'failed_queries': len(test_cases) - len(valid_results),
            'detailed_results': results
        }

