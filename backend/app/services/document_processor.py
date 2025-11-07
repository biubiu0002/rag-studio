"""
文档处理服务
提供文档解析和分块功能
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Chunk:
    """文档分块"""
    index: int
    content: str
    start_pos: int
    end_pos: int
    char_count: int
    token_count: Optional[int] = None
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "content": self.content,
            "start_pos": self.start_pos,
            "end_pos": self.end_pos,
            "char_count": self.char_count,
            "token_count": self.token_count,
            "metadata": self.metadata or {}
        }


class DocumentProcessor:
    """文档处理器"""
    
    @staticmethod
    def parse_txt(file_path: str) -> str:
        """解析TXT文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # 尝试其他编码
            with open(file_path, 'r', encoding='gbk') as f:
                return f.read()
    
    @staticmethod
    def parse_text(text: str) -> str:
        """清理和规范化文本"""
        # 移除多余空行
        lines = text.split('\n')
        lines = [line.strip() for line in lines if line.strip()]
        return '\n'.join(lines)
    
    @staticmethod
    def chunk_by_fixed_size(
        text: str,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        **kwargs
    ) -> List[Chunk]:
        """
        固定大小分块
        
        Args:
            text: 输入文本
            chunk_size: 分块大小（字符数）
            chunk_overlap: 重叠大小（字符数）
            
        Returns:
            分块列表
        """
        chunks = []
        text_length = len(text)
        
        start = 0
        index = 0
        
        while start < text_length:
            end = min(start + chunk_size, text_length)
            
            # 提取分块内容
            chunk_content = text[start:end]
            
            # 如果不是最后一个分块，尝试在句子边界结束
            if end < text_length:
                # 查找句子结束符
                sentence_endings = ['。', '！', '？', '\n', '.', '!', '?']
                for i in range(len(chunk_content) - 1, max(0, len(chunk_content) - 100), -1):
                    if chunk_content[i] in sentence_endings:
                        end = start + i + 1
                        chunk_content = text[start:end]
                        break
            
            # 创建分块对象
            chunk = Chunk(
                index=index,
                content=chunk_content.strip(),
                start_pos=start,
                end_pos=end,
                char_count=len(chunk_content),
                token_count=None,  # 后续可以添加token计数
                metadata={"chunk_method": "fixed_size"}
            )
            
            chunks.append(chunk)
            
            # 移动到下一个分块
            start = end - chunk_overlap
            index += 1
            
            # 避免无限循环
            if end >= text_length:
                break
        
        logger.info(f"文本分块完成: {len(chunks)} 个分块")
        return chunks
    
    @staticmethod
    def chunk_by_paragraph(text: str, **kwargs) -> List[Chunk]:
        """
        按段落分块
        
        Args:
            text: 输入文本
            
        Returns:
            分块列表
        """
        paragraphs = text.split('\n\n')
        chunks = []
        
        current_pos = 0
        for index, para in enumerate(paragraphs):
            para = para.strip()
            if not para:
                current_pos += 2  # 跳过空行
                continue
            
            chunk = Chunk(
                index=index,
                content=para,
                start_pos=current_pos,
                end_pos=current_pos + len(para),
                char_count=len(para),
                metadata={"chunk_method": "paragraph"}
            )
            
            chunks.append(chunk)
            current_pos += len(para) + 2
        
        logger.info(f"段落分块完成: {len(chunks)} 个分块")
        return chunks
    
    @staticmethod
    def chunk_by_sentence(
        text: str,
        max_sentences: int = 5,
        **kwargs
    ) -> List[Chunk]:
        """
        按句子分块
        
        Args:
            text: 输入文本
            max_sentences: 每个分块最多包含的句子数
            
        Returns:
            分块列表
        """
        import re
        
        # 简单的句子分割（中英文）
        sentence_pattern = r'[^。！？.!?]+[。！？.!?]+'
        sentences = re.findall(sentence_pattern, text)
        
        chunks = []
        current_pos = 0
        
        for i in range(0, len(sentences), max_sentences):
            chunk_sentences = sentences[i:i + max_sentences]
            chunk_content = ''.join(chunk_sentences)
            
            chunk = Chunk(
                index=len(chunks),
                content=chunk_content.strip(),
                start_pos=current_pos,
                end_pos=current_pos + len(chunk_content),
                char_count=len(chunk_content),
                metadata={"chunk_method": "sentence", "sentence_count": len(chunk_sentences)}
            )
            
            chunks.append(chunk)
            current_pos += len(chunk_content)
        
        logger.info(f"句子分块完成: {len(chunks)} 个分块")
        return chunks
    
    @classmethod
    def chunk_document(
        cls,
        text: str,
        method: str = "fixed_size",
        **kwargs
    ) -> List[Chunk]:
        """
        文档分块（统一入口）
        
        Args:
            text: 输入文本
            method: 分块方法 (fixed_size, paragraph, sentence)
            **kwargs: 方法特定参数
            
        Returns:
            分块列表
        """
        # 清理文本
        text = cls.parse_text(text)
        
        # 根据方法分块
        if method == "fixed_size":
            return cls.chunk_by_fixed_size(text, **kwargs)
        elif method == "paragraph":
            return cls.chunk_by_paragraph(text, **kwargs)
        elif method == "sentence":
            return cls.chunk_by_sentence(text, **kwargs)
        else:
            raise ValueError(f"不支持的分块方法: {method}")
    
    @staticmethod
    def estimate_tokens(text: str) -> int:
        """
        估算token数量
        中文: 1字 ≈ 1.5 tokens
        英文: 1词 ≈ 1 token
        """
        chinese_chars = len([c for c in text if '\u4e00' <= c <= '\u9fff'])
        other_chars = len(text) - chinese_chars
        
        # 粗略估算
        tokens = int(chinese_chars * 1.5 + other_chars / 4)
        return tokens


class DocumentParser:
    """文档解析器（支持多种格式）"""
    
    @staticmethod
    def parse_file(file_path: str) -> str:
        """
        解析文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            解析后的文本内容
        """
        path = Path(file_path)
        extension = path.suffix.lower()
        
        if extension == '.txt':
            return DocumentParser.parse_txt(file_path)
        elif extension == '.md':
            return DocumentParser.parse_markdown(file_path)
        elif extension == '.pdf':
            return DocumentParser.parse_pdf(file_path)
        elif extension == '.docx':
            return DocumentParser.parse_docx(file_path)
        else:
            raise ValueError(f"不支持的文件格式: {extension}")
    
    @staticmethod
    def parse_txt(file_path: str) -> str:
        """解析TXT文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            with open(file_path, 'r', encoding='gbk') as f:
                return f.read()
    
    @staticmethod
    def parse_markdown(file_path: str) -> str:
        """解析Markdown文件"""
        # 对于markdown，可以直接当文本读取
        # 或者使用markdown库转换为纯文本
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    @staticmethod
    def parse_pdf(file_path: str) -> str:
        """解析PDF文件"""
        try:
            import PyPDF2
            text = []
            with open(file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                for page in pdf_reader.pages:
                    text.append(page.extract_text())
            return '\n\n'.join(text)
        except ImportError:
            logger.warning("PyPDF2未安装，PDF解析功能不可用")
            return ""
        except Exception as e:
            logger.error(f"PDF解析失败: {e}")
            return ""
    
    @staticmethod
    def parse_docx(file_path: str) -> str:
        """解析DOCX文件"""
        try:
            import docx
            doc = docx.Document(file_path)
            paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
            return '\n\n'.join(paragraphs)
        except ImportError:
            logger.warning("python-docx未安装，DOCX解析功能不可用")
            return ""
        except Exception as e:
            logger.error(f"DOCX解析失败: {e}")
            return ""

