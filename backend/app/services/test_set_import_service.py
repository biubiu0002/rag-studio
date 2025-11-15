"""
测试集导入服务
处理测试集导入到知识库的业务逻辑
"""

from typing import Dict, Any, List, Tuple, Optional
import uuid
import asyncio
import logging
from datetime import datetime

from app.models.test import (
    TestSet, TestSetKnowledgeBase, ImportTask,
    RetrieverTestCase, GenerationTestCase
)
from app.schemas.test import ImportTestSetToKnowledgeBaseRequest, ImportPreviewResponse
from app.repositories.factory import RepositoryFactory
from app.core.exceptions import NotFoundException
from app.services.document import DocumentService
from app.services.knowledge_base import KnowledgeBaseService
from app.services.document_processor import DocumentProcessor
from app.services.rag_service import RAGService
from app.models.document import DocumentChunk, DocumentStatus

logger = logging.getLogger(__name__)


class TestSetImportService:
    """测试集导入服务"""
    
    def __init__(self):
        self.test_set_repo = RepositoryFactory.create_test_set_repository()
        self.test_set_kb_repo = RepositoryFactory.create_test_set_knowledge_base_repository()
        self.import_task_repo = RepositoryFactory.create_import_task_repository()
        self.retriever_case_repo = RepositoryFactory.create_retriever_test_case_repository()
        self.generation_case_repo = RepositoryFactory.create_generation_test_case_repository()
        self.document_service = DocumentService()
        self.kb_service = KnowledgeBaseService()
    
    async def preview_import(
        self,
        test_set_id: str,
        kb_id: str
    ) -> ImportPreviewResponse:
        """预览导入结果"""
        # 验证测试集存在
        test_set = await self.test_set_repo.get_by_id(test_set_id)
        if not test_set:
            raise NotFoundException(message=f"测试集不存在: {test_set_id}")
        
        # 验证知识库存在
        kb = await self.kb_service.get_knowledge_base(kb_id)
        if not kb:
            raise NotFoundException(message=f"知识库不存在: {kb_id}")
        
        # 提取所有答案文本
        answers = await self._extract_answers_from_test_set(test_set_id, test_set.test_type)
        
        # 检查已存在的文档（基于external_id）
        existing_count = 0
        for answer in answers:
            external_id = answer["external_id"]
            # 检查知识库中是否存在该external_id的文档
            doc_repo = RepositoryFactory.create_document_repository()
            filters = {"kb_id": kb_id, "external_id": external_id}
            existing_docs = await doc_repo.get_all(skip=0, limit=1, filters=filters)
            if existing_docs:
                existing_count += 1
        
        total_answers = len(answers)
        new_docs = total_answers - existing_count
        
        return ImportPreviewResponse(
            total_answers=total_answers,
            new_docs=new_docs,
            existing_docs=existing_count,
            skipped_docs=0
        )
    
    async def import_test_set_to_kb(
        self,
        test_set_id: str,
        request: ImportTestSetToKnowledgeBaseRequest
    ) -> ImportTask:
        """导入测试集到知识库（异步任务）"""
        # 验证测试集存在
        test_set = await self.test_set_repo.get_by_id(test_set_id)
        if not test_set:
            raise NotFoundException(message=f"测试集不存在: {test_set_id}")
        
        # 验证知识库存在
        kb = await self.kb_service.get_knowledge_base(request.kb_id)
        if not kb:
            raise NotFoundException(message=f"知识库不存在: {request.kb_id}")
        
        # 检查是否已导入过
        filters = {"test_set_id": test_set_id, "kb_id": request.kb_id}
        existing_associations = await self.test_set_kb_repo.get_all(skip=0, limit=1, filters=filters)
        
        # 获取知识库配置快照
        import_config = await self._get_kb_config_snapshot(request.kb_id)
        
        # 创建或更新关联记录
        if existing_associations:
            association = existing_associations[0]
            association.import_config = import_config
            association.imported_at = datetime.now()
            await self.test_set_kb_repo.update(association.id, association)
        else:
            association_id = f"tskb_{uuid.uuid4().hex[:12]}"
            association = TestSetKnowledgeBase(
                id=association_id,
                test_set_id=test_set_id,
                kb_id=request.kb_id,
                imported_at=datetime.now(),
                import_config=import_config
            )
            await self.test_set_kb_repo.create(association)
        
        # 创建导入任务
        import_task_id = f"import_{uuid.uuid4().hex[:12]}"
        import_task = ImportTask(
            id=import_task_id,
            test_set_id=test_set_id,
            kb_id=request.kb_id,
            status="pending",
            progress=0.0,
            import_config={
                "update_existing": request.update_existing,
                "kb_config": import_config
            }
        )
        await self.import_task_repo.create(import_task)
        
        # 异步执行导入任务
        asyncio.create_task(self._execute_import_task(import_task_id, request.update_existing))
        
        return import_task
    
    async def _execute_import_task(self, import_task_id: str, update_existing: bool):
        """执行导入任务（后台异步）"""
        import_task = await self.import_task_repo.get_by_id(import_task_id)
        if not import_task:
            logger.error(f"导入任务不存在: {import_task_id}")
            return
        
        try:
            # 更新任务状态为运行中
            import_task.status = "running"
            import_task.started_at = datetime.now()
            await self.import_task_repo.update(import_task_id, import_task)
            
            # 提取答案文本
            test_set = await self.test_set_repo.get_by_id(import_task.test_set_id)
            answers = await self._extract_answers_from_test_set(
                import_task.test_set_id,
                test_set.test_type
            )
            
            import_task.total_docs = len(answers)
            await self.import_task_repo.update(import_task_id, import_task)
            
            # 批量导入文档
            imported_count = 0
            failed_count = 0
            
            for i, answer in enumerate(answers):
                try:
                    external_id = answer["external_id"]
                    content = answer["content"]
                    
                    # 检查文档是否已存在
                    doc_repo = RepositoryFactory.create_document_repository()
                    filters = {"kb_id": import_task.kb_id, "external_id": external_id}
                    existing_docs = await doc_repo.get_all(skip=0, limit=1, filters=filters)
                    
                    if existing_docs and update_existing:
                        # 更新已存在的文档
                        doc = existing_docs[0]
                        doc.content = content
                        doc.metadata = answer.get("metadata", {})
                        await doc_repo.update(doc.id, doc)
                        imported_count += 1
                    elif not existing_docs:
                        # 创建新文档
                        documents_dict = {external_id: content}
                        created_docs, failed_docs = await self.document_service.batch_create_documents_from_dict(
                            kb_id=import_task.kb_id,
                            documents=documents_dict,
                            source=f"test_set_import_{import_task.test_set_id}"
                        )
                        if created_docs:
                            # 文档创建时已经设置了external_id，只需要更新metadata
                            doc = created_docs[0]
                            if doc.metadata:
                                doc.metadata.update(answer.get("metadata", {}))
                            else:
                                doc.metadata = answer.get("metadata", {})
                            await doc_repo.update(doc.id, doc)
                            
                            # 处理文档：分块、嵌入、写入向量库
                            try:
                                await self._process_imported_document(doc, import_task.kb_id)
                                imported_count += 1
                            except Exception as e:
                                logger.error(f"处理文档失败 {doc.id}: {e}", exc_info=True)
                                failed_count += 1
                        else:
                            failed_count += 1
                    else:
                        # 跳过（已存在但不更新）
                        pass
                    
                    # 更新进度
                    progress = (i + 1) / len(answers)
                    import_task.progress = progress
                    import_task.imported_docs = imported_count
                    import_task.failed_docs = failed_count
                    await self.import_task_repo.update(import_task_id, import_task)
                    
                except Exception as e:
                    logger.error(f"导入文档失败: {e}", exc_info=True)
                    failed_count += 1
                    import_task.failed_docs = failed_count
                    await self.import_task_repo.update(import_task_id, import_task)
            
            # 完成任务
            import_task.status = "completed"
            import_task.completed_at = datetime.now()
            import_task.progress = 1.0
            await self.import_task_repo.update(import_task_id, import_task)
            
        except Exception as e:
            logger.error(f"导入任务执行失败: {e}", exc_info=True)
            import_task.status = "failed"
            import_task.error_message = str(e)
            import_task.completed_at = datetime.now()
            await self.import_task_repo.update(import_task_id, import_task)
    
    async def _extract_answers_from_test_set(
        self,
        test_set_id: str,
        test_type: str
    ) -> List[Dict[str, Any]]:
        """从测试集中提取所有答案文本"""
        answers = []
        
        if test_type == "retrieval":
            # 获取所有检索器测试用例
            filters = {"test_set_id": test_set_id}
            cases = await self.retriever_case_repo.get_all(skip=0, limit=10000, filters=filters)
            
            for case in cases:
                for idx, expected_answer in enumerate(case.expected_answers):
                    answer_text = expected_answer.get("answer_text", "")
                    if answer_text:
                        # 生成external_id
                        external_id = f"test_set_{test_set_id}_case_{case.id}_answer_{idx}"
                        answers.append({
                            "external_id": external_id,
                            "content": answer_text,
                            "metadata": {
                                "test_case_id": case.id,
                                "question": case.question,
                                "answer_index": idx,
                                "relevance_score": expected_answer.get("relevance_score", 1.0)
                            }
                        })
        
        elif test_type == "generation":
            # 获取所有生成测试用例
            filters = {"test_set_id": test_set_id}
            cases = await self.generation_case_repo.get_all(skip=0, limit=10000, filters=filters)
            
            for case in cases:
                # 生成用例的reference_answer作为一个文档
                if case.reference_answer:
                    external_id = f"test_set_{test_set_id}_case_{case.id}_reference_answer"
                    answers.append({
                        "external_id": external_id,
                        "content": case.reference_answer,
                        "metadata": {
                            "test_case_id": case.id,
                            "question": case.question,
                            "type": "reference_answer"
                        }
                    })
                
                # reference_contexts也作为独立文档
                for idx, context in enumerate(case.reference_contexts or []):
                    if context:
                        external_id = f"test_set_{test_set_id}_case_{case.id}_context_{idx}"
                        answers.append({
                            "external_id": external_id,
                            "content": context,
                            "metadata": {
                                "test_case_id": case.id,
                                "question": case.question,
                                "type": "reference_context",
                                "context_index": idx
                            }
                        })
        
        return answers
    
    async def _get_kb_config_snapshot(self, kb_id: str) -> Dict[str, Any]:
        """获取知识库配置快照"""
        kb = await self.kb_service.get_knowledge_base(kb_id)
        if not kb:
            raise NotFoundException(message=f"知识库不存在: {kb_id}")
        
        # 获取schema配置
        kb_schema = await self.kb_service.get_knowledge_base_schema(kb_id)
        
        config = {
            "vector_db_type": kb.vector_db_type,
            "embedding_provider": kb.embedding_provider,
            "embedding_model": kb.embedding_model,
            "embedding_dimension": kb.embedding_dimension,
            "vector_db_config": kb.vector_db_config or {},
            "chunk_size": kb.chunk_size,
            "chunk_overlap": kb.chunk_overlap,
        }
        
        if kb_schema:
            config["schema_fields"] = kb_schema.get("fields", [])
        
        return config
    
    async def get_import_task(self, import_task_id: str) -> Optional[ImportTask]:
        """获取导入任务"""
        return await self.import_task_repo.get_by_id(import_task_id)
    
    async def list_import_history(
        self,
        test_set_id: str,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Dict[str, Any]], int]:
        """获取测试集的导入历史"""
        filters = {"test_set_id": test_set_id}
        skip = (page - 1) * page_size
        
        associations = await self.test_set_kb_repo.get_all(skip=skip, limit=page_size, filters=filters)
        total = await self.test_set_kb_repo.count(filters=filters)
        
        # 获取每个关联的导入任务信息
        result = []
        for assoc in associations:
            # 查找对应的导入任务
            import_filters = {
                "test_set_id": test_set_id,
                "kb_id": assoc.kb_id
            }
            import_tasks = await self.import_task_repo.get_all(skip=0, limit=1, filters=import_filters)
            
            import_task = import_tasks[0] if import_tasks else None
            
            result.append({
                "id": assoc.id,
                "test_set_id": assoc.test_set_id,
                "kb_id": assoc.kb_id,
                "imported_at": assoc.imported_at.isoformat() if isinstance(assoc.imported_at, datetime) else str(assoc.imported_at),
                "import_config": assoc.import_config,
                "kb_deleted": assoc.kb_deleted,
                "test_set_deleted": assoc.test_set_deleted,
                "import_task": {
                    "id": import_task.id if import_task else None,
                    "status": import_task.status if import_task else None,
                    "progress": import_task.progress if import_task else None,
                    "total_docs": import_task.total_docs if import_task else None,
                    "imported_docs": import_task.imported_docs if import_task else None,
                    "failed_docs": import_task.failed_docs if import_task else None,
                } if import_task else None
            })
        
        return result, total
    
    async def _process_imported_document(self, document, kb_id: str):
        """
        处理导入的文档：分块、嵌入、写入向量库
        
        Args:
            document: 文档对象
            kb_id: 知识库ID
        """
        # 获取知识库配置
        kb = await self.kb_service.get_knowledge_base(kb_id)
        if not kb:
            raise NotFoundException(message=f"知识库不存在: {kb_id}")
        
        # 获取schema配置
        kb_schema = await self.kb_service.get_knowledge_base_schema(kb_id)
        
        # 1. 分块文档
        content = document.content or ""
        if not content:
            logger.warning(f"文档 {document.id} 内容为空，跳过处理")
            return
        
        chunks = DocumentProcessor.chunk_document(
            text=content,
            method="fixed_size",
            chunk_size=kb.chunk_size or 500,
            chunk_overlap=kb.chunk_overlap or 50
        )
        
        if not chunks:
            logger.warning(f"文档 {document.id} 分块后为空，跳过处理")
            return
        
        # 2. 创建DocumentChunk记录
        chunk_repo = RepositoryFactory.create_document_chunk_repository()
        document_chunks = []
        
        for chunk in chunks:
            chunk_id = f"chunk_{uuid.uuid4().hex[:12]}"
            token_count = DocumentProcessor.estimate_tokens(chunk.content)
            
            doc_chunk = DocumentChunk(
                id=chunk_id,
                document_id=document.id,
                kb_id=kb_id,
                chunk_index=chunk.index,
                content=chunk.content,
                start_pos=chunk.start_pos,
                end_pos=chunk.end_pos,
                token_count=token_count,
                metadata=chunk.metadata or {}
            )
            
            await chunk_repo.create(doc_chunk)
            document_chunks.append(doc_chunk)
        
        # 3. 准备chunk文本和元数据
        chunk_contents = [chunk.content for chunk in chunks]
        metadata_list = []
        
        for i, doc_chunk in enumerate(document_chunks):
            metadata = {
                "document_id": document.id,
                "chunk_id": doc_chunk.id,
                "content": doc_chunk.content,
                "char_count": len(doc_chunk.content),
                "token_count": doc_chunk.token_count,
                "source": document.metadata.get("source", "import"),
                "external_id": document.external_id,
            }
            # 添加chunk的metadata
            if doc_chunk.metadata:
                metadata.update(doc_chunk.metadata)
            metadata_list.append(metadata)
        
        # 4. 使用RAGService写入向量索引
        rag_service = RAGService(kb_id=kb_id)
        write_result = await rag_service.write_index(chunk_contents, metadata_list=metadata_list)
        
        # 5. 更新chunk的vector_id和is_indexed
        # IndexWritingService会使用metadata_list中的chunk_id作为向量ID
        for doc_chunk in document_chunks:
            doc_chunk.vector_id = doc_chunk.id
            doc_chunk.is_indexed = True
            await chunk_repo.update(doc_chunk.id, doc_chunk)
        
        # 更新文档状态
        document.status = DocumentStatus.COMPLETED
        doc_repo = RepositoryFactory.create_document_repository()
        await doc_repo.update(document.id, document)
        
        logger.info(f"文档 {document.id} 处理完成: {len(chunks)} 个分块已写入向量库")

