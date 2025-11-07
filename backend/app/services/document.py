"""
文档业务逻辑服务
"""

from typing import Optional, List, Tuple, Dict
import uuid
from pathlib import Path
from fastapi import UploadFile

from app.models.document import Document, DocumentChunk, DocumentStatus, DocumentType
from app.repositories.factory import RepositoryFactory
from app.core.exceptions import NotFoundException, BadRequestException
from app.config import settings


class DocumentService:
    """文档服务"""
    
    def __init__(self):
        self.doc_repository = RepositoryFactory.create_document_repository()
        self.chunk_repository = RepositoryFactory.create_document_chunk_repository()
    
    async def upload_document(self, kb_id: str, file: UploadFile) -> Document:
        """
        上传文档
        
        Args:
            kb_id: 知识库ID
            file: 上传的文件
        
        Returns:
            文档对象
        """
        # 验证文件类型
        file_extension = Path(file.filename).suffix.lower().lstrip('.')
        try:
            file_type = DocumentType(file_extension)
        except ValueError:
            raise BadRequestException(
                message=f"不支持的文件类型: {file_extension}",
                details={"supported_types": [t.value for t in DocumentType]}
            )
        
        # 生成文档ID和存储路径
        doc_id = f"doc_{uuid.uuid4().hex[:12]}"
        file_path = Path(settings.STORAGE_PATH) / "documents" / kb_id / f"{doc_id}{Path(file.filename).suffix}"
        
        # 保存文件
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # TODO: 实现文件保存
        # content = await file.read()
        # with open(file_path, "wb") as f:
        #     f.write(content)
        # file_size = len(content)
        
        file_size = 0  # 临时
        
        # 创建文档记录
        document = Document(
            id=doc_id,
            kb_id=kb_id,
            name=file.filename,
            file_path=str(file_path),
            file_size=file_size,
            file_type=file_type,
            status=DocumentStatus.UPLOADED,
        )
        
        await self.doc_repository.create(document)
        
        return document
    
    async def batch_create_documents_from_dict(
        self,
        kb_id: str,
        documents: dict[str, str],
        source: str = "import"
    ) -> Tuple[List[Document], List[dict]]:
        """
        批量从字典创建文档
        
        Args:
            kb_id: 知识库ID
            documents: 文档字典 {external_id: content}
            source: 数据来源标识
        
        Returns:
            (成功创建的文档列表, 失败记录列表)
        """
        created_docs = []
        failed_records = []
        
        for external_id, content in documents.items():
            try:
                doc_id = f"doc_{uuid.uuid4().hex[:12]}"
                
                # 创建文档对象（纯文本，不需要文件）
                document = Document(
                    id=doc_id,
                    kb_id=kb_id,
                    name=external_id,  # 使用external_id作为名称
                    external_id=external_id,
                    file_path=f"virtual://import/{source}/{external_id}",  # 虚拟路径
                    file_size=len(content.encode('utf-8')),
                    file_type=DocumentType.TXT,
                    content=content,  # 直接保存内容
                    status=DocumentStatus.UPLOADED,
                    metadata={
                        "source": source,
                        "import_method": "batch_create_from_dict"
                    }
                )
                
                await self.doc_repository.create(document)
                created_docs.append(document)
                
            except Exception as e:
                failed_records.append({
                    "external_id": external_id,
                    "error": str(e)
                })
        
        return created_docs, failed_records
    
    async def get_document(self, document_id: str) -> Optional[Document]:
        """获取文档"""
        return await self.doc_repository.get_by_id(document_id)
    
    async def list_documents(
        self,
        kb_id: str,
        page: int = 1,
        page_size: int = 20,
        status: Optional[DocumentStatus] = None
    ) -> Tuple[List[Document], int]:
        """
        获取文档列表
        
        Args:
            kb_id: 知识库ID
            page: 页码
            page_size: 每页大小
            status: 状态筛选
        
        Returns:
            (文档列表, 总数量)
        """
        filters = {"kb_id": kb_id}
        if status:
            filters["status"] = status
        
        skip = (page - 1) * page_size
        docs = await self.doc_repository.get_all(skip=skip, limit=page_size, filters=filters)
        total = await self.doc_repository.count(filters=filters)
        
        return docs, total
    
    async def delete_document(self, document_id: str) -> bool:
        """
        删除文档
        
        Args:
            document_id: 文档ID
        
        Returns:
            是否删除成功
        """
        # TODO: 删除文档文件
        # TODO: 删除文档分块
        # TODO: 删除向量索引
        
        return await self.doc_repository.delete(document_id)
    
    async def process_document(self, document_id: str, force_reprocess: bool = False):
        """
        处理文档（解析、分块、嵌入、索引）
        
        Args:
            document_id: 文档ID
            force_reprocess: 是否强制重新处理
        """
        document = await self.doc_repository.get_by_id(document_id)
        if not document:
            raise NotFoundException(message=f"文档不存在: {document_id}")
        
        # 更新状态为处理中
        document.status = DocumentStatus.PROCESSING
        await self.doc_repository.update(document_id, document)
        
        # TODO: 异步执行处理流程
        # 1. 解析文档内容
        # 2. 分块
        # 3. 嵌入
        # 4. 写入向量数据库
        
        # 临时：直接标记为完成
        document.status = DocumentStatus.COMPLETED
        await self.doc_repository.update(document_id, document)
    
    async def list_document_chunks(
        self,
        document_id: str,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[DocumentChunk], int]:
        """
        获取文档分块列表
        
        Args:
            document_id: 文档ID
            page: 页码
            page_size: 每页大小
        
        Returns:
            (分块列表, 总数量)
        """
        filters = {"document_id": document_id}
        skip = (page - 1) * page_size
        
        chunks = await self.chunk_repository.get_all(skip=skip, limit=page_size, filters=filters)
        total = await self.chunk_repository.count(filters=filters)
        
        return chunks, total
    
    # ========== 私有方法（待实现） ==========
    
    async def _parse_document(self, document: Document) -> str:
        """
        解析文档内容
        
        TODO: 实现
        1. 根据文件类型选择解析器
        2. 提取文本内容
        3. 处理特殊格式（表格、图片等）
        """
        pass
    
    async def _chunk_document(self, document: Document, content: str) -> List[DocumentChunk]:
        """
        分块文档
        
        TODO: 实现
        1. 根据知识库配置的chunk_size分块
        2. 处理overlap
        3. 生成分块对象
        """
        pass
    
    async def _embed_chunks(self, chunks: List[DocumentChunk]):
        """
        嵌入分块
        
        TODO: 实现
        1. 获取嵌入模型
        2. 批量嵌入
        3. 更新分块的embedding字段
        """
        pass
    
    async def _index_chunks(self, chunks: List[DocumentChunk]):
        """
        索引分块到向量数据库
        
        TODO: 实现
        1. 连接向量数据库
        2. 批量写入向量
        3. 更新分块的is_indexed状态
        """
        pass

