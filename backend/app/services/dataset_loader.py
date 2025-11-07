"""
数据集加载服务
支持加载和处理T2Ranking等检索评测数据集
"""

from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class T2RankingDataset:
    """T2Ranking数据集加载器"""
    
    def __init__(
        self,
        collection_path: str,
        queries_path: str,
        qrels_path: str,
        max_docs: Optional[int] = None,
        max_queries: Optional[int] = None
    ):
        """
        初始化T2Ranking数据集加载器
        
        Args:
            collection_path: 文档集合文件路径 (collection.tsv)
            queries_path: 查询文件路径 (queries.dev.tsv)
            qrels_path: 相关性标注文件路径 (qrels.dev.tsv)
            max_docs: 最大文档数量限制（优化大数据集）
            max_queries: 最大查询数量限制（优化大数据集）
        """
        self.collection_path = Path(collection_path)
        self.queries_path = Path(queries_path)
        self.qrels_path = Path(qrels_path)
        self.max_docs = max_docs
        self.max_queries = max_queries
        
        self._collection = None
        self._queries = None
        self._qrels = None
        
    def load_collection(self) -> Dict[str, str]:
        """
        加载文档集合
        
        Returns:
            dict: {doc_id: doc_text}
        """
        if self._collection is not None:
            return self._collection
            
        logger.info(f"加载文档集合: {self.collection_path}")
        
        # 读取TSV文件，格式: doc_id \t doc_text
        df = pd.read_csv(
            self.collection_path,
            sep='\t',
            header=None,
            names=['doc_id', 'text'],
            nrows=self.max_docs
        )
        
        self._collection = dict(zip(df['doc_id'].astype(str), df['text']))
        
        logger.info(f"成功加载 {len(self._collection)} 个文档")
        return self._collection
    
    def load_queries(self) -> Dict[str, str]:
        """
        加载查询集合
        
        Returns:
            dict: {query_id: query_text}
        """
        if self._queries is not None:
            return self._queries
            
        logger.info(f"加载查询集合: {self.queries_path}")
        
        # 读取TSV文件，格式: query_id \t query_text
        df = pd.read_csv(
            self.queries_path,
            sep='\t',
            header=None,
            names=['query_id', 'text'],
            nrows=self.max_queries
        )
        
        self._queries = dict(zip(df['query_id'].astype(str), df['text']))
        
        logger.info(f"成功加载 {len(self._queries)} 个查询")
        return self._queries
    
    def load_qrels(self) -> Dict[str, List[str]]:
        """
        加载查询-文档相关性标注
        
        Returns:
            dict: {query_id: [relevant_doc_ids]}
        """
        if self._qrels is not None:
            return self._qrels
            
        logger.info(f"加载相关性标注: {self.qrels_path}")
        
        # 读取TSV文件，格式: query_id \t 0 \t doc_id \t relevance
        df = pd.read_csv(
            self.qrels_path,
            sep='\t',
            header=None,
            names=['query_id', 'q0', 'doc_id', 'relevance']
        )
        
        # 转换relevance列为数值类型，过滤掉无效行
        df['relevance'] = pd.to_numeric(df['relevance'], errors='coerce')
        df = df.dropna(subset=['relevance'])  # 删除relevance为NaN的行
        
        # 只保留相关文档（relevance > 0）
        df = df[df['relevance'] > 0]
        
        # 如果有查询数量限制，过滤查询
        if self.max_queries:
            queries = self.load_queries()
            df = df[df['query_id'].astype(str).isin(queries.keys())]
        
        # 按query_id分组，获取相关文档列表
        self._qrels = df.groupby('query_id')['doc_id'].apply(
            lambda x: x.astype(str).tolist()
        ).to_dict()
        
        # 转换query_id为字符串
        self._qrels = {str(k): v for k, v in self._qrels.items()}
        
        logger.info(f"成功加载 {len(self._qrels)} 个查询的相关性标注")
        return self._qrels
    
    def get_test_cases(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        获取测试用例列表
        
        Args:
            limit: 限制返回的测试用例数量
        
        Returns:
            测试用例列表，每个包含: query_id, query, relevant_doc_ids
        """
        queries = self.load_queries()
        qrels = self.load_qrels()
        
        test_cases = []
        for query_id, query_text in queries.items():
            if query_id in qrels:
                test_cases.append({
                    'query_id': query_id,
                    'query': query_text,
                    'relevant_doc_ids': qrels[query_id]
                })
        
        if limit:
            test_cases = test_cases[:limit]
        
        logger.info(f"生成 {len(test_cases)} 个测试用例")
        return test_cases
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取数据集统计信息
        
        Returns:
            统计信息字典
        """
        collection = self.load_collection()
        queries = self.load_queries()
        qrels = self.load_qrels()
        
        # 计算平均相关文档数
        avg_relevant_docs = sum(len(docs) for docs in qrels.values()) / len(qrels) if qrels else 0
        
        return {
            'total_documents': len(collection),
            'total_queries': len(queries),
            'total_query_doc_pairs': sum(len(docs) for docs in qrels.values()),
            'queries_with_relevant_docs': len(qrels),
            'avg_relevant_docs_per_query': round(avg_relevant_docs, 2),
            'max_relevant_docs': max(len(docs) for docs in qrels.values()) if qrels else 0,
            'min_relevant_docs': min(len(docs) for docs in qrels.values()) if qrels else 0,
        }


class DatasetService:
    """数据集管理服务"""
    
    @staticmethod
    def load_t2ranking(
        collection_path: str,
        queries_path: str,
        qrels_path: str,
        max_docs: Optional[int] = None,
        max_queries: Optional[int] = None
    ) -> T2RankingDataset:
        """
        加载T2Ranking数据集
        
        Args:
            collection_path: 文档集合文件路径
            queries_path: 查询文件路径
            qrels_path: 相关性标注文件路径
            max_docs: 最大文档数量限制
            max_queries: 最大查询数量限制
        
        Returns:
            T2RankingDataset实例
        """
        return T2RankingDataset(
            collection_path=collection_path,
            queries_path=queries_path,
            qrels_path=qrels_path,
            max_docs=max_docs,
            max_queries=max_queries
        )
    
    @staticmethod
    def sample_dataset(
        dataset: T2RankingDataset,
        n_queries: int = 100
    ) -> Tuple[Dict[str, str], List[Dict[str, Any]]]:
        """
        采样数据集以优化测试性能
        
        Args:
            dataset: 数据集实例
            n_queries: 采样的查询数量
        
        Returns:
            (sampled_collection, sampled_test_cases)
        """
        # 获取测试用例
        test_cases = dataset.get_test_cases(limit=n_queries)
        
        # 收集所有相关文档ID
        relevant_doc_ids = set()
        for case in test_cases:
            relevant_doc_ids.update(case['relevant_doc_ids'])
        
        # 加载完整文档集合
        full_collection = dataset.load_collection()
        
        # 只保留相关文档
        sampled_collection = {
            doc_id: text for doc_id, text in full_collection.items()
            if doc_id in relevant_doc_ids
        }
        
        logger.info(f"采样完成: {len(test_cases)} 个查询, {len(sampled_collection)} 个文档")
        
        return sampled_collection, test_cases

