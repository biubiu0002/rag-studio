"""
测试管理业务逻辑服务
支持测试集、检索器测试用例和生成测试用例的管理
"""

from typing import Optional, List, Tuple, Dict, Any
import uuid
import time
import logging

from app.models.test import (
    TestSet, RetrievalTestResult, GenerationTestResult,
    RetrieverTestCase, GenerationTestCase,
    TestType, TestStatus
)
from app.schemas.test import (
    TestSetCreate, TestSetUpdate,
    RetrieverTestCaseCreate, RetrieverTestCaseUpdate,
    GenerationTestCaseCreate, GenerationTestCaseUpdate,
    ExpectedAnswerCreate
)
from app.repositories.factory import RepositoryFactory
from app.core.exceptions import NotFoundException
from app.core.singleton import singleton

logger = logging.getLogger(__name__)


@singleton
class TestService:
    """测试服务"""
    
    def __init__(self):
        self.test_set_repo = RepositoryFactory.create_test_set_repository()
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
        
        # 删除测试用例（检索器和生成测试用例）
        try:
            retriever_service = RetrieverTestCaseService()
            generation_service = GenerationTestCaseService()
            
            # 删除检索器测试用例
            retriever_cases, _ = await retriever_service.list_test_cases(test_set_id, page=1, page_size=10000)
            for case in retriever_cases:
                await retriever_service.delete_test_case(case.id)
            if retriever_cases:
                logger.info(f"已删除测试集 {test_set_id} 下的 {len(retriever_cases)} 个检索器测试用例")
            
            # 删除生成测试用例
            generation_cases, _ = await generation_service.list_test_cases(test_set_id, page=1, page_size=10000)
            for case in generation_cases:
                await generation_service.delete_test_case(case.id)
            if generation_cases:
                logger.info(f"已删除测试集 {test_set_id} 下的 {len(generation_cases)} 个生成测试用例")
        except Exception as e:
            logger.warning(f"删除测试用例时出错: {e}")
        
        # 删除测试集
        return await self.test_set_repo.delete(test_set_id)
    
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


@singleton
class RetrieverTestCaseService:
    """检索器测试用例服务"""
    
    def __init__(self):
        self.test_case_repo = RepositoryFactory.create_retriever_test_case_repository()
        self.test_set_repo = RepositoryFactory.create_test_set_repository()
    
    async def create_test_case(self, data: RetrieverTestCaseCreate) -> RetrieverTestCase:
        """创建检索器测试用例"""
        # 验证测试集存在
        test_set = await self.test_set_repo.get_by_id(data.test_set_id)
        if not test_set:
            raise NotFoundException(message=f"测试集不存在: {data.test_set_id}")
        
        test_case_id = f"rtc_{uuid.uuid4().hex[:12]}"
        
        # 转换expected_answers为字典格式
        expected_answers = [
            {
                "answer_text": ans.answer_text,
                "chunk_id": ans.chunk_id,
                "relevance_score": ans.relevance_score
            }
            for ans in data.expected_answers
        ]
        
        test_case = RetrieverTestCase(
            id=test_case_id,
            test_set_id=data.test_set_id,
            question=data.question,
            expected_answers=expected_answers,
            metadata=data.metadata
        )
        
        await self.test_case_repo.create(test_case)
        
        # 更新测试集的用例数量
        test_set.case_count += 1
        await self.test_set_repo.update(test_set.id, test_set)
        
        return test_case
    
    async def batch_create_test_cases(
        self,
        test_set_id: str,
        cases_data: List[Dict[str, Any]]
    ) -> Tuple[int, int, List[Dict]]:
        """
        批量创建检索器测试用例
        
        Args:
            test_set_id: 测试集ID
            cases_data: 测试用例数据列表
        
        Returns:
            (成功数量, 失败数量, 失败记录列表)
        """
        # 验证测试集存在
        test_set = await self.test_set_repo.get_by_id(test_set_id)
        if not test_set:
            raise NotFoundException(message=f"测试集不存在: {test_set_id}")
        
        success_count = 0
        failed_records = []
        
        for idx, case_data in enumerate(cases_data):
            try:
                test_case_id = f"rtc_{uuid.uuid4().hex[:12]}"
                
                # 确保expected_answers格式正确
                expected_answers = case_data.get("expected_answers", [])
                if not expected_answers:
                    raise ValueError("expected_answers不能为空")
                
                test_case = RetrieverTestCase(
                    id=test_case_id,
                    test_set_id=test_set_id,
                    question=case_data.get("question"),
                    expected_answers=expected_answers,
                    metadata=case_data.get("metadata", {})
                )
                
                await self.test_case_repo.create(test_case)
                success_count += 1
                
            except Exception as e:
                failed_records.append({
                    "index": idx,
                    "question": case_data.get("question", ""),
                    "error": str(e)
                })
        
        # 更新测试集的用例数量
        if success_count > 0:
            test_set.case_count += success_count
            await self.test_set_repo.update(test_set.id, test_set)
        
        failed_count = len(failed_records)
        return success_count, failed_count, failed_records
    
    async def get_test_case(self, case_id: str) -> Optional[RetrieverTestCase]:
        """获取检索器测试用例详情"""
        return await self.test_case_repo.get_by_id(case_id)
    
    async def list_test_cases(
        self,
        test_set_id: str,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[RetrieverTestCase], int]:
        """获取检索器测试用例列表"""
        filters = {"test_set_id": test_set_id}
        skip = (page - 1) * page_size
        
        cases = await self.test_case_repo.get_all(skip=skip, limit=page_size, filters=filters)
        total = await self.test_case_repo.count(filters=filters)
        
        return cases, total
    
    async def update_test_case(
        self,
        case_id: str,
        data: RetrieverTestCaseUpdate
    ) -> Optional[RetrieverTestCase]:
        """更新检索器测试用例"""
        test_case = await self.test_case_repo.get_by_id(case_id)
        if not test_case:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        
        # 特殊处理expected_answers
        # model_dump()会将嵌套的Pydantic模型转换为字典，所以这里直接按字典访问
        if "expected_answers" in update_data and update_data["expected_answers"]:
            expected_answers = [
                {
                    "answer_text": ans["answer_text"],
                    "chunk_id": ans.get("chunk_id"),
                    "relevance_score": ans.get("relevance_score", 1.0)
                }
                for ans in update_data["expected_answers"]
            ]
            update_data["expected_answers"] = expected_answers
        
        for field, value in update_data.items():
            setattr(test_case, field, value)
        
        await self.test_case_repo.update(case_id, test_case)
        return test_case
    
    async def delete_test_case(self, case_id: str) -> bool:
        """删除检索器测试用例"""
        test_case = await self.test_case_repo.get_by_id(case_id)
        if not test_case:
            return False
        
        # 更新测试集的用例数量
        test_set = await self.test_set_repo.get_by_id(test_case.test_set_id)
        if test_set:
            test_set.case_count = max(0, test_set.case_count - 1)
            await self.test_set_repo.update(test_set.id, test_set)
        
        return await self.test_case_repo.delete(case_id)
    
    async def batch_delete_test_cases(self, case_ids: List[str]) -> Tuple[int, int]:
        """
        批量删除检索器测试用例
        
        Returns:
            (成功数量, 失败数量)
        """
        success_count = 0
        failed_count = 0
        
        for case_id in case_ids:
            try:
                deleted = await self.delete_test_case(case_id)
                if deleted:
                    success_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                logger.error(f"删除测试用例失败 {case_id}: {e}")
                failed_count += 1
        
        return success_count, failed_count
    
    async def add_expected_answer(
        self,
        case_id: str,
        answer_data: ExpectedAnswerCreate
    ) -> Optional[RetrieverTestCase]:
        """添加期望答案到测试用例"""
        test_case = await self.test_case_repo.get_by_id(case_id)
        if not test_case:
            return None
        
        new_answer = {
            "answer_text": answer_data.answer_text,
            "chunk_id": answer_data.chunk_id,
            "relevance_score": answer_data.relevance_score
        }
        
        test_case.expected_answers.append(new_answer)
        await self.test_case_repo.update(case_id, test_case)
        
        return test_case
    
    async def update_expected_answer(
        self,
        case_id: str,
        answer_index: int,
        answer_data: ExpectedAnswerCreate
    ) -> Optional[RetrieverTestCase]:
        """更新测试用例的某个期望答案"""
        test_case = await self.test_case_repo.get_by_id(case_id)
        if not test_case:
            return None
        
        if answer_index < 0 or answer_index >= len(test_case.expected_answers):
            raise ValueError(f"答案索引超出范围: {answer_index}")
        
        test_case.expected_answers[answer_index] = {
            "answer_text": answer_data.answer_text,
            "chunk_id": answer_data.chunk_id,
            "relevance_score": answer_data.relevance_score
        }
        
        await self.test_case_repo.update(case_id, test_case)
        return test_case
    
    async def delete_expected_answer(
        self,
        case_id: str,
        answer_index: int
    ) -> Optional[RetrieverTestCase]:
        """删除测试用例的某个期望答案"""
        test_case = await self.test_case_repo.get_by_id(case_id)
        if not test_case:
            return None
        
        if answer_index < 0 or answer_index >= len(test_case.expected_answers):
            raise ValueError(f"答案索引超出范围: {answer_index}")
        
        if len(test_case.expected_answers) <= 1:
            raise ValueError("测试用例至少需要一个期望答案")
        
        test_case.expected_answers.pop(answer_index)
        await self.test_case_repo.update(case_id, test_case)
        
        return test_case


@singleton
class GenerationTestCaseService:
    """生成测试用例服务"""
    
    def __init__(self):
        self.test_case_repo = RepositoryFactory.create_generation_test_case_repository()
        self.test_set_repo = RepositoryFactory.create_test_set_repository()
    
    async def create_test_case(self, data: GenerationTestCaseCreate) -> GenerationTestCase:
        """创建生成测试用例"""
        # 验证测试集存在
        test_set = await self.test_set_repo.get_by_id(data.test_set_id)
        if not test_set:
            raise NotFoundException(message=f"测试集不存在: {data.test_set_id}")
        
        test_case_id = f"gtc_{uuid.uuid4().hex[:12]}"
        
        test_case = GenerationTestCase(
            id=test_case_id,
            test_set_id=data.test_set_id,
            question=data.question,
            reference_answer=data.reference_answer,
            reference_contexts=data.reference_contexts,
            metadata=data.metadata
        )
        
        await self.test_case_repo.create(test_case)
        
        # 更新测试集的用例数量
        test_set.case_count += 1
        await self.test_set_repo.update(test_set.id, test_set)
        
        return test_case
    
    async def batch_create_test_cases(
        self,
        test_set_id: str,
        cases_data: List[Dict[str, Any]]
    ) -> Tuple[int, int, List[Dict]]:
        """
        批量创建生成测试用例
        
        Args:
            test_set_id: 测试集ID
            cases_data: 测试用例数据列表
        
        Returns:
            (成功数量, 失败数量, 失败记录列表)
        """
        # 验证测试集存在
        test_set = await self.test_set_repo.get_by_id(test_set_id)
        if not test_set:
            raise NotFoundException(message=f"测试集不存在: {test_set_id}")
        
        success_count = 0
        failed_records = []
        
        for idx, case_data in enumerate(cases_data):
            try:
                test_case_id = f"gtc_{uuid.uuid4().hex[:12]}"
                
                test_case = GenerationTestCase(
                    id=test_case_id,
                    test_set_id=test_set_id,
                    question=case_data.get("question"),
                    reference_answer=case_data.get("reference_answer"),
                    reference_contexts=case_data.get("reference_contexts", []),
                    metadata=case_data.get("metadata", {})
                )
                
                await self.test_case_repo.create(test_case)
                success_count += 1
                
            except Exception as e:
                failed_records.append({
                    "index": idx,
                    "question": case_data.get("question", ""),
                    "error": str(e)
                })
        
        # 更新测试集的用例数量
        if success_count > 0:
            test_set.case_count += success_count
            await self.test_set_repo.update(test_set.id, test_set)
        
        failed_count = len(failed_records)
        return success_count, failed_count, failed_records
    
    async def get_test_case(self, case_id: str) -> Optional[GenerationTestCase]:
        """获取生成测试用例详情"""
        return await self.test_case_repo.get_by_id(case_id)
    
    async def list_test_cases(
        self,
        test_set_id: str,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[GenerationTestCase], int]:
        """获取生成测试用例列表"""
        filters = {"test_set_id": test_set_id}
        skip = (page - 1) * page_size
        
        cases = await self.test_case_repo.get_all(skip=skip, limit=page_size, filters=filters)
        total = await self.test_case_repo.count(filters=filters)
        
        return cases, total
    
    async def update_test_case(
        self,
        case_id: str,
        data: GenerationTestCaseUpdate
    ) -> Optional[GenerationTestCase]:
        """更新生成测试用例"""
        test_case = await self.test_case_repo.get_by_id(case_id)
        if not test_case:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(test_case, field, value)
        
        await self.test_case_repo.update(case_id, test_case)
        return test_case
    
    async def delete_test_case(self, case_id: str) -> bool:
        """删除生成测试用例"""
        test_case = await self.test_case_repo.get_by_id(case_id)
        if not test_case:
            return False
        
        # 更新测试集的用例数量
        test_set = await self.test_set_repo.get_by_id(test_case.test_set_id)
        if test_set:
            test_set.case_count = max(0, test_set.case_count - 1)
            await self.test_set_repo.update(test_set.id, test_set)
        
        return await self.test_case_repo.delete(case_id)
    
    async def batch_delete_test_cases(self, case_ids: List[str]) -> Tuple[int, int]:
        """
        批量删除生成测试用例
        
        Returns:
            (成功数量, 失败数量)
        """
        success_count = 0
        failed_count = 0
        
        for case_id in case_ids:
            try:
                deleted = await self.delete_test_case(case_id)
                if deleted:
                    success_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                logger.error(f"删除测试用例失败 {case_id}: {e}")
                failed_count += 1
        
        return success_count, failed_count

