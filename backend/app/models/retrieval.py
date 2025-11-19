"""
检索相关数据模型
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class RetrievalResult:
    """检索结果"""
    doc_id: str
    chunk_id: str
    content: str
    score: float
    rank: int
    source: str  # "vector", "keyword", "hybrid"
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> dict:
        return {
            "doc_id": self.doc_id,
            "chunk_id": self.chunk_id,
            "content": self.content,
            "score": self.score,
            "rank": self.rank,
            "source": self.source,
            "metadata": self.metadata or {}
        }

