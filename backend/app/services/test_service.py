"""
测试管理业务逻辑服务
"""

from typing import Optional, List, Tuple, Dict, Any
import uuid
import time
import logging

from app.models.test import (
    TestSet, TestCase, RetrievalTestResult, GenerationTestResult,
    TestType, TestStatus
)
from app.schemas.test import (
    TestSetCreate, TestSetUpdate,
    TestCaseCreate, TestCaseUpdate,
)
from app.repositories.factory import RepositoryFactory
from app.core.exceptions import NotFoundException

logger = logging.getLogger(__name__)


class TestService:
    """测试服务"""
    
    def __init__(self):
        self.test_set_repo = RepositoryFactory.create_test_set_repository()
        self.test_case_repo = RepositoryFactory.create_test_case_repository()
        self.retrieval_result_repo = RepositoryFactory.create_retrieval_test_result_repository()
        self.generation_result_repo = RepositoryFactory.create_generation_test_result_repository()
    
    # ========== 测试集管理 ==========
    
    async def create_test_set(self, data: TestSetCreate) -> TestSet:
        """创建测试集（不再绑定知识库）"""
        test_set_id = f"ts_{uuid.uuid4().hex[:12]}"
        
        # 创建测试集，不绑定知识库
        create_data = data.model_dump(exclude_none=True)
        
        # 确保所有配置字段都是字典（保留兼容性，但不再使用）
        config_fields = ["kb_config", "chunking_config", "embedding_config", "sparse_vector_config", "index_config"]
        for field in config_fields:
            if field not in create_data or create_data[field] is None:
                create_data[field] = {}
        
        # kb_id不再必填，如果提供则保留（用于兼容），但不从知识库获取配置
        if "kb_id" not in create_data:
            create_data["kb_id"] = None
        
        test_set = TestSet(
            id=test_set_id,
            **create_data
        )
        
        await self.test_set_repo.create(test_set)
        return test_set
    
    async def get_test_set(self, test_set_id: str) -> Optional[TestSet]:
        """获取测试集"""
        return await self.test_set_repo.get_by_id(test_set_id)
    
    async def list_test_sets(
        self,
        kb_id: Optional[str] = None,
        test_type: Optional[TestType] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[TestSet], int]:
        """获取测试集列表"""
        filters = {}
        if kb_id:
            filters["kb_id"] = kb_id
        if test_type:
            filters["test_type"] = test_type
        
        skip = (page - 1) * page_size
        test_sets = await self.test_set_repo.get_all(skip=skip, limit=page_size, filters=filters)
        total = await self.test_set_repo.count(filters=filters)
        
        return test_sets, total
    
    async def update_test_set(self, test_set_id: str, data: TestSetUpdate) -> Optional[TestSet]:
        """更新测试集"""
        test_set = await self.test_set_repo.get_by_id(test_set_id)
        if not test_set:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(test_set, field, value)
        
        await self.test_set_repo.update(test_set_id, test_set)
        return test_set
    
    async def delete_test_set(self, test_set_id: str) -> bool:
        """删除测试集（检查是否有关联）"""
        # 检查是否已导入到知识库
        from app.models.test import TestSetKnowledgeBase
        test_set_kb_repo = RepositoryFactory.create_test_set_knowledge_base_repository()
        filters = {"test_set_id": test_set_id, "test_set_deleted": False}
        associations = await test_set_kb_repo.get_all(skip=0, limit=1, filters=filters)
        
        if associations:
            raise ValueError(f"测试集 {test_set_id} 已导入到知识库，无法删除。请先解除关联。")
        
        # 先删除所有关联的测试用例
        try:
            test_cases, _ = await self.list_test_cases(test_set_id, page=1, page_size=10000)
            for test_case in test_cases:
                await self.test_case_repo.delete(test_case.id)
            logger.info(f"已删除测试集 {test_set_id} 下的 {len(test_cases)} 个测试用例")
        except Exception as e:
            logger.warning(f"删除测试用例时出错: {e}")
        
        # 删除测试集
        return await self.test_set_repo.delete(test_set_id)
    
    # ========== 测试用例管理 ==========
    
    async def create_test_case(self, data: TestCaseCreate) -> TestCase:
        """创建测试用例"""
        # 验证测试集存在
        test_set = await self.test_set_repo.get_by_id(data.test_set_id)
        if not test_set:
            raise NotFoundException(message=f"测试集不存在: {data.test_set_id}")
        
        test_case_id = f"tc_{uuid.uuid4().hex[:12]}"
        
        test_case = TestCase(
            id=test_case_id,
            kb_id=test_set.kb_id,
            **data.model_dump()
        )
        
        await self.test_case_repo.create(test_case)
        
        # 更新测试集的用例数量
        test_set.case_count += 1
        await self.test_set_repo.update(test_set.id, test_set)
        
        return test_case
    
    async def batch_create_test_cases(
        self,
        test_set_id: str,
        test_cases_data: List[Dict[str, Any]]
    ) -> Tuple[List[TestCase], List[Dict]]:
        """
        批量创建测试用例
        
        Args:
            test_set_id: 测试集ID
            test_cases_data: 测试用例数据列表，每个包含:
                - query: 查询文本
                - expected_chunks: 期望的chunk_ids列表
                - expected_answer: 期望答案（可选）
                - metadata: 元数据（可选）
        
        Returns:
            (成功创建的测试用例列表, 失败记录列表)
        """
        # 验证测试集存在
        test_set = await self.test_set_repo.get_by_id(test_set_id)
        if not test_set:
            raise NotFoundException(message=f"测试集不存在: {test_set_id}")
        
        created_cases = []
        failed_records = []
        
        for idx, case_data in enumerate(test_cases_data):
            try:
                test_case_id = f"tc_{uuid.uuid4().hex[:12]}"
                
                test_case = TestCase(
                    id=test_case_id,
                    test_set_id=test_set_id,
                    kb_id=test_set.kb_id,
                    query=case_data.get("query"),
                    expected_chunks=case_data.get("expected_chunks"),
                    expected_answer=case_data.get("expected_answer"),
                    metadata=case_data.get("metadata", {})
                )
                
                await self.test_case_repo.create(test_case)
                created_cases.append(test_case)
                
            except Exception as e:
                failed_records.append({
                    "index": idx,
                    "query": case_data.get("query", ""),
                    "error": str(e)
                })
        
        # 更新测试集的用例数量
        test_set.case_count += len(created_cases)
        await self.test_set_repo.update(test_set.id, test_set)
        
        return created_cases, failed_records
    
    async def get_test_case(self, test_case_id: str) -> Optional[TestCase]:
        """获取测试用例"""
        return await self.test_case_repo.get_by_id(test_case_id)
    
    async def list_test_cases(
        self,
        test_set_id: str,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[TestCase], int]:
        """获取测试用例列表"""
        filters = {"test_set_id": test_set_id}
        skip = (page - 1) * page_size
        
        cases = await self.test_case_repo.get_all(skip=skip, limit=page_size, filters=filters)
        total = await self.test_case_repo.count(filters=filters)
        
        return cases, total
    
    async def update_test_case(self, test_case_id: str, data: TestCaseUpdate) -> Optional[TestCase]:
        """更新测试用例"""
        test_case = await self.test_case_repo.get_by_id(test_case_id)
        if not test_case:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(test_case, field, value)
        
        await self.test_case_repo.update(test_case_id, test_case)
        return test_case
    
    async def delete_test_case(self, test_case_id: str) -> bool:
        """删除测试用例"""
        test_case = await self.test_case_repo.get_by_id(test_case_id)
        if not test_case:
            return False
        
        # 更新测试集的用例数量
        test_set = await self.test_set_repo.get_by_id(test_case.test_set_id)
        if test_set:
            test_set.case_count = max(0, test_set.case_count - 1)
            await self.test_set_repo.update(test_set.id, test_set)
        
        return await self.test_case_repo.delete(test_case_id)
    
    # ========== 检索测试 ==========
    
    async def run_retrieval_test(
        self,
        test_case_id: Optional[str] = None,
        test_set_id: Optional[str] = None
    ) -> dict:
        """
        执行检索测试
        
        TODO: 实现
        1. 获取测试用例
        2. 执行检索
        3. 计算评估指标
        4. 保存测试结果
        """
        # 临时返回
        return {"message": "检索测试待实现"}
    
    async def list_retrieval_results(
        self,
        test_set_id: str,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[RetrievalTestResult], int]:
        """获取检索测试结果列表"""
        filters = {"test_set_id": test_set_id}
        skip = (page - 1) * page_size
        
        results = await self.retrieval_result_repo.get_all(skip=skip, limit=page_size, filters=filters)
        total = await self.retrieval_result_repo.count(filters=filters)
        
        return results, total
    
    # ========== 生成测试 ==========
    
    async def run_generation_test(
        self,
        test_case_id: Optional[str] = None,
        test_set_id: Optional[str] = None,
        llm_model: Optional[str] = None
    ) -> dict:
        """
        执行生成测试
        
        TODO: 实现
        1. 获取测试用例
        2. 执行检索
        3. 调用LLM生成答案
        4. 计算评估指标
        5. 保存测试结果
        """
        # 临时返回
        return {"message": "生成测试待实现"}
    
    async def list_generation_results(
        self,
        test_set_id: str,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[GenerationTestResult], int]:
        """获取生成测试结果列表"""
        filters = {"test_set_id": test_set_id}
        skip = (page - 1) * page_size
        
        results = await self.generation_result_repo.get_all(skip=skip, limit=page_size, filters=filters)
        total = await self.generation_result_repo.count(filters=filters)
        
        return results, total
    
    # ========== 评估指标计算（待实现） ==========
    
    def _calculate_precision(self, retrieved: List[str], expected: List[str]) -> float:
        """
        计算精确率
        
        TODO: 实现
        """
        return 0.0
    
    def _calculate_recall(self, retrieved: List[str], expected: List[str]) -> float:
        """
        计算召回率
        
        TODO: 实现
        """
        return 0.0
    
    def _calculate_f1_score(self, precision: float, recall: float) -> float:
        """
        计算F1分数
        
        TODO: 实现
        """
        return 0.0
    
    def _calculate_mrr(self, retrieved: List[str], expected: List[str]) -> float:
        """
        计算MRR（平均倒数排名）
        
        TODO: 实现
        """
        return 0.0

