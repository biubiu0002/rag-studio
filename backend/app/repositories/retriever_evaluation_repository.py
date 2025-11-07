"""
检索器评估结果仓储
"""

from typing import List, Optional, Dict, Any
from app.repositories.base import BaseRepository
from app.models.retriever_evaluation import RetrieverEvaluationResult


class RetrieverEvaluationRepository(BaseRepository[RetrieverEvaluationResult]):
    """检索器评估结果仓储基类"""
    
    async def get_by_kb_and_test_set(
        self,
        kb_id: str,
        test_set_id: str
    ) -> List[RetrieverEvaluationResult]:
        """
        获取指定知识库和测试集的评估结果
        
        Args:
            kb_id: 知识库ID
            test_set_id: 测试集ID
        
        Returns:
            评估结果列表
        """
        filters = {
            'kb_id': kb_id,
            'test_set_id': test_set_id
        }
        return await self.get_all(filters=filters)
    
    async def get_latest_by_kb(
        self,
        kb_id: str,
        limit: int = 10
    ) -> List[RetrieverEvaluationResult]:
        """
        获取指定知识库的最新评估结果
        
        Args:
            kb_id: 知识库ID
            limit: 返回数量限制
        
        Returns:
            评估结果列表（按时间倒序）
        """
        filters = {'kb_id': kb_id}
        results = await self.get_all(filters=filters, limit=limit)
        # 按创建时间倒序排序
        return sorted(results, key=lambda x: x.created_at, reverse=True)

